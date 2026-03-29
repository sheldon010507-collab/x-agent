"""
openclaw_agent.py - OpenClaw 发布 Agent

独立的后台进程，监听发布队列并通过 OpenClaw 执行 X 发布
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Optional

from dotenv import load_dotenv

from modules.database import Database
from modules.openclaw_bridge import OpenClawBridge

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [OpenClaw Agent] - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class OpenClawAgent:
    """OpenClaw 发布 Agent - 管理所有 X 平台发布"""

    def __init__(self):
        self.db = Database()
        self.openclaw = OpenClawBridge(
            api_endpoint=os.getenv("OPENCLAW_API_ENDPOINT", "http://localhost:8080")
        )
        self.running = False

    async def initialize(self) -> bool:
        """初始化 Agent"""
        logger.info("🚀 OpenClaw Agent 启动中...")

        # 初始化 OpenClaw
        success = await self.openclaw.initialize()
        if not success:
            logger.error("❌ 无法初始化 OpenClaw，请检查配置")
            return False

        # 启用自动发帖
        self.openclaw.set_auto_post(True)
        logger.info("✅ OpenClaw 已初始化，自动发帖已启用")

        return True

    async def process_queue(self):
        """处理发布队列"""
        logger.info("🔄 开始监听发布队列...")

        while self.running:
            try:
                # 从数据库获取待发布内容
                pending_posts = self.db.get_pending_posts(limit=5)

                for post in pending_posts:
                    await self._publish_post(post)

                # 每 10 秒检查一次
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"❌ 处理队列时出错: {e}")
                await asyncio.sleep(30)

    async def _publish_post(self, post: Dict):
        """发布单条内容"""
        post_id = post.get("id")
        content = post.get("content")
        post_type = post.get("type", "A")  # A/B/C

        logger.info(f"📤 发布 {post_type} 类内容 (ID: {post_id})")

        try:
            result = await self.openclaw.post_content(
                content=content, niche=post.get("niche", "general"), apply_variant=True
            )

            if result.get("success"):
                # 更新数据库
                self.db.update_post_status(post_id, "published", result)
                logger.info(f"✅ 发布成功: {post_id}")
            else:
                logger.warning(f"⚠️ 发布失败 (ID: {post_id}): {result.get('reason')}")
                self.db.update_post_status(post_id, "failed", result)

        except Exception as e:
            logger.error(f"❌ 发布异常 (ID: {post_id}): {e}")
            self.db.update_post_status(post_id, "error", {"error": str(e)})

    async def get_status(self) -> Dict:
        """获取 Agent 状态"""
        return {
            "agent": "openclaw",
            "status": "running" if self.running else "stopped",
            "openclaw_status": self.openclaw.get_status(),
            "timestamp": datetime.now().isoformat(),
        }

    async def run(self):
        """启动 Agent"""
        if not await self.initialize():
            logger.error("❌ Agent 初始化失败，退出")
            return

        self.running = True
        logger.info("✨ OpenClaw Agent 已启动")

        try:
            await self.process_queue()
        except KeyboardInterrupt:
            logger.info("⏹️  收到停止信号")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """优雅关闭"""
        logger.info("🛑 OpenClaw Agent 关闭中...")
        self.running = False
        await self.openclaw.close()
        logger.info("✅ OpenClaw Agent 已关闭")


async def main():
    agent = OpenClawAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
