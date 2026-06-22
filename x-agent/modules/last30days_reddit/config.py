"""
config.py — last30days_reddit 子模块的共享配置

参考原版 lib/env.py + lib/dates.py，集中时区、UA、缓存目录等常量。
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CACHE_DIR = PROJECT_ROOT / "x-agent" / "data" / "reddit_cache"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 复用 x-agent 已有的 proxy 环境变量，避免在代码里硬编码
HTTP_PROXY = os.environ.get("REDDIT_HTTP_PROXY") or os.environ.get("HTTP_PROXY")

# 深度 → 抓取上限
DEPTH_LIMITS = {
    "quick": 10,
    "default": 25,
    "deep": 50,
}

# listing 抓取的排序组合
LISTING_SORTS = {
    "quick": ["top"],
    "default": ["top", "hot"],
    "deep": ["top", "hot", "new"],
}

# HTTP timeout（秒）
FEED_TIMEOUT = 15
LISTING_TIMEOUT = 15
SVC_TIMEOUT = 12


def cache_dir() -> Path:
    """返回缓存目录，确保存在。"""
    DEFAULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CACHE_DIR
