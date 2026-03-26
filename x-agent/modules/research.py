"""
research.py - 数据采集模块

调用 last30days CLI 进行多平台深度研究
支持：X + Reddit + YouTube + HN + Web + TikTok

v3.0: 使用真实 CLI 调用，替换假 API
"""

import subprocess
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Researcher:
    """研究员 - 负责多平台数据采集"""
    
    def __init__(self, config=None):
        """
        初始化研究员
        
        Args:
            config: Config 实例
        """
        self.config = config
        self.cache_dir = Path("data/research")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def research_topic(
        self,
        niche: str,
        days: int = 7,
        sources: str = "x,reddit,youtube,web,tiktok,hackernews"
    ) -> Dict:
        """
        调用 last30days CLI 进行多平台深度研究（情报核心）
        
        Args:
            niche: 研究领域/话题
            days: 回溯天数 (1-30)
            sources: 数据源，逗号分隔
            
        Returns:
            Dict: 研究结果，包含：
                - relevance_score: 相关度 (0-100)
                - velocity_24h: 24h互动增速
                - authority_score: 权威度
                - platform_count: 平台数
                - summary: 摘要
                - citations: 引用来源
        """
        logger.info(f"开始研究: {niche}, days={days}, sources={sources}")
        
        cmd = [
            "last30days",
            niche,
            f"--days={days}",
            f"--sources={sources}",
            "--agent",
            "--output=json"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.error(f"last30days CLI 错误: {result.stderr}")
                return self._fallback_result(niche, error=result.stderr.strip())
            
            data = json.loads(result.stdout)
            
            # 本地缓存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            cache_path = self.cache_dir / f"research_{timestamp}.json"
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"研究结果已缓存: {cache_path}")
            
            return data
            
        except subprocess.TimeoutExpired:
            logger.error("last30days CLI 超时")
            return self._fallback_result(niche, error="CLI timeout")
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误: {e}")
            return self._fallback_result(niche, error=str(e))
        except FileNotFoundError:
            logger.error("last30days CLI 未安装")
            return self._fallback_result(niche, error="CLI not found")
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return self._fallback_result(niche, error=str(e))
    
    def _fallback_result(self, niche: str, error: str = None) -> Dict:
        """
        生成降级结果（CLI 不可用时）
        
        Args:
            niche: 研究领域
            error: 错误信息
            
        Returns:
            Dict: 降级结果
        """
        return {
            "niche": niche,
            "relevance_score": 50.0,
            "velocity_24h": 0.0,
            "authority_score": 50.0,
            "platform_count": 1,
            "summary": f"研究数据暂时不可用: {error}" if error else "使用降级数据",
            "citations": [],
            "platforms": ["fallback"],
            "created_at": datetime.now().isoformat(),
            "fallback": True
        }
    
    async def research_async(
        self,
        niche: str,
        days: int = 7,
        sources: str = "x,reddit,youtube,web,tiktok,hackernews"
    ) -> Dict:
        """
        异步版本的研究方法
        
        Args:
            niche: 研究领域/话题
            days: 回溯天数
            sources: 数据源
            
        Returns:
            Dict: 研究结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.research_topic,
            niche,
            days,
            sources
        )
    
    async def research_batch(
        self,
        niches: List[str],
        days: int = 7
    ) -> List[Dict]:
        """
        批量研究多个领域
        
        Args:
            niches: 领域列表
            days: 回溯天数
            
        Returns:
            List[Dict]: 研究结果列表
        """
        tasks = [self.research_async(niche, days) for niche in niches]
        return await asyncio.gather(*tasks)


# 便捷函数
def research_topic(
    niche: str,
    days: int = 7,
    sources: str = "x,reddit,youtube,web,tiktok,hackernews"
) -> Dict:
    """
    便捷函数：研究单个话题
    
    Args:
        niche: 研究领域
        days: 回溯天数
        sources: 数据源
        
    Returns:
        Dict: 研究结果
    """
    researcher = Researcher()
    return researcher.research_topic(niche, days, sources)


async def research_batch(niches: List[str], days: int = 7) -> List[Dict]:
    """
    便捷函数：批量研究
    
    Args:
        niches: 领域列表
        days: 回溯天数
        
    Returns:
        List[Dict]: 研究结果列表
    """
    researcher = Researcher()
    return await researcher.research_batch(niches, days)
