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
    """热点评分器 - V0 Final（增强版：支持时间衰减和平台多样性）"""

    # 基础权重（V0 Final）
    WEIGHTS_BASE = {
        "relevance": 0.40,  # 40%
        "velocity": 0.30,  # 30%
        "authority": 0.15,  # 15%
        "convergence": 0.15,  # 15%
    }

    # 增强权重（包含新因子）
    WEIGHTS_ENHANCED = {
        "relevance": 0.35,  # 35%
        "velocity": 0.25,  # 25%
        "authority": 0.15,  # 15%
        "convergence": 0.15,  # 15%
        "temporal_decay": 0.05,  # 5% (新增)
        "platform_diversity": 0.05,  # 5% (新增)
    }

    # V3 权重（加入 engagement）
    WEIGHTS_V3 = {
        "relevance": 0.30,  # 30% (降低)
        "velocity": 0.20,  # 20% (降低)
        "authority": 0.15,  # 15%
        "convergence": 0.15,  # 15%
        "engagement": 0.20,  # 20% (新增 - 真实转发/点赞)
    }

    # 各维度权重（保持向后兼容）
    WEIGHTS = WEIGHTS_BASE

    # 阈值配置
    HIGH_THRESHOLD = 80.0  # 立即推送
    MEDIUM_THRESHOLD = 60.0  # 汇总展示
    STORE_THRESHOLD = 50.0  # 存储

    def __init__(self, db=None):
        """初始化评分器"""
        self.db = db

    def calculate_score(self, trend_data: Dict, use_engagement: bool = True) -> float:
        """
        计算热点的综合评分

        Args:
            trend_data: 包含评分字段的数据
            use_engagement: 是否使用 engagement 分数（默认 True）

        Returns:
            float: 综合评分 (0-100)
        """
        relevance = self._normalize_score(trend_data.get("relevance_score", 50))
        velocity = self._normalize_score(trend_data.get("velocity_24h", 0))
        authority = self._normalize_score(trend_data.get("authority_score", 50))
        convergence = self._calc_convergence(trend_data.get("platform_count", 1))

        # 支持 engagement_score（如果存在且启用）
        if use_engagement and "engagement_score" in trend_data:
            engagement = self._normalize_score(trend_data.get("engagement_score", 0))
            weights = self.WEIGHTS_V3
        else:
            engagement = 0
            weights = self.WEIGHTS

        total_score = (
            relevance * weights["relevance"]
            + velocity * weights["velocity"]
            + authority * weights["authority"]
            + convergence * weights["convergence"]
        )

        # 如果使用 engagement，添加到评分中
        if use_engagement and "engagement_score" in trend_data:
            total_score += engagement * weights.get("engagement", 0)

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

    # ========== 增强功能：时间衰减 + 平台多样性 ==========

    def _calculate_temporal_decay(self, created_at: str, half_life_days: int = 7) -> float:
        """
        计算时间衰减因子（基于指数衰减）

        新鲜内容 (0天) → 1.0 (100%)
        1天老 → 0.85
        3天老 → 0.65
        7天老 → 0.3
        14天老 → 0.1

        Args:
            created_at: ISO格式的创建时间字符串
            half_life_days: 半衰期（天数），默认7天

        Returns:
            衰减因子 (0.01-1.0)
        """
        try:
            if not created_at:
                return 1.0

            # 解析时间
            if isinstance(created_at, str):
                created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                created_dt = created_at

            # 计算年龄
            age_timedelta = datetime.now(created_dt.tzinfo) - created_dt
            age_hours = age_timedelta.total_seconds() / 3600

            # 指数衰减：decay = 0.5^(age / half_life)
            import math

            half_life_hours = half_life_days * 24
            decay = math.pow(0.5, age_hours / half_life_hours)

            # 限制在 0.01 ~ 1.0 范围内
            return max(0.01, min(1.0, decay))

        except Exception as e:
            logger.warning(f"Error calculating temporal decay: {e}, using default 1.0")
            return 1.0

    def _calculate_platform_diversity_bonus(
        self, platform_sources: List[str] = None, platform_count: int = None
    ) -> float:
        """
        计算平台多样性奖励

        逻辑：
        - 1个平台：1.0 (无奖励)
        - 2个平台：1.08 (+8%)
        - 3个平台：1.15 (+15%)
        - 4+个平台：1.20 (+20%)

        高权威平台组合额外奖励：
        - HackerNews + Reddit = +10% (都是高信号源)
        - X + HackerNews = +12%

        Args:
            platform_sources: 平台源列表 (如 ['reddit', 'hackernews', 'x'])
            platform_count: 或直接传入平台数量

        Returns:
            多样性奖励倍数 (1.0-1.25)
        """
        if platform_sources:
            unique_platforms = set(p.lower() for p in platform_sources)
            count = len(unique_platforms)

            # 基础奖励
            bonus = 1.0
            if count == 2:
                bonus = 1.08
            elif count == 3:
                bonus = 1.15
            elif count >= 4:
                bonus = 1.20

            # 高权威平台组合额外奖励
            high_authority = {"hackernews", "reddit"}
            if high_authority.issubset(unique_platforms):
                bonus += 0.02

            if {"x", "hackernews"}.issubset(unique_platforms):
                bonus += 0.02

            return min(bonus, 1.25)  # 上限1.25 (+25%)

        elif platform_count:
            # 回退到基于计数的计算
            if platform_count == 1:
                return 1.0
            elif platform_count == 2:
                return 1.08
            elif platform_count == 3:
                return 1.15
            else:
                return 1.20

        return 1.0

    def calculate_score_v2(
        self,
        trend_data: Dict,
        enable_temporal_decay: bool = True,
        enable_platform_diversity: bool = True,
    ) -> float:
        """
        增强版评分计算（支持时间衰减和平台多样性）

        向后兼容：如果缺少新字段则自动降级

        Args:
            trend_data: 趋势数据
            enable_temporal_decay: 是否启用时间衰减
            enable_platform_diversity: 是否启用平台多样性奖励

        Returns:
            float: 综合评分 (0-100)
        """
        # 基础评分
        relevance = self._normalize_score(trend_data.get("relevance_score", 50))
        velocity = self._normalize_score(trend_data.get("velocity_24h", 0))
        authority = self._normalize_score(trend_data.get("authority_score", 50))
        convergence = self._calc_convergence(trend_data.get("platform_count", 1))

        # 使用增强权重
        base_score = (
            relevance * self.WEIGHTS_ENHANCED["relevance"]
            + velocity * self.WEIGHTS_ENHANCED["velocity"]
            + authority * self.WEIGHTS_ENHANCED["authority"]
            + convergence * self.WEIGHTS_ENHANCED["convergence"]
        )

        # 应用时间衰减
        temporal_factor = 1.0
        if enable_temporal_decay and "created_at" in trend_data:
            temporal_factor = self._calculate_temporal_decay(trend_data["created_at"])
            base_score += 100 * self.WEIGHTS_ENHANCED["temporal_decay"] * temporal_factor

        # 应用平台多样性奖励
        diversity_factor = 1.0
        if enable_platform_diversity:
            diversity_factor = self._calculate_platform_diversity_bonus(
                platform_sources=trend_data.get("platform_sources"),
                platform_count=trend_data.get("platform_count"),
            )
            base_score *= diversity_factor

        return max(0.0, min(100.0, base_score))

    def score_with_details_v2(
        self,
        trend_data: Dict,
        enable_temporal_decay: bool = True,
        enable_platform_diversity: bool = True,
    ) -> Dict:
        """
        增强版详细评分（包含新因子的完整分析）

        Args:
            trend_data: 趋势数据
            enable_temporal_decay: 是否启用时间衰减
            enable_platform_diversity: 是否启用平台多样性奖励

        Returns:
            包含详细分解的评分字典
        """
        # 计算各项
        relevance = self._normalize_score(trend_data.get("relevance_score", 50))
        velocity = self._normalize_score(trend_data.get("velocity_24h", 0))
        authority = self._normalize_score(trend_data.get("authority_score", 50))
        convergence = self._calc_convergence(trend_data.get("platform_count", 1))

        # 计算新因子
        temporal_decay = 1.0
        if enable_temporal_decay and "created_at" in trend_data:
            temporal_decay = self._calculate_temporal_decay(trend_data["created_at"])

        diversity_bonus = 1.0
        if enable_platform_diversity:
            diversity_bonus = self._calculate_platform_diversity_bonus(
                platform_sources=trend_data.get("platform_sources"),
                platform_count=trend_data.get("platform_count"),
            )

        # 计算最终分数
        score = self.calculate_score_v2(
            trend_data,
            enable_temporal_decay=enable_temporal_decay,
            enable_platform_diversity=enable_platform_diversity,
        )

        return {
            **trend_data,
            "score": round(score, 2),
            "score_level": self.get_score_level(score),
            "action": self.get_action(score),
            "should_push": self.should_push_immediately(score),
            "should_store": self.should_store(score),
            "score_breakdown": {
                "relevance": relevance,
                "velocity": velocity,
                "authority": authority,
                "convergence": convergence,
                "temporal_decay": round(temporal_decay, 3),
                "platform_diversity_bonus": round(diversity_bonus, 3),
            },
            "temporal_analysis": (
                {
                    "created_at": trend_data.get("created_at"),
                    "decay_factor": round(temporal_decay, 3),
                }
                if enable_temporal_decay
                else None
            ),
            "diversity_analysis": (
                {
                    "platforms": trend_data.get("platform_sources", []),
                    "bonus_factor": round(diversity_bonus, 3),
                }
                if enable_platform_diversity
                else None
            ),
        }


def calculate_trend_score(trend_data: Dict) -> float:
    """便捷函数: 计算热点评分（基础版，V0兼容）"""
    scorer = TrendScorer()
    return scorer.calculate_score(trend_data)


def calculate_trend_score_v2(
    trend_data: Dict,
    enable_temporal_decay: bool = True,
    enable_platform_diversity: bool = True,
) -> float:
    """便捷函数: 计算热点评分（增强版，含时间衰减+平台多样性）"""
    scorer = TrendScorer()
    return scorer.calculate_score_v2(
        trend_data,
        enable_temporal_decay=enable_temporal_decay,
        enable_platform_diversity=enable_platform_diversity,
    )
