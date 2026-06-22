"""
api_client.py - X-Agent API HTTP 客户端

通过 HTTP 调用本地 X-Agent API 服务，提供给 Telegram Bot 使用
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class XAgentAPIClient:
    """X-Agent API 客户端"""

    def __init__(self, api_url: str = "http://x-agent-api:8000"):
        """
        初始化 API 客户端

        Args:
            api_url: API 基础 URL（默认本地 8000 端口）
        """
        self.api_url = api_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def health_check(self) -> bool:
        """检查 API 健康状态"""
        try:
            response = await self.client.get(f"{self.api_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def get_trends(self, niche: str = "general", days: int = 7) -> Dict[str, Any]:
        """
        获取热点趋势

        Args:
            niche: 细分领域（general/tech/finance/entertainment）
            days: 时间范围（1-30 天）

        Returns:
            趋势数据
        """
        try:
            response = await self.client.get(
                f"{self.api_url}/trends",
                params={"niche": niche, "days": min(days, 30)},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get trends: {e}")
            return {"error": str(e), "trends": []}

    async def create_content(self, niche: str, content_type: str, topic: str) -> Dict[str, Any]:
        """
        创建内容草稿

        Args:
            niche: 细分领域
            content_type: 内容类型（A=推文, B=视频脚本）
            topic: 话题/主题

        Returns:
            创建的内容及 ID
        """
        try:
            response = await self.client.post(
                f"{self.api_url}/create",
                json={"niche": niche, "type": content_type, "topic": topic},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create content: {e}")
            return {"error": str(e), "content_id": None}

    async def approve_content(self, content_id: str) -> Dict[str, Any]:
        """
        批准/确认内容发布

        Args:
            content_id: 内容 ID

        Returns:
            批准结果
        """
        try:
            response = await self.client.post(f"{self.api_url}/approve/{content_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to approve content: {e}")
            return {"error": str(e), "status": "failed"}

    async def get_report(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取每日报告

        Args:
            date: 日期（YYYY-MM-DD，默认今天）

        Returns:
            每日统计数据
        """
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            response = await self.client.get(f"{self.api_url}/report", params={"date": date})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get report: {e}")
            return {"error": str(e), "posts_count": 0}

    async def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            response = await self.client.get(f"{self.api_url}/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"error": str(e), "service": "unknown"}

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
