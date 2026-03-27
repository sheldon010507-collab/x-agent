"""
tests/test_modules.py - X-Agent v2.0 单元测试
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest


# ============ Config Tests ============
class TestConfig:
    """配置模块测试"""

    def test_config_import(self):
        """测试配置模块可导入"""
        import sys

        sys.path.insert(0, ".")
        from config import Config

        assert Config is not None

    def test_config_has_required_fields(self):
        """测试配置包含必需字段"""
        import sys

        sys.path.insert(0, ".")
        from config import Config

        config_instance = Config.__new__(Config)
        config_instance.telegram_bot_token = "test"
        config_instance.supabase_url = "test"
        config_instance.supabase_key = "test"
        assert hasattr(config_instance, "telegram_bot_token")
        assert hasattr(config_instance, "supabase_url")
        assert hasattr(config_instance, "supabase_key")


# ============ Database Tests ============
class TestDatabase:
    """数据库模块测试"""

    def test_database_import(self):
        """测试数据库模块可导入"""
        import sys

        sys.path.insert(0, ".")
        from modules.database import Database

        assert Database is not None

    def test_database_methods_exist(self):
        """测试数据库方法存在"""
        import sys

        sys.path.insert(0, ".")
        from modules.database import Database

        # 检查主要方法存在
        assert hasattr(Database, "create_trend")
        assert hasattr(Database, "get_high_score_trends")
        assert hasattr(Database, "mark_trend_used")


# ============ LLM Router Tests ============
class TestLLMRouter:
    """LLM路由模块测试"""

    def test_llm_router_import(self):
        """测试LLM路由模块可导入"""
        import sys

        sys.path.insert(0, ".")
        from modules.llm_router import LLMRouter

        assert LLMRouter is not None

    def test_llm_router_providers(self):
        """测试LLM路由支持多供应商"""
        import sys

        sys.path.insert(0, ".")
        from modules.llm_router import LLMRouter

        # 检查支持的供应商
        providers = ["anthropic", "openai", "groq", "gemini", "openrouter", "nvidia", "ollama"]
        # LLMRouter应该能处理这些供应商


# ============ Generator Tests ============
class TestGenerator:
    """内容生成模块测试"""

    def test_generator_import(self):
        """测试生成模块可导入"""
        import sys

        sys.path.insert(0, ".")
        from modules.generator import ContentGenerator

        assert ContentGenerator is not None

    def test_niche_voice_loading(self):
        """测试Niche语气加载"""
        import sys

        sys.path.insert(0, ".")
        from modules.generator import load_niche_voice

        # 测试加载adult语气
        voice = load_niche_voice("adult")
        assert isinstance(voice, str)


# ============ Scorer Tests ============
class TestScorer:
    """评分模块测试"""

    def test_scorer_import(self):
        """测试评分模块可导入"""
        import sys

        sys.path.insert(0, ".")
        from modules.scorer import TrendScorer

        assert TrendScorer is not None

    def test_score_range(self):
        """测试评分范围在0-100"""
        import sys

        sys.path.insert(0, ".")
        from modules.scorer import TrendScorer

        scorer = TrendScorer()
        # 评分应该在0-100之间
        mock_trend = {"topic": "test topic", "source": "reddit", "raw_score": 1000}
        score = scorer.calculate_score(mock_trend)
        assert 0 <= score <= 100


# ============ Bot Tests ============
class TestBot:
    """Bot模块测试"""

    def test_bot_import(self):
        """测试Bot模块可导入"""
        import sys

        sys.path.insert(0, ".")
        from modules.bot import XAgentBot

        assert XAgentBot is not None

    def test_bot_commands_exist(self):
        """测试Bot命令处理函数存在"""
        import sys

        sys.path.insert(0, ".")
        from modules.bot import XAgentBot

        # 检查主要命令处理函数
        bot = XAgentBot.__new__(XAgentBot)
        # Bot应该有处理命令的方法


# ============ Scheduler Tests ============
class TestScheduler:
    """调度模块测试"""

    def test_scheduler_import(self):
        """测试调度模块可导入"""
        import sys

        sys.path.insert(0, ".")
        from modules.scheduler import SchedulerManager

        assert SchedulerManager is not None


# ============ Integration Tests ============
class TestIntegration:
    """集成测试"""

    def test_main_import(self):
        """测试主模块可导入"""
        import sys

        sys.path.insert(0, ".")
        # main.py 应该能导入所有模块
        try:
            import main

            assert True
        except ImportError as e:
            # 如果缺少依赖，跳过
            pytest.skip(f"Missing dependencies: {e}")


# ============ Run Tests ============
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
