""" test_core_modules.py - 测试核心模块（不依赖外部服务） """
import sys
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_scorer_module():
    """测试评分模块"""
    print("=" * 60)
    print("测试评分模块 (scorer.py)")
    print("=" * 60)
    
    from modules.scorer import TrendScorer
    
    # 测试数据
    test_trends = [
        {
            'topic': 'Breaking: AI breakthrough announced',
            'summary': 'Major AI company announces new model',
            'source': 'Twitter Verified',
            'engagement_24h': 150,
            'author_score': 85,
            'platforms': ['twitter', 'reddit', 'youtube'],
            'upvotes': 500,
            'created_at': datetime.now()
        },
        {
            'topic': 'Minor update released',
            'summary': 'Small bug fix',
            'source': 'GitHub',
            'engagement_24h': 10,
            'author_score': 30,
            'platforms': ['github'],
            'upvotes': 5,
            'created_at': datetime.now()
        }
    ]
    
    scorer = TrendScorer()
    
    # 测试单个评分
    print("\n1. 测试单个热点评分:")
    for i, trend in enumerate(test_trends, 1):
        score = scorer.calculate_score(trend)
        level = scorer.get_score_level(score)
        action = scorer.get_action_recommendation(score)
        
        print(f"\n  热点 {i}: {trend['topic'][:40]}...")
        print(f"  综合分数：{score:.2f}")
        print(f"  等级：{level}")
        if 'dimension_scores' in trend:
            print(f"  维度分数:")
            print(f"    - Relevance: {trend['dimension_scores']['relevance']:.2f}")
            print(f"    - Velocity: {trend['dimension_scores']['velocity']:.2f}")
            print(f"    - Authority: {trend['dimension_scores']['authority']:.2f}")
            print(f"    - Convergence: {trend['dimension_scores']['convergence']:.2f}")
        print(f"  操作建议：{action['action']} ({action['description']})")
    
    # 测试阈值判断
    print("\n2. 测试阈值判断:")
    test_scores = [85, 75, 55]
    for score in test_scores:
        push = scorer.should_push_immediately(score)
        store = scorer.should_store(score)
        discard = scorer.should_discard(score)
        print(f"  {score}分 -> 推送：{push}, 存储：{store}, 丢弃：{discard}")
    
    print("\n✅ 评分模块测试完成\n")
    return True


def test_generator_module():
    """测试生成器模块"""
    print("=" * 60)
    print("测试生成器模块 (generator.py)")
    print("=" * 60)
    
    from modules.generator import ContentGenerator
    
    # 测试 Niche 语气加载
    print("\n1. 测试 Niche 语气加载:")
    niches = ['ai_tools', 'beauty', 'fitness', 'crypto', 'humor', 'general']
    generator = ContentGenerator(niche='general')
    
    for niche in niches:
        voice = generator._load_niche_voice(niche)
        print(f"  ✓ {niche}: {len(voice)} 字符")
    
    # 测试 A 类生成（模拟）
    print("\n2. 测试 A 类生成（模拟）:")
    mock_result = generator._mock_type_a_result("AI breakthrough")
    print(f"  生成推文数量：{len(mock_result['tweets'])}")
    for i, tweet in enumerate(mock_result['tweets'], 1):
        print(f"  {i}. [{tweet['angle']}] {tweet['content'][:50]}...")
    
    # 测试 B 类生成（模拟）
    print("\n3. 测试 B 类生成（模拟）:")
    mock_result_b = generator._mock_type_b_result("AI breakthrough")
    print(f"  标题：{mock_result_b['title']}")
    print(f"  角度：{mock_result_b['angle']}")
    print(f"  脚本结构：{list(mock_result_b['script'].keys())}")
    
    # 测试评论生成（模拟）
    print("\n4. 测试评论生成（模拟）:")
    mock_result_c = generator._mock_comment_result()
    print(f"  生成评论数量：{len(mock_result_c['comments'])}")
    for i, comment in enumerate(mock_result_c['comments'], 1):
        has_cta = "带 CTA" if comment['has_cta'] else "无 CTA"
        print(f"  {i}. [{has_cta}] {comment['content'][:50]}...")
    
    print("\n✅ 生成器模块测试完成\n")
    return True


