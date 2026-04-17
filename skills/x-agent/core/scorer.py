"""
scorer.py - 热点评分模块

两套评分系统：
1. **Trend-level scoring** (TrendScorer): 趋势整体评分
   - 4维: relevance + velocity + authority + convergence
   - 增强: 时间衰减 + 平台多样性奖励

2. **Post-level engagement scoring** (PostScorer): 单帖热度评分
   - 基于真实互动数据 (likes/retweets/views/comments)
   - 按平台不同权重
   - velocity = engagement / 已发布小时数
"""

import logging
import math
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ============ 数字解析工具 ============

def parse_count(value) -> int:
    """
    解析各种格式的数字字符串
    '1.2K' → 1200
    '3.4M' → 3400000
    '500' → 500
    1234 → 1234
    """
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip().upper().replace(",", "")
    if not s:
        return 0
    m = re.match(r"^([\d.]+)\s*([KMB])?", s)
    if not m:
        try:
            return int(float(s))
        except ValueError:
            return 0
    num_str, suffix = m.groups()
    try:
        n = float(num_str)
    except ValueError:
        return 0
    multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(suffix, 1)
    return int(n * multiplier)


# ============ Post-level Engagement Scoring ============

# 各平台的字段 → 权重映射
PLATFORM_ENGAGEMENT_WEIGHTS = {
    "x": {"likes": 1.0, "retweets": 2.0, "replies": 3.0, "views": 0.01},
    "twitter": {"likes": 1.0, "retweets": 2.0, "replies": 3.0, "views": 0.01},
    "reddit": {"score": 1.0, "num_comments": 2.0},
    "hackernews": {"score": 1.0, "descendants": 2.0},
    "youtube": {"views": 0.01, "likes": 1.0},
    "tiktok": {"engagement": 0.01},
    "google_trends": {"score": 1.0},
}


class PostScorer:
    """单帖级别的热度评分（基于真实 engagement）"""

    def engagement(self, post: Dict, platform: str) -> float:
        """计算帖子的加权总互动数"""
        weights = PLATFORM_ENGAGEMENT_WEIGHTS.get(platform.lower(), {})
        if not weights:
            # 兜底：尝试常见字段
            return float(parse_count(post.get("score", 0)))
        total = 0.0
        for field, weight in weights.items():
            val = parse_count(post.get(field, 0))
            total += val * weight
        return total

    def age_hours(self, post: Dict) -> float:
        """估算帖子年龄（小时）"""
        # 不同平台的时间字段不同
        for field in ("created_at", "time", "created_utc", "published"):
            v = post.get(field)
            if v is None:
                continue
            try:
                # ISO string
                if isinstance(v, str):
                    if v.replace(".", "").isdigit():
                        ts = float(v)
                        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    else:
                        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                # Unix timestamp
                elif isinstance(v, (int, float)):
                    dt = datetime.fromtimestamp(float(v), tz=timezone.utc)
                else:
                    continue
                age = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                return max(0.5, age)  # 最小 0.5 小时
            except (ValueError, OSError):
                continue
        return 24.0  # 未知则当 1 天前

    def velocity(self, post: Dict, platform: str) -> float:
        """每小时获得的 engagement（窜得多快）"""
        return self.engagement(post, platform) / self.age_hours(post)

    def score_post(self, post: Dict, platform: str) -> Dict:
        """给单帖打分并返回详细字段"""
        engagement = self.engagement(post, platform)
        age_h = self.age_hours(post)
        vel = engagement / age_h
        return {
            **post,
            "platform": platform,
            "engagement_score": round(engagement, 1),
            "age_hours": round(age_h, 2),
            "velocity_per_hour": round(vel, 2),
        }

    def rank_posts(self, posts: List[Dict], platform: str, by: str = "engagement") -> List[Dict]:
        """按 engagement 或 velocity 给帖子排序（降序）"""
        scored = [self.score_post(p, platform) for p in posts]
        key = "engagement_score" if by == "engagement" else "velocity_per_hour"
        return sorted(scored, key=lambda p: p.get(key, 0), reverse=True)


