"""
reddit_shreddit.py — shreddit /svc 评论 enrichtment

从 /svc/shreddit/comments/r/{sub}/t3_{id} 拿到 <shreddit-comment> 评论
标签，携带 score / author / created ，解析出 top_comments。

参考 mvanhorn/last30days-skill/lib/reddit_shreddit.py。
"""

from __future__ import annotations

import html as _html
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import SVC_TIMEOUT
from .http import get_text_async

_COMMENT_START = re.compile(r"<shreddit-comment(?=[\s>])[^>]*>")
_TOTAL_COMMENTS = re.compile(r'total-comments="(\d+)"')
_PARA = re.compile(r"<p[^>]*>(.*?)</p>", re.S)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_NEXT_RTJSON = re.compile(r'id="t1_[A-Za-z0-9]+-(?:comment|post)-rtjson-content"')

ENRICH_LIMITS = {"quick": 3, "default": 5, "deep": 8}
MAX_COMMENTS = 10

logger = logging.getLogger(__name__)


def extract_post_ref(url: str) -> Optional[tuple]:
    m = re.search(r"/r/([^/]+)/comments/([A-Za-z0-9]+)", url or "")
    if not m:
        return None
    return m.group(1), m.group(2)


def _svc_url(subreddit: str, post_id: str) -> str:
    return (
        f"https://www.reddit.com/svc/shreddit/comments/r/{subreddit}/t3_{post_id}"
        f"?sort=top"
    )


def _attr(tag: str, name: str) -> str:
    m = re.search(rf'\b{name}="([^"]*)"', tag)
    return _html.unescape(m.group(1)) if m else ""


def _iso_to_date(value: str) -> Optional[str]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.strip()).date().isoformat()
    except (ValueError, TypeError):
        return None


def _body_for(html_text: str, thing_id: str) -> str:
    if not thing_id:
        return ""
    anchor = f'id="{thing_id}-post-rtjson-content"'
    idx = html_text.find(anchor)
    if idx == -1:
        return ""
    window = html_text[idx + len(anchor): idx + len(anchor) + 8000]
    nxt = _NEXT_RTJSON.search(window)
    if nxt:
        window = window[: nxt.start()]
    paras = _PARA.findall(window)
    if not paras:
        return ""
    text = " ".join(_TAG.sub("", p) for p in paras)
    return _WS.sub(" ", _html.unescape(text)).strip()


def parse_comments(html_text: str, limit: int = MAX_COMMENTS) -> List[Dict[str, Any]]:
    comments: List[Dict[str, Any]] = []
    for m in _COMMENT_START.finditer(html_text or ""):
        tag = m.group(0)
        author = _attr(tag, "author") or "[deleted]"
        if author in ("[deleted]", "[removed]"):
            continue
        thing_id = _attr(tag, "thingId")
        body = _body_for(html_text, thing_id)
        if not body or body in ("[deleted]", "[removed]"):
            continue
        try:
            score = int(_attr(tag, "score") or 0)
        except ValueError:
            score = 0
        permalink = _attr(tag, "permalink")
        comments.append({
            "score": score,
            "author": author,
            "body": body[:300],
            "excerpt": body[:200],
            "permalink": permalink,
            "date": _iso_to_date(_attr(tag, "created")),
            "url": f"https://reddit.com{permalink}" if permalink else "",
        })

    comments.sort(key=lambda c: c.get("score", 0), reverse=True)
    return comments[:limit]


def _total_comments(html_text: str) -> Optional[int]:
    m = _TOTAL_COMMENTS.search(html_text or "")
    return int(m.group(1)) if m else None


def extract_comment_insights(comments: List[Dict]) -> List[str]:
    """从 top comments 提取简短洞见（最多5条）。"""
    insights = []
    for c in comments[:5]:
        body = c.get("body") or c.get("excerpt") or ""
        if len(body) > 40:
            body = body[:80] + "…"
        insights.append(body)
    return insights


class RedditShredditEnricher:
    """异步 shreddit 评论 enrichter。"""

    async def fetch_comments(self, post_url: str, timeout: int = SVC_TIMEOUT) -> Dict[str, Any]:
        ref = extract_post_ref(post_url)
        if not ref:
            return {"top_comments": [], "comment_insights": [], "num_comments": None}
        sub, post_id = ref

        html_text = await get_text_async(
            _svc_url(sub, post_id), timeout=timeout, accept="text/html"
        )
        if not html_text:
            return {"top_comments": [], "comment_insights": [], "num_comments": None}

        comments = parse_comments(html_text, limit=MAX_COMMENTS)
        insights = extract_comment_insights(comments)
        return {
            "top_comments": [
                {"score": c["score"], "date": c["date"], "author": c["author"],
                 "excerpt": c["excerpt"], "url": c["url"]}
                for c in comments
            ],
            "comment_insights": insights,
            "num_comments": _total_comments(html_text),
        }
