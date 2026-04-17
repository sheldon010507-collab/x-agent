"""
youtube.py - YouTube 动作 (comment, like, subscribe)
"""

import logging
from typing import Dict

from .base import BaseActor

logger = logging.getLogger(__name__)


class YouTubeActor(BaseActor):
    PLATFORM = "youtube"
    REQUIRES_LOGIN = True

    async def comment(self, url: str, content: str) -> Dict:
        self._check_login()
        self._check_quota("comment")
        content = self._vary(content)

        async with self.browser.page("youtube") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # 滚到评论区加载
                await page.evaluate("window.scrollTo(0, 800)")
                await self.safety.short_delay(3, 6)

                placeholder = await page.wait_for_selector(
                    "ytd-comment-simplebox-renderer #placeholder-area, #simple-box",
                    timeout=15000,
                )
                await placeholder.click()
                await self.safety.short_delay(1, 3)

                editor = await page.wait_for_selector(
                    "#contenteditable-root", timeout=10000
                )
                await editor.click()
                await editor.type(content, delay=50)
                await self.safety.short_delay(2, 4)

                submit = await page.wait_for_selector(
                    "#submit-button button, ytd-button-renderer#submit-button",
                    timeout=8000,
                )
                await submit.click()
                await self.safety.short_delay(3, 6)

                return self._success("comment", url=url, content=content)
            except Exception as e:
                logger.error(f"YouTube comment failed: {e}")
                return self._failure("comment", str(e), url=url)

    async def like(self, url: str) -> Dict:
        self._check_login()
        self._check_quota("like")

        async with self.browser.page("youtube") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self.safety.short_delay(3, 6)

                like_btn = await page.wait_for_selector(
                    "button[aria-label*='like this video'], #segmented-like-button button",
                    timeout=15000,
                )
                await like_btn.click()
                await self.safety.short_delay(1, 3)
                return self._success("like", url=url)
            except Exception as e:
                logger.error(f"YouTube like failed: {e}")
                return self._failure("like", str(e), url=url)

    async def subscribe(self, channel_url: str) -> Dict:
        self._check_login()
        self._check_quota("subscribe")

        async with self.browser.page("youtube") as page:
            try:
                await page.goto(channel_url, wait_until="domcontentloaded", timeout=30000)
                await self.safety.short_delay(3, 6)

                btn = await page.wait_for_selector(
                    "ytd-subscribe-button-renderer button, button:has-text('Subscribe')",
                    timeout=15000,
                )
                await btn.click()
                await self.safety.short_delay(2, 4)
                return self._success("subscribe", channel_url=channel_url)
            except Exception as e:
                logger.error(f"YouTube subscribe failed: {e}")
                return self._failure("subscribe", str(e), channel_url=channel_url)

    async def post(self, *args, **kwargs):
        return self._failure("post", "YouTube video upload not implemented (requires video file handling)")
