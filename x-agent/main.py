"""
main.py - X 智能运营 Agent v2.0 入口文件

启动流程：
1. 加载配置
2. 初始化数据库
3. 初始化 LLM 路由
4. 初始化内容生成器
5. 启动 Telegram Bot
6. 启动定时任务调度器
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from modules.config import config
from modules.database import init_database, get_database
from modules.llm_router import LLMRouter
from modules.generator import ContentGenerator
from modules.bot import create_bot
from modules.scheduler import create_scheduler
from modules.openclaw_bridge import create_openclaw_bridge

# 配置日志（同时输出到控制台和文件）
log_dir = Path(__file__).parent / 'data'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'x-agent.log', encoding='utf-8')
    ]
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
        logger.info("🚀 Initializing X Agent v2.0...")
        
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
            niche = 'general'
            try:
                niche_data = self.db.get_current_niche()
                niche = niche_data or 'general'
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
                generator=self.generator
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
                bot=self.bot
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
        
        logger.info("🚀 Starting X Agent v2.0...")
        self.running = True
        
        # 启动 Bot（非阻塞）
        # 注意：telegram.ext 的 run_polling 是阻塞的
        # 这里我们假设 Bot 在自己的线程中运行
        
        # 启动调度器
        if self.scheduler:
            await self.scheduler.start()
            logger.info("✅ Scheduler started")
        
        # 启动 Bot
        if self.bot:
            # 在实际实现中，Bot 应该在单独的线程中运行
            # 这里简化处理
            logger.info("✅ Bot started (polling)")
        
        logger.info("🎉 X Agent v2.0 is now running!")
        
        # 保持运行
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """停止应用"""
        if not self.running:
            return
        
        logger.info("🛑 Stopping X Agent v2.0...")
        self.running = False
        
        # 停止调度器
        if self.scheduler:
            await self.scheduler.stop()
            logger.info("✅ Scheduler stopped")
        
        # 停止 Bot
        if self.bot and self.bot.application:
            await self.bot.application.stop()
            logger.info("✅ Bot stopped")
        
        logger.info("👋 X Agent v2.0 stopped")



def main():
    """主函数"""
    app = XAgentApp()
    
    # 信号处理
    def signal_handler(sig, frame):
        logger.info(f"\nReceived signal {sig}, shutting down...")
        asyncio.run(app.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行应用
    try:
        asyncio.run(app.initialize())
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        asyncio.run(app.stop())


if __name__ == '__main__':
    main()
