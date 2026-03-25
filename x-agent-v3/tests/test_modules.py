"""
测试后端核心模块
"""
import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime


def test_scorer():
    """测试评分模块"""
    print("=" * 60)
    print("测试评分模块 (scorer.py)")
    print("=" * 60)
    
    from modules.scorer import TrendScorer, batch_calculate_scores, categorize_by_score
    
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
        print(f"    综合分数：{score:.2f}")
        print(f"    等级：{level}")
        print(f"    维度分数:")
        print(f"      - Relevance: {trend['dimension_scores']['relevance']:.2f}")
        print(f"      - Velocity: {trend['dimension_scores']['velocity']:.2f}")
        print(f"      - Authority: {trend['dimension_scores']['authority']:.2f}")
        print(f"      - Convergence: {trend['dimension_scores']['convergence']:.2f}")
        print(f"    操作建议：{action['action']} ({action['description']})")
    
    # 测试批量评分
    print("\n2. 测试批量评分:")
    results = batch_calculate_scores(test_trends)
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['topic'][:40]}... - {result['score']:.2f}分 ({result['score_level']})")
    
    # 测试分类
    print("\n3. 测试分类:")
    categories = categorize_by_score(results)
    print(f"  HIGH (≥80 分): {len(categories['high'])} 个")
    print(f"  MEDIUM (60-79 分): {len(categories['medium'])} 个")
    print(f"  LOW (<60 分): {len(categories['low'])} 个")
    
    print("\n✅ 评分模块测试完成\n")


def test_llm_router():
    """测试 LLM 路由模块"""
    print("=" * 60)
    print("测试 LLM 路由模块 (llm_router.py)")
    print("=" * 60)
    
    from modules.llm_router import LLMRouter, get_llm_router, PROVIDER_MODELS
    
    # 测试可用供应商
    print("\n1. 支持的供应商:")
    for provider, models in PROVIDER_MODELS.items():
        print(f"  - {provider}: {len(models)} 个模型")
        print(f"    默认模型：{models[0]}")
    
    # 测试路由器初始化
    print("\n2. 测试路由器初始化:")
    try:
        # 注意：这里不会真正调用 API，只是测试初始化
        router = LLMRouter(provider='anthropic', api_key='test_key')
        print(f"  ✓ Anthropic 路由器初始化成功")
        print(f"    当前供应商：{router.get_current_provider()}")
        print(f"    当前模型：{router.model}")
    except Exception as e:
        print(f"  ✗ 初始化失败：{e}")
    
    # 测试供应商切换
    print("\n3. 测试供应商切换:")
    providers = ['anthropic', 'openai', 'groq']
    for provider in providers:
        try:
            router = LLMRouter(provider=provider, api_key='test_key')
            print(f"  ✓ {provider}: {router.model}")
        except Exception as e:
            print(f"  ✗ {provider} 失败：{e}")
    
    print("\n✅ LLM 路由模块测试完成\n")


def test_generator():
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


def test_database_structure():
    """测试数据库结构（不实际连接）"""
    print("=" * 60)
    print("测试数据库结构 (database.py)")
    print("=" * 60)
    
    from modules.database import Database
    
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
    
    for table_name, table_desc in tables:
        print(f"  - {table_name} ({table_desc})")
    
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
        if hasattr(Database, method):
            print(f"  ✓ {method}")
        else:
            print(f"  ✗ {method} (缺失)")
    
    print("\n3. 测试初始化（需要 Supabase 凭据）:")
    print("  ⚠ 跳过实际连接测试（需要有效的 SUPABASE_URL 和 SUPABASE_KEY）")
    print("  提示：设置环境变量后运行完整测试")
    
    print("\n✅ 数据库结构测试完成\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("X-Agent v3 后端模块测试")
    print("=" * 60 + "\n")
    
    try:
        # 测试评分模块
        test_scorer()
        
        # 测试 LLM 路由模块
        test_llm_router()
        
        # 测试生成器模块
        test_generator()
        
        # 测试数据库结构
        test_database_structure()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
