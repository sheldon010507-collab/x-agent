"""
youtube.py - YouTube scraper (Playwright)

抓取 YouTube 搜索/Trending 页面的热门视频。
"""

import logging
import urllib.parse
from typing import Dict, List

from .base import BaseScraper

logger = logging.getLogger(__name__)


NICHE_QUERIES = {
    "ai_tools": "AI tools",
    "crypto": "cryptocurrency",
    "fitness": "fitness workout",
    "beauty": "beauty skincare",
    "humor": "funny shorts",
    "adult": "lingerie",
    "general": "trending",
}


class YouTubeScraper(BaseScraper):
    PLATFORM = "youtube"
    REQUIRES_LOGIN = False

    async def fetch_trends(
        self, niche: str, days: int = 7, limit: int = 20, query: str = None
    ) -> Dict:
        search_query = query if query else NICHE_QUERIES.get(niche, niche)
        # 按今日上传 + 按观看次数排序
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}&sp=CAMSAhAB"

        async with self.browser.page("youtube") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector("ytd-video-renderer", timeout=15000)
                for _ in range(2):
                    await page.evaluate("window.scrollBy(0, 1500)")
                    await page.wait_for_timeout(1500)

                videos = await self._extract_videos(page, limit)
                return self._wrap_result(niche, videos, query=search_query)
            except Exception as e:
                logger.error(f"YouTube scrape failed: {e}")
                return self._empty_result(niche, error=str(e))

    async def _extract_videos(self, page, limit: int) -> List[Dict]:
        videos = await page.evaluate(
            """(limit) => {
                const items = document.querySelectorAll("ytd-video-renderer");
                const results = [];
                for (let i = 0; i < Math.min(items.length, limit); i++) {
                    const v = items[i];
                    const titleEl = v.querySelector("a#video-title");
                    const channelEl = v.querySelector("ytd-channel-name a");
                    const meta = v.querySelectorAll("#metadata-line span");
                    results.push({
                        title: titleEl ? titleEl.title : '',
                        text: titleEl ? titleEl.title : '',
                        url: titleEl ? 'https://www.youtube.com' + titleEl.getAttribute('href') : '',
                        author: channelEl ? channelEl.innerText : '',
                        views: meta[0] ? meta[0].innerText : '',
                        published: meta[1] ? meta[1].innerText : '',
                        score: 0,
                    });
                }
                return results;
            }""",
            limit,
        )
        return videos
