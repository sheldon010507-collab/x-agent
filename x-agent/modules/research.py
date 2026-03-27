"""
research.py - 数据采集模块

【V0 Final】此版本为生产级开源版本

功能：
- 多平台深度研究（X + Reddit + YouTube + HN + Web + TikTok）
- 调用 last30days CLI（可选增强模块）
- 生成带 risk_score 的研究结果
- 异步并行采集支持

风险提示：
- last30days CLI 未安装时使用 fallback 模式
- 数据采集结果仅供参考，不构成投资建议

版本：V0 Final
"""

import subprocess
import json
import asyncio
import shutil
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Researcher:
    """研究员 - 负责多平台数据采集
    
    【V0 Final】风险提示：自动化数据采集可能触发平台限流
    """
    
    def __init__(self, config=None):
        """初始化研究员
        
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
        """调用 last30days CLI 进行多平台深度研究
        
        【V0 Final】风险提示：研究结果包含 risk_score，用于判断是否可自动发布
        
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
                - risk_score: 风险评分 (V0 Final 新增)
                - summary: 摘要
                - citations: 引用来源
        """
        logger.info(f"开始研究: {niche}, days={days}, sources={sources}")
        
        # V0 Final: 使用 shutil.which 检查 CLI 是否安装
        if not shutil.which("last30days"):
            logger.warning("last30days CLI 未安装，使用 fallback 趋势源")
            return self._fallback_result(niche, error="CLI not installed (optional enhancement)")
        
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
            
            # V0 Final: 添加 risk_score 计算
            data['risk_score'] = self._calculate_risk_score(data)
            
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
    
    def _calculate_risk_score(self, data: Dict) -> float:
        """V0 Final: 计算风险评分
        
        风险评分逻辑：
        - velocity 过高 (+20风险)
        - 平台数过少 (+15风险)
        - authority 过低 (+10风险)
        
        risk_score 越低越安全，< 70 才可自动发布
        
        Args:
            data: 研究数据
        
        Returns:
            float: 风险评分 (0-100)，越低越安全
        """
        base_risk = 30.0  # 基础风险
        
        velocity = data.get('velocity_24h', 0)
        platform_count = data.get('platform_count', 1)
        authority = data.get('authority_score', 50)
        
        # 增速过高增加风险
        if velocity > 80:
            base_risk += 20
        elif velocity > 60:
            base_risk += 10
        
        # 平台数过少增加风险
        if platform_count < 2:
            base_risk += 15
        elif platform_count < 3:
            base_risk += 8
        
        # 权威度过低增加风险
        if authority < 40:
            base_risk += 10
        elif authority < 60:
            base_risk += 5
        
        return min(100.0, max(0.0, base_risk))
    
    def _fallback_result(self, niche: str, error: str = None) -> Dict:
        """生成降级结果（CLI 不可用时）
        
        Args:
            niche: 研究领域
            error: 错误信息
        
        Returns:
            Dict: 降级结果，包含默认 risk_score=50
        """
        return {
            "niche": niche,
            "relevance_score": 50.0,
            "velocity_24h": 0.0,
            "authority_score": 50.0,
            "platform_count": 1,
            "risk_score": 50.0,  # V0 Final: fallback 风险评分
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
        """异步版本的研究方法
        
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
        """批量研究多个领域
        
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
    """便捷函数：研究单个话题
    
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
    """便捷函数：批量研究
    
    Args:
        niches: 领域列表
        days: 回溯天数
    
    Returns:
        List[Dict]: 研究结果列表
    """
    researcher = Researcher()
    return await researcher.research_batch(niches, days)
