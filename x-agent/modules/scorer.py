"""
scorer.py - 热点复合评分模块

复合评分公式（满分 100）：
- Relevance (40%): last30days relevance_score
- Velocity (30%): 24h 互动增速 velocity_24h
- Authority (15%): 高赞作者/跨平台 authority_score
- Convergence (15%): 多平台同时出现 platform_count

v3.0: 直接使用 last30days 返回的字段
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TrendScorer:
    """热点评分器"""
    
    # 各维度权重
    WEIGHTS = {
        'relevance': 0.40,    # 40%
        'velocity': 0.30,    # 30%
        'authority': 0.15,   # 15%
        'convergence': 0.15  # 15%
    }
    
    # 阈值配置
    HIGH_THRESHOLD = 80.0    # 立即推送
    MEDIUM_THRESHOLD = 60.0  # 汇总展示
    STORE_THRESHOLD = 50.0   # 存储
    
    def __init__(self, db=None):
        """
        初始化评分器
        
        Args:
            db: Database 实例（用于查询历史数据）
        """
        self.db = db
    
    def calculate_score(self, trend_data: Dict) -> float:
        """
        计算热点的综合评分
        
        Args:
            trend_data: last30days 返回的数据，包含：
                - relevance_score: 相关度 (0-100)
                - velocity_24h: 24h互动增速 (0-100)
                - authority_score: 权威度 (0-100)
                - platform_count: 出现平台数
                
        Returns:
            float: 综合评分 (0-100)
        """
        # 从 last30days 字段计算
        relevance = self._normalize_score(trend_data.get('relevance_score', 50))
        velocity = self._normalize_score(trend_data.get('velocity_24h', 0))
        authority = self._normalize_score(trend_data.get('authority_score', 50))
        convergence = self._calc_convergence(trend_data.get('platform_count', 1))
        
        # 加权平均
        total_score = (
            relevance * self.WEIGHTS['relevance'] +
            velocity * self.WEIGHTS['velocity'] +
            authority * self.WEIGHTS['authority'] +
            convergence * self.WEIGHTS['convergence']
        )
        
        # 确保在 0-100 范围内
        final_score = max(0.0, min(100.0, total_score))
        
        logger.debug(
            f"评分计算: relevance={relevance:.1f}, velocity={velocity:.1f}, "
            f"authority={authority:.1f}, convergence={convergence:.1f} => {final_score:.1f}"
        )
        
        return final_score
    
    def _normalize_score(self, value: float) -> float:
        """
        标准化分数到 0-100
        
        Args:
            value: 原始分数
            
        Returns:
            float: 标准化后的分数
        """
        return max(0.0, min(100.0, float(value)))
    
    def _calc_convergence(self, platform_count: int) -> float:
        """
        计算汇聚性得分
        
        Args:
            platform_count: 出现的平台数量
            
        Returns:
            float: 汇聚性得分 (0-100)
        """
        # 平台数映射到分数
        # 5+ 平台: 100
        # 4 平台: 85
        # 3 平台: 70
        # 2 平台: 50
        # 1 平台: 30
        convergence_map = {
            1: 30.0,
            2: 50.0,
            3: 70.0,
            4: 85.0,
        }
        
        if platform_count >= 5:
            return 100.0
        return convergence_map.get(platform_count, 30.0)
    
    def get_score_level(self, score: float) -> str:
        """
        根据分数返回等级
        
        Args:
            score: 分数 (0-100)
            
        Returns:
            str: 等级 ('HIGH', 'MEDIUM', 'LOW')
        """
        if score >= self.HIGH_THRESHOLD:
            return 'HIGH'      # 立即推送
        elif score >= self.MEDIUM_THRESHOLD:
            return 'MEDIUM'    # 汇总展示
        else:
            return 'LOW'       # 丢弃或低优先级
    
    def should_push_immediately(self, score: float) -> bool:
        """是否应该立即推送"""
        return score >= self.HIGH_THRESHOLD
    
    def should_store(self, score: float) -> bool:
        """是否应该存储"""
        return score >= self.STORE_THRESHOLD
    
    def get_action(self, score: float) -> str:
        """
        根据分数返回建议动作
        
        Args:
            score: 分数 (0-100)
            
        Returns:
            str: 建议动作
        """
        if score >= self.HIGH_THRESHOLD:
            return 'PUSH_NOW'       # 立即推送到 Telegram
        elif score >= self.MEDIUM_THRESHOLD:
            return 'ADD_TO_DIGEST'  # 加入每日汇总
        elif score >= self.STORE_THRESHOLD:
            return 'STORE_ONLY'     # 仅存储，不推送
        else:
            return 'DISCARD'        # 丢弃
    
    def score_with_details(self, trend_data: Dict) -> Dict:
        """
        计算分数并返回详细信息
        
        Args:
            trend_data: 热点数据
            
        Returns:
            Dict: 包含分数和详情的结果
        """
        score = self.calculate_score(trend_data)
        
        return {
            **trend_data,
            'score': round(score, 2),
            'score_level': self.get_score_level(score),
            'action': self.get_action(score),
            'should_push': self.should_push_immediately(score),
            'should_store': self.should_store(score),
            'score_breakdown': {
                'relevance': self._normalize_score(trend_data.get('relevance_score', 50)),
                'velocity': self._normalize_score(trend_data.get('velocity_24h', 0)),
                'authority': self._normalize_score(trend_data.get('authority_score', 50)),
                'convergence': self._calc_convergence(trend_data.get('platform_count', 1))
            }
        }


def calculate_trend_score(trend_data: Dict, db=None) -> float:
    """
    便捷函数：计算热点评分
    
    Args:
        trend_data: 热点数据
        db: Database 实例
        
    Returns:
        float: 综合评分
    """
    scorer = TrendScorer(db)
    return scorer.calculate_score(trend_data)


def batch_calculate_scores(trend_list: List[Dict], db=None) -> List[Dict]:
    """
    批量计算热点评分
    
    Args:
        trend_list: 热点数据列表
        db: Database 实例
        
    Returns:
        List[Dict]: 添加了 score、score_level、action 的热点列表
    """
    scorer = TrendScorer(db)
    results = [scorer.score_with_details(trend) for trend in trend_list]
    
    # 按分数降序排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    logger.info(f"批量评分完成: {len(results)} 条, "
                f"HIGH={sum(1 for r in results if r['score_level'] == 'HIGH')}, "
                f"MEDIUM={sum(1 for r in results if r['score_level'] == 'MEDIUM')}")
    
    return results
