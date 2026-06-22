"""
pipeline.py — 对外统一入口

提供 ``RedditPipeline`` 类，把 keyless 三层管线 + 旧 PRAW + Playwright
整合为一条 fallback 链:

  RedditKeylessFetcher (HTTP 层) → RedditPlaywrightCrawler → PRAW mock

research.py 只需调用 ``RedditPipeline.search()`` 即可。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .reddit_keyless import RedditKeylessFetcher

logger = logging.getLogger(__name__)


class RedditPipeline:
    """统一 Reddit 搜索入口 — keyless 优先，Playwright/PRAW 兜底。"""

    def __init__(self, playwright_crawler=None, praw_fetcher=None):
        self._keyless = RedditKeylessFetcher()
        self._playwright = playwright_crawler
        self._praw = praw_fetcher

    async def search(
        self,
        topic: str,
        depth: str = "default",
        subreddits: Optional[List[str]] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """全管线搜索，返回与 research.py 兼容格式。"""
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        # 1. keyless (HTTP)
        try:
            posts = await self._keyless.search_and_enrich(
                topic, from_date, to_date, depth=depth, subreddits=subreddits
            )
            if posts:
                logger.info(f"[Pipeline] Keyless returned {len(posts)} posts")
                return self._format_result(posts, source="keyless")
        except Exception as e:
            logger.warning(f"[Pipeline] Keyless failed: {e}")

        # 2. Playwright 回退
        if self._playwright:
            try:
                pw_posts = await self._playwright.search(topic, subreddits=subreddits, limit=25)
                if pw_posts:
                    logger.info(f"[Pipeline] Playwright returned {len(pw_posts)} posts")
                    return self._format_playwright_result(pw_posts)
            except Exception as e:
                logger.warning(f"[Pipeline] Playwright failed: {e}")

        # 3. PRAW 回退
        if self._praw:
            try:
                praw_result = await self._praw.fetch(topic, days=days)
                if praw_result and praw_result.get("posts"):
                    logger.info(f"[Pipeline] PRAW returned {len(praw_result['posts'])} posts")
                    return praw_result
            except Exception as e:
                logger.warning(f"[Pipeline] PRAW failed: {e}")

        logger.warning("[Pipeline] All tiers failed, returning empty")
        return self._empty_result(topic)

    def _format_result(self, posts: List[Dict], source: str = "keyless") -> Dict[str, Any]:
        return {
            "platform": "reddit",
            "source": source,
            "posts": posts,
            "total": len(posts),
            "fetched_at": datetime.now().isoformat(),
        }

    def _format_playwright_result(self, pw_posts: list) -> Dict[str, Any]:
        """将 RedditPost dataclass 转为标准 dict。"""
        posts = []
        for p in pw_posts:
            if isinstance(p, dict):
                posts.append(p)
            else:
                posts.append({
                    "id": p.id,
                    "title": p.title,
                    "url": p.url,
                    "score": p.upvotes,
                    "num_comments": p.comment_count,
                    "subreddit": p.subreddit,
                    "author": p.author,
                    "date": p.created_utc.isoformat() if hasattr(p.created_utc, "isoformat") else str(p.created_utc),
                    "engagement": {"score": p.upvotes, "num_comments": p.comment_count},
                    "top_comments": p.top_comments,
                    "selftext": p.content[:500] if p.content else "",
                    "metadata": {},
                })
        return self._format_result(posts, source="playwright")

    def _empty_result(self, topic: str) -> Dict[str, Any]:
        return {
            "platform": "reddit",
            "source": "none",
            "posts": [],
            "total": 0,
            "fetched_at": datetime.now().isoformat(),
            "topic": topic,
        }
