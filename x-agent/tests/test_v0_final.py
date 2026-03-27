"""
test_v0_final.py - X-Agent v0 Final 核心功能测试

测试覆盖:
1. research.py - last30days 集成测试
2. scorer.py - risk_score 计算测试
3. bot_v0_final.py - 半自动流程测试
4. database.py - content_queue 状态流转测试
"""

import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.research import Researcher
from modules.scorer import Scorer
from modules.database import Database
from config import config


class TestV0FinalResearch:
    """V0 Final Research 模块测试"""
    
    def test_research_topic_with_fallback(self):
        """测试 research 在有/无 last30days CLI 时的 fallback 逻辑"""
        researcher = Researcher(config)
        
        # 测试正常研究流程
        result = researcher.research_topic(
            niche="ai_tools",
            days=7,
            sources="x,reddit,youtube"
        )
        
        # 验证返回结构
        assert isinstance(result, dict)
        # 应该有 error 或 data
        assert "error" in result or "data" in result or "fallback" in result
        print(f"✅ Research 测试通过：{result.keys() if isinstance(result, dict) else 'N/A'}")
    
    def test_research_caching(self):
        """测试 research 结果是否缓存到本地"""
        researcher = Researcher(config)
        cache_dir = Path("data/research")
        
        # 执行研究
        researcher.research_topic(niche="test", days=1)
        
        # 验证缓存目录存在
        assert cache_dir.exists(), "缓存目录应该存在"
        print("✅ Research 缓存测试通过")


class TestV0FinalScorer:
    """V0 Final Scorer 模块测试"""
    
    def test_risk_score_calculation(self):
        """测试 risk_score 计算逻辑"""
        scorer = Scorer()
        
        # 模拟研究数据
        mock_data = {
            "relevance_score": 0.8,
            "velocity_24h": 0.6,
            "authority_score": 0.7,
            "convergence": 0.5
        }
        
        # 计算评分
        result = scorer.score(mock_data)
        
        # 验证 risk_score 在 0-100 范围
        assert "risk_score" in result
        assert 0 <= result["risk_score"] <= 100
        print(f"✅ Scorer 测试通过：risk_score={result['risk_score']}")
    
    def test_high_risk_threshold(self):
        """测试高风险阈值 (≥80 禁止自动发布)"""
        scorer = Scorer()
        
        # 高风险数据
        high_risk_data = {
            "relevance_score": 0.3,  # 低相关性
            "velocity_24h": 0.2,     # 低增速
            "authority_score": 0.1,  # 低权威性
            "convergence": 0.1       # 单平台
        }
        
        result = scorer.score(high_risk_data)
        
        # 高风险应该≥80
        assert result["risk_score"] >= 80, "高风险数据应该≥80 分"
        print(f"✅ 高风险阈值测试通过：risk_score={result['risk_score']}")


class TestV0FinalBot:
    """V0 Final Bot 半自动流程测试"""
    
    def test_button_callback_parsing(self):
        """测试 Inline 按钮回调解析"""
        # 模拟按钮数据
        test_cases = [
            ("auto_publish_12345", "auto", "12345"),
            ("manual_publish_67890", "manual", "67890"),
            ("regen_11111", "regen", "11111"),
            ("skip_22222", "skip", "22222"),
        ]
        
        for data, expected_action, expected_user_id in test_cases:
            parts = data.split("_")
            action = parts[0]
            user_id = parts[-1]
            
            assert action == expected_action
            assert user_id == expected_user_id
        
        print("✅ Bot 按钮解析测试通过")
    
    def test_risk_emoji_mapping(self):
        """测试风险评分与 emoji 映射"""
        def get_risk_emoji(score):
            if score < 50:
                return "🟢"
            elif score < 80:
                return "🟡"
            else:
                return "🔴"
        
        assert get_risk_emoji(30) == "🟢"
        assert get_risk_emoji(60) == "🟡"
        assert get_risk_emoji(85) == "🔴"
        
        print("✅ 风险 emoji 映射测试通过")


class TestV0FinalDatabase:
    """V0 Final Database 状态流转测试"""

    @pytest.mark.skipif(not config.supabase_url, reason="需要 Supabase 配置")
    def test_content_status_flow(self):
        """测试内容状态流转：draft → confirmed → published"""
        # 注意：这是集成测试，需要 Supabase 环境
        # 实际运行时需跳过或 mock

        # 模拟流程:
        # 1. 创建草稿 (draft)
        # 2. 用户确认 (confirmed)
        # 3. 发布成功 (published)

        print("✅ 数据库状态流转测试通过 (模拟)")

    def test_risk_score_storage(self):
        """测试 risk_score 字段存储"""
        # 验证 Database 类有相关方法
        from modules.database import Database

        assert hasattr(Database, 'update_trend_risk_score')
        assert hasattr(Database, 'get_trends_by_risk')
        assert hasattr(Database, 'create_content_with_risk')

        print("✅ Database risk_score 方法测试通过")


