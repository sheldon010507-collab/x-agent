"""
x_dm_monitor.py - X/Twitter 私信监控模块（指纹浏览器版）

功能：
- 使用 Playwright 模拟指纹浏览器（Anti-bot 规避）
- 持久化 Session Cookies，避免每次重新登录
- 定时监控私信新回复，通过 Telegram 推送通知
- 支持手动查看私信列表

使用：
- 配置 X_USERNAME / X_PASSWORD 到 .env
- 调用 start_monitoring(interval=300) 启动后台监控
- 或直接调用 fetch_dms() 获取当前私信列表
"""

import asyncio
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import TimeoutError as PWTimeoutError
    from playwright.async_api import async_playwright

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


# ─── 指纹伪装 JS（注入到每个页面，规避 bot 检测）────────────────────────────
STEALTH_JS = """
// 1. 隐藏 webdriver 特征
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

// 2. 伪造 plugins（真实浏览器有插件，无头浏览器默认为空）
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
        {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''},
    ]
});

// 3. 语言设置
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});

// 4. chrome 对象（无头浏览器缺少此对象）
if (!window.chrome) {
    window.chrome = {
        app: {isInstalled: false, InstallState: {DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed'}, RunningState: {CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running'}},
        runtime: {OnInstalledReason: {CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update'}, OnRestartRequiredReason: {APP_UPDATE: 'app_update', GC_PRESSURE: 'gc_pressure', OS_UPDATE: 'os_update'}, PlatformArch: {ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64'}, PlatformNaclArch: {ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64'}, PlatformOs: {ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win'}, RequestUpdateCheckStatus: {NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available'}},
    };
}

// 5. Notification permissions
const originalQuery = window.navigator.permissions ? window.navigator.permissions.query : null;
if (originalQuery) {
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({state: Notification.permission}) :
            originalQuery(parameters)
    );
}

// 6. 修正 outerWidth/outerHeight（无头模式下与 inner 不匹配会被识别）
Object.defineProperty(window, 'outerWidth', {get: () => window.innerWidth});
Object.defineProperty(window, 'outerHeight', {get: () => window.innerHeight + 88});

// 7. 随机 deviceMemory
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});

// 8. 随机 hardwareConcurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
"""


