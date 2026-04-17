"""
google_trends.py - Google Trends scraper (Playwright)

抓取 Google Trends Daily Trends 页面。
"""

import logging
import urllib.parse
from typing import Dict, List

from .base import BaseScraper

logger = logging.getLogger(__name__)


# 平台关键词
NICHE_GEO = {
    "ai_tools": ("AI", "US"),
    "crypto": ("crypto", "US"),
    "fitness": ("fitness", "US"),
    "beauty": ("skincare", "US"),
    "humor": ("memes", "US"),
    "adult": ("dating", "US"),
    "general": ("trending", "US"),
}


class GoogleTrendsScraper(BaseScraper):
    PLATFORM = "google_trends"
    REQUIRES_LOGIN = False

    async def fetch_trends(
        self, niche: str, days: int = 7, limit: int = 20, query: str = None
    ) -> Dict:
        # 自定义 query → explore 页面（按关键词查趋势）
        # 否则 → trending 页面（地区热搜榜）
        if query:
            url = f"https://trends.google.com/trends/explore?q={query}&hl=en-US"
        else:
            keyword, geo = NICHE_GEO.get(niche, NICHE_GEO["general"])
            url = f"https://trends.google.com/trending?geo={geo}&hl=en-US"

        async with self.browser.page("google_trends") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Trending list 用 Material Design 组件，多种选择器尝试
                await page.wait_for_timeout(3000)
                trends = await page.evaluate(
                    """(limit) => {
                        const results = [];
                        // 尝试多种选择器
                        const items = document.querySelectorAll(
                            "[jsname], div[role='listitem'], tr.feed-item-header, td.details-bottom"
                        );
                        const seen = new Set();
                        for (const it of items) {
                            if (results.length >= limit) break;
                            const text = it.innerText ? it.innerText.trim() : '';
                            if (!text || text.length < 3 || text.length > 120) continue;
                            if (seen.has(text)) continue;
                            seen.add(text);
                            results.push({
                                title: text.split('\\n')[0],
                                text: text,
                                url: 'https://trends.google.com/trends/explore?q=' + encodeURIComponent(text.split('\\n')[0]),
                                score: 0,
                            });
                        }
                        return results;
                    }""",
                    limit,
                )
                return self._wrap_result(niche, trends, query=query)
            except Exception as e:
                logger.error(f"Google Trends scrape failed: {e}")
                return self._empty_result(niche, error=str(e))
