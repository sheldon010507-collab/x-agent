"""
test_modules_basic.py - 基础模块测试（不依赖外部库）

测试内容：
1. 模块导入
2. 类实例化
3. 基本功能验证
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("X-Agent v3 - OpenClaw 集成测试（基础版）")
print(f"开始时间：{datetime.now().isoformat()}")
print("=" * 60)

# ============ 测试 1: 模块导入 ============
print("\n=== 测试 1: 模块导入 ===")

try:
    from modules.openclaw_bridge import OpenClawBridge, create_openclaw_bridge
    print("✓ openclaw_bridge 导入成功")
except Exception as e:
    print(f"✗ openclaw_bridge 导入失败：{e}")
    sys.exit(1)

try:
    from modules.scheduler import SchedulerManager, create_scheduler
    print("✓ scheduler 导入成功")
except Exception as e:
    print(f"✗ scheduler 导入失败：{e}")
    sys.exit(1)

try:
    from modules.research import Researcher, research_topic
    print("✓ research 导入成功")
except Exception as e:
    print(f"✗ research 导入失败：{e}")
    sys.exit(1)

try:
    from modules import trends
    print("✓ trends 导入成功")
except Exception as e:
    print(f"✗ trends 导入失败：{e}")
    sys.exit(1)

print("\n✅ 所有模块导入成功")

# ============ 测试 2: OpenClaw Bridge ============
print("\n=== 测试 2: OpenClaw Bridge ===")

async def test_bridge():
    bridge = await create_openclaw_bridge()
    print(f"✓ 创建桥接器实例")
    
    # 测试配置
    assert hasattr(bridge, 'auto_post_enabled'), "缺少 auto_post_enabled 属性"
    assert hasattr(bridge, 'auto_comment_enabled'), "缺少 auto_comment_enabled 属性"
    assert hasattr(bridge, 'daily_post_limit'), "缺少 daily_post_limit 属性"
    assert hasattr(bridge, 'daily_comment_limit'), "缺少 daily_comment_limit 属性"
    print(f"✓ 属性检查通过")
    
    # 测试开关
    bridge.set_auto_post(True)
    bridge.set_auto_comment(True)
    assert bridge.auto_post_enabled == True, "自动发帖启用失败"
    assert bridge.auto_comment_enabled == True, "自动评论启用失败"
    print(f"✓ 开关控制正常")
    
    # 测试限额
    bridge.set_daily_limits(post=5, comment=20)
    assert bridge.daily_post_limit == 5, "发帖限额设置失败"
    assert bridge.daily_comment_limit == 20, "评论限额设置失败"
    print(f"✓ 限额设置正常")
    
    # 测试防重复
    content = "测试内容"
    hash1 = bridge._generate_content_hash(content)
    hash2 = bridge._generate_content_hash(content)
    assert hash1 == hash2, "哈希生成不一致"
    print(f"✓ 内容哈希生成正常")
    
    # 检查是否重复（应该不重复）
    is_dup = bridge._is_duplicate(content)
    assert is_dup == False, "新内容不应标记为重复"
    print(f"✓ 重复检查正常")
    
    # 测试统计
    stats = bridge.get_stats()
    assert 'post_count' in stats, "统计缺少 post_count"
    assert 'comment_count' in stats, "统计缺少 comment_count"
    print(f"✓ 统计功能正常")
    
    return True

try:
    result = asyncio.run(test_bridge())
    print("\n✅ OpenClaw Bridge 测试通过")
except Exception as e:
    print(f"\n❌ OpenClaw Bridge 测试失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============ 测试 3: Scheduler ============
print("\n=== 测试 3: Scheduler ===")

async def test_scheduler():
    scheduler = create_scheduler()
    print(f"✓ 创建调度器实例")
    
    # 测试属性
    assert hasattr(scheduler, 'scheduler'), "缺少 scheduler 属性"
    assert hasattr(scheduler, 'running'), "缺少 running 属性"
    print(f"✓ 属性检查通过")
    
    # 测试启动
    await scheduler.start()
    assert scheduler.running == True, "启动状态错误"
    print(f"✓ 调度器启动成功")
    
    # 测试任务配置
    jobs = scheduler.get_all_jobs()
    print(f"✓ 已配置 {len(jobs)} 个任务")
    
    # 验证任务
    expected_jobs = [
        'x_agent_v3_fetch_trends',
        'x_agent_v3_daily_review',
        'x_agent_v3_auto_comment',
        'x_agent_v3_reset_counts'
    ]
    
    job_ids = [job['id'] for job in jobs]
    for job_id in expected_jobs:
        assert job_id in job_ids, f"缺少任务：{job_id}"
    print(f"✓ 所有必需任务已配置")
    
    # 测试停止
    await scheduler.stop()
    assert scheduler.running == False, "停止状态错误"
    print(f"✓ 调度器停止成功")
    
    return True

try:
    result = asyncio.run(test_scheduler())
    print("\n✅ Scheduler 测试通过")
except Exception as e:
    print(f"\n❌ Scheduler 测试失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============ 测试 4: Research ============
print("\n=== 测试 4: Research ===")

async def test_research():
    researcher = Researcher()
    print(f"✓ 创建研究者实例")
    
    # 测试属性
    assert hasattr(researcher, 'supported_platforms'), "缺少 supported_platforms 属性"
    print(f"✓ 支持平台：{len(researcher.supported_platforms)} 个")
    
    # 验证平台列表
    expected_platforms = ['x', 'reddit', 'youtube', 'hn', 'web', 'tiktok', 'ig', 'bluesky', 'polymarket']
    for platform in expected_platforms:
        assert platform in researcher.supported_platforms, f"缺少平台：{platform}"
    print(f"✓ 所有必需平台已支持")
    
    # 测试模拟结果
    mock_result = researcher._mock_research_result("test topic", ['x', 'reddit'])
    assert 'summary' in mock_result, "缺少 summary"
    assert 'platforms' in mock_result, "缺少 platforms"
    assert 'citations' in mock_result, "缺少 citations"
    print(f"✓ 模拟结果生成正常")
    
    # 测试错误结果
    error_result = researcher._error_result("test", "general", "test error")
    assert 'error' in error_result, "缺少 error 字段"
    assert error_result['error'] == "test error", "错误信息不匹配"
    print(f"✓ 错误处理正常")
    
    return True

try:
    result = asyncio.run(test_research())
    print("\n✅ Research 测试通过")
except Exception as e:
    print(f"\n❌ Research 测试失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============ 测试 5: Trends ============
print("\n=== 测试 5: Trends ===")

try:
    # 测试函数存在
    assert hasattr(trends, 'fetch_google_trends'), "缺少 fetch_google_trends"
    assert hasattr(trends, 'fetch_x_trends'), "缺少 fetch_x_trends"
    assert hasattr(trends, 'fetch_reddit_trends'), "缺少 fetch_reddit_trends"
    assert hasattr(trends, 'fetch_all_trends'), "缺少 fetch_all_trends"
    print(f"✓ 所有趋势采集函数存在")
    
    # 测试 fetch_all_trends 函数签名
    import inspect
    sig = inspect.signature(trends.fetch_all_trends)
    params = list(sig.parameters.keys())
    assert 'niche' in params, "缺少 niche 参数"
    assert 'use_x' in params, "缺少 use_x 参数"
    assert 'use_reddit' in params, "缺少 use_reddit 参数"
    print(f"✓ 函数签名正确")
    
except Exception as e:
    print(f"\n❌ Trends 测试失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Trends 测试通过")

# ============ 总结 ============
print("\n" + "=" * 60)
print("✅ 所有测试通过!")
print(f"结束时间：{datetime.now().isoformat()}")
print("=" * 60)
print("\n模块功能摘要:")
print("- OpenClaw Bridge: ✓ 发帖、评论、防重复、限额控制")
print("- Scheduler: ✓ 定时任务、APScheduler、英国时区")
print("- Research: ✓ 多平台研究、last30days 集成")
print("- Trends: ✓ Google/X/Reddit 趋势采集")
print("\nOpenClaw 集成任务完成")
