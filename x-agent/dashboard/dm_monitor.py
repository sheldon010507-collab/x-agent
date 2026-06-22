"""
dm_monitor.py — 多平台 DM/消息监控模块

支持：
- X/Twitter 私信监控（复用 x_dm_monitor 的 Playwright 能力）
- Reddit 私信监控（通过 Playwright 登录态 + inbox 页面抓取）

Dashboard 通过 ``/api/dm/x`` 和 ``/api/dm/reddit`` 调用。
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ─── 数据模型 ────────────────────────────────────────────────────────────


@dataclass
class DMMessage:
    """统一 DM 消息格式"""

    platform: str
    conversation_id: str
    sender: str
    preview: str
    is_from_me: bool
    timestamp: str
    url: str
    unread: bool = False
    raw: Dict = field(default_factory=dict)


# ─── X/Twitter DM 监控 ──────────────────────────────────────────────────


class XDMMonitor:
    """X/Twitter 私信监控 — 基于 Playwright + 持久化 Cookie"""

    DM_URL = "https://x.com/messages"
    LOGIN_URL = "https://x.com/i/flow/login"

    def __init__(self, username: str = "", password: str = "", data_dir: str = "data"):
        self.username = username or os.environ.get("X_USERNAME", "")
        self.password = password or os.environ.get("X_PASSWORD", "")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.data_dir / "x_session_cookies.json"
        self._playwright_available = False
        try:
            from playwright.async_api import async_playwright

            self._async_playwright = async_playwright
            self._playwright_available = True
        except ImportError:
            self._async_playwright = None

    async def fetch_dms(self, limit: int = 30) -> List[DMMessage]:
        if not self._playwright_available or not self.username or not self.password:
            return []

        try:
            from playwright.async_api import TimeoutError as PWTimeoutError

            HAS_TIMEOUT = True
        except ImportError:
            HAS_TIMEOUT = False

            class PWTimeoutError(Exception):
                pass

        dms: List[DMMessage] = []
        try:
            async with self._async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=VizDisplayCompositor",
                        "--window-size=1280,800",
                    ],
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                    locale="en-US",
                    timezone_id="America/New_York",
                )
                # 注入 stealth JS（与 x_dm_monitor 一致）
                await context.add_init_script(self._stealth_js())

                # 加载已有 Cookie
                if self.session_file.exists():
                    try:
                        saved = json.loads(self.session_file.read_text())
                        cookies = saved.get("cookies", [])
                        if cookies:
                            age_hours = (
                                datetime.now() - datetime.fromisoformat(saved.get("saved_at", ""))
                            ).total_seconds() / 3600
                            if age_hours < 20:
                                await context.add_cookies(cookies)
                                logger.info(f"Loaded {len(cookies)} X session cookies")
                    except Exception as e:
                        logger.debug(f"Cookie load failed: {e}")

                page = await context.new_page()
                needs_login = False

                try:
                    await page.goto(self.DM_URL, timeout=25000)
                    await asyncio_sleep(2)
                    needs_login = "/i/flow/login" in page.url or "/login" in page.url
                except Exception:
                    needs_login = True

                if needs_login:
                    logger.info("X DM: need login")
                    if not await self._login_x(page):
                        await browser.close()
                        return []
                    cookies = await context.cookies()
                    self.session_file.write_text(
                        json.dumps(
                            {
                                "saved_at": datetime.now().isoformat(),
                                "cookies": cookies,
                            }
                        )
                    )
                    await page.goto(self.DM_URL, timeout=20000)
                    await asyncio_sleep(2)
                    try:
                        if HAS_TIMEOUT:
                            await page.wait_for_selector(
                                '[data-testid="conversation"]', timeout=15000
                            )
                    except Exception:
                        logger.warning("X DM: conversation list not loaded after login")
                        await browser.close()
                        return []

                # 提取会话列表
                convs = await page.query_selector_all('[data-testid="conversation"]')
                logger.info(f"X DM: found {len(convs)} conversations")
                for conv in convs[:limit]:
                    try:
                        dm = await self._parse_x_conversation(conv)
                        if dm:
                            dms.append(dm)
                    except Exception:
                        continue

                cookies = await context.cookies()
                self.session_file.write_text(
                    json.dumps(
                        {
                            "saved_at": datetime.now().isoformat(),
                            "cookies": cookies,
                        }
                    )
                )
                await browser.close()
        except Exception as e:
            logger.error(f"X DM fetch error: {e}")

        return dms

    async def _login_x(self, page) -> bool:
        try:
            await page.goto(self.LOGIN_URL, timeout=30000)
            await page.wait_for_selector('input[autocomplete="username"]', timeout=15000)
            await asyncio_sleep(random_uniform(0.8, 1.5))
            await page.fill('input[autocomplete="username"]', self.username)
            await asyncio_sleep(random_uniform(0.4, 0.9))
            await page.keyboard.press("Enter")
            try:
                await page.wait_for_selector(
                    'input[name="password"], input[type="password"]', timeout=10000
                )
            except Exception:
                logger.warning("X DM: extra verification triggered")
                return False
            await asyncio_sleep(random_uniform(0.5, 1.0))
            await page.fill('input[name="password"], input[type="password"]', self.password)
            await asyncio_sleep(random_uniform(0.4, 0.8))
            await page.keyboard.press("Enter")
            await page.wait_for_url("https://x.com/**", timeout=20000)
            if "/login" in page.url or "/i/flow/login" in page.url:
                return False
            await asyncio_sleep(1)
            logger.info("X DM: login OK")
            return True
        except Exception as e:
            logger.error(f"X DM login failed: {e}")
            return False

    async def _parse_x_conversation(self, el) -> Optional[DMMessage]:
        """解析 X 私信会话卡片"""
        try:
            name_el = await el.query_selector('[data-testid="DM-Conversation-title"]')
            name = (await name_el.inner_text()).strip() if name_el else "Unknown"

            text_el = await el.query_selector(
                '[data-testid="DM-Conversation-lastMessage"], '
                '[data-testid="conversation-message-preview"]'
            )
            preview = (await text_el.inner_text()).strip() if text_el else ""

            unread_el = await el.query_selector('[data-testid="DM-unreadBadge"], .unread')
            unread = unread_el is not None

            time_el = await el.query_selector("time")
            ts = ""
            if time_el:
                ts = await time_el.get_attribute("datetime") or ""

            url = ""
            link_el = await el.query_selector('a[href*="/messages/"]')
            if link_el:
                href = await link_el.get_attribute("href")
                if href:
                    url = f"https://x.com{href}" if href.startswith("/") else href

            conv_id = url.rsplit("/", 1)[-1] if url else f"x_{id(el)}"

            return DMMessage(
                platform="x",
                conversation_id=conv_id,
                sender=name,
                preview=preview[:200],
                is_from_me=preview.startswith("You:"),
                timestamp=ts,
                url=url,
                unread=unread,
            )
        except Exception:
            return None

    @staticmethod
    def _stealth_js() -> str:
        return r"""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {
            get: () => [{name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer',
                         description: 'Portable Document Format'}]
        });
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        if (!window.chrome) { window.chrome = {runtime: {PlatformOs: {WIN:'win',MAC:'mac'}}} }
        Object.defineProperty(window, 'outerWidth', {get: () => window.innerWidth});
        Object.defineProperty(window, 'outerHeight', {get: () => window.innerHeight + 88});
        """


# ─── Reddit 私信(消息)监控 ───────────────────────────────────────────────


class RedditDMMonitor:
    """Reddit 消息/私信监控 — 通过 Playwright 登录态访问 inbox"""

    INBOX_URL = "https://www.reddit.com/messages/"

    def __init__(self, accounts: Optional[List[Dict]] = None, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.accounts = accounts or []
        self._playwright_available = False
        try:
            from playwright.async_api import async_playwright

            self._async_playwright = async_playwright
            self._playwright_available = True
        except ImportError:
            self._async_playwright = None

    async def fetch_dms(self, account_index: int = 0, limit: int = 20) -> List[DMMessage]:
        if not self._playwright_available or not self.accounts:
            return []

        acc = self.accounts[min(account_index, len(self.accounts) - 1)]
        cookies_path = Path(acc.get("cookies_file", ""))
        if not cookies_path.exists():
            return []

        try:
            import asyncio
            import random as _rnd

            async with self._async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--window-size=1920,1080",
                    ],
                )
                context = await browser.new_context(
                    user_agent=acc.get("user_agent")
                    or random.choice(
                        [
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36",
                        ]
                    ),
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    timezone_id="America/New_York",
                )
                await context.add_init_script(
                    RedditPlaywrightCrawler.STEALTH_JS
                    if "RedditPlaywrightCrawler" in globals()
                    else "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                )
                cookies = json.loads(cookies_path.read_text())
                await context.add_cookies(cookies)
                page = await context.new_page()

                await page.goto(self.INBOX_URL, timeout=25000)
                await asyncio_sleep(2)

                if "/login" in page.url or "/i/flow/login" in page.url:
                    logger.info(f"[{acc.get('username')}] Reddit cookie expired, skip DM")
                    await browser.close()
                    return []

                # 等待加载
                for sel in ['[data-testid="message"]', "shreddit-post", ".thing"]:
                    try:
                        await page.wait_for_selector(sel, timeout=8000)
                        break
                    except Exception:
                        continue

                # 提取消息列表
                dms: List[DMMessage] = []
                msg_els = await page.query_selector_all(
                    '[data-testid="message"], .thing[data-type="message"], shreddit-post'
                )
                for el in msg_els[:limit]:
                    try:
                        dm = await self._parse_reddit_message(el, acc.get("id", "reddit"))
                        if dm:
                            dms.append(dm)
                    except Exception:
                        continue

                # 刷新 cookie
                fresh = await context.cookies()
                cookies_path.write_text(json.dumps(fresh))
                await browser.close()
                return dms
        except Exception as e:
            logger.error(f"Reddit DM fetch error ({acc.get('id')}): {e}")
            return []

    async def _parse_reddit_message(self, el, account_id: str) -> Optional[DMMessage]:
        try:
            sender_el = await el.query_selector('[data-testid="message-author"], a[href*="/user/"]')
            sender = (await sender_el.inner_text()).strip() if sender_el else "Unknown"

            preview_el = await el.query_selector(
                '[data-testid="message-body"], .usertext-body, [data-testid="post-content"]'
            )
            preview = (await preview_el.inner_text()).strip()[:200] if preview_el else ""

            time_el = await el.query_selector("time")
            ts = await time_el.get_attribute("datetime") if time_el else ""

            unread_el = await el.query_selector('.new, [data-testid="unread"]')
            unread = unread_el is not None

            url_el = await el.query_selector('a[href*="/message/"]')
            url = ""
            if url_el:
                href = await url_el.get_attribute("href")
                url = (
                    f"https://www.reddit.com{href}"
                    if href and href.startswith("/")
                    else (href or "")
                )

            return DMMessage(
                platform="reddit",
                conversation_id=url.rsplit("/", 1)[-1] or f"rd_{id(el)}",
                sender=sender,
                preview=preview,
                is_from_me=False,
                timestamp=ts or datetime.now().isoformat(),
                url=url,
                unread=unread,
                account_id=account_id,
            )
        except Exception:
            return None


# ─── 统一 DM 聚合器 ─────────────────────────────────────────────────────


class AggregatedDMMonitor:
    """聚合 X + Reddit 的 DM 监控"""

    def __init__(
        self,
        x_monitor: Optional[XDMMonitor] = None,
        reddit_monitor: Optional[RedditDMMonitor] = None,
    ):
        self.x = x_monitor or XDMMonitor()
        self.reddit = reddit_monitor or RedditDMMonitor()

    async def fetch_all(self, limit_per_platform: int = 20) -> List[Dict[str, Any]]:
        import asyncio

        results = await asyncio.gather(
            self.x.fetch_dms(limit=limit_per_platform),
            self.reddit.fetch_dms(limit=limit_per_platform),
            return_exceptions=True,
        )
        messages: List[Dict[str, Any]] = []
        for r in results:
            if isinstance(r, Exception):
                continue
            for dm in r:
                messages.append(
                    {
                        "platform": dm.platform,
                        "conversation_id": dm.conversation_id,
                        "sender": dm.sender,
                        "preview": dm.preview,
                        "is_from_me": dm.is_from_me,
                        "timestamp": dm.timestamp,
                        "url": dm.url,
                        "unread": dm.unread,
                        "raw": dm.raw,
                    }
                )
        messages.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
        return messages


# ─── 工具 ───────────────────────────────────────────────────────────────


def asyncio_sleep(seconds: float):
    import asyncio

    return asyncio.sleep(seconds)


def random_uniform(a: float, b: float) -> float:
    import random

    return random.uniform(a, b)