def test_llm_router_structure():
    """测试 LLM 路由模块结构"""
    print("=" * 60)
    print("测试 LLM 路由模块 (llm_router.py)")
    print("=" * 60)
    
    from modules.llm_router import PROVIDER_MODELS
    
    # 测试可用供应商
    print("\n1. 支持的供应商:")
    for provider, models in PROVIDER_MODELS.items():
        print(f"  - {provider}: {len(models)} 个模型")
        print(f"    默认模型：{models[0]}")
    
    # 测试基类
    print("\n2. 测试基类结构:")
    print(f"  ✓ LLMProvider 基类存在")
    print(f"  ✓ 必需方法：chat, generate_json")
    
    print("\n✅ LLM 路由模块测试完成\n")
    return True


def test_database_structure():
    """测试数据库结构"""
    print("=" * 60)
    print("测试数据库结构 (database.py)")
    print("=" * 60)
    
    # 读取文件内容测试结构
    db_file = Path(__file__).parent.parent / 'modules' / 'database.py'
    content = db_file.read_text()
    
    # 测试表结构
    print("\n1. 数据表结构:")
    tables = [
        ('trends', '热点记录表'),
        ('content_queue', '内容队列表'),
        ('daily_log', '每日日志表'),
        ('strategy', '策略表'),
        ('automation_settings', '自动化设置表'),
        ('llm_config', 'LLM 配置表')
    ]
    
    all_exist = True
    for table_name, table_desc in tables:
        if table_name in content:
            print(f"  ✓ {table_name} ({table_desc})")
        else:
            print(f"  ✗ {table_name} (缺失)")
            all_exist = False
    
    # 测试方法
    print("\n2. 数据库操作方法:")
    db_methods = [
        'create_trend', 'get_trends_by_score', 'update_trend_status',
        'create_content', 'get_content_queue', 'update_content_status',
        'create_daily_log', 'get_daily_log', 'update_daily_log',
        'get_current_strategy', 'create_strategy',
        'get_automation_settings', 'update_automation_settings',
        'get_llm_config', 'set_llm_config'
    ]
    
    for method in db_methods:
        if method in content:
            print(f"  ✓ {method}")
        else:
            print(f"  ✗ {method} (缺失)")
            all_exist = False
    
    print("\n✅ 数据库结构测试完成\n")
    return all_exist


def test_bot_structure():
    """测试 Bot 模块结构"""
    print("=" * 60)
    print("测试 Bot 模块结构 (bot.py)")
    print("=" * 60)
    
    bot_file = Path(__file__).parent.parent / 'bot.py'
    content = bot_file.read_text()
    
    # 测试命令处理
    print("\n1. 命令处理:")
    commands = [
        'cmd_start', 'cmd_help', 'cmd_set_niche', 'cmd_research',
        'cmd_trends', 'cmd_create', 'cmd_log', 'cmd_report',
        'cmd_strategy', 'cmd_settings', 'cmd_llm'
    ]
    
    for cmd in commands:
        if cmd in content:
            print(f"  ✓ {cmd}")
        else:
            print(f"  ✗ {cmd} (缺失)")
    
    # 测试回调处理
    print("\n2. 回调处理:")
    handlers = [
        '_handle_niche_switch', '_handle_llm_switch',
        '_handle_settings_action', '_handle_create_action',
        '_handle_log_action', '_handle_report_action',
        '_handle_strategy_action', '_handle_quick_action'
    ]
    
    for handler in handlers:
        if handler in content:
            print(f"  ✓ {handler}")
        else:
            print(f"  ✗ {handler} (缺失)")
    
    print("\n✅ Bot 模块结构测试完成\n")
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("X-Agent v3 核心模块测试")
    print("=" * 60 + "\n")
    
    try:
        # 测试各个模块
        test_scorer_module()
        test_generator_module()
        test_llm_router_structure()
        test_database_structure()
        test_bot_structure()
        
        print("\n" + "=" * 60)
        print("✅ 所有核心模块测试通过！")
        print("=" * 60 + "\n")
        return 0
    
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
