"""
manager.py - Playwright 浏览器生命周期管理

提供共享浏览器实例和按平台隔离的 context（带会话）
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from .session import SessionManager
from .stealth import STEALTH_INIT_SCRIPT, random_context_options

logger = logging.getLogger(__name__)


class BrowserManager:
    """浏览器实例管理器（懒加载）"""

    def __init__(self, headless: bool = True, sessions_dir: Optional[Path] = None):
        self.headless = headless
        self._playwright = None
        self._browser = None
        self.session_mgr = SessionManager(sessions_dir)

    async def start(self):
        """启动 playwright 和浏览器"""
        if self._browser is not None:
            return
        try:
            from playwright.async_api import async_playwright
        except ImportError as e:
            raise ImportError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            ) from e

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        logger.info(f"Browser started (headless={self.headless})")

    async def stop(self):
        """关闭浏览器和 playwright"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser stopped")

    @asynccontextmanager
    async def context(self, platform: str, use_session: bool = True):
        """
        获取一个平台的 browser context（带会话）

        Args:
            platform: 平台名 (x/tiktok/youtube/reddit/hackernews/google_trends)
            use_session: 是否加载已保存的会话
        """
        await self.start()

        opts = random_context_options()
        session_path = self.session_mgr.get_session(platform) if use_session else None
        if session_path:
            opts["storage_state"] = str(session_path)

        ctx = await self._browser.new_context(**opts)
        await ctx.add_init_script(STEALTH_INIT_SCRIPT)

        try:
            yield ctx
        finally:
            await ctx.close()

    @asynccontextmanager
    async def page(self, platform: str, use_session: bool = True):
        """快捷：获取一个 page（封装 context + page 创建）"""
        async with self.context(platform, use_session=use_session) as ctx:
            page = await ctx.new_page()
            try:
                yield page
            finally:
                await page.close()

    async def save_session(self, platform: str, context, metadata: dict = None):
        """保存当前 context 的会话状态到文件"""
        path = self.session_mgr.session_path(platform)
        await context.storage_state(path=str(path))
        if metadata:
            self.session_mgr.save_session_metadata(platform, metadata)
        logger.info(f"Session saved for {platform}: {path}")

    @asynccontextmanager
    async def login_session(self, platform: str):
        """
        登录会话上下文（强制 headed 模式）

        用法:
            async with mgr.login_session("x") as page:
                await page.goto(LOGIN_URL)
                # 用户手动登录...
                # 退出 with 时自动保存会话
        """
        # 强制启动 headed 浏览器（不影响主 _browser）
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=False)
        opts = random_context_options()
        ctx = await browser.new_context(**opts)
        await ctx.add_init_script(STEALTH_INIT_SCRIPT)
        page = await ctx.new_page()
        try:
            yield page
            # 登录完成后保存
            await self.save_session(platform, ctx, metadata={"login_method": "manual"})
        finally:
            await ctx.close()
            await browser.close()
            await pw.stop()
