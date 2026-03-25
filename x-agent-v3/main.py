"""
main.py - X-Agent v3 入口文件

启动流程：
1. 加载配置
2. 初始化数据库
3. 初始化 LLM 路由
4. 初始化内容生成器
5. 启动 Telegram Bot
6. 启动定时任务调度器

功能：
- 整合所有模块
- 实现 LLM 路由配置
- 实现 Niche 切换逻辑
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入配置
from config import Config
from modules.database import init_database, get_database
from modules.llm_router import LLMRouter
from modules.generator import ContentGenerator
from bot import create_bot
from modules.scheduler import create_scheduler
from modules.openclaw_bridge import create_openclaw_bridge

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class XAgentV3App:
    """
    X-Agent v3 主应用类
    
    负责：
    - 初始化所有组件
    - 管理应用生命周期
    - 处理信号和异常
    """
    
    def __init__(self):
        """初始化应用"""
        self.config = None
        self.db = None
        self.llm_router = None
        self.generator = None
        self.bot = None
        self.scheduler = None
        self.openclaw_bridge = None
        self.running = False
    
    async def initialize(self):
        """
        初始化所有组件
        
        初始化顺序：
        1. 配置加载
        2. 数据库连接
        3. LLM 路由
        4. 内容生成器
        5. OpenClaw 桥接器
        6. Telegram Bot
        7. 调度器
        """
        logger.info("🚀 Initializing X-Agent v3.0...")
        
        # 1. 加载配置
        try:
            self.config = Config()
            logger.info(f"✅ Config loaded (LLM: {self.config.llm.provider})")
        except Exception as e:
            logger.error(f"❌ Config loading failed: {e}")
            raise
        
        # 2. 初始化数据库
        try:
            self.db = init_database(self.config.supabase_url, self.config.supabase_key)
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
        
        # 3. 初始化 LLM 路由
        try:
            self.llm_router = LLMRouter(self.config)
            logger.info(f"✅ LLM Router initialized (Provider: {self.config.llm.provider})")
        except Exception as e:
            logger.error(f"❌ LLM Router initialization failed: {e}")
            raise
        
        # 4. 初始化内容生成器
        try:
            # 获取当前 Niche
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
        
        # 5. 初始化 OpenClaw 桥接器
        try:
            self.openclaw_bridge = await create_openclaw_bridge(
                self.config.openclaw_api_endpoint
            )
            logger.info("✅ OpenClaw Bridge initialized")
        except Exception as e:
            logger.error(f"❌ OpenClaw Bridge initialization failed: {e}")
            # OpenClaw 可选，失败不影响启动
            logger.warning("⚠️  OpenClaw Bridge disabled")
        
        # 6. 初始化 Bot
        try:
            self.bot = create_bot(
                self.config.telegram_bot_token,
                db=self.db,
                llm_router=self.llm_router,
                generator=self.generator,
                config=self.config
            )
            await self.bot.initialize()
            logger.info("✅ Telegram Bot initialized")
        except Exception as e:
            logger.error(f"❌ Telegram Bot initialization failed: {e}")
            raise
        
        # 7. 初始化调度器
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
            # 调度器可选，失败不影响启动
            logger.warning("⚠️  Scheduler disabled")
        
        logger.info("🎉 All components initialized successfully!")
    
    async def start(self):
        """
        启动应用
        
        启动顺序：
        1. 启动调度器
        2. 启动 Bot
        """
        if self.running:
            logger.warning("Application is already running")
            return
        
        logger.info("🚀 Starting X-Agent v3.0...")
        self.running = True
        
        # 1. 启动调度器
        if self.scheduler:
            await self.scheduler.start()
            logger.info("✅ Scheduler started")
        
        # 2. 启动 Bot
        if self.bot:
            # 启动 Bot（非阻塞）
            await self.bot.start_polling()
            logger.info("✅ Bot started (polling)")
        
        logger.info("🎉 X-Agent v3.0 is now running!")
        
        # 保持运行
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """
        停止应用
        
        停止顺序：
        1. 停止调度器
        2. 停止 Bot
        """
        if not self.running:
            return
        
        logger.info("🛑 Stopping X-Agent v3.0...")
        self.running = False
        
        # 1. 停止调度器
        if self.scheduler:
            await self.scheduler.stop()
            logger.info("✅ Scheduler stopped")
        
        # 2. 停止 Bot
        if self.bot:
            await self.bot.stop_polling()
            logger.info("✅ Bot stopped")
        
        logger.info("👋 X-Agent v3.0 stopped")
    
    def handle_signal(self, sig, frame):
        """
        处理系统信号
        
        Args:
            sig: 信号类型
            frame: 当前栈帧
        """
        logger.info(f"\nReceived signal {sig}, shutting down...")
        asyncio.run(self.stop())
        sys.exit(0)


def setup_signal_handlers(app: XAgentV3App):
    """
    设置信号处理器
    
    Args:
        app: XAgentV3App 实例
    """
    signal.signal(signal.SIGINT, app.handle_signal)
    signal.signal(signal.SIGTERM, app.handle_signal)


def main():
    """主函数"""
    # 创建应用实例
    app = XAgentV3App()
    
    # 设置信号处理
    setup_signal_handlers(app)
    
    # 运行应用
    try:
        # 初始化
        asyncio.run(app.initialize())
        
        # 启动
        asyncio.run(app.start())
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        # 清理
        asyncio.run(app.stop())


if __name__ == '__main__':
    main()
