"""
test_v3_modules.py - X-Agent v3.0 核心模块测试

测试范围：
1. research.py - last30days 集成
2. scorer.py - 4 维复合评分
3. generator.py - Niche 语气注入
4. openclaw_bridge.py - 防封强化
"""

import asyncio
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.research import Researcher
from modules.scorer import TrendScorer
from modules.generator import ContentGenerator
from modules.openclaw_bridge import OpenClawBridge


async def test_researcher():
    """测试 research 模块"""
    print("\n" + "="*60)
    print("测试 1: research.py - last30days 集成")
    print("="*60)

    researcher = Researcher()

    # 测试研究功能
    result = await researcher.research(
        topic='AI breakthrough',
        niche='ai_tools',
        days=7,
        sources=['x', 'reddit', 'youtube']
    )

    # 验证 last30days 字段
    assert 'relevance_score' in result, "缺少 relevance_score 字段"
    assert 'velocity_24h' in result, "缺少 velocity_24h 字段"
    assert 'authority_score' in result, "缺少 authority_score 字段"
    assert 'platform_count' in result, "缺少 platform_count 字段"

    # 验证分数范围
    assert 0 <= result['relevance_score'] <= 100, "relevance_score 超出范围"
    assert 0 <= result['velocity_24h'] <= 100, "velocity_24h 超出范围"
    assert 0 <= result['authority_score'] <= 100, "authority_score 超出范围"

    print(f"✓ 话题：{result.get('topic')}")
    print(f"✓ Relevance Score: {result.get('relevance_score'):.1f}")
    print(f"✓ Velocity 24h: {result.get('velocity_24h'):.1f}")
    print(f"✓ Authority Score: {result.get('authority_score'):.1f}")
    print(f"✓ Platform Count: {result.get('platform_count')}")
    print(f"✓ 摘要：{result.get('summary', '')[:50]}...")
    print("✓ research.py 测试通过")
    return True


async def test_scorer():
    """测试 scorer 模块"""
    print("\n" + "="*60)
    print("测试 2: scorer.py - 4 维复合评分")
    print("="*60)

    scorer = TrendScorer()

    # 测试数据（模拟 last30days 返回）
    test_trend = {
        'topic': 'Breaking: AI breakthrough announced',
        'summary': 'Major AI company announces new model',
        'source': 'Twitter Verified',
        'engagement_24h': 150,
        'author_score': 85,
        'platforms': ['twitter', 'reddit', 'youtube'],
        'upvotes': 500,
        # last30days 字段
        'relevance_score': 85.0,
        'velocity_24h': 75.0,
        'authority_score': 80.0,
        'platform_count': 3
    }

    # 计算评分
    score = scorer.calculate_score(test_trend)

    # 验证评分逻辑
    assert 0 <= score <= 100, f"评分超出范围：{score}"
    assert 'dimension_scores' in test_trend, "缺少维度分数"

    # 验证阈值判断
    assert scorer.get_score_level(score) in ['HIGH', 'MEDIUM', 'LOW'], "等级判断错误"

    print(f"✓ 综合评分：{score:.2f}")
    print(f"✓ 等级：{scorer.get_score_level(score)}")
    print(f"✓ 立即推送：{scorer.should_push_immediately(score)}")
    print(f"✓ 存储：{scorer.should_store(score)}")
    print(f"✓ 丢弃：{scorer.should_discard(score)}")
    print(f"✓ 各维度分数：{test_trend.get('dimension_scores', {})}")
    print("✓ scorer.py 测试通过")
    return True


