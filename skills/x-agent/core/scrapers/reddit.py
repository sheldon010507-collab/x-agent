"""
reddit.py - Reddit scraper (Playwright)

通过浏览器访问 old.reddit.com 抓取热门帖子（DOM 比新版稳定）。
"""

import logging
from typing import Dict, List

from .base import BaseScraper

logger = logging.getLogger(__name__)


NICHE_SUBREDDITS = {
    "ai_tools": ["artificial", "ChatGPT", "OpenAI"],
    "crypto": ["CryptoCurrency", "Bitcoin"],
    "fitness": ["fitness", "bodybuilding"],
    "beauty": ["MakeupAddiction", "SkincareAddiction"],
    "humor": ["funny", "memes"],
    "adult": ["sex"],
    "general": ["AskReddit", "worldnews"],
}


class RedditScraper(BaseScraper):
    PLATFORM = "reddit"
    REQUIRES_LOGIN = False

    async def fetch_trends(
        self, niche: str, days: int = 7, limit: int = 20, query: str = None
    ) -> Dict:
        # 自定义 query → 全站搜索；否则按 niche 走 subreddit
        if query:
            urls = [f"https://old.reddit.com/search?q={query}&sort=top&t=week"]
        else:
            subs = NICHE_SUBREDDITS.get(niche, NICHE_SUBREDDITS["general"])
            urls = [f"https://old.reddit.com/r/{sub}/hot/" for sub in subs[:2]]

        all_posts: List[Dict] = []

        async with self.browser.page("reddit") as page:
            for url in urls:
                if len(all_posts) >= limit:
                    break
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_selector("div.thing", timeout=10000)
                    posts = await page.evaluate(
                        """(remaining) => {
                            const items = document.querySelectorAll("div.thing");
                            const results = [];
                            for (let i = 0; i < Math.min(items.length, remaining); i++) {
                                const el = items[i];
                                if (el.classList.contains('promoted')) continue;
                                const titleEl = el.querySelector("a.title");
                                const scoreEl = el.querySelector("div.score.unvoted");
                                const commentsEl = el.querySelector("a.comments");
                                const subEl = el.querySelector("a.subreddit");
                                results.push({
                                    title: titleEl ? titleEl.innerText : '',
                                    text: titleEl ? titleEl.innerText : '',
                                    url: titleEl ? titleEl.href : '',
                                    score: parseInt((scoreEl ? scoreEl.innerText : '0').replace('k', '000').replace('.','')) || 0,
                                    num_comments: parseInt((commentsEl ? commentsEl.innerText : '0').replace(/\\D/g,'')) || 0,
                                    subreddit: subEl ? subEl.innerText : '',
                                });
                            }
                            return results;
                        }""",
                        limit - len(all_posts),
                    )
                    all_posts.extend(posts)
                except Exception as e:
                    logger.warning(f"Reddit fetch failed for {url}: {e}")

        return self._wrap_result(niche, all_posts[:limit], query=query)
