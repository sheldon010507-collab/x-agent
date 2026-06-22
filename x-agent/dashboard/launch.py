"""
启动脚本 - 一键启动 X-Agent 多账号监控系统

Usage: python dashboard/launch.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.app import Platform, _make_account, account_pool, update_account_status_task
from dashboard.app import app  # noqa: F401


def init_sample_accounts():
    """初始化示例账号（实际应从数据库/配置文件读取）"""
    samples = [
        ("reddit_1", Platform.REDDIT, "xagent_research1", "Research Bot 1", 10),
        ("reddit_2", Platform.REDDIT, "xagent_research2", "Research Bot 2", 10),
        ("reddit_3", Platform.REDDIT, "xagent_research3", "Research Bot 3", 10),
        ("x_1", Platform.X, "xagent_poster", "X Content Bot", 10),
        ("ig_1", Platform.INSTAGRAM, "xagent_visual", "Visual Bot", 5),
        ("tt_1", Platform.TIKTOK, "xagent_shorts", "Shorts Bot", 3),
        ("yt_1", Platform.YOUTUBE, "xagent_longform", "Longform Bot", 2),
    ]
    for acc_id, plat, username, display, limit in samples:
        existing = account_pool.get_account(acc_id)
        if existing:
            continue
        account_pool.add_account(_make_account(acc_id, plat, username, display, limit))

    print(f"Initialized {len(account_pool.get_all_accounts())} accounts")


async def main():
    import uvicorn

    print("X-Agent Dashboard Starting...")
    print("=" * 50)

    init_sample_accounts()
    asyncio.create_task(update_account_status_task())

    config = uvicorn.Config(
        "dashboard.app:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )
    server = uvicorn.Server(config)

    print("Dashboard available at: http://localhost:8080")
    print("WebSocket endpoint: ws://localhost:8080/ws")
    print("=" * 50)

    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
