"""
conftest.py - pytest 全局 fixtures

提供所有测试共用的 mock 对象，统一测试配置。
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# 确保 modules/ 可被 import
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def mock_config():
    """模拟 Config 对象（不依赖 .env 文件）"""
    config = MagicMock()
    config.telegram_bot_token = "test_bot_token"
    config.telegram_chat_id = "test_chat_id"
    config.supabase_url = "https://test.supabase.co"
    config.supabase_key = "test_supabase_key"
    config.llm_provider = "anthropic"
    config.anthropic_api_key = "sk-test-anthropic-key"
    config.openai_api_key = "sk-test-openai-key"
    config.groq_api_key = "gsk-test-groq-key"
    config.openrouter_api_key = "or-test-key"
    config.nvidia_api_key = "nvapi-test-key"
    config.ollama_base_url = "http://localhost:11434/v1"
    config.openclaw_api_endpoint = "http://localhost:8080"
    config.get = MagicMock(return_value="general")
    return config


@pytest.fixture
def mock_db():
    """模拟 Database 对象"""
    db = MagicMock()
    db.get_trends.return_value = [
        {"id": "trend-1", "title": "AI News", "score": 85.0, "risk_score": 40.0},
        {"id": "trend-2", "title": "Crypto Update", "score": 72.0, "risk_score": 65.0},
    ]
    db.create_content_with_risk.return_value = {"id": "content-1", "status": "draft"}
    db.get_current_niche.return_value = "ai_tools"
    db.set_niche.return_value = True
    return db


@pytest.fixture
def mock_llm_router():
    """模拟 LLMRouter（返回预设 JSON 响应）"""
    router = MagicMock()
    router.generate_json = AsyncMock(
        return_value={
            "tweets": [
                {"angle": "Hot take", "content": "Test tweet 1 #AI", "hashtags": ["#AI"]},
                {"angle": "Data/Research", "content": "Test tweet 2 #Data", "hashtags": ["#Data"]},
                {
                    "angle": "Interactive Poll",
                    "content": "Test tweet 3? #Poll",
                    "hashtags": ["#Poll"],
                },
            ],
            "media_suggestion": "ai, tech",
        }
    )
    router.chat = AsyncMock(return_value="Mock LLM response")
    return router


@pytest.fixture
def mock_openclaw():
    """模拟 OpenClawBridge"""
    bridge = MagicMock()
    bridge.post_content = AsyncMock(
        return_value={
            "success": True,
            "post_id": "mock_post_123",
            "url": "https://x.com/status/mock_post_123",
        }
    )
    bridge.comment_on_post = AsyncMock(
        return_value={
            "success": True,
            "comment_id": "mock_comment_123",
        }
    )
    return bridge
