"""
x.py - X/Twitter 动作执行 (post, comment, like, retweet)

所有动作通过 Playwright 模拟用户操作，需要登录会话。
"""

import logging
from typing import Dict

from .base import BaseActor

logger = logging.getLogger(__name__)


class XActor(BaseActor):
    PLATFORM = "x"
    REQUIRES_LOGIN = True

    HOME_URL = "https://x.com/home"
    COMPOSE_URL = "https://x.com/compose/post"

    async def post(self, content: str) -> Dict:
        """发布一条推文"""
        self._check_login()
        self._check_quota("post")

        content = self._vary(content)

        async with self.browser.page("x") as page:
            try:
                await page.goto(self.HOME_URL, wait_until="domcontentloaded", timeout=30000)
                await self.safety.short_delay(2, 5)

                # 等待并点击发布框
                await page.wait_for_selector("[data-testid='SideNav_NewTweet_Button'], [data-testid='tweetTextarea_0']", timeout=15000)
                btn = await page.query_selector("[data-testid='SideNav_NewTweet_Button']")
                if btn:
                    await btn.click()
                    await self.safety.short_delay(1, 3)

                # 输入推文
                editor = await page.wait_for_selector("[data-testid='tweetTextarea_0']", timeout=10000)
                await editor.click()
                await editor.type(content, delay=50)  # 模拟人类打字
                await self.safety.short_delay(2, 4)

                # 点击发送
                tweet_btn = await page.wait_for_selector(
                    "[data-testid='tweetButton'], [data-testid='tweetButtonInline']",
                    timeout=10000,
                )
                await tweet_btn.click()
                await self.safety.short_delay(3, 6)

                return self._success("post", content=content)
            except Exception as e:
                logger.error(f"X post failed: {e}")
                return self._failure("post", str(e), content=content)

    async def comment(self, url: str, content: str) -> Dict:
        """在指定推文下评论"""
        self._check_login()
        self._check_quota("comment")

        content = self._vary(content)

        async with self.browser.page("x") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self.safety.short_delay(2, 5)

                # 点击 Reply 按钮
                reply_btn = await page.wait_for_selector("[data-testid='reply']", timeout=10000)
                await reply_btn.click()
                await self.safety.short_delay(1, 3)

                # 输入评论
                editor = await page.wait_for_selector("[data-testid='tweetTextarea_0']", timeout=10000)
                await editor.click()
                await editor.type(content, delay=50)
                await self.safety.short_delay(2, 4)

                # 发送
                send_btn = await page.wait_for_selector("[data-testid='tweetButton']", timeout=10000)
                await send_btn.click()
                await self.safety.short_delay(3, 6)

                return self._success("comment", url=url, content=content)
            except Exception as e:
                logger.error(f"X comment failed: {e}")
                return self._failure("comment", str(e), url=url)

    async def like(self, url: str) -> Dict:
        """给指定推文点赞"""
        self._check_login()
        self._check_quota("like")

        async with self.browser.page("x") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self.safety.short_delay(2, 5)

                like_btn = await page.wait_for_selector("[data-testid='like']", timeout=10000)
                await like_btn.click()
                await self.safety.short_delay(1, 3)

                return self._success("like", url=url)
            except Exception as e:
                logger.error(f"X like failed: {e}")
                return self._failure("like", str(e), url=url)

    async def retweet(self, url: str, with_quote: str = None) -> Dict:
        """转发指定推文（可选带引用）"""
        self._check_login()
        self._check_quota("retweet")

        async with self.browser.page("x") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self.safety.short_delay(2, 5)

                rt_btn = await page.wait_for_selector("[data-testid='retweet']", timeout=10000)
                await rt_btn.click()
                await self.safety.short_delay(1, 2)

                if with_quote:
                    # 引用转发
                    quote_btn = await page.wait_for_selector(
                        "[data-testid='quoteRetweet'], [role='menuitem']:has-text('Quote')",
                        timeout=8000,
                    )
                    await quote_btn.click()
                    await self.safety.short_delay(1, 3)
                    editor = await page.wait_for_selector("[data-testid='tweetTextarea_0']", timeout=10000)
                    await editor.type(self._vary(with_quote), delay=50)
                    await self.safety.short_delay(2, 4)
                    send_btn = await page.wait_for_selector("[data-testid='tweetButton']", timeout=10000)
                    await send_btn.click()
                else:
                    # 简单转发
                    confirm_btn = await page.wait_for_selector(
                        "[data-testid='retweetConfirm']", timeout=8000
                    )
                    await confirm_btn.click()

                await self.safety.short_delay(3, 6)
                return self._success("retweet", url=url, with_quote=with_quote)
            except Exception as e:
                logger.error(f"X retweet failed: {e}")
                return self._failure("retweet", str(e), url=url)
