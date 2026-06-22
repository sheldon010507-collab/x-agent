"""
reddit_keyless.py — 三层 keyless Reddit 管线编排

Tier 0  legacy .json 搜索（大概率 403 但成本低）
Tier 1  RSS 订阅发现 + listing 分数回填
Tier 2  shreddit 评论 enrichment

参考 mvanhorn/last30days-skill/lib/reddit_keyless.py。
"""

from __future__ import annotations

import asyncio
import logging
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from .config import DEPTH_LIMITS
from .reddit_listing import RedditListingFetcher, _post_id
from .reddit_rss import RedditRSSFetcher
from .reddit_shreddit import ENRICH_LIMITS, RedditShredditEnricher

logger = logging.getLogger(__name__)

ENRICH_BUDGET = 45  # 秒，enrichment 线程总时限
MAX_ENRICH_WORKERS = 4
MAX_DERIVED_SUBS = 5


class RedditKeylessFetcher:
    """三层 keyless Reddit 抓取器。"""

    def __init__(self):
        self._rss = RedditRSSFetcher()
        self._listing = RedditListingFetcher()
        self._shreddit = RedditShredditEnricher()

    def _tier0_json(self, topic: str, depth: str) -> List[Dict[str, Any]]:
        """一次性 legacy .json 尝试（同步，配合线程池）。"""
        try:
            from .http import get_text
            limit = DEPTH_LIMITS.get(depth, DEPTH_LIMITS["default"])
            from urllib.parse import quote_plus
            url = (
                f"https://www.reddit.com/search.json"
                f"?q={quote_plus(topic)}&sort=relevance&t=month&limit={limit}&raw_json=1"
            )
            raw = get_text(url, timeout=15, accept="application/json")
            if not raw:
                return []
            import json
            data = json.loads(raw)
            children = data.get("data", {}).get("children", [])
            posts = []
            for child in children:
                if child.get("kind") != "t3":
                    continue
                post = child.get("data", {})
                permalink = str(post.get("permalink", "")).strip()
                if not permalink or "/comments/" not in permalink:
                    continue
                score = int(post.get("score", 0) or 0)
                num_comments = int(post.get("num_comments", 0) or 0)
                created_utc = post.get("created_utc")
                date_str = None
                if created_utc:
                    try:
                        from datetime import datetime as _dt, timezone as _tz
                        dt = _dt.fromtimestamp(float(created_utc), tz=_tz.utc)
                        date_str = dt.strftime("%Y-%m-%d")
                    except Exception:
                        pass
                posts.append({
                    "id": "",
                    "title": str(post.get("title", "")).strip(),
                    "url": f"https://www.reddit.com{permalink}",
                    "score": score,
                    "num_comments": num_comments,
                    "subreddit": str(post.get("subreddit", "")).strip(),
                    "created_utc": float(created_utc) if created_utc else None,
                    "author": str(post.get("author", "[deleted]")),
                    "selftext": str(post.get("selftext", ""))[:500],
                    "date": date_str,
                    "engagement": {"score": score, "num_comments": num_comments, "upvote_ratio": post.get("upvote_ratio")},
                    "relevance": 0.5,
                    "why_relevant": "Reddit .json",
                    "metadata": {},
                })
            # 去重
            seen, unique = set(), []
            for p in posts:
                if p["url"] not in seen:
                    seen.add(p["url"])
                    unique.append(p)
            for i, p in enumerate(unique):
                p["id"] = f"R{i + 1}"
            logger.info(f"Tier 0 (.json) returned {len(unique)} posts")
            return unique
        except Exception as e:
            logger.debug(f"Tier 0 (.json) unavailable: {e}")
            return []

    def _top_subreddits(self, posts: List[Dict], limit: int = MAX_DERIVED_SUBS) -> List[str]:
        counts = Counter(p.get("subreddit", "") for p in posts if p.get("subreddit"))
        return [sub for sub, _ in counts.most_common(limit)]

    def _apply_scores(self, post: Dict, scored: Dict[str, int]) -> None:
        post["score"] = scored["score"]
        post["num_comments"] = scored["num_comments"]
        post.setdefault("engagement", {})["score"] = scored["score"]
        post["engagement"]["num_comments"] = scored["num_comments"]

    async def _enrich(self, posts: List[Dict[str, Any]], depth: str) -> List[Dict[str, Any]]:
        """用 shreddit 对 top N 帖子做评论 enrichment。"""
        limit = ENRICH_LIMITS.get(depth, ENRICH_LIMITS["default"])
        to_enrich = posts[:limit]
        rest = posts[limit:]
        if not to_enrich:
            return posts

        async def _enrich_one(post: Dict) -> Dict:
            try:
                data = await self._shreddit.fetch_comments(post.get("url", ""))
                if data.get("top_comments"):
                    post["top_comments"] = data["top_comments"]
                if data.get("comment_insights"):
                    post["comment_insights"] = data["comment_insights"]
                num = data.get("num_comments")
                if num is not None:
                    post["num_comments"] = num
                    post.setdefault("engagement", {})["num_comments"] = num
            except Exception:
                pass
            return post

        tasks = [_enrich_one(p) for p in to_enrich]
        try:
            enriched = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=ENRICH_BUDGET,
            )
            result = []
            for i, e in enumerate(enriched):
                result.append(e if isinstance(e, dict) else to_enrich[i])
            return result + rest
        except asyncio.TimeoutError:
            return to_enrich + rest

    async def search_and_enrich(
        self,
        topic: str,
        from_date: str = "",
        to_date: str = "",
        depth: str = "default",
        subreddits: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """完整 keyless Reddit 管线: discover → enrich。"""

        # ── Tier 0: .json ──
        loop = asyncio.get_event_loop()
        posts = await loop.run_in_executor(None, self._tier0_json, topic, depth)
        if posts:
            logger.info(f"[Keyless] Tier 0 hit: {len(posts)} posts")

        # ── Tier 1: RSS + listing ──
        if not posts:
            rss_posts = await self._rss.search_rss(topic, depth=depth, subreddits=subreddits)

            if subreddits:
                listing_posts = await self._listing.fetch_listings(subreddits, depth=depth, query=topic)
                score_source = listing_posts
            else:
                listing_posts = []
                derived = self._top_subreddits(rss_posts)
                score_source = await self._listing.fetch_listings(derived, depth=depth, query=topic)

            logger.info(
                f"[Keyless] Tier 1 — RSS {len(rss_posts)}; "
                f"{'listing ' + str(len(listing_posts)) if subreddits else 'score-only'}; "
                f"{len(score_source)} scored cards"
            )

            # 分数回填
            score_map: Dict[str, Dict[str, int]] = {}
            for p in score_source:
                pid = p.get("metadata", {}).get("post_id", "")
                if pid:
                    score_map[pid] = {"score": p["score"], "num_comments": p["num_comments"]}

            merged: List[Dict[str, Any]] = []
            seen: set = set()
            for p in listing_posts:
                if p["url"] not in seen:
                    seen.add(p["url"])
                    merged.append(p)
            for p in rss_posts:
                if p["url"] in seen:
                    continue
                pid = _post_id(p["url"])
                if pid in score_map:
                    self._apply_scores(p, score_map[pid])
                seen.add(p["url"])
                merged.append(p)
            posts = merged

        if not posts:
            return []

        # 日期过滤
        if from_date and to_date:
            posts = [
                p for p in posts
                if p.get("date") is None or (from_date <= p["date"] <= to_date)
            ]

        # 排序
        posts.sort(
            key=lambda p: (
                p.get("engagement", {}).get("score", 0) or 0,
                p.get("relevance", 0) or 0,
                p.get("date") or "",
            ),
            reverse=True,
        )

        # ── Tier 2: shreddit enrichment ──
        posts = await self._enrich(posts, depth)

        for i, post in enumerate(posts):
            post["id"] = f"R{i + 1}"

        return posts