# ============ Trend-level Scoring ============

class TrendScorer:
    """趋势整体评分（多平台聚合）"""

    WEIGHTS = {
        "relevance": 0.25,
        "velocity": 0.30,
        "authority": 0.15,
        "convergence": 0.15,
        "engagement": 0.10,        # 真实互动数据
        "temporal_decay": 0.025,
        "platform_diversity": 0.025,
    }

    HIGH_THRESHOLD = 80.0
    MEDIUM_THRESHOLD = 60.0
    STORE_THRESHOLD = 50.0

    def __init__(self):
        self.post_scorer = PostScorer()

    def calculate_score(self, trend_data: Dict) -> float:
        relevance = self._normalize(trend_data.get("relevance_score", 50))
        velocity = self._normalize(trend_data.get("velocity_24h", 0))
        authority = self._normalize(trend_data.get("authority_score", 50))
        convergence = self._calc_convergence(trend_data.get("platform_count", 1))
        engagement = self._normalize(trend_data.get("engagement_score", 50))

        base = (
            relevance * self.WEIGHTS["relevance"]
            + velocity * self.WEIGHTS["velocity"]
            + authority * self.WEIGHTS["authority"]
            + convergence * self.WEIGHTS["convergence"]
            + engagement * self.WEIGHTS["engagement"]
        )

        # 时间衰减
        if "created_at" in trend_data:
            decay = self._temporal_decay(trend_data["created_at"])
            base += 100 * self.WEIGHTS["temporal_decay"] * decay

        # 平台多样性
        diversity = self._platform_diversity_bonus(
            trend_data.get("platform_sources"), trend_data.get("platform_count")
        )
        base *= diversity

        return max(0.0, min(100.0, base))

    @staticmethod
    def _normalize(value) -> float:
        try:
            return max(0.0, min(100.0, float(value)))
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _calc_convergence(platform_count: int) -> float:
        if platform_count >= 5:
            return 100.0
        return {1: 30.0, 2: 50.0, 3: 70.0, 4: 85.0}.get(platform_count, 30.0)

    @staticmethod
    def _temporal_decay(created_at, half_life_days: int = 7) -> float:
        try:
            if not created_at:
                return 1.0
            if isinstance(created_at, str):
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                dt = created_at
            age_hours = (datetime.now(dt.tzinfo) - dt).total_seconds() / 3600
            return max(0.01, min(1.0, math.pow(0.5, age_hours / (half_life_days * 24))))
        except Exception:
            return 1.0

    @staticmethod
    def _platform_diversity_bonus(platform_sources=None, platform_count=None) -> float:
        if platform_sources:
            unique = set(p.lower() for p in platform_sources)
            count = len(unique)
            bonus = {1: 1.0, 2: 1.08, 3: 1.15}.get(count, 1.20 if count >= 4 else 1.0)
            if {"hackernews", "reddit"}.issubset(unique):
                bonus += 0.02
            if {"x", "hackernews"}.issubset(unique):
                bonus += 0.02
            return min(bonus, 1.25)
        elif platform_count:
            return {1: 1.0, 2: 1.08, 3: 1.15}.get(platform_count, 1.20)
        return 1.0

    def get_level(self, score: float) -> str:
        if score >= self.HIGH_THRESHOLD:
            return "HIGH"
        elif score >= self.MEDIUM_THRESHOLD:
            return "MEDIUM"
        return "LOW"

    def get_action(self, score: float) -> str:
        if score >= self.HIGH_THRESHOLD:
            return "PUSH_NOW"
        elif score >= self.MEDIUM_THRESHOLD:
            return "ADD_TO_DIGEST"
        elif score >= self.STORE_THRESHOLD:
            return "STORE_ONLY"
        return "DISCARD"

    def score_with_details(self, trend_data: Dict) -> Dict:
        score = self.calculate_score(trend_data)
        return {
            **trend_data,
            "score": round(score, 2),
            "score_level": self.get_level(score),
            "action": self.get_action(score),
        }
