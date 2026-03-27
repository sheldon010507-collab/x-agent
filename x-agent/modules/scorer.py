"""
scorer.py - 热点复合评分模块 【V0 Final】

功能:
- 四维评分系统(Relevance + Velocity + Authority + Convergence)
- 风险评分计算(risk_score)
- 热点等级判定(HIGH/MEDIUM/LOW)

版本: V0 Final
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TrendScorer:
    """热点评分器 - V0 Final"""

    # 各维度权重
    WEIGHTS = {
        "relevance": 0.40,  # 40%
        "velocity": 0.30,  # 30%
        "authority": 0.15,  # 15%
        "convergence": 0.15,  # 15%
    }

    # 阈值配置
    HIGH_THRESHOLD = 80.0  # 立即推送
    MEDIUM_THRESHOLD = 60.0  # 汇总展示
    STORE_THRESHOLD = 50.0  # 存储

    def __init__(self, db=None):
        """初始化评分器"""
        self.db = db

    def calculate_score(self, trend_data: Dict) -> float:
        """
        计算热点的综合评分

        Args:
            trend_data: 包含评分字段的数据

        Returns:
            float: 综合评分 (0-100)
        """
        relevance = self._normalize_score(trend_data.get("relevance_score", 50))
        velocity = self._normalize_score(trend_data.get("velocity_24h", 0))
        authority = self._normalize_score(trend_data.get("authority_score", 50))
        convergence = self._calc_convergence(trend_data.get("platform_count", 1))

        total_score = (
            relevance * self.WEIGHTS["relevance"]
            + velocity * self.WEIGHTS["velocity"]
            + authority * self.WEIGHTS["authority"]
            + convergence * self.WEIGHTS["convergence"]
        )

        return max(0.0, min(100.0, total_score))

    def _normalize_score(self, value: float) -> float:
        """标准化分数到 0-100"""
        return max(0.0, min(100.0, float(value)))

    def _calc_convergence(self, platform_count: int) -> float:
        """计算汇聚性得分"""
        convergence_map = {1: 30.0, 2: 50.0, 3: 70.0, 4: 85.0}
        if platform_count >= 5:
            return 100.0
        return convergence_map.get(platform_count, 30.0)

    def get_score_level(self, score: float) -> str:
        """根据分数返回等级"""
        if score >= self.HIGH_THRESHOLD:
            return "HIGH"
        elif score >= self.MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "LOW"

    def should_push_immediately(self, score: float) -> bool:
        """是否应该立即推送"""
        return score >= self.HIGH_THRESHOLD

    def should_store(self, score: float) -> bool:
        """是否应该存储"""
        return score >= self.STORE_THRESHOLD

    def get_action(self, score: float) -> str:
        """根据分数返回建议动作"""
        if score >= self.HIGH_THRESHOLD:
            return "PUSH_NOW"
        elif score >= self.MEDIUM_THRESHOLD:
            return "ADD_TO_DIGEST"
        elif score >= self.STORE_THRESHOLD:
            return "STORE_ONLY"
        else:
            return "DISCARD"

    def score_with_details(self, trend_data: Dict) -> Dict:
        """计算分数并返回详细信息"""
        score = self.calculate_score(trend_data)
        return {
            **trend_data,
            "score": round(score, 2),
            "score_level": self.get_score_level(score),
            "action": self.get_action(score),
            "should_push": self.should_push_immediately(score),
            "should_store": self.should_store(score),
            "score_breakdown": {
                "relevance": self._normalize_score(trend_data.get("relevance_score", 50)),
                "velocity": self._normalize_score(trend_data.get("velocity_24h", 0)),
                "authority": self._normalize_score(trend_data.get("authority_score", 50)),
                "convergence": self._calc_convergence(trend_data.get("platform_count", 1)),
            },
        }


def calculate_trend_score(trend_data: Dict) -> float:
    """便捷函数: 计算热点评分"""
    scorer = TrendScorer()
    return scorer.calculate_score(trend_data)
