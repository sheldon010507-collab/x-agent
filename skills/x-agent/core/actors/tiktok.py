"""
tiktok.py - TikTok 动作 (comment, like, follow)

注意：TikTok 选择器变化频繁，本实现需要在实际环境中验证。
"""

import logging
from typing import Dict

from .base import BaseActor

logger = logging.getLogger(__name__)


class TikTokActor(BaseActor):
    PLATFORM = "tiktok"
    REQUIRES_LOGIN = True

    async def comment(self, url: str, content: str) -> Dict:
        self._check_login()
        self._check_quota("comment")
        content = self._vary(content)

        async with self.browser.page("tiktok") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self.safety.short_delay(3, 6)

                # 点击评论图标
                comment_btn = await page.wait_for_selector(
                    "[data-e2e='comment-icon'], button[aria-label*='Comment']",
                    timeout=15000,
                )
                await comment_btn.click()
                await self.safety.short_delay(2, 4)

                # 输入框
                editor = await page.wait_for_selector(
                    "[data-e2e='comment-input'], div[contenteditable='true']",
                    timeout=10000,
                )
                await editor.click()
                await editor.type(content, delay=50)
                await self.safety.short_delay(2, 4)

                # 提交
                submit = await page.wait_for_selector(
                    "[data-e2e='comment-post'], button[type='submit']",
                    timeout=8000,
                )
                await submit.click()
                await self.safety.short_delay(3, 6)

                return self._success("comment", url=url, content=content)
            except Exception as e:
                logger.error(f"TikTok comment failed: {e}")
                return self._failure("comment", str(e), url=url)

    async def like(self, url: str) -> Dict:
        self._check_login()
        self._check_quota("like")

        async with self.browser.page("tiktok") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self.safety.short_delay(3, 6)

                like_btn = await page.wait_for_selector(
                    "[data-e2e='like-icon'], button[aria-label*='Like']",
                    timeout=15000,
                )
                await like_btn.click()
                await self.safety.short_delay(1, 3)

                return self._success("like", url=url)
            except Exception as e:
                logger.error(f"TikTok like failed: {e}")
                return self._failure("like", str(e), url=url)

    async def follow(self, profile_url: str) -> Dict:
        self._check_login()
        self._check_quota("follow")

        async with self.browser.page("tiktok") as page:
            try:
                await page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
                await self.safety.short_delay(3, 6)

                follow_btn = await page.wait_for_selector(
                    "[data-e2e='follow-button'], button:has-text('Follow')",
                    timeout=15000,
                )
                await follow_btn.click()
                await self.safety.short_delay(2, 4)

                return self._success("follow", profile_url=profile_url)
            except Exception as e:
                logger.error(f"TikTok follow failed: {e}")
                return self._failure("follow", str(e), profile_url=profile_url)

    async def post(self, *args, **kwargs):
        return self._failure("post", "TikTok video upload not implemented (requires video file handling)")
