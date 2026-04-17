"""
tiktok.py - TikTok scraper (Playwright)

抓取 TikTok 探索页/搜索页的热门视频。
注意：TikTok 反爬较强，可能需要登录会话才能看到完整数据。
"""

import logging
import urllib.parse
from typing import Dict, List

from .base import BaseScraper

logger = logging.getLogger(__name__)


NICHE_HASHTAGS = {
    "ai_tools": "ai",
    "crypto": "crypto",
    "fitness": "fitness",
    "beauty": "beauty",
    "humor": "funny",
    "adult": "lingerie",
    "general": "fyp",
}


class TikTokScraper(BaseScraper):
    PLATFORM = "tiktok"
    REQUIRES_LOGIN = False  # 公开页面可访问，但登录后数据更完整

    async def fetch_trends(
        self, niche: str, days: int = 7, limit: int = 20, query: str = None
    ) -> Dict:
        # 用户自定义 query → 走搜索；否则走标签页
        if query:
            url = f"https://www.tiktok.com/search?q={urllib.parse.quote(query)}"
            tag = query
        else:
            tag = NICHE_HASHTAGS.get(niche, niche)
            url = f"https://www.tiktok.com/tag/{urllib.parse.quote(tag)}"

        async with self.browser.page("tiktok") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # TikTok 用懒加载，等视频卡片
                await page.wait_for_selector(
                    "[data-e2e='challenge-item'], div[class*='DivItemContainer']",
                    timeout=15000,
                )
                # 滚动加载
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 1500)")
                    await page.wait_for_timeout(2000)

                posts = await self._extract_videos(page, limit)
                return self._wrap_result(niche, posts, query=tag)
            except Exception as e:
                logger.error(f"TikTok scrape failed: {e}")
                return self._empty_result(niche, error=str(e))

    async def _extract_videos(self, page, limit: int) -> List[Dict]:
        videos = await page.evaluate(
            """(limit) => {
                // TikTok DOM 经常变化，多种选择器尝试
                const items = document.querySelectorAll(
                    "[data-e2e='challenge-item'], div[class*='DivItemContainer'] a[href*='/video/']"
                );
                const results = [];
                const seen = new Set();
                for (const item of items) {
                    if (results.length >= limit) break;
                    const link = item.querySelector("a[href*='/video/']") || (item.tagName === 'A' ? item : null);
                    if (!link) continue;
                    const href = link.href;
                    if (seen.has(href)) continue;
                    seen.add(href);

                    const titleEl = item.querySelector("[data-e2e='challenge-item-desc'], [class*='Desc']");
                    const authorEl = item.querySelector("[data-e2e='challenge-item-username'], a[href^='/@']");
                    const likesEl = item.querySelector("strong[data-e2e='video-views'], strong");

                    results.push({
                        title: titleEl ? titleEl.innerText : '',
                        text: titleEl ? titleEl.innerText : '',
                        url: href,
                        author: authorEl ? authorEl.innerText : '',
                        engagement: likesEl ? likesEl.innerText : '0',
                        score: 0,
                    });
                }
                return results;
            }""",
            limit,
        )
        return videos