async def test_generator():
    """测试 generator 模块"""
    print("\n" + "="*60)
    print("测试 3: generator.py - Niche 语气注入")
    print("="*60)

    generator = ContentGenerator(niche='ai_tools')

    # 测试 A 类生成
    result_a = await generator.generate_type_a(
        topic='AI breakthrough',
        summary='New model achieves unprecedented performance',
        source='Twitter',
        score=85.0
    )

    assert 'tweets' in result_a, "缺少 tweets 字段"
    assert len(result_a['tweets']) >= 1, "推文数量不足"

    print(f"✓ A 类生成：{len(result_a['tweets'])} 条推文")
    for i, tweet in enumerate(result_a['tweets'][:2]):  # 显示前 2 条
        print(f"  - {tweet.get('angle')}: {tweet.get('content')[:50]}...")

    # 测试 B 类生成
    result_b = await generator.generate_type_b(
        topic='AI breakthrough',
        summary='New model achieves unprecedented performance',
        source='Twitter',
        score=85.0
    )

    assert 'script' in result_b, "缺少 script 字段"
    assert 'title' in result_b, "缺少 title 字段"

    print(f"✓ B 类生成：{result_b.get('title')}")
    print(f"  - 开场钩子：{result_b['script']['hook']['content'][:30]}...")

    # 测试评论生成
    result_c = await generator.generate_comment(
        post_content='Just launched my new AI product!',
        author='tech_ceo',
        hashtags=['#AI', '#Launch']
    )

    assert 'comments' in result_c, "缺少 comments 字段"

    print(f"✓ 评论生成：{len(result_c['comments'])} 条")
    for i, comment in enumerate(result_c['comments'][:2]):  # 显示前 2 条
        print(f"  - {comment.get('content')[:50]}...")

    print("✓ generator.py 测试通过")
    return True


async def test_openclaw_bridge():
    """测试 openclaw_bridge 模块"""
    print("\n" + "="*60)
    print("测试 4: openclaw_bridge.py - 防封强化")
    print("="*60)

    bridge = OpenClawBridge()

    # 测试统计信息
    stats = bridge.get_stats()
    assert 'post_count' in stats, "缺少 post_count"
    assert 'comment_count' in stats, "缺少 comment_count"
    assert 'daily_post_limit' in stats, "缺少 daily_post_limit"

    print(f"✓ 统计信息：")
    print(f"  - 发帖数：{stats['post_count']}/{stats['daily_post_limit']}")
    print(f"  - 评论数：{stats['comment_count']}/{stats['daily_comment_limit']}")
    print(f"  - 已发布哈希：{stats['posted_hashes_count']}")

    # 测试内容变体
    original = "This is a test post about AI"
    variants = set()
    for _ in range(3):
        variant = bridge._create_content_variant(original)
        variants.add(variant)

    print(f"✓ 内容变体测试：")
    print(f"  - 原始：{original}")
    for i, v in enumerate(variants, 1):
        print(f"  - 变体{i}: {v}")

    # 测试哈希生成
    hash1 = bridge._generate_content_hash("test content")
    hash2 = bridge._generate_content_hash("test content")
    hash3 = bridge._generate_content_hash("different content")

    assert hash1 == hash2, "相同内容哈希不一致"
    assert hash1 != hash3, "不同内容哈希相同"

    print(f"✓ 哈希生成：{hash1[:16]}...")
    print("✓ openclaw_bridge.py 测试通过")
    return True


async def test_score_thresholds():
    """测试评分阈值逻辑"""
    print("\n" + "="*60)
    print("测试 5: 评分阈值过滤逻辑")
    print("="*60)

    scorer = TrendScorer()

    # 测试不同分数段
    test_cases = [
        (50.0, 'LOW', False, False, True),    # <60 丢弃
        (65.0, 'MEDIUM', False, True, False), # 60-79 汇总
        (85.0, 'HIGH', True, True, False),    # ≥80 立即推送
    ]

    for score, expected_level, expect_push, expect_store, expect_discard in test_cases:
        level = scorer.get_score_level(score)
        should_push = scorer.should_push_immediately(score)
        should_store = scorer.should_store(score)
        should_discard = scorer.should_discard(score)

        assert level == expected_level, f"等级错误：{score} -> {level}"
        assert should_push == expect_push, f"推送判断错误：{score}"
        assert should_store == expect_store, f"存储判断错误：{score}"
        assert should_discard == expect_discard, f"丢弃判断错误：{score}"

        print(f"✓ {score}分 -> {level} (推送:{should_push}, 存储:{should_store}, 丢弃:{should_discard})")

    print("✓ 评分阈值逻辑测试通过")
    return True


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("X-Agent v3.0 核心模块测试")
    print("="*60)

    tests = [
        ("Research", test_researcher),
        ("Scorer", test_scorer),
        ("Generator", test_generator),
        ("OpenClaw Bridge", test_openclaw_bridge),
        ("Score Thresholds", test_score_thresholds),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {name} 测试失败：{e}")
            failed += 1

    print("\n" + "="*60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("="*60)

    return failed == 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
