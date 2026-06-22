"""Shared Playwright browser utilities for X-Agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import Browser, BrowserContext, Playwright

DEFAULT_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-features=VizDisplayCompositor",
    "--window-size=1280,800",
]

REDDIT_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--disable-gpu",
    "--window-size=1920,1080",
]

STEALTH_JS = r"""
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
        {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''},
    ]
});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
if (!window.chrome) {
    window.chrome = {
        runtime: {
            PlatformArch: {ARM: 'arm', ARM64: 'arm64', X86_32: 'x86-32', X86_64: 'x86-64'},
            PlatformOs: {ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', WIN: 'win'},
        }
    };
}
const originalQuery = window.navigator.permissions ? window.navigator.permissions.query : null;
if (originalQuery) {
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({state: Notification.permission})
            : originalQuery(parameters);
}
Object.defineProperty(window, 'outerWidth', {get: () => window.innerWidth});
Object.defineProperty(window, 'outerHeight', {get: () => window.innerHeight + 88});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
"""


class BrowserPool:
    def __init__(self):
        self._contexts: Dict[str, BrowserContext] = {}
        self._browser: Optional[Browser] = None
        self._playwright: Optional[Playwright] = None

    async def start(self, *, headless: bool = True, launch_args: Optional[List[str]] = None):
        if self._playwright is None:
            self._playwright = (
                await __import__("playwright.async_api", fromlist=["async_playwright"])
                .async_playwright()
                .start()
            )
        if self._browser is None:
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                args=launch_args or DEFAULT_LAUNCH_ARGS,
            )
        return self._browser

    async def get_context(
        self,
        account_id: str,
        cookies_file: Optional[str] = None,
        *,
        user_agent: str = "",
        viewport: Optional[Dict] = None,
        locale: str = "en-US",
        timezone_id: str = "America/New_York",
        stealth: bool = True,
        launch_args: Optional[List[str]] = None,
        headless: bool = True,
        proxy: Optional[str] = None,
    ) -> BrowserContext:
        context = self._contexts.get(account_id)
        if context is not None:
            return context

        await self.start(headless=headless, launch_args=launch_args)
        if launch_args is not None:
            await self._browser.close()
            self._browser = await self._playwright.chromium.launch(
                headless=headless, args=launch_args
            )

        kwargs = {
            "user_agent": user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "viewport": viewport or {"width": 1280, "height": 800},
            "locale": locale,
            "timezone_id": timezone_id,
            "java_script_enabled": True,
        }
        if proxy:
            kwargs["proxy"] = {"server": proxy}
        context = await self._browser.new_context(**kwargs)
        if stealth:
            await context.add_init_script(STEALTH_JS)
        if cookies_file:
            path = Path(cookies_file)
            if path.exists():
                try:
                    await context.add_cookies(json.loads(path.read_text("utf-8")))
                    logger = __import__("logging").getLogger(__name__)
                    logger.info(f"Loaded {account_id} cookies from {cookies_file}")
                except Exception as exc:
                    __import__("logging").getLogger(__name__).debug(
                        f"Cookie load failed for {account_id}: {exc}"
                    )
        self._contexts[account_id] = context
        return context

    async def close_context(self, account_id: str) -> None:
        context = self._contexts.pop(account_id, None)
        if context is not None:
            await context.close()

    async def close(self) -> None:
        for context in list(self._contexts.values()):
            await context.close()
        self._contexts.clear()
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
