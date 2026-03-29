"""
test_openclaw_integration.py - OpenClaw Bridge 集成测试

测试 OpenClawBridge 的公开 API：
- 初始化和状态管理
- 每日限额检查
- 发帖、点赞、转发
- 每日计数重置
- 配置方法
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.openclaw_bridge import OpenClawBridge


@pytest.fixture
def bridge():
    """创建基础 OpenClawBridge 实例"""
    return OpenClawBridge(api_endpoint="http://localhost:8080")


@pytest.fixture
def initialized_bridge():
    """创建已初始化并启用功能的 OpenClawBridge 实例"""
    b = OpenClawBridge(api_endpoint="http://localhost:8080")
    b.initialized = True
    b.x_automation = MagicMock()
    b.x_automation.logged_in = True
    b.auto_post_enabled = True
    b.auto_like_enabled = True
    b.auto_rt_enabled = True
    return b


class TestOpenClawBridgeInit:
    """初始化测试"""

    def test_default_initialization(self, bridge):
        assert bridge.api_endpoint == "http://localhost:8080"
        assert bridge.initialized is False
        assert bridge.x_automation is None

    def test_default_switches(self, bridge):
        assert bridge.auto_like_enabled is False
        assert bridge.auto_rt_enabled is False
        assert bridge.auto_post_enabled is False
        assert bridge.auto_comment_enabled is True

    def test_default_counts(self, bridge):
        assert bridge.like_count == 0
        assert bridge.rt_count == 0
        assert bridge.post_count == 0
        assert bridge.comment_count == 0


class TestDailyLimitCheck:
    """每日限额检查测试"""

    def test_within_limit(self, bridge):
        bridge.like_count = 0
        bridge.daily_like_limit = 30
        assert bridge._check_daily_limit("like") is True

    def test_at_limit(self, bridge):
        bridge.like_count = 30
        bridge.daily_like_limit = 30
        assert bridge._check_daily_limit("like") is False

    def test_over_limit(self, bridge):
        bridge.post_count = 15
        bridge.daily_post_limit = 10
        assert bridge._check_daily_limit("post") is False

    def test_unknown_action_uses_default(self, bridge):
        # Unknown action defaults to (0, 10)
        assert bridge._check_daily_limit("unknown_action") is True


class TestPostContent:
    """发帖功能测试"""

    @pytest.mark.asyncio
    async def test_post_disabled(self, bridge):
        bridge.auto_post_enabled = False
        result = await bridge.post_content("test content")
        assert result["success"] is False
        assert "disabled" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_post_not_initialized(self, bridge):
        bridge.auto_post_enabled = True
        bridge.initialized = False
        result = await bridge.post_content("test content")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_post_success(self, initialized_bridge):
        initialized_bridge.x_automation.post = AsyncMock(
            return_value={"success": True, "url": "https://x.com/post/123"}
        )
        result = await initialized_bridge.post_content("test content")
        assert result["success"] is True
        assert initialized_bridge.post_count == 1

    @pytest.mark.asyncio
    async def test_post_limit_reached(self, initialized_bridge):
        initialized_bridge.post_count = initialized_bridge.daily_post_limit
        result = await initialized_bridge.post_content("test content")
        assert result["success"] is False
        assert "limit" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_post_error_handling(self, initialized_bridge):
        initialized_bridge.x_automation.post = AsyncMock(side_effect=Exception("Network error"))
        result = await initialized_bridge.post_content("test content")
        assert result["success"] is False
        assert "Network error" in result["reason"]


class TestLikePost:
    """点赞功能测试"""

    @pytest.mark.asyncio
    async def test_like_disabled(self, bridge):
        bridge.auto_like_enabled = False
        result = await bridge.like_post("https://x.com/post/123")
        assert result["success"] is False
        assert "disabled" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_like_success(self, initialized_bridge):
        initialized_bridge.x_automation.like = AsyncMock(return_value={"success": True})
        result = await initialized_bridge.like_post("https://x.com/post/123")
        assert result["success"] is True
        assert initialized_bridge.like_count == 1

    @pytest.mark.asyncio
    async def test_like_limit_reached(self, initialized_bridge):
        initialized_bridge.like_count = initialized_bridge.daily_like_limit
        result = await initialized_bridge.like_post("https://x.com/post/123")
        assert result["success"] is False
        assert "limit" in result["reason"].lower()


class TestRetweetPost:
    """转发功能测试"""

    @pytest.mark.asyncio
    async def test_rt_disabled(self, bridge):
        bridge.auto_rt_enabled = False
        result = await bridge.retweet_post("https://x.com/post/123")
        assert result["success"] is False
        assert "disabled" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_rt_success(self, initialized_bridge):
        initialized_bridge.x_automation.retweet = AsyncMock(return_value={"success": True})
        result = await initialized_bridge.retweet_post("https://x.com/post/123")
        assert result["success"] is True
        assert initialized_bridge.rt_count == 1

    @pytest.mark.asyncio
    async def test_rt_with_comment(self, initialized_bridge):
        initialized_bridge.x_automation.retweet = AsyncMock(return_value={"success": True})
        result = await initialized_bridge.retweet_post("https://x.com/post/123", comment="Great!")
        assert result["success"] is True


class TestDailyReset:
    """每日计数重置测试"""

    def test_reset_clears_all_counts(self, bridge):
        bridge.like_count = 10
        bridge.rt_count = 5
        bridge.post_count = 3
        bridge.comment_count = 8
        bridge.reset_daily_counts()
        assert bridge.like_count == 0
        assert bridge.rt_count == 0
        assert bridge.post_count == 0
        assert bridge.comment_count == 0


class TestConfigMethods:
    """配置方法测试"""

    def test_set_auto_like(self, bridge):
        bridge.set_auto_like(True)
        assert bridge.auto_like_enabled is True
        bridge.set_auto_like(False)
        assert bridge.auto_like_enabled is False

    def test_set_auto_rt(self, bridge):
        bridge.set_auto_rt(True)
        assert bridge.auto_rt_enabled is True

    def test_set_auto_post(self, bridge):
        bridge.set_auto_post(True)
        assert bridge.auto_post_enabled is True

    def test_set_daily_limits(self, bridge):
        bridge.set_daily_limits(like=50, rt=20, post=15, comment=25)
        assert bridge.daily_like_limit == 50
        assert bridge.daily_rt_limit == 20
        assert bridge.daily_post_limit == 15
        assert bridge.daily_comment_limit == 25

    def test_set_partial_daily_limits(self, bridge):
        original_rt = bridge.daily_rt_limit
        bridge.set_daily_limits(like=99)
        assert bridge.daily_like_limit == 99
        assert bridge.daily_rt_limit == original_rt  # unchanged


class TestGetStatus:
    """状态查询测试"""

    def test_status_without_automation(self, bridge):
        status = bridge.get_status()
        assert status["initialized"] is False
        assert status["x_logged_in"] is False
        assert "daily_counts" in status
        assert "daily_limits" in status
        assert "auto_settings" in status

    def test_status_with_automation(self, initialized_bridge):
        initialized_bridge.x_automation.get_status = MagicMock(return_value={"browser": "ok"})
        status = initialized_bridge.get_status()
        assert status["initialized"] is True
        assert status["x_logged_in"] is True
        assert status["x_automation"] == {"browser": "ok"}
