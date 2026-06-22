"""
reddit_rss.py — keyless Reddit RSS/Atom 订阅抓取

从 r/{sub}/top.rss 和 /search.rss 获取帖子列表。
无需 API key，HTTP 200 稳定。

参考 mvanhorn/last30days-skill/lib/reddit_rss.py 适配到 x-agent。
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from asyncio import get_event_loop
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from .config import DEPTH_LIMITS, FEED_TIMEOUT, LISTING_SORTS
from .http import get_text_async, url_encode
from .relevance import token_overlap_relevance

ATOM = "{http://www.w3.org/2005/Atom}"
logger = logging.getLogger(__name__)


def _iso_to_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.strip())
        return dt.date().isoformat()
    except (ValueError, TypeError):
        return None


def _iso_to_epoch(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError):
        return None


def _subreddit_from(category: str, url: str) -> str:
    if category:
        return category
    parts = url.split("/r/", 1)
    if len(parts) == 2:
        return parts[1].split("/", 1)[0]
    return ""


def _parse_feed(xml_text: str, query: str = "") -> List[Dict[str, Any]]:
    if not xml_text:
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.debug(f"RSS feed parse error: {e}")
        return []

    posts: List[Dict[str, Any]] = []
    for entry in root.iter(f"{ATOM}entry"):
        link_el = entry.find(f"{ATOM}link")
        url = link_el.get("href", "").strip() if link_el is not None else ""
        if not url or "/comments/" not in url:
            continue

        title_el = entry.find(f"{ATOM}title")
        title = (title_el.text or "").strip() if title_el is not None else ""

        author = ""
        author_el = entry.find(f"{ATOM}author/{ATOM}name")
        if author_el is not None and author_el.text:
            author = author_el.text.strip().removeprefix("/u/").removeprefix("u/")
        if author in ("[deleted]", "[removed]", ""):
            author = "[deleted]"

        cat_el = entry.find(f"{ATOM}category")
        category = cat_el.get("term", "").strip() if cat_el is not None else ""
        subreddit = _subreddit_from(category, url)

        updated_el = entry.find(f"{ATOM}updated")
        updated = (updated_el.text or "").strip() if updated_el is not None else ""

        content_el = entry.find(f"{ATOM}content")
        selftext = ""
        if content_el is not None and content_el.text:
            selftext = re.sub(r"<[^>]+>", " ", content_el.text)
            selftext = re.sub(r"\s+", " ", selftext).strip()[:500]

        relevance = round(token_overlap_relevance(query, title), 3) if query else 0.0

        posts.append({
            "id": "",
            "title": title,
            "url": url,
            "score": 0,
            "num_comments": 0,
            "subreddit": subreddit,
            "created_utc": _iso_to_epoch(updated),
            "author": author,
            "selftext": selftext,
            "date": _iso_to_date(updated),
            "engagement": {"score": 0, "num_comments": 0, "upvote_ratio": None},
            "relevance": relevance,
            "why_relevant": "Reddit RSS",
            "metadata": {},
        })
    return posts


def _build_urls(query: str, depth: str, subreddits: Optional[List[str]]) -> List[str]:
    q = quote_plus(query)
    urls: List[str] = [
        f"https://www.reddit.com/search.rss?q={q}&sort=relevance&t=month"
    ]
    for raw_sub in (subreddits or []):
        sub = raw_sub.removeprefix("r/").strip()
        if not sub:
            continue
        urls.append(
            f"https://www.reddit.com/r/{sub}/search.rss"
            f"?q={q}&restrict_sr=on&sort=relevance&t=month"
        )
        for sort in LISTING_SORTS.get(depth, LISTING_SORTS["default"]):
            urls.append(f"https://www.reddit.com/r/{sub}/{sort}.rss?t=month")
    return urls


class RedditRSSFetcher:
    """异步 RSS 订阅抓取器。"""

    async def search_rss(
        self,
        query: str,
        depth: str = "default",
        subreddits: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        limit = DEPTH_LIMITS.get(depth, DEPTH_LIMITS["default"])
        urls = _build_urls(query, depth, subreddits)

        all_posts: List[Dict[str, Any]] = []
        # 并发拉取（无 aiohttp 时退回空列表，但 get_text_async 返回 None）
        import asyncio
        tasks = [get_text_async(url, timeout=FEED_TIMEOUT, accept="application/atom+xml") for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for xml_text in results:
            if isinstance(xml_text, Exception) or not xml_text:
                continue
            all_posts.extend(_parse_feed(xml_text, query))

        # 去重
        seen: set = set()
        unique: List[Dict[str, Any]] = []
        for post in all_posts:
            if post["url"] not in seen:
                seen.add(post["url"])
                unique.append(post)

        for i, post in enumerate(unique):
            post["id"] = f"R{i + 1}"

        return unique[:limit]
