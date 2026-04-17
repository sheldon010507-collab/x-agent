"""
x.py - X/Twitter scraper (Playwright)

通过浏览器访问 X 的 explore/search 页面抓取热门推文。
需要登录会话才能看到完整内容。
"""

import logging
import re
import urllib.parse
from typing import Dict, List

from .base import BaseScraper

logger = logging.getLogger(__name__)


# Niche → 搜索关键词映射
NICHE_QUERIES = {
    "ai_tools": "AI tools OR ChatGPT OR Claude min_faves:100",
    "crypto": "crypto OR bitcoin OR ethereum min_faves:200",
    "fitness": "fitness OR workout min_faves:100",
    "beauty": "skincare OR makeup min_faves:100",
    "humor": "meme min_faves:500",
    "adult": "OnlyFans OR adult min_faves:50",
    "general": "trending min_faves:1000",
}


class XScraper(BaseScraper):
    PLATFORM = "x"
    REQUIRES_LOGIN = True

    async def fetch_trends(
        self, niche: str, days: int = 7, limit: int = 20, query: str = None
    ) -> Dict:
        if not self.browser.session_mgr.has_session("x"):
            return self._empty_result(
                niche, error="X requires login. Run: x-agent login --platform x"
            )

        # 用户自定义 query 优先，否则用 niche 默认查询
        search_query = query if query else NICHE_QUERIES.get(niche, niche)
        encoded = urllib.parse.quote(search_query)
        search_url = f"https://x.com/search?q={encoded}&src=typed_query&f=top"

        async with self.browser.page("x") as page:
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                # 等待推文加载
                await page.wait_for_selector("article[data-testid='tweet']", timeout=15000)
                # 滚动加载更多
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 1500)")
                    await page.wait_for_timeout(1500)

                posts = await self._extract_tweets(page, limit)
                return self._wrap_result(niche, posts, query=search_query)
            except Exception as e:
                logger.error(f"X scrape failed: {e}")
                return self._empty_result(niche, error=str(e))

    async def _extract_tweets(self, page, limit: int) -> List[Dict]:
        """从页面提取推文数据"""
        tweets = await page.evaluate(
            """(limit) => {
                const articles = document.querySelectorAll("article[data-testid='tweet']");
                const results = [];
                for (let i = 0; i < Math.min(articles.length, limit); i++) {
                    const a = articles[i];
                    const textEl = a.querySelector("[data-testid='tweetText']");
                    const userEl = a.querySelector("[data-testid='User-Name'] a");
                    const linkEl = a.querySelector("a[href*='/status/']");
                    const timeEl = a.querySelector("time");

                    const stats = {};
                    a.querySelectorAll("[data-testid$='-count']").forEach(el => {
                        const key = el.getAttribute('data-testid').replace('-count', '');
                        stats[key] = el.textContent.trim();
                    });

                    results.push({
                        title: textEl ? textEl.innerText : '',
                        text: textEl ? textEl.innerText : '',
                        author: userEl ? userEl.innerText : '',
                        url: linkEl ? 'https://x.com' + linkEl.getAttribute('href') : '',
                        time: timeEl ? timeEl.getAttribute('datetime') : '',
                        replies: stats.reply || '0',
                        retweets: stats.retweet || '0',
                        likes: stats.like || '0',
                        views: stats.views || '0',
                    });
                }
                return results;
            }""",
            limit,
        )

        # 把字符串数字转成 int 用于 score
        for t in tweets:
            t["score"] = self._parse_count(t.get("likes", "0"))

        return tweets

    @staticmethod
    def _parse_count(text: str) -> int:
        """解析 X 的数字文本：'1.2K' → 1200, '3.4M' → 3400000"""
        if not text:
            return 0
        text = text.strip().upper().replace(",", "")
        m = re.match(r"^([\d.]+)([KMB])?$", text)
        if not m:
            try:
                return int(float(text))
            except ValueError:
                return 0
        num, suffix = m.groups()
        try:
            n = float(num)
        except ValueError:
            return 0
        multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(suffix, 1)
        return int(n * multiplier)
