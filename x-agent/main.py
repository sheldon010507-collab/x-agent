"""
main.py - X 智能运营 Agent v3.0 入口文件

启动流程：
1. 加载配置
2. 初始化数据库
3. 初始化 LLM 路由
4. 初始化内容生成器
5. 启动 Telegram Bot
6. 启动定时任务调度器

v3.0 更新：
- 完善 logging 系统
- 支持 last30days 研究模块
- 防封机制集成
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from modules.bot_v0_final import create_bot_v0_final as create_bot
from modules.database import get_database, init_database
from modules.generator import ContentGenerator
from modules.llm_router import LLMRouter
from modules.openclaw_bridge import create_openclaw_bridge
from modules.scheduler import create_scheduler

log_dir = Path(__file__).parent / "data"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "x-agent.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


class XAgentApp:
    """X Agent 主应用类"""

    def __init__(self):
        """初始化应用"""
        self.db = None
        self.llm_router = None
        self.generator = None
        self.bot = None
        self.scheduler = None
        self.openclaw_bridge = None
        self.running = False

    async def initialize(self):
        """初始化所有组件"""
        logger.info("🚀 Initializing X Agent v3.0...")

        # 1. 初始化数据库
        try:
            self.db = init_database(config.supabase_url, config.supabase_key)
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

        # 2. 初始化 LLM 路由
        try:
            self.llm_router = LLMRouter(config)
            logger.info(f"✅ LLM Router initialized (Provider: {config.llm_provider})")
        except Exception as e:
            logger.error(f"❌ LLM Router initialization failed: {e}")
            raise

        # 3. 初始化内容生成器
        try:
            niche = "general"
            try:
                niche_data = self.db.get_current_niche()
                niche = niche_data or "general"
            except:
                pass
            self.generator = ContentGenerator(self.llm_router, niche)
            logger.info(f"✅ Content Generator initialized (Niche: {niche})")
        except Exception as e:
            logger.error(f"❌ Content Generator initialization failed: {e}")
            raise

        # 4. 初始化 OpenClaw 桥接器
        try:
            self.openclaw_bridge = await create_openclaw_bridge(config.openclaw_api_endpoint)
            logger.info("✅ OpenClaw Bridge initialized")
        except Exception as e:
            logger.error(f"❌ OpenClaw Bridge initialization failed: {e}")
            raise

        # 5. 初始化 Bot
        try:
            self.bot = create_bot(
                config.telegram_bot_token,
                db=self.db,
                llm_router=self.llm_router,
                generator=self.generator,
            )
            logger.info("✅ Telegram Bot initialized")
        except Exception as e:
            logger.error(f"❌ Telegram Bot initialization failed: {e}")
            raise

        # 6. 初始化调度器
        try:
            self.scheduler = create_scheduler(
                db=self.db,
                generator=self.generator,
                openclaw_bridge=self.openclaw_bridge,
                bot=self.bot,
            )
            logger.info("✅ Scheduler initialized")
        except Exception as e:
            logger.error(f"❌ Scheduler initialization failed: {e}")
            raise

        logger.info("🎉 All components initialized successfully!")

    async def start(self):
        """启动应用"""
        if self.running:
            logger.warning("Application is already running")
            return

        logger.info("🚀 Starting X Agent v3.0...")
        self.running = True

        # 启动调度器
        if self.scheduler:
            await self.scheduler.start()
            logger.info("✅ Scheduler started")

        # 启动 Bot
        if self.bot:
            logger.info("✅ Bot started (polling)")

        logger.info("🎉 X Agent v3.0 is now running!")

        # 保持运行
        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        """停止应用"""
        if not self.running:
            return

        logger.info("🛑 Stopping X Agent v3.0...")
        self.running = False

        # 停止调度器
        if self.scheduler:
            await self.scheduler.stop()
            logger.info("✅ Scheduler stopped")

        # 停止 Bot
        if self.bot and self.bot.application:
            await self.bot.application.stop()
            logger.info("✅ Bot stopped")

        logger.info("👋 X Agent v3.0 stopped")


async def main_async():
    """主异步函数 - 统一事件循环，避免多次 asyncio.run() 的冲突"""
    app = XAgentApp()

    loop = asyncio.get_running_loop()

    def _shutdown():
        logger.info("Received shutdown signal, stopping...")
        loop.create_task(app.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:
            # Windows 不支持 add_signal_handler，降级为 signal.signal
            signal.signal(sig, lambda s, f: loop.call_soon_threadsafe(_shutdown))

    try:
        await app.initialize()
        await app.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await app.stop()


def main():
    """主函数入口 - 单一事件循环"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