class XDMMonitor:
    """X/Twitter 私信监控 - 指纹浏览器 + 会话持久化"""

    LOGIN_URL = "https://x.com/i/flow/login"
    DM_URL = "https://x.com/messages"

    def __init__(self, config, notify_callback: Optional[Callable] = None):
        """
        Args:
            config: Config 实例（需含 x_username / x_password）
            notify_callback: async 函数，签名 async def callback(new_dms: List[Dict])
        """
        self.config = config
        self.notify_callback = notify_callback
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.data_dir / "x_session_cookies.json"
        self.seen_file = self.data_dir / "dm_seen.json"
        self.seen_ids: set = self._load_seen()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

    # ─── 持久化 ────────────────────────────────────────────────────────────────

    def _load_seen(self) -> set:
        if self.seen_file.exists():
            try:
                return set(json.loads(self.seen_file.read_text()))
            except Exception:
                return set()
        return set()

    def _save_seen(self):
        self.seen_file.write_text(json.dumps(list(self.seen_ids)))

    def _load_cookies(self) -> Optional[list]:
        """加载保存的 Session Cookies（20小时内有效）"""
        if not self.session_file.exists():
            return None
        try:
            data = json.loads(self.session_file.read_text())
            saved_at = data.get("saved_at", "")
            if saved_at:
                age_hours = (
                    datetime.now() - datetime.fromisoformat(saved_at)
                ).total_seconds() / 3600
                if age_hours > 20:
                    logger.info("Session Cookies 已超过 20 小时，需要重新登录")
                    return None
            return data.get("cookies", [])
        except Exception:
            return None

    def _save_cookies(self, cookies: list):
        """保存 Session Cookies 到本地文件"""
        self.session_file.write_text(
            json.dumps(
                {
                    "saved_at": datetime.now().isoformat(),
                    "cookies": cookies,
                }
            )
        )
        logger.debug("Session Cookies 已保存")

    # ─── 浏览器上下文 ──────────────────────────────────────────────────────────

    async def _make_context(self, pw):
        """创建带指纹伪装的浏览器上下文"""
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                # 关键：关闭自动化标志位
                "--disable-blink-features=AutomationControlled",
                "--disable-features=VizDisplayCompositor",
                "--window-size=1280,800",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        # 注入指纹伪装脚本（在每个页面加载前执行）
        await context.add_init_script(STEALTH_JS)
        return browser, context

    # ─── 登录 ──────────────────────────────────────────────────────────────────

    async def _login(self, page, username: str, password: str) -> bool:
        """登录 X 账号（人工化延迟，减少机器人检测风险）"""
        try:
            await page.goto(self.LOGIN_URL, timeout=30000)
            await page.wait_for_selector('input[autocomplete="username"]', timeout=15000)

            # 随机延迟模拟人工输入
            await asyncio.sleep(random.uniform(0.8, 1.8))
            await page.fill('input[autocomplete="username"]', username)
            await asyncio.sleep(random.uniform(0.4, 0.9))
            await page.keyboard.press("Enter")

            # 等待密码框或额外验证框
            try:
                await page.wait_for_selector(
                    'input[name="password"], input[type="password"], '
                    'input[data-testid="ocfEnterTextTextInput"]',
                    timeout=10000,
                )
            except PWTimeoutError:
                logger.warning("等待密码框超时，可能遇到 Bot 验证")
                return False

            # 如果出现了额外验证步骤（手机号/邮箱）
            if await page.query_selector('input[data-testid="ocfEnterTextTextInput"]'):
                logger.warning("X 触发了额外验证（手机号/邮箱）—— 需要手动处理一次")
                return False

            await asyncio.sleep(random.uniform(0.5, 1.2))
            pw_selector = 'input[name="password"], input[type="password"]'
            await page.fill(pw_selector, password)
            await asyncio.sleep(random.uniform(0.4, 0.8))
            await page.keyboard.press("Enter")

            # 等待跳转到 home 或 messages
            await page.wait_for_url("https://x.com/**", timeout=20000)
            if "/i/flow/login" in page.url or "/login" in page.url:
                logger.warning("登录后仍在登录页，密码可能错误或触发了验证")
                return False

            await asyncio.sleep(random.uniform(1.5, 2.5))
            logger.info("✅ X 登录成功")
            return True

        except PWTimeoutError as e:
            logger.warning(f"登录超时: {e}")
            return False
        except Exception as e:
            logger.error(f"登录异常: {e}")
            return False

    # ─── 核心：获取私信 ────────────────────────────────────────────────────────

    async def fetch_dms(self) -> List[Dict]:
        """
        获取私信列表（最多 30 条会话）

        Returns:
            List of dicts: conv_id, sender, preview, is_unread, timestamp, url
        """
        if not HAS_PLAYWRIGHT:
            logger.warning("Playwright 未安装，无法监控私信")
            return []

        username = getattr(self.config, "x_username", None)
        password = getattr(self.config, "x_password", None)
        if not username or not password:
            logger.warning("X 账号未配置（X_USERNAME / X_PASSWORD）")
            return []

        dms = []
        async with async_playwright() as pw:
            browser, context = await self._make_context(pw)

            # 尝试恢复 Session
            saved_cookies = self._load_cookies()
            if saved_cookies:
                await context.add_cookies(saved_cookies)
                logger.info(f"已加载 {len(saved_cookies)} 个 Session Cookies")

            page = await context.new_page()

            try:
                # 直接访问私信页面
                await page.goto(self.DM_URL, timeout=25000)
                await asyncio.sleep(2)

                # 判断是否需要重新登录
                needs_login = (
                    "/i/flow/login" in page.url or "/login" in page.url or not saved_cookies
                )
                if needs_login:
                    logger.info("需要登录...")
                    if not await self._login(page, username, password):
                        return []
                    # 保存新 Cookies
                    cookies = await context.cookies()
                    self._save_cookies(cookies)
                    # 跳转到私信页
                    await page.goto(self.DM_URL, timeout=20000)
                    await asyncio.sleep(2)

                # 等待私信列表加载
                try:
                    await page.wait_for_selector('[data-testid="conversation"]', timeout=15000)
                except PWTimeoutError:
                    # 可能需要重新登录（Cookie 失效）
                    logger.info("私信列表加载失败，清除 Cookies 重新登录...")
                    self.session_file.unlink(missing_ok=True)
                    if not await self._login(page, username, password):
                        return []
                    cookies = await context.cookies()
                    self._save_cookies(cookies)
                    await page.goto(self.DM_URL, timeout=20000)
                    try:
                        await page.wait_for_selector('[data-testid="conversation"]', timeout=12000)
                    except PWTimeoutError:
                        logger.warning("私信列表仍无法加载，账号可能没有私信权限")
                        return []

                # 滚动加载更多会话
                for _ in range(2):
                    await page.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(0.8)

                # 提取会话列表
                conversations = await page.query_selector_all('[data-testid="conversation"]')
                logger.info(f"找到 {len(conversations)} 个私信会话")

                for conv in conversations[:30]:
                    try:
                        dm = await self._parse_conversation(conv)
                        if dm:
                            dms.append(dm)
                    except Exception as e:
                        logger.debug(f"解析会话失败: {e}")

                # 更新 Cookies
                cookies = await context.cookies()
                self._save_cookies(cookies)

            except Exception as e:
                logger.error(f"fetch_dms 异常: {e}")
            finally:
                await browser.close()

        logger.info(f"✅ 共获取 {len(dms)} 条私信会话")
        return dms

    async def _parse_conversation(self, conv) -> Optional[Dict]:
        """解析单个私信会话 DOM 元素"""
        # 会话链接（含会话 ID）
        link = await conv.query_selector('a[href*="/messages/"]')
        href = await link.get_attribute("href") if link else ""
        conv_id = href.rsplit("/", 1)[-1] if "/" in href else ""

        # 发送者名称（尝试多个选择器）
        sender = ""
        for sel in [
            '[data-testid="conversationParticipants"] span',
            'div[dir="ltr"] > span > span',
            'span[class*="css-1jxf684"]',
        ]:
            el = await conv.query_selector(sel)
            if el:
                sender = (await el.inner_text()).strip()
                if sender:
                    break

        # 消息预览
        preview = ""
        for sel in [
            '[data-testid="messageEntry"]',
            'div[dir="auto"] span',
        ]:
            el = await conv.query_selector(sel)
            if el:
                preview = (await el.inner_text()).strip()
                if preview:
                    break

        # 未读标记
        unread_badge = await conv.query_selector(
            '[data-testid="unreadCount"], [class*="UnreadBadge"], [class*="unread"]'
        )
        is_unread = unread_badge is not None

        # 时间戳
        time_el = await conv.query_selector("time")
        timestamp = (
            await time_el.get_attribute("datetime") if time_el else datetime.now().isoformat()
        )

        if not sender and not preview:
            return None

        return {
            "conv_id": conv_id or f"dm_{hash(href)}",
            "sender": sender[:60] or "unknown",
            "preview": preview[:200],
            "is_unread": is_unread,
            "timestamp": timestamp,
            "url": f"https://x.com{href}" if href and href.startswith("/") else self.DM_URL,
        }

    # ─── 新消息检测 ────────────────────────────────────────────────────────────

    async def check_new_messages(self) -> List[Dict]:
        """
        检查新私信（未在 seen_ids 中的会话）

        Returns:
            新发现的私信列表
        """
        dms = await self.fetch_dms()
        new_dms = []
        for dm in dms:
            cid = dm.get("conv_id", "")
            if cid and cid not in self.seen_ids:
                new_dms.append(dm)
                self.seen_ids.add(cid)
        if new_dms:
            self._save_seen()
            logger.info(f"🆕 发现 {len(new_dms)} 条新私信")
        return new_dms

    # ─── 后台监控循环 ──────────────────────────────────────────────────────────

    async def _monitor_loop(self, interval: int):
        """后台监控循环（每 interval 秒检查一次）"""
        logger.info(f"🔔 私信监控循环启动，间隔 {interval}s")
        while self._running:
            try:
                new_dms = await self.check_new_messages()
                if new_dms and self.notify_callback:
                    await self.notify_callback(new_dms)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
            # 加上随机抖动，防止固定间隔被检测
            jitter = random.randint(-30, 30)
            await asyncio.sleep(max(60, interval + jitter))

    def start_monitoring(self, interval: int = 300) -> bool:
        """
        启动后台私信监控

        Args:
            interval: 检查间隔（秒），默认 300s (5 分钟)

        Returns:
            True 表示成功启动，False 表示已在运行
        """
        if self._running:
            logger.info("监控已在运行中")
            return False
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info(f"✅ X 私信监控已启动（间隔 {interval}s）")
        return True

    def stop_monitoring(self) -> bool:
        """
        停止后台私信监控

        Returns:
            True 表示成功停止，False 表示原本未在运行
        """
        if not self._running:
            return False
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
        logger.info("🛑 X 私信监控已停止")
        return True

    @property
    def is_running(self) -> bool:
        """监控是否正在运行"""
        return self._running

    def clear_session(self):
        """清除保存的 Session（下次会重新登录）"""
        self.session_file.unlink(missing_ok=True)
        logger.info("Session Cookies 已清除")

    def reset_seen(self):
        """重置已读记录（下次 check 会把所有当前私信当作新消息）"""
        self.seen_ids.clear()
        self.seen_file.unlink(missing_ok=True)
        logger.info("DM 已读记录已重置")
