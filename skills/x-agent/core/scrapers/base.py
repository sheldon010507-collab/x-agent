"""
base.py - 抓取器抽象基类
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """所有平台抓取器基类"""

    PLATFORM: str = "base"
    REQUIRES_LOGIN: bool = False

    def __init__(self, browser_manager):
        self.browser = browser_manager

    @abstractmethod
    async def fetch_trends(
        self,
        niche: str,
        days: int = 7,
        limit: int = 20,
        query: Optional[str] = None,
    ) -> Dict:
        """
        抓取该平台与 niche/query 相关的内容

        Args:
            niche: 预定义 niche (如 'ai_tools')
            days: 回溯天数
            limit: 最多返回数量
            query: 用户自定义关键词（优先级高于 niche 默认查询）
        """
        pass

    def _empty_result(self, niche: str, error: str = None) -> Dict:
        return {
            "platform": self.PLATFORM,
            "niche": niche,
            "posts": [],
            "fetched_at": datetime.now().isoformat(),
            "error": error,
        }

    def _wrap_result(self, niche: str, posts: List[Dict], query: str = None) -> Dict:
        return {
            "platform": self.PLATFORM,
            "niche": niche,
            "query": query,
            "posts": posts,
            "fetched_at": datetime.now().isoformat(),
        }
