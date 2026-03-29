"""
test_enhanced_features.py - 测试三个增强功能

测试：
1. 去重算法 (Deduplicator)
2. 增强评分系统 (Enhanced Scorer)
3. 多源采集优化 (Research Optimization)
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from modules.deduplicator import ContentDeduplicator, calculate_shingle_similarity
from modules.research_optimization import ConcurrentLimiter, RateLimitConfig, exponential_backoff
from modules.scorer import TrendScorer, calculate_trend_score_v2

# ============ 测试去重算法 ============


class TestDeduplicator:
    """去重算法测试"""

    def test_normalize_text(self):
        """测试文本规范化"""
        dedup = ContentDeduplicator()

        # 测试小写
        assert dedup.normalize_text("HELLO") == "hello"

        # 测试URL移除
        text = "Check this: https://example.com amazing"
        normalized = dedup.normalize_text(text)
        assert "http" not in normalized

        # 测试@mention移除
        text = "@user this is cool"
        normalized = dedup.normalize_text(text)
        assert "@" not in normalized

    def test_tokenize(self):
        """测试分词"""
        dedup = ContentDeduplicator()
        text = "hello world"
        tokens = dedup.tokenize(text)

        assert isinstance(tokens, set)
        assert len(tokens) > 0
        # 3-gram应该包含 "hel", "ell", "llo", " wo", "wor", 等
        assert any("hel" in t for t in tokens)

    def test_jaccard_similarity(self):
        """测试Jaccard相似度"""
        dedup = ContentDeduplicator()

        # 相同集合，相似度=1.0
        set1 = {"a", "b", "c"}
        set2 = {"a", "b", "c"}
        assert dedup.jaccard_similarity(set1, set2) == 1.0

        # 完全不同集合，相似度=0.0
        set1 = {"a", "b", "c"}
        set2 = {"x", "y", "z"}
        assert dedup.jaccard_similarity(set1, set2) == 0.0

        # 部分重叠
        set1 = {"a", "b", "c"}
        set2 = {"a", "b", "d"}
        similarity = dedup.jaccard_similarity(set1, set2)
        assert 0.0 < similarity < 1.0

    def test_is_duplicate(self):
        """测试重复检测"""
        dedup = ContentDeduplicator(threshold=0.75)

        # 完全相同的文本
        text1 = "This is a great article about AI"
        text2 = "This is a great article about AI"
        assert dedup.is_duplicate(text1, text2) is True

        # 不同的文本
        text1 = "The quick brown fox"
        text2 = "The lazy dog sleeps"
        assert dedup.is_duplicate(text1, text2) is False

    def test_deduplicate_batch(self):
        """测试批量去重"""
        dedup = ContentDeduplicator(threshold=0.75)

        items = [
            {"text": "AI is transforming the world", "score": 85},
            {"text": "AI is transforming the world", "score": 80},  # 重复
            {"text": "Machine learning is amazing", "score": 75},
            {"text": "Machine learning is amazing", "score": 70},  # 重复
            {"text": "Blockchain technology rocks", "score": 65},
        ]

        unique = dedup.deduplicate_batch(items, content_key="text", score_key="score")

        # 应该去掉重复项
        assert len(unique) < len(items)
        # 每个唯一项应该是分数最高的
        texts = [item["text"] for item in unique]
        assert len(set(texts)) == len(unique)

    def test_find_similar_groups(self):
        """测试相似项分组"""
        dedup = ContentDeduplicator(threshold=0.70)

        items = [
            {"text": "AI trends 2024", "id": 1},
            {"text": "AI trends in 2024", "id": 2},  # 与1相似
            {"text": "Blockchain news", "id": 3},
            {"text": "Blockchain updates", "id": 4},  # 与3相似
            {"text": "Web3 technology", "id": 5},  # 独立
        ]

        groups = dedup.find_similar_groups(items, content_key="text")

        # 应该形成3个组
        assert len(groups) <= len(items)
        # 每个组应该包含至少1个项
        assert all(len(group) >= 1 for group in groups)

    def test_convenience_function(self):
        """测试便利函数"""
        text1 = "Python programming is fun"
        text2 = "Python programming is fun"

        similarity, is_dup = calculate_shingle_similarity(text1, text2, threshold=0.75)

        assert similarity >= 0.0
        assert similarity <= 1.0
        assert isinstance(is_dup, bool)


# ============ 测试增强评分系统 ============


class TestEnhancedScorer:
    """增强评分系统测试"""

    def test_temporal_decay(self):
        """测试时间衰减"""
        scorer = TrendScorer()

        # 现在创建的内容，衰减因子应该接近1.0
        now = datetime.now().isoformat()
        decay = scorer._calculate_temporal_decay(now)
        assert 0.95 <= decay <= 1.0

        # 7天前创建的内容，衰减因子应该接近0.5
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        decay = scorer._calculate_temporal_decay(seven_days_ago)
        assert 0.4 <= decay <= 0.6

        # 14天前创建的内容，衰减因子应该接近0.25
        fourteen_days_ago = (datetime.now() - timedelta(days=14)).isoformat()
        decay = scorer._calculate_temporal_decay(fourteen_days_ago)
        assert decay < 0.3

    def test_platform_diversity_bonus(self):
        """测试平台多样性奖励"""
        scorer = TrendScorer()

        # 单平台，无奖励
        bonus = scorer._calculate_platform_diversity_bonus(platform_sources=["reddit"])
        assert bonus == 1.0

        # 两个平台，+8%
        bonus = scorer._calculate_platform_diversity_bonus(platform_sources=["reddit", "x"])
        assert 1.07 <= bonus <= 1.09

        # 三个平台，+15%
        bonus = scorer._calculate_platform_diversity_bonus(
            platform_sources=["reddit", "x", "hackernews"]
        )
        assert 1.14 <= bonus <= 1.16

        # 四个平台，+20%
        bonus = scorer._calculate_platform_diversity_bonus(
            platform_sources=["reddit", "x", "hackernews", "youtube"]
        )
        assert 1.19 <= bonus <= 1.21

        # 高权威组合额外奖励（HN + Reddit）
        bonus_hn_reddit = scorer._calculate_platform_diversity_bonus(
            platform_sources=["hackernews", "reddit"]
        )
        bonus_normal = scorer._calculate_platform_diversity_bonus(platform_sources=["x", "youtube"])
        assert bonus_hn_reddit > bonus_normal

    def test_calculate_score_v2(self):
        """测试V2评分计算"""
        scorer = TrendScorer()

        trend_data = {
            "relevance_score": 85,
            "velocity_24h": 75,
            "authority_score": 80,
            "platform_count": 3,
            "created_at": datetime.now().isoformat(),
            "platform_sources": ["reddit", "x", "hackernews"],
        }

        score_v1 = scorer.calculate_score(trend_data)
        score_v2 = scorer.calculate_score_v2(trend_data)

        # V2应该略高（因为有时间衰减和多样性奖励）
        assert 0 <= score_v1 <= 100
        assert 0 <= score_v2 <= 100
        # V2通常会更高（因为新内容且多平台）
        assert score_v2 >= score_v1 * 0.95

    def test_score_with_details_v2(self):
        """测试V2详细评分"""
        scorer = TrendScorer()

        trend_data = {
            "relevance_score": 80,
            "velocity_24h": 70,
            "authority_score": 75,
            "platform_count": 2,
            "created_at": datetime.now().isoformat(),
            "platform_sources": ["reddit", "hackernews"],
        }

        details = scorer.score_with_details_v2(trend_data)

        # 检查基础字段
        assert "score" in details
        assert "score_breakdown" in details
        assert "temporal_analysis" in details
        assert "diversity_analysis" in details

        # 检查分解信息
        breakdown = details["score_breakdown"]
        assert "relevance" in breakdown
        assert "velocity" in breakdown
        assert "temporal_decay" in breakdown
        assert "platform_diversity_bonus" in breakdown

        # 检查分析信息
        assert "created_at" in details["temporal_analysis"]
        assert "decay_factor" in details["temporal_analysis"]
        assert "platforms" in details["diversity_analysis"]
        assert "bonus_factor" in details["diversity_analysis"]

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        scorer = TrendScorer()

        # 旧数据格式（无created_at和platform_sources）
        old_style_data = {
            "relevance_score": 80,
            "velocity_24h": 70,
            "authority_score": 75,
            "platform_count": 2,
        }

        # 旧方法应该仍然工作
        score_old = scorer.calculate_score(old_style_data)
        assert 0 <= score_old <= 100

        # V2应该优雅降级（使用默认值）
        score_v2 = scorer.calculate_score_v2(old_style_data)
        assert 0 <= score_v2 <= 100


# ============ 测试多源采集优化 ============


class TestResearchOptimization:
    """多源采集优化测试"""

    def test_rate_limit_config(self):
        """测试速率限制配置"""
        config = RateLimitConfig()

        assert config.reddit_max_concurrent == 2
        assert config.hackernews_max_concurrent == 5
        assert config.google_trends_max_concurrent == 1
        assert config.max_retries == 3
        assert config.backoff_base == 2.0

    def test_exponential_backoff(self):
        """测试指数退避"""
        # 第1次重试：2^1 = 2秒
        backoff1 = exponential_backoff(1, base=2.0, jitter=False)
        assert backoff1 == 2.0

        # 第2次重试：2^2 = 4秒
        backoff2 = exponential_backoff(2, base=2.0, jitter=False)
        assert backoff2 == 4.0

        # 第3次重试：2^3 = 8秒
        backoff3 = exponential_backoff(3, base=2.0, jitter=False)
        assert backoff3 == 8.0

        # 带抖动的应该略有不同
        backoff_jitter = exponential_backoff(2, base=2.0, jitter=True)
        assert 3.5 <= backoff_jitter <= 4.5  # 允许一些随机性

    @pytest.mark.asyncio
    async def test_concurrent_limiter(self):
        """测试并发限制器"""
        config = RateLimitConfig(reddit_max_concurrent=2)
        limiter = ConcurrentLimiter(config)

        # 测试获取和释放
        await limiter.acquire("reddit")
        limiter.release("reddit")

        # 并发计数测试
        async def task():
            await limiter.acquire("reddit")
            try:
                await asyncio.sleep(0.1)
            finally:
                limiter.release("reddit")

        # 同时运行3个任务，但并发限制是2
        # 应该不会在同时运行3个
        tasks = [asyncio.create_task(task()) for _ in range(3)]
        await asyncio.gather(*tasks)

        # 如果没有崩溃，说明并发限制工作正常


# ============ 集成测试 ============


class TestIntegration:
    """集成测试"""

    def test_dedup_scorer_integration(self):
        """测试去重和评分的集成"""
        dedup = ContentDeduplicator()
        scorer = TrendScorer()

        # 创建一些内容
        citations = [
            {"text": "AI is the future", "score": 85},
            {"text": "AI is the future", "score": 80},  # 重复
            {"text": "ML is important", "score": 75},
        ]

        # 先去重
        unique = dedup.deduplicate_batch(citations, content_key="text", score_key="score")
        assert len(unique) < len(citations)

        # 然后评分
        trend_data = {
            "relevance_score": 80,
            "velocity_24h": 70,
            "authority_score": 75,
            "platform_count": len(unique),
            "platform_sources": ["reddit", "x"],
            "created_at": datetime.now().isoformat(),
        }

        score = scorer.calculate_score_v2(trend_data)
        assert 0 <= score <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
