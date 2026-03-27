"""
test_research.py - 研究模块测试

mock subprocess.run 和 shutil.which，完全离线运行。
测试 CLI 调用、fallback 逻辑、风险评分计算。
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.research import Researcher, research_topic


class TestResearcherInit:
    """初始化测试"""

    def test_cache_dir_created_on_init(self):
        researcher = Researcher()
        assert researcher.cache_dir.exists()

    def test_cache_dir_name_is_research(self):
        researcher = Researcher()
        assert researcher.cache_dir.name == "research"


class TestResearcherFallback:
    """降级结果测试"""

    def setup_method(self):
        self.researcher = Researcher()

    def test_fallback_has_all_required_fields(self):
        result = self.researcher._fallback_result("ai_tools", "test error")
        for field in (
            "niche",
            "relevance_score",
            "velocity_24h",
            "authority_score",
            "platform_count",
            "risk_score",
            "summary",
            "citations",
            "fallback",
        ):
            assert field in result, f"缺少字段: {field}"

    def test_fallback_preserves_niche(self):
        result = self.researcher._fallback_result("crypto")
        assert result["niche"] == "crypto"

    def test_fallback_flag_is_true(self):
        result = self.researcher._fallback_result("test")
        assert result["fallback"] is True

    def test_fallback_scores_in_valid_range(self):
        result = self.researcher._fallback_result("test")
        assert 0.0 <= result["relevance_score"] <= 100.0
        assert 0.0 <= result["authority_score"] <= 100.0
        assert 0.0 <= result["risk_score"] <= 100.0

    def test_fallback_with_error_message_in_summary(self):
        result = self.researcher._fallback_result("test", "CLI not found")
        assert "CLI not found" in result["summary"]

    def test_fallback_without_error(self):
        result = self.researcher._fallback_result("test")
        assert result["niche"] == "test"


class TestResearcherCLINotInstalled:
    """CLI 未安装时的行为"""

    def setup_method(self):
        self.researcher = Researcher()

    def test_returns_fallback_when_cli_missing(self):
        with patch("shutil.which", return_value=None):
            result = self.researcher.research_topic("ai_tools")
        assert result.get("fallback") is True

    def test_fallback_niche_correct(self):
        with patch("shutil.which", return_value=None):
            result = self.researcher.research_topic("crypto")
        assert result["niche"] == "crypto"


class TestResearcherCLISuccess:
    """CLI 成功执行时的行为"""

    def setup_method(self):
        self.researcher = Researcher()

    def test_parses_json_output(self):
        mock_output = {
            "niche": "ai_tools",
            "relevance_score": 85.0,
            "velocity_24h": 70.0,
            "authority_score": 75.0,
            "platform_count": 4,
            "summary": "Test summary",
            "citations": [],
        }
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(mock_output)

        with (
            patch("shutil.which", return_value="/usr/bin/last30days"),
            patch("subprocess.run", return_value=mock_result),
        ):
            result = self.researcher.research_topic("ai_tools")

        assert result["relevance_score"] == 85.0
        assert result["niche"] == "ai_tools"

    def test_adds_risk_score_to_result(self):
        """CLI 成功时应自动附加 risk_score 字段"""
        mock_output = {
            "niche": "ai_tools",
            "relevance_score": 80.0,
            "velocity_24h": 60.0,
            "authority_score": 70.0,
            "platform_count": 3,
            "summary": "Test",
            "citations": [],
        }
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(mock_output)

        with (
            patch("shutil.which", return_value="/usr/bin/last30days"),
            patch("subprocess.run", return_value=mock_result),
        ):
            result = self.researcher.research_topic("ai_tools")

        assert "risk_score" in result
        assert 0.0 <= result["risk_score"] <= 100.0


class TestResearcherCLIErrors:
    """CLI 错误场景"""

    def setup_method(self):
        self.researcher = Researcher()

    def test_nonzero_return_code_gives_fallback(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: rate limit exceeded"

        with (
            patch("shutil.which", return_value="/usr/bin/last30days"),
            patch("subprocess.run", return_value=mock_result),
        ):
            result = self.researcher.research_topic("test")
        assert result.get("fallback") is True

    def test_timeout_gives_fallback(self):
        import subprocess

        with (
            patch("shutil.which", return_value="/usr/bin/last30days"),
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="last30days", timeout=120),
            ),
        ):
            result = self.researcher.research_topic("test")
        assert result.get("fallback") is True

    def test_invalid_json_gives_fallback(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not valid json {{{"

        with (
            patch("shutil.which", return_value="/usr/bin/last30days"),
            patch("subprocess.run", return_value=mock_result),
        ):
            result = self.researcher.research_topic("test")
        assert result.get("fallback") is True

    def test_file_not_found_gives_fallback(self):
        with (
            patch("shutil.which", return_value="/usr/bin/last30days"),
            patch("subprocess.run", side_effect=FileNotFoundError("last30days not found")),
        ):
            result = self.researcher.research_topic("test")
        assert result.get("fallback") is True


class TestResearcherRiskScore:
    """风险评分计算测试"""

    def setup_method(self):
        self.researcher = Researcher()

    def test_base_risk_is_30(self):
        """低速、多平台、高权威度时接近基础分 30"""
        data = {"velocity_24h": 10, "platform_count": 5, "authority_score": 90}
        score = self.researcher._calculate_risk_score(data)
        assert score == 30.0

    def test_high_velocity_increases_risk(self):
        low = self.researcher._calculate_risk_score(
            {"velocity_24h": 10, "platform_count": 3, "authority_score": 70}
        )
        high = self.researcher._calculate_risk_score(
            {"velocity_24h": 95, "platform_count": 3, "authority_score": 70}
        )
        assert high > low

    def test_few_platforms_increases_risk(self):
        many = self.researcher._calculate_risk_score(
            {"velocity_24h": 30, "platform_count": 5, "authority_score": 70}
        )
        few = self.researcher._calculate_risk_score(
            {"velocity_24h": 30, "platform_count": 1, "authority_score": 70}
        )
        assert few > many

    def test_low_authority_increases_risk(self):
        high_auth = self.researcher._calculate_risk_score(
            {"velocity_24h": 30, "platform_count": 3, "authority_score": 90}
        )
        low_auth = self.researcher._calculate_risk_score(
            {"velocity_24h": 30, "platform_count": 3, "authority_score": 20}
        )
        assert low_auth > high_auth

    def test_risk_never_exceeds_100(self):
        score = self.researcher._calculate_risk_score(
            {"velocity_24h": 100, "platform_count": 1, "authority_score": 0}
        )
        assert score <= 100.0

    def test_risk_never_below_zero(self):
        score = self.researcher._calculate_risk_score(
            {"velocity_24h": 0, "platform_count": 10, "authority_score": 100}
        )
        assert score >= 0.0


class TestResearcherAsync:
    """异步接口测试"""

    def setup_method(self):
        self.researcher = Researcher()

    @pytest.mark.asyncio
    async def test_research_async_returns_same_structure(self):
        with patch("shutil.which", return_value=None):
            result = await self.researcher.research_async("ai_tools")
        assert "niche" in result
        assert result.get("fallback") is True

    @pytest.mark.asyncio
    async def test_research_batch_returns_all_results(self):
        with patch("shutil.which", return_value=None):
            results = await self.researcher.research_batch(["ai", "crypto", "fitness"])
        assert len(results) == 3
        for r in results:
            assert "niche" in r


class TestResearchConvenienceFunction:
    """便捷函数测试"""

    def test_research_topic_returns_dict(self):
        with patch("shutil.which", return_value=None):
            result = research_topic("ai_tools")
        assert isinstance(result, dict)
        assert "niche" in result
