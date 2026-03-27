"""
test_scorer.py - 热点评分模块单元测试

覆盖 scorer.py 的全部公开方法和边界条件。
测试不依赖外部 API 或数据库，完全离线运行。
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.scorer import TrendScorer, calculate_trend_score


class TestTrendScorerHighScore:
    """高分（≥80）场景测试"""

    def setup_method(self):
        self.scorer = TrendScorer()

    def test_high_score_triggers_push_now(self):
        data = {
            "relevance_score": 90,
            "velocity_24h": 85,
            "authority_score": 80,
            "platform_count": 5,
        }
        score = self.scorer.calculate_score(data)
        assert score >= 80.0
        assert self.scorer.should_push_immediately(score) is True
        assert self.scorer.get_score_level(score) == "HIGH"
        assert self.scorer.get_action(score) == "PUSH_NOW"

    def test_high_score_also_stored(self):
        data = {"relevance_score": 90, "velocity_24h": 85, "authority_score": 80, "platform_count": 5}
        score = self.scorer.calculate_score(data)
        assert self.scorer.should_store(score) is True


class TestTrendScorerMediumScore:
    """中分（60-79）场景测试"""

    def setup_method(self):
        self.scorer = TrendScorer()

    def test_medium_score_goes_to_digest(self):
        data = {
            "relevance_score": 70,
            "velocity_24h": 60,
            "authority_score": 50,
            "platform_count": 3,
        }
        score = self.scorer.calculate_score(data)
        assert 60.0 <= score < 80.0
        assert self.scorer.should_push_immediately(score) is False
        assert self.scorer.should_store(score) is True
        assert self.scorer.get_score_level(score) == "MEDIUM"
        assert self.scorer.get_action(score) == "ADD_TO_DIGEST"


class TestTrendScorerLowScore:
    """低分（<50）场景测试"""

    def setup_method(self):
        self.scorer = TrendScorer()

    def test_low_score_discarded(self):
        data = {
            "relevance_score": 20,
            "velocity_24h": 15,
            "authority_score": 30,
            "platform_count": 1,
        }
        score = self.scorer.calculate_score(data)
        assert score < 50.0
        assert self.scorer.should_store(score) is False
        assert self.scorer.get_score_level(score) == "LOW"
        assert self.scorer.get_action(score) == "DISCARD"


class TestTrendScorerBoundaryValues:
    """边界值测试"""

    def setup_method(self):
        self.scorer = TrendScorer()

    def test_all_max_values_give_100(self):
        data = {
            "relevance_score": 100,
            "velocity_24h": 100,
            "authority_score": 100,
            "platform_count": 5,
        }
        assert self.scorer.calculate_score(data) == 100.0

    def test_all_zero_values_nonnegative(self):
        data = {
            "relevance_score": 0,
            "velocity_24h": 0,
            "authority_score": 0,
            "platform_count": 1,
        }
        assert self.scorer.calculate_score(data) >= 0.0

    def test_over_max_capped_at_100(self):
        data = {
            "relevance_score": 999,
            "velocity_24h": 999,
            "authority_score": 999,
            "platform_count": 100,
        }
        assert self.scorer.calculate_score(data) == 100.0

    def test_negative_values_floor_at_zero(self):
        data = {
            "relevance_score": -50,
            "velocity_24h": -100,
            "authority_score": -10,
            "platform_count": 0,
        }
        assert self.scorer.calculate_score(data) >= 0.0

    def test_missing_all_fields_no_crash(self):
        score = self.scorer.calculate_score({})
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_missing_partial_fields_no_crash(self):
        score = self.scorer.calculate_score({"relevance_score": 80})
        assert isinstance(score, float)


class TestTrendScorerWeightFormula:
    """权重公式验证：R×0.40 + V×0.30 + A×0.15 + C×0.15"""

    def setup_method(self):
        self.scorer = TrendScorer()

    def test_uniform_50_gives_50(self):
        """全 50 分（platform_count=2 → convergence=50）结果应为 50"""
        data = {
            "relevance_score": 50,
            "velocity_24h": 50,
            "authority_score": 50,
            "platform_count": 2,
        }
        score = self.scorer.calculate_score(data)
        assert abs(score - 50.0) < 0.01

    def test_exact_formula(self):
        """验证公式：R=100,V=50,A=50,C=50(pc=2) → 100*0.4+50*0.3+50*0.15+50*0.15=70"""
        data = {
            "relevance_score": 100,
            "velocity_24h": 50,
            "authority_score": 50,
            "platform_count": 2,
        }
        score = self.scorer.calculate_score(data)
        assert abs(score - 70.0) < 0.01

    def test_relevance_impacts_more_than_velocity(self):
        """相关度（40%）对分数影响应大于速度（30%）"""
        base = {"velocity_24h": 50, "authority_score": 50, "platform_count": 2}
        relevance_impact = (
            self.scorer.calculate_score({**base, "relevance_score": 100})
            - self.scorer.calculate_score({**base, "relevance_score": 0})
        )
        base2 = {"relevance_score": 50, "authority_score": 50, "platform_count": 2}
        velocity_impact = (
            self.scorer.calculate_score({**base2, "velocity_24h": 100})
            - self.scorer.calculate_score({**base2, "velocity_24h": 0})
        )
        assert relevance_impact > velocity_impact


class TestTrendScorerConvergence:
    """平台汇聚性映射测试"""

    def setup_method(self):
        self.scorer = TrendScorer()

    @pytest.mark.parametrize("platform_count,expected", [
        (1, 30.0),
        (2, 50.0),
        (3, 70.0),
        (4, 85.0),
        (5, 100.0),
        (10, 100.0),
        (0, 30.0),
    ])
    def test_convergence_mapping(self, platform_count, expected):
        assert self.scorer._calc_convergence(platform_count) == expected


class TestTrendScorerNormalizeScore:
    """分数标准化测试"""

    def setup_method(self):
        self.scorer = TrendScorer()

    def test_normalize_normal_value(self):
        assert self.scorer._normalize_score(50) == 50.0

    def test_normalize_over_100(self):
        assert self.scorer._normalize_score(150) == 100.0

    def test_normalize_negative(self):
        assert self.scorer._normalize_score(-10) == 0.0

    def test_normalize_zero(self):
        assert self.scorer._normalize_score(0) == 0.0

    def test_normalize_100(self):
        assert self.scorer._normalize_score(100) == 100.0


class TestScoreWithDetails:
    """score_with_details 方法测试"""

    def setup_method(self):
        self.scorer = TrendScorer()

    def test_returns_all_required_keys(self):
        data = {"relevance_score": 75, "velocity_24h": 60, "authority_score": 70, "platform_count": 3}
        result = self.scorer.score_with_details(data)
        for key in ("score", "score_level", "action", "should_push", "should_store", "score_breakdown"):
            assert key in result, f"缺少字段: {key}"

    def test_score_breakdown_has_four_dimensions(self):
        data = {"relevance_score": 75, "velocity_24h": 60, "authority_score": 70, "platform_count": 3}
        breakdown = self.scorer.score_with_details(data)["score_breakdown"]
        for dim in ("relevance", "velocity", "authority", "convergence"):
            assert dim in breakdown

    def test_original_fields_preserved(self):
        data = {"relevance_score": 80, "topic": "AI tools"}
        result = self.scorer.score_with_details(data)
        assert result["topic"] == "AI tools"

    def test_score_rounded_to_2_decimal(self):
        data = {"relevance_score": 75, "velocity_24h": 60, "authority_score": 70, "platform_count": 3}
        result = self.scorer.score_with_details(data)
        assert result["score"] == round(result["score"], 2)


class TestCalculateTrendScoreFunction:
    """便捷函数 calculate_trend_score 测试"""

    def test_returns_float(self):
        result = calculate_trend_score({"relevance_score": 70})
        assert isinstance(result, float)

    def test_consistent_with_class_method(self):
        data = {"relevance_score": 80, "velocity_24h": 70, "platform_count": 3}
        scorer = TrendScorer()
        assert calculate_trend_score(data) == scorer.calculate_score(data)

    def test_empty_dict_no_crash(self):
        result = calculate_trend_score({})
        assert isinstance(result, float)
