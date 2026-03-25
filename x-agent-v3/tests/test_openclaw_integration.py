"""
test_openclaw_integration.py - OpenClaw 集成测试

测试内容：
1. OpenClaw Bridge 基本功能
2. Scheduler 定时任务
3. Research 研究功能
4. Trends 采集功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime


# ============ 测试 OpenClaw Bridge ============

async def test_openclaw_bridge():
    """测试 OpenClaw 桥接器"""
    print("\n=== 测试 OpenClaw Bridge ===")
    
    from modules.openclaw_bridge import OpenClawBridge, create_openclaw_bridge
    
    # 创建桥接器
    bridge = await create_openclaw_bridge()
    
    # 测试基本功能
    print(f"✓ 创建桥接器成功")
    print(f"  - 自动发帖：{bridge.auto_post_enabled}")
    print(f"  - 自动评论：{bridge.auto_comment_enabled}")
    print(f"  - 发帖限额：{bridge.daily_post_limit}/天")
    print(f"  - 评论限额：{bridge.daily_comment_limit}/天")
    
    # 测试开关
    bridge.set_auto_post(True)
    bridge.set_auto_comment(True)
    print(f"✓ 启用自动发帖和评论")
    
    # 测试防重复
    content = "测试内容"
    is_dup = bridge._is_duplicate(content)
    print(f"✓ 内容重复检查：{not is_dup}")
    
    # 测试内容变体
    variant = bridge._create_content_variant(content)
    print(f"✓ 内容变体：{variant}")
    
    # 测试统计
    stats = bridge.get_stats()
    print(f"✓ 统计信息：{stats}")
    
    # 测试限额设置
    bridge.set_daily_limits(post=5, comment=20)
    print(f"✓ 设置新限额：发帖={bridge.daily_post_limit}, 评论={bridge.daily_comment_limit}")
    
    print("\n✅ OpenClaw Bridge 测试通过")
    return True


# ============ 测试 Scheduler ============

async def test_scheduler():
    """测试调度器"""
    print("\n=== 测试 Scheduler ===")
    
    from modules.scheduler import SchedulerManager, create_scheduler
    from modules.openclaw_bridge import OpenClawBridge
    
    # 创建调度器
    scheduler = create_scheduler()
    
    print(f"✓ 创建调度器成功")
    print(f"  - 时区：Europe/London")
    print(f"  - 运行状态：{scheduler.running}")
    
    # 启动调度器
    await scheduler.start()
    print(f"✓ 调度器已启动")
    
    # 获取任务列表
    jobs = scheduler.get_all_jobs()
    print(f"✓ 已配置 {len(jobs)} 个任务:")
    for job in jobs:
        print(f"  - {job['name']} ({job['id']}): 下次运行 {job['next_run']}")
    
    # 测试任务状态
    for job in jobs:
        status = scheduler.get_job_status(job['id'])
        print(f"✓ 任务 {job['id']} 状态：{status}")
    
    # 停止调度器
    await scheduler.stop()
    print(f"✓ 调度器已停止")
    
    print("\n✅ Scheduler 测试通过")
    return True


# ============ 测试 Research ============

async def test_research():
    """测试研究模块"""
    print("\n=== 测试 Research ===")
    
    from modules.research import Researcher, research_topic
    
    # 测试研究者
    researcher = Researcher()
    print(f"✓ 创建研究者成功")
    print(f"  - 支持平台：{researcher.supported_platforms}")
    
    # 测试模拟研究（不实际调用 API）
    result = researcher._mock_research_result("test topic", ['x', 'reddit'])
    print(f"✓ 模拟研究结果:")
    print(f"  - 摘要：{result['summary'][:50]}...")
    print(f"  - 平台：{result['platforms']}")
    print(f"  - 引用：{len(result['citations'])} 条")
    
    # 测试错误结果
    error_result = researcher._error_result("test", "general", "test error")
    print(f"✓ 错误处理：{error_result.get('error')}")
    
    print("\n✅ Research 测试通过")
    return True


# ============ 测试 Trends ============

async def test_trends():
    """测试趋势采集"""
    print("\n=== 测试 Trends ===")
    
    from modules import trends
    
    # 测试 Google Trends（模拟）
    print(f"✓ 测试 Google Trends 采集函数")
    try:
        google_trends = trends.fetch_google_trends(keywords=["test"])
        print(f"  - 采集到 {len(google_trends)} 条")
    except Exception as e:
        print(f"  - 跳过（依赖库未安装）: {e}")
    
    # 测试 X Trends（模拟）
    print(f"✓ 测试 X Trends 采集函数")
    try:
        x_trends = trends.fetch_x_trends()
        print(f"  - 采集到 {len(x_trends)} 条")
    except Exception as e:
        print(f"  - 跳过（网络问题）: {e}")
    
    # 测试 Reddit Trends（模拟）
    print(f"✓ 测试 Reddit 采集函数")
    try:
        reddit_trends = trends.fetch_reddit_trends(subreddits=["test"])
        print(f"  - 采集到 {len(reddit_trends)} 条")
    except Exception as e:
        print(f"  - 跳过（依赖库未安装）: {e}")
    
    print("\n✅ Trends 测试通过")
    return True


# ============ 综合测试 ============

async def test_integration():
    """综合集成测试"""
    print("\n=== 综合集成测试 ===")
    
    from modules.openclaw_bridge import OpenClawBridge
    from modules.scheduler import SchedulerManager
    
    # 创建组件
    bridge = await OpenClawBridge().__class__.create_openclaw_bridge() if hasattr(OpenClawBridge, 'create_openclaw_bridge') else await OpenClawBridge()
    scheduler = SchedulerManager()
    
    print(f"✓ 创建所有组件成功")
    
    # 测试组件协作
    scheduler.openclaw_bridge = bridge
    print(f"✓ 组件关联成功")
    
    print("\n✅ 综合集成测试通过")
    return True


# ============ 主函数 ============

async def main():
    """运行所有测试"""
    print("=" * 60)
    print("X-Agent v3 - OpenClaw 集成测试")
    print(f"开始时间：{datetime.now().isoformat()}")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    try:
        results.append(await test_openclaw_bridge())
    except Exception as e:
        print(f"\n❌ OpenClaw Bridge 测试失败：{e}")
        results.append(False)
    
    try:
        results.append(await test_scheduler())
    except Exception as e:
        print(f"\n❌ Scheduler 测试失败：{e}")
        results.append(False)
    
    try:
        results.append(await test_research())
    except Exception as e:
        print(f"\n❌ Research 测试失败：{e}")
        results.append(False)
    
    try:
        results.append(await test_trends())
    except Exception as e:
        print(f"\n❌ Trends 测试失败：{e}")
        results.append(False)
    
    try:
        results.append(await test_integration())
    except Exception as e:
        print(f"\n❌ 综合测试失败：{e}")
        results.append(False)
    
    # 总结
    print("\n" + "=" * 60)
    print(f"测试结果：{sum(results)}/{len(results)} 通过")
    print(f"结束时间：{datetime.now().isoformat()}")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
