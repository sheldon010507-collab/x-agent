"""
reddit_listing.py — keyless subreddit listing 抓取（真实 upvote 分数）

通过 shreddit /svc/shreddit/community-more-posts/{sort}/?name={sub} 拿到
包含 ``score`` / ``comment-count`` 属性的 ``<shreddit-post>`` 卡片。

参考 mvanhorn/last30days-skill/lib/reddit_listing.py。
"""

from __future__ import annotations

import html as _html
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .config import DEPTH_LIMITS, LISTING_SORTS, LISTING_TIMEOUT
from .http import get_text_async
from .relevance import token_overlap_relevance

_POST_CARD = re.compile(r"<shreddit-post(?=[\s>])[^>]*>")
logger = logging.getLogger(__name__)


def _attr(tag: str, name: str) -> Optional[str]:
    m = re.search(rf'\b{name}="([^"]*)"', tag)
    return _html.unescape(m.group(1)) if m else None


def _to_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.strip()).date().isoformat()
    except (ValueError, TypeError):
        return None


def _to_epoch(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError):
        return None


def _post_id(permalink: str) -> str:
    m = re.search(r"/comments/([A-Za-z0-9]+)", permalink or "")
    return m.group(1) if m else ""


def parse_cards(html_text: str, query: str = "") -> List[Dict[str, Any]]:
    """从 shreddit HTML 解析帖卡，携带真实 score。"""
    posts: List[Dict[str, Any]] = []
    for m in _POST_CARD.finditer(html_text or ""):
        tag = m.group(0)
        permalink = _attr(tag, "permalink") or ""
        if "/comments/" not in permalink:
            continue
        try:
            score = int(_attr(tag, "score") or 0)
        except ValueError:
            score = 0
        try:
            num_comments = int(_attr(tag, "comment-count") or 0)
        except ValueError:
            num_comments = 0
        title = _attr(tag, "post-title") or ""
        author = _attr(tag, "author") or "[deleted]"
        subreddit = _attr(tag, "subreddit-name") or ""
        created = _attr(tag, "created-timestamp")
        url = f"https://www.reddit.com{permalink}"

        posts.append({
            "id": "",
            "title": title,
            "url": url,
            "score": score,
            "num_comments": num_comments,
            "subreddit": subreddit,
            "created_utc": _to_epoch(created),
            "author": author if author not in ("[deleted]", "[removed]") else "[deleted]",
            "selftext": "",
            "date": _to_date(created),
            "engagement": {"score": score, "num_comments": num_comments, "upvote_ratio": None},
            "relevance": round(token_overlap_relevance(query, title), 3) if query else 0.0,
            "why_relevant": "Reddit listing",
            "metadata": {"post_id": _post_id(permalink)},
        })
    return posts


class RedditListingFetcher:
    """异步抓取 subreddit listing partials。"""

    def _listing_url(self, subreddit: str, sort: str) -> str:
        sub = subreddit.removeprefix("r/").strip()
        url = f"https://www.reddit.com/svc/shreddit/community-more-posts/{sort}/?name={sub}"
        if sort == "top":
            url += "&t=month"
        return url

    async def _fetch_one(self, subreddit: str, sort: str, query: str) -> List[Dict[str, Any]]:
        try:
            text = await get_text_async(
                self._listing_url(subreddit, sort),
                timeout=LISTING_TIMEOUT,
                accept="text/html",
            )
            return parse_cards(text, query) if text else []
        except Exception as e:
            logger.debug(f"listing fetch failed r/{subreddit} {sort}: {e}")
            return []

    async def fetch_listings(
        self,
        subreddits: List[str],
        depth: str = "default",
        query: str = "",
    ) -> List[Dict[str, Any]]:
        if not subreddits:
            return []
        sorts = LISTING_SORTS.get(depth, LISTING_SORTS["default"])
        jobs = [(sub, sort) for sub in subreddits for sort in sorts]

        import asyncio
        tasks = [self._fetch_one(sub, s, query) for sub, s in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_posts: List[Dict[str, Any]] = []
        for r in results:
            if isinstance(r, Exception):
                continue
            all_posts.extend(r)

        # 去重
        seen: set = set()
        unique: List[Dict[str, Any]] = []
        for p in all_posts:
            if p["url"] not in seen:
                seen.add(p["url"])
                unique.append(p)
        return unique

    async def score_index(
        self, subreddits: List[str], depth: str = "default"
    ) -> Dict[str, Dict[str, int]]:
        """构建 {post_id: {score, num_comments}} 索引，用于 RSS 结果回填分数。"""
        index: Dict[str, Dict[str, int]] = {}
        for p in await self.fetch_listings(subreddits, depth=depth):
            pid = p.get("metadata", {}).get("post_id") or _post_id(p["url"])
            if pid:
                index[pid] = {"score": p["score"], "num_comments": p["num_comments"]}
        return index
