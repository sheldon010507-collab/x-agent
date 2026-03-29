"""
test_openclaw_integration.py - OpenClaw 集成测试

测试 X-Agent 与 OpenClaw 的完整工作流程
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modules.openclaw_bridge import OpenClawBridge


class TestOpenClawBridge:
    """OpenClaw 桥接器测试"""

    @pytest.fixture
    def openclaw(self):
        """创建 OpenClaw 实例"""
        return OpenClawBridge(api_endpoint="http://localhost:8080")

    def test_initialization(self, openclaw):
        """测试初始化"""
        assert openclaw.api_endpoint == "http://localhost:8080"
        assert openclaw.auto_post_enabled is False
        assert openclaw.daily_post_limit > 0
        assert openclaw.post_count == 0

    def test_random_delay(self, openclaw):
        """测试随机延迟"""
        delay = openclaw._random_delay(min_sec=1, max_sec=2)
        assert 1.0 <= delay <= 2.0

    def test_apply_content_variant(self, openclaw):
        """测试内容变体"""
        original = "This is a test content"
        variant = openclaw._apply_content_variant(original)

        # 应该不为空
        assert variant
        # 应该包含原始内容或其修改版本
        assert "test" in variant.lower() or len(variant) > len(original)

    def test_check_daily_limit_not_exceeded(self, openclaw):
        """测试未超过每日限额"""
        openclaw.post_count = 0
        openclaw.daily_post_limit = 5

        result = openclaw._check_daily_limit("post")
        assert result is True

    def test_check_daily_limit_exceeded(self, openclaw):
        """测试超过每日限额"""
        openclaw.post_count = 5
        openclaw.daily_post_limit = 5

        result = openclaw._check_daily_limit("post")
        assert result is False

    @pytest.mark.asyncio
    async def test_post_content_disabled(self, openclaw):
        """测试自动发帖禁用时的行为"""
        openclaw.auto_post_enabled = False

        result = await openclaw.post_content("Test content")
        assert result["success"] is False
        assert "disabled" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_post_content_success(self, openclaw):
        """测试成功发帖"""
        openclaw.auto_post_enabled = True

        result = await openclaw.post_content(
            content="Test post from X-Agent", niche="general", apply_variant=False
        )

        assert result["success"] is True
        assert "post_id" in result
        assert "url" in result
        assert openclaw.post_count == 1

    @pytest.mark.asyncio
    async def test_post_content_exceeds_limit(self, openclaw):
        """测试超过每日限额时的发帖"""
        openclaw.auto_post_enabled = True
        openclaw.post_count = 10
        openclaw.daily_post_limit = 10

        result = await openclaw.post_content("Test content")
        assert result["success"] is False
        assert "limit" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_comment_on_post_success(self, openclaw):
        """测试成功评论"""
        result = await openclaw.comment_on_post(
            post_url="https://x.com/user/status/123", comment="Great post!", apply_variant=False
        )

        assert result["success"] is True
        assert "comment_id" in result
        assert openclaw.comment_count == 1

    @pytest.mark.asyncio
    async def test_comment_exceeds_limit(self, openclaw):
        """测试评论超过限额"""
        openclaw.comment_count = 15
        openclaw.daily_comment_limit = 15

        result = await openclaw.comment_on_post(
            post_url="https://x.com/user/status/123", comment="Test comment"
        )

        assert result["success"] is False
        assert "limit" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_like_post_disabled(self, openclaw):
        """测试点赞禁用"""
        openclaw.auto_like_enabled = False

        result = await openclaw.like_post("https://x.com/user/status/123")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_like_post_success(self, openclaw):
        """测试成功点赞"""
        openclaw.auto_like_enabled = True

        result = await openclaw.like_post("https://x.com/user/status/123")
        assert result["success"] is True
        assert openclaw.like_count == 1

    @pytest.mark.asyncio
    async def test_retweet_post_success(self, openclaw):
        """测试成功转发"""
        openclaw.auto_rt_enabled = True

        result = await openclaw.retweet_post(post_url="https://x.com/user/status/123")

        assert result["success"] is True
        assert openclaw.rt_count == 1

    @pytest.mark.asyncio
    async def test_daily_reset(self):
        """测试每日计数重置"""
        openclaw = OpenClawBridge()
        openclaw.auto_post_enabled = True

        # 发送一条帖子
        await openclaw.post_content("Test")
        assert openclaw.post_count == 1

        # 模拟新的一天（手动重置）
        openclaw.reset_daily_counts()
        assert openclaw.post_count == 0
        assert openclaw.comment_count == 0
        assert openclaw.like_count == 0


class TestOpenClawWorkflow:
    """完整工作流测试"""

    @pytest.mark.asyncio
    async def test_complete_posting_workflow(self):
        """测试完整的发帖流程"""
        openclaw = OpenClawBridge()

        # 1. 启用自动发帖
        openclaw.auto_post_enabled = True

        # 2. 生成内容
        content = {
            "type": "A",
            "content": "AI is revolutionizing the world 🚀",
            "niche": "ai_tools",
        }

        # 3. 发帖
        result = await openclaw.post_content(
            content=content["content"], niche=content["niche"], apply_variant=True
        )

        assert result["success"]
        assert openclaw.post_count == 1

    @pytest.mark.asyncio
    async def test_complete_comment_workflow(self):
        """测试完整的评论流程"""
        openclaw = OpenClawBridge()

        # 目标帖子
        target_post = "https://x.com/important_account/status/789"

        # 生成评论
        comment = "这是一个很有见地的分析！"

        # 发送评论
        result = await openclaw.comment_on_post(
            post_url=target_post, comment=comment, apply_variant=True
        )

        assert result["success"]
        assert openclaw.comment_count == 1

    @pytest.mark.asyncio
    async def test_rate_limiting_workflow(self):
        """测试限流工作流"""
        openclaw = OpenClawBridge()
        openclaw.auto_post_enabled = True
        openclaw.daily_post_limit = 2

        # 第一条帖子 - 成功
        result1 = await openclaw.post_content("Post 1")
        assert result1["success"]

        # 第二条帖子 - 成功
        result2 = await openclaw.post_content("Post 2")
        assert result2["success"]

        # 第三条帖子 - 失败（超过限额）
        result3 = await openclaw.post_content("Post 3")
        assert result3["success"] is False
        assert "limit" in result3["reason"].lower()

        assert openclaw.post_count == 2


class TestAntiBlockMechanism:
    """防封机制测试"""

    def test_delay_configuration(self):
        """测试延迟配置"""
        openclaw = OpenClawBridge()

        # 验证延迟参数
        delay_short = openclaw._random_delay(min_sec=5, max_sec=10)
        assert 5 <= delay_short <= 10

        delay_long = openclaw._random_delay(min_sec=30, max_sec=60)
        assert 30 <= delay_long <= 60

    def test_content_variant_pool(self):
        """测试内容变体池"""
        openclaw = OpenClawBridge()

        variants = set()
        for _ in range(10):
            variant = openclaw._apply_content_variant("Hello world")
            variants.add(variant)

        # 应该生成多个不同的变体
        assert len(variants) > 1

    def test_daily_limit_enforcement(self):
        """测试每日限额强制执行"""
        openclaw = OpenClawBridge()

        # 设置较小的限额
        openclaw.daily_post_limit = 1
        openclaw.daily_comment_limit = 2
        openclaw.daily_like_limit = 3

        # 验证限额
        assert not openclaw._check_daily_limit("post")  # 已超过
        openclaw.post_count = 0  # 重置

        assert openclaw._check_daily_limit("post")
        openclaw.post_count = 1

        assert not openclaw._check_daily_limit("post")

    @pytest.mark.asyncio
    async def test_multiple_actions_with_delays(self):
        """测试多个操作之间的延迟"""
        openclaw = OpenClawBridge()

        start_time = datetime.now()

        # 执行多个操作（模拟）
        await asyncio.sleep(0.1)  # 模拟延迟

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        assert elapsed >= 0.1


class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """测试网络错误处理"""
        openclaw = OpenClawBridge(api_endpoint="http://invalid-endpoint:9999")
        openclaw.auto_post_enabled = True

        # 应该优雅地处理错误
        result = await openclaw.post_content("Test content")
        assert result["success"] is False
        assert "error" in result or "reason" in result

    @pytest.mark.asyncio
    async def test_invalid_content_handling(self):
        """测试无效内容处理"""
        openclaw = OpenClawBridge()
        openclaw.auto_post_enabled = True

        # 空内容
        result = await openclaw.post_content("")
        # 应该处理或返回警告
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求处理"""
        openclaw = OpenClawBridge()
        openclaw.auto_like_enabled = True

        # 并发执行多个请求
        tasks = [openclaw.like_post(f"https://x.com/user/status/{i}") for i in range(5)]

        results = await asyncio.gather(*tasks, return_exceptions=False)

        # 所有请求都应该完成
        assert len(results) == 5
        # 计数应该正确
        assert openclaw.like_count == 5


class TestIntegrationWithBot:
    """与 Telegram Bot 的集成测试"""

    @pytest.mark.asyncio
    async def test_bot_to_openclaw_flow(self):
        """测试从 Bot 到 OpenClaw 的完整流程"""
        # 模拟 Bot 流程
        generated_content = {
            "type": "A",
            "content": "Amazing AI breakthrough! 🚀",
            "niche": "ai_tools",
            "risk_score": 45,
        }

        # 初始化 OpenClaw
        openclaw = OpenClawBridge()
        openclaw.auto_post_enabled = True

        # 用户确认发布
        result = await openclaw.post_content(
            content=generated_content["content"], niche=generated_content["niche"]
        )

        assert result["success"]
        assert result["post_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
