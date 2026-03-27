"""
test_research.py - Researcher 单元测试

测试策略：Mock 所有平台 fetcher，完全离线
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.research import Researcher, research_topic

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def researcher(tmp_path):
    """创建 Researcher 实例，mock 所有网络依赖"""
    with (
        patch("modules.research.RedditFetcher") as mock_reddit,
        patch("modules.research.HackerNewsFetcher") as mock_hn,
        patch("modules.research.GoogleTrendsFetcher") as mock_trends,
        patch("modules.research.SimulatedPlatformFetcher") as mock_sim,
    ):
        mock_reddit.return_value.fetch = AsyncMock(
            return_value={"posts": [], "engagement": 500, "top_posts": []}
        )
        mock_hn.return_value.fetch = AsyncMock(
            return_value={"posts": [], "engagement": 200, "top_posts": []}
        )
        mock_trends.return_value.fetch = AsyncMock(
            return_value={"posts": [], "interest": 75, "related_queries": []}
        )
        mock_sim.return_value.fetch = AsyncMock(
            return_value={"posts": [], "engagement": 800, "top_posts": []}
        )
        r = Researcher(config=None)
        r.cache_dir = tmp_path / "research"
        r.cache_dir.mkdir()
        yield r


# ---------------------------------------------------------------------------
# Researcher init
# ---------------------------------------------------------------------------


class TestResearcherInit:
    def test_cache_dir_created(self, researcher):
        assert researcher.cache_dir.exists()

    def test_has_all_fetchers(self, researcher):
        assert hasattr(researcher, "reddit_fetcher")
        assert hasattr(researcher, "hn_fetcher")
        assert hasattr(researcher, "trends_fetcher")
        assert hasattr(researcher, "simulated_fetcher")


# ---------------------------------------------------------------------------
# _empty_result
# ---------------------------------------------------------------------------


class TestEmptyResult:
    def test_has_all_required_fields(self, researcher):
        result = researcher._empty_result("ai_tools")
        for field in [
            "niche",
            "relevance_score",
            "velocity_24h",
            "authority_score",
            "platform_count",
            "risk_score",
            "summary",
            "citations",
            "platforms",
            "created_at",
            "error",
        ]:
            assert field in result, f"Missing field: {field}"

    def test_preserves_niche(self, researcher):
        result = researcher._empty_result("crypto")
        assert result["niche"] == "crypto"

    def test_error_none_by_default(self, researcher):
        result = researcher._empty_result("general")
        assert result["error"] is None

    def test_error_stored_when_provided(self, researcher):
        result = researcher._empty_result("general", "connection timeout")
        assert "connection timeout" in result["error"]
        assert "connection timeout" in result["summary"]

    def test_risk_score_100_on_empty(self, researcher):
        result = researcher._empty_result("general")
        assert result["risk_score"] == 100.0

    def test_scores_are_zero(self, researcher):
        result = researcher._empty_result("general")
        assert result["relevance_score"] == 0.0
        assert result["velocity_24h"] == 0.0
        assert result["authority_score"] == 0.0
        assert result["platform_count"] == 0


# ---------------------------------------------------------------------------
# _calculate_risk_score
# ---------------------------------------------------------------------------


class TestCalculateRiskScore:
    def test_base_risk_is_30(self, researcher):
        # platform_count >= 3, velocity <= 60, authority >= 60 → pure base 30
        metrics = {"velocity": 50, "authority": 65, "platform_count": 3}
        score = researcher._calculate_risk_score(metrics)
        assert score == 30

    def test_high_velocity_increases_risk(self, researcher):
        low_v = researcher._calculate_risk_score(
            {"velocity": 50, "authority": 65, "platform_count": 3}
        )
        high_v = researcher._calculate_risk_score(
            {"velocity": 90, "authority": 65, "platform_count": 3}
        )
        assert high_v > low_v

    def test_few_platforms_increases_risk(self, researcher):
        many = researcher._calculate_risk_score(
            {"velocity": 50, "authority": 65, "platform_count": 5}
        )
        few = researcher._calculate_risk_score(
            {"velocity": 50, "authority": 65, "platform_count": 1}
        )
        assert few > many

    def test_low_authority_increases_risk(self, researcher):
        high_a = researcher._calculate_risk_score(
            {"velocity": 50, "authority": 80, "platform_count": 3}
        )
        low_a = researcher._calculate_risk_score(
            {"velocity": 50, "authority": 20, "platform_count": 3}
        )
        assert low_a > high_a

    def test_risk_capped_at_100(self, researcher):
        score = researcher._calculate_risk_score(
            {"velocity": 100, "authority": 5, "platform_count": 1}
        )
        assert score <= 100

    def test_risk_never_negative(self, researcher):
        score = researcher._calculate_risk_score(
            {"velocity": 0, "authority": 100, "platform_count": 10}
        )
        assert score >= 0


# ---------------------------------------------------------------------------
# research_async
# ---------------------------------------------------------------------------


class TestResearchAsync:
    @pytest.mark.asyncio
    async def test_returns_dict_with_niche(self, researcher):
        result = await researcher.research_async("ai_tools")
        assert isinstance(result, dict)
        assert result["niche"] == "ai_tools"

    @pytest.mark.asyncio
    async def test_has_required_keys(self, researcher):
        result = await researcher.research_async("general")
        for key in ["niche", "risk_score", "summary", "created_at"]:
            assert key in result

    @pytest.mark.asyncio
    async def test_batch_returns_all_niches(self, researcher):
        niches = ["ai_tools", "crypto", "general"]
        results = await researcher.research_batch(niches)
        assert len(results) == 3
        result_niches = [r["niche"] for r in results]
        for niche in niches:
            assert niche in result_niches


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


class TestResearchTopicFunction:
    def test_research_topic_returns_dict(self):
        with (
            patch("modules.research.RedditFetcher"),
            patch("modules.research.HackerNewsFetcher"),
            patch("modules.research.GoogleTrendsFetcher"),
            patch("modules.research.SimulatedPlatformFetcher"),
            patch("modules.research.Researcher.research_topic") as mock_rt,
        ):
            mock_rt.return_value = {"niche": "ai_tools", "risk_score": 30}
            result = research_topic("ai_tools")
        assert isinstance(result, dict)
