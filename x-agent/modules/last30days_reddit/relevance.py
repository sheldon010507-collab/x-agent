"""
relevance.py — 简易 token 重叠打分

不再调 LLM，纯本地规则，对一个查询是否命中帖子提供 0..1 的相关度评估。
原 last30days 里有更复杂的 rerank，这里为了不引入额外依赖做一个最小可用版。
"""

from __future__ import annotations

import re
from typing import Iterable, List, Set

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[一-鿿]+")
_STOP = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "and",
    "or",
    "is",
    "are",
    "for",
    "with",
    "on",
    "in",
    "by",
    "this",
    "that",
    "it",
}


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def token_set(text: str) -> Set[str]:
    return {t for t in tokenize(text) if t not in _STOP and len(t) > 1}


def token_overlap_relevance(query: str, target: str) -> float:
    """Jaccard 风格的重叠度，返回 0..1。"""
    q_tokens = token_set(query)
    t_tokens = token_set(target)
    if not q_tokens or not t_tokens:
        return 0.0
    overlap = q_tokens & t_tokens
    if not overlap:
        return 0.0
    return len(overlap) / len(q_tokens | t_tokens)


def token_overlap_relevance_prepared(prepared: Set[str], target: str) -> float:
    """直接接受已预算好的 query token 集合。"""
    if not prepared or not target:
        return 0.0
    t_tokens = token_set(target)
    if not t_tokens:
        return 0.0
    overlap = prepared & t_tokens
    if not overlap:
        return 0.0
    return len(overlap) / len(prepared | t_tokens)


class PreparedQuery:
    __slots__ = ("text", "tokens")

    def __init__(self, text: str):
        self.text = text
        self.tokens = token_set(text)


def iter_tokens(text: str) -> Iterable[str]:
    """公开 token 流，供 cluster / rerank 等共用。"""
    return tokenize(text)
