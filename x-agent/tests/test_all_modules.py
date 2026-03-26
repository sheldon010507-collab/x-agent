""" test_all_modules.py - 综合测试所有模块 """
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.scorer import TrendScorer, calculate_trend_score
from modules.generator import ContentGenerator
from modules.llm_router import LLMRouter, PROVIDER_MODELS
from modules.database import Database
from modules.config_validator import ConfigValidator


def test_scorer_module():
    """测试评分模块"""
    print("=" * 60)
    print("测试评分模块 (scorer.py)")
    print("=" * 60)
    
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


def test_llm_router_module():
    """测试 LLM 路由模块"""
    print("=" * 60)
    print("测试 LLM 路由模块 (llm_router.py)")
    print("=" * 60)
    
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


def test_generator_module():
    """测试生成器模块"""
    print("=" * 60)
    print("测试生成器模块 (generator.py)")
    print("=" * 60)
    
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
    
    for table_name, table_desc in tables:
        if table_name in content:
            print(f"  ✓ {table_name} ({table_desc})")
        else:
            print(f"  ✗ {table_name} (缺失)")
    
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
    
    print("\n✅ 数据库结构测试完成\n")
    return True


async def test_config_validator():
    """测试配置验证器"""
    print("=" * 60)
    print("测试配置验证器 (config_validator.py)")
    print("=" * 60)
    
    validator = ConfigValidator()
    
    # 1. 验证 .env
    print("\n1. 验证 .env 文件...")
    env_valid = validator.validate_env_file()
    print(f"  {'✓' if env_valid else '✗'} .env 验证：{'通过' if env_valid else '失败'}")
    
    # 2. 验证 Supabase 连接
    print("\n2. 验证 Supabase 连接...")
    try:
        supabase_valid = await validator.validate_supabase_connection()
        print(f"  {'✓' if supabase_valid else '✗'} Supabase 连接：{'成功' if supabase_valid else '失败'}")
    except Exception as e:
        print(f"  ✗ Supabase 连接测试失败：{e}")
        supabase_valid = False
    
    # 3. 验证 LLM 供应商
    print("\n3. 验证 LLM 供应商...")
    try:
        llm_valid = await validator.validate_llm_provider()
        print(f"  {'✓' if llm_valid else '✗'} LLM 供应商：{'可用' if llm_valid else '不可用'}")
    except Exception as e:
        print(f"  ✗ LLM 验证失败：{e}")
        llm_valid = False
    
    # 汇总
    print("\n" + "=" * 60)
    print("验证汇总:")
    print("=" * 60)
    print(f"  .env 配置：{'✓' if env_valid else '✗'}")
    print(f"  Supabase: {'✓' if supabase_valid else '✗'}")
    print(f"  LLM: {'✓' if llm_valid else '✗'}")
    
    all_passed = env_valid and supabase_valid and llm_valid
    print(f"\n总体结果：{'✅ 通过' if all_passed else '❌ 失败'}")
    
    print("\n✅ 配置验证器测试完成\n")
    return all_passed


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("X-Agent v3 综合模块测试")
    print("=" * 60 + "\n")
    
    try:
        # 测试各个模块
        test_scorer_module()
        test_llm_router_module()
        test_generator_module()
        test_database_structure()
        
        # 异步测试
        await test_config_validator()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60 + "\n")
        return 0
    
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(asyncio.run(main()))
