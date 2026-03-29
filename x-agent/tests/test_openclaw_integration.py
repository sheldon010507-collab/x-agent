"""
test_openclaw_integration.py - OpenClaw 集成测试

测试 X-Agent 与 OpenClaw 的完整工作流程
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

try:
    from modules.openclaw_bridge import OpenClawBridge

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

pytestmark = pytest.mark.skipif(not HAS_DEPS, reason="playwright not installed")


class TestOpenClawBridge:
    """OpenClaw 桥接器测试"""

    @pytest.fixture
    def openclaw(self):
        """创建 OpenClaw 实例"""
        return OpenClawBridge(api_endpoint="http://localhost:8080")

    @pytest.fixture
    def openclaw_with_mock(self):
        """创建带 mock x_automation 的实例"""
        bridge = OpenClawBridge(api_endpoint="http://localhost:8080")
        bridge.x_automation = MagicMock()
        bridge.x_automation.logged_in = True
        bridge.x_automation.post = AsyncMock(
            return_value={"success": True, "post_id": "123", "url": "https://x.com/status/123"}
        )
        bridge.x_automation.like = AsyncMock(return_value={"success": True})
        bridge.x_automation.retweet = AsyncMock(return_value={"success": True})
        bridge.x_automation.close = AsyncMock()
        bridge.initialized = True
        return bridge

    def test_initialization(self, openclaw):
        """测试初始化"""
        assert openclaw.api_endpoint == "http://localhost:8080"
        assert openclaw.auto_post_enabled is False
        assert openclaw.daily_post_limit > 0
        assert openclaw.post_count == 0

    def test_check_daily_limit_not_exceeded(self, openclaw):
        """测试未超过每日限额"""
        openclaw.post_count = 0
        openclaw.daily_post_limit = 5
        assert openclaw._check_daily_limit("post") is True

    def test_check_daily_limit_exceeded(self, openclaw):
        """测试超过每日限额"""
        openclaw.post_count = 5
        openclaw.daily_post_limit = 5
        assert openclaw._check_daily_limit("post") is False

    @pytest.mark.asyncio
    async def test_post_content_disabled(self, openclaw):
        """测试自动发帖禁用时的行为"""
        openclaw.auto_post_enabled = False
        result = await openclaw.post_content("Test content")
        assert result["success"] is False
        assert "disabled" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_post_content_not_initialized(self, openclaw):
        """测试未初始化时的发帖"""
        openclaw.auto_post_enabled = True
        result = await openclaw.post_content("Test content")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_post_content_success(self, openclaw_with_mock):
        """测试成功发帖"""
        openclaw_with_mock.auto_post_enabled = True
        result = await openclaw_with_mock.post_content(
            content="Test post from X-Agent", niche="general", apply_variant=False
        )
        assert result["success"] is True
        assert openclaw_with_mock.post_count == 1

    @pytest.mark.asyncio
    async def test_post_content_exceeds_limit(self, openclaw_with_mock):
        """测试超过每日限额时的发帖"""
        openclaw_with_mock.auto_post_enabled = True
        openclaw_with_mock.post_count = 10
        openclaw_with_mock.daily_post_limit = 10
        result = await openclaw_with_mock.post_content("Test content")
        assert result["success"] is False
        assert "limit" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_like_post_disabled(self, openclaw):
        """测试点赞禁用"""
        openclaw.auto_like_enabled = False
        result = await openclaw.like_post("https://x.com/user/status/123")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_like_post_success(self, openclaw_with_mock):
        """测试成功点赞"""
        openclaw_with_mock.auto_like_enabled = True
        result = await openclaw_with_mock.like_post("https://x.com/user/status/123")
        assert result["success"] is True
        assert openclaw_with_mock.like_count == 1

    @pytest.mark.asyncio
    async def test_retweet_post_success(self, openclaw_with_mock):
        """测试成功转发"""
        openclaw_with_mock.auto_rt_enabled = True
        result = await openclaw_with_mock.retweet_post(post_url="https://x.com/user/status/123")
        assert result["success"] is True
        assert openclaw_with_mock.rt_count == 1

    def test_daily_reset(self):
        """测试每日计数重置"""
        openclaw = OpenClawBridge()
        openclaw.post_count = 5
        openclaw.comment_count = 10
        openclaw.like_count = 20
        openclaw.rt_count = 3

        openclaw.reset_daily_counts()
        assert openclaw.post_count == 0
        assert openclaw.comment_count == 0
        assert openclaw.like_count == 0
        assert openclaw.rt_count == 0


class TestOpenClawWorkflow:
    """完整工作流测试"""

    @pytest.fixture
    def openclaw_ready(self):
        """创建已就绪的 OpenClaw 实例"""
        bridge = OpenClawBridge()
        bridge.x_automation = MagicMock()
        bridge.x_automation.logged_in = True
        bridge.x_automation.post = AsyncMock(
            return_value={"success": True, "post_id": "456", "url": "https://x.com/status/456"}
        )
        bridge.x_automation.like = AsyncMock(return_value={"success": True})
        bridge.x_automation.retweet = AsyncMock(return_value={"success": True})
        bridge.initialized = True
        return bridge

    @pytest.mark.asyncio
    async def test_complete_posting_workflow(self, openclaw_ready):
        """测试完整的发帖流程"""
        openclaw_ready.auto_post_enabled = True
        content = "AI is revolutionizing the world"
        result = await openclaw_ready.post_content(content=content, niche="ai_tools")
        assert result["success"]
        assert openclaw_ready.post_count == 1

    @pytest.mark.asyncio
    async def test_rate_limiting_workflow(self, openclaw_ready):
        """测试限流工作流"""
        openclaw_ready.auto_post_enabled = True
        openclaw_ready.daily_post_limit = 2

        result1 = await openclaw_ready.post_content("Post 1")
        assert result1["success"]

        result2 = await openclaw_ready.post_content("Post 2")
        assert result2["success"]

        result3 = await openclaw_ready.post_content("Post 3")
        assert result3["success"] is False
        assert "limit" in result3["reason"].lower()
        assert openclaw_ready.post_count == 2


class TestAntiBlockMechanism:
    """防封机制测试"""

    def test_daily_limit_enforcement(self):
        """测试每日限额强制执行"""
        openclaw = OpenClawBridge()
        openclaw.daily_post_limit = 1

        # post_count=0, limit=1 → within limit
        assert openclaw._check_daily_limit("post") is True

        openclaw.post_count = 1
        # post_count=1, limit=1 → exceeded
        assert openclaw._check_daily_limit("post") is False

    def test_set_daily_limits(self):
        """测试设置每日限额"""
        openclaw = OpenClawBridge()
        openclaw.set_daily_limits(like=50, rt=20, post=15, comment=25)
        assert openclaw.daily_like_limit == 50
        assert openclaw.daily_rt_limit == 20
        assert openclaw.daily_post_limit == 15
        assert openclaw.daily_comment_limit == 25

    def test_auto_toggles(self):
        """测试自动化开关"""
        openclaw = OpenClawBridge()

        openclaw.set_auto_like(True)
        assert openclaw.auto_like_enabled is True

        openclaw.set_auto_rt(True)
        assert openclaw.auto_rt_enabled is True

        openclaw.set_auto_post(True)
        assert openclaw.auto_post_enabled is True

        openclaw.set_auto_like(False)
        assert openclaw.auto_like_enabled is False

    @pytest.mark.asyncio
    async def test_multiple_actions_with_delays(self):
        """测试多个操作之间的延迟"""
        start_time = datetime.now()
        await asyncio.sleep(0.1)
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        assert elapsed >= 0.1


class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_post_without_initialization(self):
        """测试未初始化时的发帖"""
        openclaw = OpenClawBridge()
        openclaw.auto_post_enabled = True
        result = await openclaw.post_content("Test content")
        assert result["success"] is False
        assert "reason" in result

    @pytest.mark.asyncio
    async def test_like_without_initialization(self):
        """测试未初始化时的点赞"""
        openclaw = OpenClawBridge()
        openclaw.auto_like_enabled = True
        result = await openclaw.like_post("https://x.com/user/status/123")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_concurrent_likes(self):
        """测试并发点赞"""
        bridge = OpenClawBridge()
        bridge.x_automation = MagicMock()
        bridge.x_automation.logged_in = True
        bridge.x_automation.like = AsyncMock(return_value={"success": True})
        bridge.initialized = True
        bridge.auto_like_enabled = True

        tasks = [bridge.like_post(f"https://x.com/user/status/{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert bridge.like_count == 5

    def test_get_status_without_automation(self):
        """测试获取状态（无自动化实例）"""
        openclaw = OpenClawBridge()
        status = openclaw.get_status()
        assert status["initialized"] is False
        assert status["x_logged_in"] is False
        assert "daily_counts" in status
        assert "daily_limits" in status


class TestIntegrationWithBot:
    """与 Telegram Bot 的集成测试"""

    @pytest.mark.asyncio
    async def test_bot_to_openclaw_flow(self):
        """测试从 Bot 到 OpenClaw 的完整流程"""
        generated_content = {
            "type": "A",
            "content": "Amazing AI breakthrough!",
            "niche": "ai_tools",
            "risk_score": 45,
        }

        bridge = OpenClawBridge()
        bridge.x_automation = MagicMock()
        bridge.x_automation.logged_in = True
        bridge.x_automation.post = AsyncMock(
            return_value={"success": True, "post_id": "789", "url": "https://x.com/status/789"}
        )
        bridge.initialized = True
        bridge.auto_post_enabled = True

        result = await bridge.post_content(
            content=generated_content["content"], niche=generated_content["niche"]
        )
        assert result["success"]
        assert result["post_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
