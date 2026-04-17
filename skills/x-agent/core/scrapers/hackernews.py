"""
hackernews.py - Hacker News scraper (Playwright)

抓取 HN 首页的热门 stories。
"""

import logging
from typing import Dict, List

from .base import BaseScraper

logger = logging.getLogger(__name__)


class HackerNewsScraper(BaseScraper):
    PLATFORM = "hackernews"
    REQUIRES_LOGIN = False

    async def fetch_trends(
        self, niche: str, days: int = 7, limit: int = 30, query: str = None
    ) -> Dict:
        # 自定义 query → 用 HN Algolia 搜索；否则取首页 hot
        if query:
            url = f"https://hn.algolia.com/?q={query}&sort=byPopularity"
        else:
            url = "https://news.ycombinator.com/"

        async with self.browser.page("hackernews") as page:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                # Algolia 页面用不同的 DOM
                if query:
                    return await self._extract_algolia(page, niche, query, limit)
                await page.wait_for_selector("tr.athing", timeout=10000)
                posts = await page.evaluate(
                    """(limit) => {
                        const rows = document.querySelectorAll("tr.athing");
                        const results = [];
                        for (let i = 0; i < Math.min(rows.length, limit); i++) {
                            const r = rows[i];
                            const titleEl = r.querySelector(".titleline a");
                            const subtext = r.nextElementSibling ? r.nextElementSibling.querySelector(".subtext") : null;
                            const scoreEl = subtext ? subtext.querySelector(".score") : null;
                            const userEl = subtext ? subtext.querySelector(".hnuser") : null;
                            const ageEl = subtext ? subtext.querySelector(".age a") : null;
                            const commentsLinks = subtext ? subtext.querySelectorAll("a") : [];
                            const commentsEl = commentsLinks.length > 0 ? commentsLinks[commentsLinks.length - 1] : null;
                            results.push({
                                title: titleEl ? titleEl.innerText : '',
                                text: titleEl ? titleEl.innerText : '',
                                url: titleEl ? titleEl.href : '',
                                score: scoreEl ? parseInt(scoreEl.innerText) : 0,
                                by: userEl ? userEl.innerText : '',
                                age: ageEl ? ageEl.innerText : '',
                                descendants: commentsEl ? parseInt(commentsEl.innerText) || 0 : 0,
                            });
                        }
                        return results;
                    }""",
                    limit,
                )
                # niche filter (very basic - keyword match in title)
                if niche != "general":
                    keywords = niche.replace("_", " ").lower().split()
                    posts = [p for p in posts if any(k in p["title"].lower() for k in keywords)] or posts
                return self._wrap_result(niche, posts, query=query)
            except Exception as e:
                logger.error(f"HN scrape failed: {e}")
                return self._empty_result(niche, error=str(e))

    async def _extract_algolia(self, page, niche: str, query: str, limit: int) -> Dict:
        """从 hn.algolia.com 搜索结果页提取"""
        try:
            await page.wait_for_selector(".Story", timeout=10000)
            posts = await page.evaluate(
                """(limit) => {
                    const items = document.querySelectorAll(".Story");
                    const results = [];
                    for (let i = 0; i < Math.min(items.length, limit); i++) {
                        const it = items[i];
                        const titleEl = it.querySelector(".Story_title a");
                        const metaEls = it.querySelectorAll(".Story_meta a");
                        const score = metaEls[0] ? parseInt(metaEls[0].innerText) || 0 : 0;
                        const author = metaEls[1] ? metaEls[1].innerText : '';
                        const comments = metaEls[3] ? parseInt(metaEls[3].innerText) || 0 : 0;
                        results.push({
                            title: titleEl ? titleEl.innerText : '',
                            text: titleEl ? titleEl.innerText : '',
                            url: titleEl ? titleEl.href : '',
                            score: score,
                            by: author,
                            descendants: comments,
                        });
                    }
                    return results;
                }""",
                limit,
            )
            return self._wrap_result(niche, posts, query=query)
        except Exception as e:
            logger.error(f"HN Algolia scrape failed: {e}")
            return self._empty_result(niche, error=str(e))
