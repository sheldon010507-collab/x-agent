"""
search.py - 多层级联搜索 + 全文匹配

支持：
- 在 posts 列表中按关键词过滤（标题 + 正文 + 描述 + 作者）
- 多层级联：每层在前一层结果上继续过滤
- 多词 AND 语义：'uk fitness' = 同时包含两个词
- 大小写不敏感
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# 用于匹配的字段（按优先级）
MATCHABLE_FIELDS = ("title", "text", "description", "caption", "author", "by", "subreddit")


def _build_haystack(post: Dict) -> str:
    """把 post 中所有可搜索字段拼成一个小写字符串"""
    parts = []
    for field in MATCHABLE_FIELDS:
        val = post.get(field)
        if val:
            parts.append(str(val))
    # 也包含 hashtags / tags
    for field in ("hashtags", "tags"):
        val = post.get(field)
        if isinstance(val, list):
            parts.extend(str(v) for v in val)
        elif val:
            parts.append(str(val))
    return " ".join(parts).lower()


def _matches(post: Dict, query: str, mode: str = "and") -> bool:
    """
    检查 post 是否匹配 query

    Args:
        post: 帖子字典
        query: 查询字符串（可以多词）
        mode: 'and' (所有词都要在) | 'or' (任一词在即可)
    """
    if not query or not query.strip():
        return True
    haystack = _build_haystack(post)
    if not haystack:
        return False
    # 分词（支持中英文：英文按空格，中文按字符）
    terms = [t.strip().lower() for t in re.split(r"\s+", query.strip()) if t.strip()]
    if not terms:
        return True
    if mode == "or":
        return any(t in haystack for t in terms)
    return all(t in haystack for t in terms)


def filter_posts(posts: List[Dict], query: str, mode: str = "and") -> List[Dict]:
    """单层过滤"""
    if not query or not query.strip():
        return posts
    return [p for p in posts if _matches(p, query, mode=mode)]


def cascade(posts: List[Dict], queries: List[str], mode: str = "and") -> List[Dict]:
    """
    多层级联过滤：每个 query 在前一层结果上继续缩小范围

    Args:
        posts: 初始 post 列表
        queries: 查询列表，按顺序应用
        mode: 'and' | 'or' （针对单个 query 内多个词的关系）

    Returns:
        所有 query 都匹配的 posts 列表
    """
    result = posts
    for q in queries:
        if not q or not q.strip():
            continue
        before = len(result)
        result = filter_posts(result, q, mode=mode)
        logger.info(f"[search] filter '{q}': {before} → {len(result)}")
    return result


def cascade_with_trace(posts: List[Dict], queries: List[str], mode: str = "and") -> Dict:
    """级联过滤并返回每层的命中数追踪"""
    trace = []
    result = posts
    trace.append({"step": 0, "query": "<initial>", "count": len(result)})
    for i, q in enumerate(queries, 1):
        if not q or not q.strip():
            continue
        result = filter_posts(result, q, mode=mode)
        trace.append({"step": i, "query": q, "count": len(result)})
    return {"posts": result, "trace": trace}


def search_in_data(
    platform_data: Dict[str, Dict],
    queries: List[str],
    mode: str = "and",
) -> Dict[str, List[Dict]]:
    """
    在多平台数据中搜索（每个平台分别级联过滤）

    Args:
        platform_data: {'x': {posts: [...]}, 'reddit': {posts: [...]}, ...}
        queries: 级联过滤查询
        mode: 单 query 多词关系

    Returns:
        {platform: [matched_posts]}
    """
    out = {}
    for platform, data in platform_data.items():
        if not isinstance(data, dict):
            continue
        posts = data.get("posts", [])
        out[platform] = cascade(posts, queries, mode=mode)
    return out
