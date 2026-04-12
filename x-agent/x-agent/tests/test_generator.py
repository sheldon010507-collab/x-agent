"""
test_generator.py - 内容生成模块测试

使用 unittest.mock 模拟 LLM 调用，完全离线运行，无需真实 API Key。
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.generator import ContentGenerator


@pytest.fixture
def mock_llm_router():
    """返回预设 A 类推文响应的 mock LLM"""
    router = MagicMock()
    router.generate_json = AsyncMock(
        return_value={
            "tweets": [
                {"angle": "Hot take", "content": "Test tweet 1 #AI", "hashtags": ["#AI"]},
                {"angle": "Data", "content": "Test tweet 2 #Data", "hashtags": ["#Data"]},
                {"angle": "Poll", "content": "Test tweet 3? #Poll", "hashtags": ["#Poll"]},
            ],
            "media_suggestion": "ai, tech",
        }
    )
    return router


@pytest.fixture
def generator(mock_llm_router):
    return ContentGenerator(mock_llm_router, "ai_tools")


# ======== A 类推文 ========


class TestTypeAGeneration:

    @pytest.mark.asyncio
    async def test_type_a_returns_tweets(self, generator):
        result = await generator.generate_type_a("AI tools 2024")
        assert "tweets" in result
        assert isinstance(result["tweets"], list)

    @pytest.mark.asyncio
    async def test_type_a_has_three_tweets(self, generator):
        result = await generator.generate_type_a("AI tools 2024")
        assert len(result["tweets"]) == 3

    @pytest.mark.asyncio
    async def test_type_a_tweet_has_required_fields(self, generator):
        result = await generator.generate_type_a("AI tools 2024")
        for tweet in result["tweets"]:
            assert "angle" in tweet
            assert "content" in tweet
            assert "hashtags" in tweet

    @pytest.mark.asyncio
    async def test_type_a_fallback_on_llm_error(self, mock_llm_router):
        mock_llm_router.generate_json = AsyncMock(side_effect=Exception("API error"))
        gen = ContentGenerator(mock_llm_router, "ai_tools")
        result = await gen.generate_type_a("test topic")
        assert "tweets" in result
        assert len(result["tweets"]) == 3

    @pytest.mark.asyncio
    async def test_type_a_fallback_on_invalid_response(self, mock_llm_router):
        mock_llm_router.generate_json = AsyncMock(return_value="not a dict")
        gen = ContentGenerator(mock_llm_router, "ai_tools")
        result = await gen.generate_type_a("test topic")
        assert "tweets" in result


# ======== B 类脚本 ========


class TestTypeBGeneration:

    @pytest.fixture(autouse=True)
    def setup_mock(self, mock_llm_router):
        mock_llm_router.generate_json = AsyncMock(
            return_value={
                "title": "Test Video",
                "angle": "Quick overview",
                "script": {
                    "hook": {"time": "0-5s", "content": "Hook content"},
                    "body": {"time": "5-20s", "content": "Body content"},
                    "cta": {"time": "20-30s", "content": "CTA content"},
                },
                "caption": "Test caption",
                "hashtags": ["#Test"],
                "media_suggestion": "test",
                "best_posting_time": "19:00",
            }
        )

    @pytest.mark.asyncio
    async def test_type_b_returns_script(self, generator):
        result = await generator.generate_type_b("AI tools 2024")
        assert "title" in result
        assert "script" in result

    @pytest.mark.asyncio
    async def test_type_b_script_has_all_segments(self, generator):
        result = await generator.generate_type_b("AI tools 2024")
        script = result["script"]
        assert "hook" in script
        assert "body" in script
        assert "cta" in script

    @pytest.mark.asyncio
    async def test_type_b_fallback_on_error(self, mock_llm_router):
        mock_llm_router.generate_json = AsyncMock(side_effect=RuntimeError("timeout"))
        gen = ContentGenerator(mock_llm_router, "ai_tools")
        result = await gen.generate_type_b("test")
        assert "script" in result


# ======== C 类评论 ========


class TestCommentGeneration:

    @pytest.fixture(autouse=True)
    def setup_mock(self, mock_llm_router):
        mock_llm_router.generate_json = AsyncMock(
            return_value={
                "comments": [
                    {"content": "Great point! 🔥", "has_cta": False},
                    {"content": "Interesting perspective 💡", "has_cta": False},
                    {"content": "Check this out!", "has_cta": True},
                ]
            }
        )

    @pytest.mark.asyncio
    async def test_comment_returns_list(self, generator):
        result = await generator.generate_comment("AI is amazing")
        assert "comments" in result
        assert isinstance(result["comments"], list)

    @pytest.mark.asyncio
    async def test_comment_has_required_fields(self, generator):
        result = await generator.generate_comment("test post")
        for comment in result["comments"]:
            assert "content" in comment
            assert "has_cta" in comment

    @pytest.mark.asyncio
    async def test_comment_fallback_on_error(self, mock_llm_router):
        mock_llm_router.generate_json = AsyncMock(side_effect=Exception("error"))
        gen = ContentGenerator(mock_llm_router, "ai_tools")
        result = await gen.generate_comment("test")
        assert "comments" in result


# ======== 风险评分 ========


class TestRiskScoreCalculation:

    def setup_method(self):
        router = MagicMock()
        self.gen = ContentGenerator(router, "general")

    def test_base_type_a_risk(self):
        """A 类基础风险 = 30 + 10 = 40"""
        score = self.gen._calculate_risk_score("normal topic", "a")
        assert score == 40

    def test_type_c_higher_risk_than_a(self):
        score_a = self.gen._calculate_risk_score("normal topic", "a")
        score_c = self.gen._calculate_risk_score("normal topic", "c")
        assert score_c > score_a

    def test_sensitive_keyword_increases_risk(self):
        score_normal = self.gen._calculate_risk_score("normal topic", "a")
        score_sensitive = self.gen._calculate_risk_score("crypto news", "a")
        assert score_sensitive > score_normal

    def test_adult_niche_highest_risk(self):
        router = MagicMock()
        gen_adult = ContentGenerator(router, "adult")
        gen_general = ContentGenerator(router, "general")
        assert gen_adult._calculate_risk_score("topic", "a") > gen_general._calculate_risk_score(
            "topic", "a"
        )

    def test_risk_capped_at_100(self):
        router = MagicMock()
        gen = ContentGenerator(router, "adult")
        score = gen._calculate_risk_score("crypto adult xxx onlyfans", "c")
        assert score <= 100

    @pytest.mark.parametrize(
        "niche,topic,content_type,expected_high_risk",
        [
            ("adult", "onlyfans promo", "c", True),
            ("general", "tech news", "a", False),
            ("crypto", "bitcoin", "a", True),
        ],
    )
    def test_risk_scenarios(self, niche, topic, content_type, expected_high_risk):
        router = MagicMock()
        gen = ContentGenerator(router, niche)
        score = gen._calculate_risk_score(topic, content_type)
        if expected_high_risk:
            assert score >= 50, f"Expected high risk for {niche}/{topic}, got {score}"
        else:
            assert score < 60, f"Expected low risk for {niche}/{topic}, got {score}"


# ======== Niche 语气 ========


class TestNicheVoice:

    def test_set_niche_updates_attribute(self):
        router = MagicMock()
        gen = ContentGenerator(router, "general")
        gen.set_niche("crypto")
        assert gen.niche == "crypto"

    def test_nonexistent_niche_returns_default(self):
        router = MagicMock()
        gen = ContentGenerator(router, "nonexistent_xyz_niche")
        assert gen.voice_style is not None
        assert len(gen.voice_style) > 0

    def test_ai_tools_voice_loaded(self):
        router = MagicMock()
        gen = ContentGenerator(router, "ai_tools")
        assert len(gen.voice_style) > 0


# ======== 统一 generate() 方法 ========


class TestUnifiedGenerateMethod:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.router = MagicMock()
        self.router.generate_json = AsyncMock(
            return_value={
                "tweets": [
                    {"angle": "test", "content": "content1", "hashtags": []},
                    {"angle": "test2", "content": "content2", "hashtags": []},
                    {"angle": "test3", "content": "content3", "hashtags": []},
                ]
            }
        )
        self.gen = ContentGenerator(self.router, "general")

    @pytest.mark.asyncio
    async def test_generate_type_a_returns_content(self):
        result = await self.gen.generate("test topic", content_type="a")
        assert "content" in result
        assert "risk_score" in result
        assert result["type"] == "a"

    @pytest.mark.asyncio
    async def test_generate_returns_niche(self):
        result = await self.gen.generate("topic", content_type="a")
        assert result["niche"] == "general"

    @pytest.mark.asyncio
    async def test_generate_unknown_type_returns_error_safely(self):
        result = await self.gen.generate("topic", content_type="z")
        assert "content" in result
        assert result["risk_score"] == 100

    @pytest.mark.asyncio
    async def test_generate_risk_score_in_result(self):
        result = await self.gen.generate("topic", content_type="a")
        assert isinstance(result["risk_score"], (int, float))
        assert 0 <= result["risk_score"] <= 100