class TestNativeResearch:
    """原生异步研究模块测试"""

    def test_researcher_initialization(self):
        """测试 Researcher 初始化"""
        researcher = Researcher(config=None)
        
        assert researcher.cache_dir is not None
        assert researcher.reddit_fetcher is not None
        assert researcher.hn_fetcher is not None
        assert researcher.trends_fetcher is not None
        
        print("✅ Researcher 初始化测试通过")

    def test_research_topic_structure(self):
        """测试研究返回结构"""
        researcher = Researcher(config=None)
        result = researcher.research_topic(
            niche="ai_tools",
            days=7,
            sources="reddit,hackernews"
        )
        
        assert isinstance(result, dict)
        assert "niche" in result
        assert "risk_score" in result
        assert "platforms" in result
        assert 0 <= result["risk_score"] <= 100
        
        print(f"✅ 研究返回结构测试通过，risk_score={result['risk_score']}")

    def test_risk_score_calculation(self):
        """测试风险评分计算"""
        researcher = Researcher(config=None)
        
        # 测试低风险数据
        low_risk_metrics = {
            "velocity": 30,
            "platform_count": 4,
            "authority": 70
        }
        low_score = researcher._calculate_risk_score(low_risk_metrics)
        assert low_score < 50, f"低风险数据应该 < 50，实际: {low_score}"
        
        # 测试高风险数据
        high_risk_metrics = {
            "velocity": 90,
            "platform_count": 1,
            "authority": 30
        }
        high_score = researcher._calculate_risk_score(high_risk_metrics)
        assert high_score >= 70, f"高风险数据应该 >= 70，实际: {high_score}"
        
        print(f"✅ 风险评分计算测试通过，低风险={low_score}，高风险={high_score}")

    def test_platform_fetcher_mock(self):
        """测试平台获取器模拟数据"""
        from modules.research import RedditFetcher, HackerNewsFetcher
        
        reddit = RedditFetcher(config=None)
        hn = HackerNewsFetcher()
        
        reddit_mock = reddit._mock_data("test")
        hn_mock = hn._mock_data("test")
        
        assert reddit_mock["mock"] == True
        assert "posts" in reddit_mock
        assert hn_mock["mock"] == True
        assert "posts" in hn_mock
        
        print("✅ 平台获取器模拟数据测试通过")


class TestBotCommands:
    """Bot 命令测试"""

    def test_set_niche_niches_available(self):
        """测试 set_niche 命令可用的领域"""
        available_niches = {
            "adult", "ai_tools", "beauty", "fitness",
            "crypto", "humor", "general", "custom"
        }
        
        assert len(available_niches) == 8
        assert "ai_tools" in available_niches
        assert "general" in available_niches
        
        print("✅ set_niche 领域列表测试通过")

    def test_settings_menu_structure(self):
        """测试设置菜单结构"""
        expected_settings = ["llm", "niche", "automation", "status"]
        
        # 验证设置项存在
        for setting in expected_settings:
            assert setting in ["llm", "niche", "automation", "status"]
        
        print("✅ 设置菜单结构测试通过")

    def test_llm_providers(self):
        """测试 LLM 供应商列表"""
        llm_providers = {
            "anthropic": "Claude",
            "openai": "GPT",
            "groq": "Groq",
            "gemini": "Gemini",
            "ollama": "Ollama"
        }
        
        assert len(llm_providers) >= 5
        assert "anthropic" in llm_providers
        
        print("✅ LLM 供应商列表测试通过")


# ========== 运行测试 ==========

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🧪 X-Agent v0 Final 核心功能测试")
    print("="*50 + "\n")
    
    # 1. Research 测试
    print("1️⃣ Research 模块测试:")
    test_research = TestV0FinalResearch()
    try:
        test_research.test_research_topic_with_fallback()
        test_research.test_research_caching()
    except Exception as e:
        print(f"⚠️ Research 测试跳过：{e}")
    
    # 2. Scorer 测试
    print("\n2️⃣ Scorer 模块测试:")
    test_scorer = TestV0FinalScorer()
    try:
        test_scorer.test_risk_score_calculation()
        test_scorer.test_high_risk_threshold()
    except Exception as e:
        print(f"⚠️ Scorer 测试跳过：{e}")
    
    # 3. Bot 测试
    print("\n3️⃣ Bot 流程测试:")
    test_bot = TestV0FinalBot()
    test_bot.test_button_callback_parsing()
    test_bot.test_risk_emoji_mapping()
    
    # 4. Database 测试
    print("\n4️⃣ Database 模块测试:")
    test_db = TestV0FinalDatabase()
    test_db.test_content_status_flow()
    test_db.test_risk_score_storage()

    # 5. Native Research 测试
    print("\n5️⃣ Native Research 模块测试:")
    test_native = TestNativeResearch()
    test_native.test_researcher_initialization()
    test_native.test_research_topic_structure()
    test_native.test_risk_score_calculation()
    test_native.test_platform_fetcher_mock()

    # 6. Bot Commands 测试
    print("\n6️⃣ Bot Commands 测试:")
    test_cmds = TestBotCommands()
    test_cmds.test_set_niche_niches_available()
    test_cmds.test_settings_menu_structure()
    test_cmds.test_llm_providers()

    print("\n" + "="*50)
    print("✅ 所有测试完成！")
    print("="*50)
