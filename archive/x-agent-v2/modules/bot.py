"""
bot.py - Telegram Bot 交互模块

实现所有 Bot 指令：
- /start - 今日热点概览
- /set_niche - 切换 Niche
- /research - 深度研究
- /trends - 热点列表
- /create - 创建内容
- /queue - 草稿队列
- /log - 录入数据
- /report - 复盘报告
- /strategy - 查看策略
- /settings - 自动化设置
- /llm - LLM 切换
"""

import logging
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

logger = logging.getLogger(__name__)


class XAgentBot:
    """Telegram Bot 主类"""
    
    def __init__(self, token: str, db=None, llm_router=None, generator=None):
        """
        初始化 Bot
        
        Args:
            token: Telegram Bot Token
            db: Database 实例
            llm_router: LLMRouter 实例
            generator: ContentGenerator 实例
        """
        self.token = token
        self.db = db
        self.llm_router = llm_router
        self.generator = generator
        self.application = None
        
        # 当前用户状态
        self.user_states: Dict[int, str] = {}
    
    def start(self):
        """启动 Bot"""
        # 创建应用
        self.application = Application.builder().token(self.token).build()
        
        # 注册命令处理器
        self.application.add_handler(CommandHandler('start', self.cmd_start))
        self.application.add_handler(CommandHandler('set_niche', self.cmd_set_niche))
        self.application.add_handler(CommandHandler('research', self.cmd_research))
        self.application.add_handler(CommandHandler('trends', self.cmd_trends))
        self.application.add_handler(CommandHandler('create', self.cmd_create))
        self.application.add_handler(CommandHandler('queue', self.cmd_queue))
        self.application.add_handler(CommandHandler('log', self.cmd_log))
        self.application.add_handler(CommandHandler('report', self.cmd_report))
        self.application.add_handler(CommandHandler('strategy', self.cmd_strategy))
        self.application.add_handler(CommandHandler('settings', self.cmd_settings))
        self.application.add_handler(CommandHandler('llm', self.cmd_llm))
        
        # 注册回调处理器（Inline 按钮）
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        
        logger.info("Bot started")
    
    async def cmd_start(self, update: Update, context: CallbackContext):
        """处理 /start 命令"""
        welcome_text = """
🤖 X 智能运营 Agent v2.0

欢迎使用！我可以帮你：
- 🔥 监控多平台热点
- 🤖 自动生成内容（A 类/B 类/C 类）
- 🎭 注入专属 Niche 语气
- ⚙️ 自动化运营

当前 Niche: {niche}
LLM: {llm}

使用 /help 查看完整指令列表。
        """
        
        # 获取当前 Niche 和 LLM
        niche = 'general'
        llm = 'default'
        
        if self.db:
            try:
                niche = self.db.get_current_niche() or 'general'
            except:
                pass
        
        await update.message.reply_text(
            welcome_text.format(niche=niche, llm=llm),
            parse_mode='Markdown'
        )
    
    async def cmd_set_niche(self, update: Update, context: CallbackContext):
        """处理 /set_niche 命令"""
        niche_options = [
            ('adult', '成人用品'),
            ('ai_tools', 'AI 工具'),
            ('beauty', '美妆'),
            ('fitness', '健身'),
            ('crypto', '加密货币'),
            ('humor', '搞笑'),
            ('custom', '自定义')
        ]
        
        keyboard = [
            [InlineKeyboardButton(f"{name} - {desc}", callback_data=f"set_niche_{name}")]
            for name, desc in niche_options
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            '请选择要切换的 Niche：',
            reply_markup=reply_markup
        )
    
    async def cmd_research(self, update: Update, context: CallbackContext):
        """处理 /research 命令"""
        if context.args:
            topic = ' '.join(context.args)
            await update.message.reply_text(f'🔍 开始研究话题：{topic}')
            # 实际实现需要调用 research.py
        else:
            await update.message.reply_text('请提供要研究的话题，例如：/research AI trends')
    
    async def cmd_trends(self, update: Update, context: CallbackContext):
        """处理 /trends 命令"""
        if self.db:
            try:
                trends = self.db.get_trends_by_score(min_score=60, limit=10)
                if trends:
                    text = "🔥 当前热点（按评分排序）:\n\n"
                    for i, trend in enumerate(trends, 1):
                        text += f"{i}. {trend.get('topic', 'Unknown')} - 评分：{trend.get('score', 0):.1f}\n"
                    await update.message.reply_text(text)
                else:
                    await update.message.reply_text('暂无热点数据')
            except Exception as e:
                logger.error(f"Error getting trends: {e}")
                await update.message.reply_text('获取热点失败')
        else:
            await update.message.reply_text('数据库未初始化')
    
    async def cmd_create(self, update: Update, context: CallbackContext):
        """处理 /create 命令"""
        await update.message.reply_text('内容创建功能开发中...')
    
    async def cmd_queue(self, update: Update, context: CallbackContext):
        """处理 /queue 命令"""
        await update.message.reply_text('草稿队列功能开发中...')
    
    async def cmd_log(self, update: Update, context: CallbackContext):
        """处理 /log 命令"""
        await update.message.reply_text('数据录入功能开发中...')
    
    async def cmd_report(self, update: Update, context: CallbackContext):
        """处理 /report 命令"""
        await update.message.reply_text('复盘报告功能开发中...')
    
    async def cmd_strategy(self, update: Update, context: CallbackContext):
        """处理 /strategy 命令"""
        await update.message.reply_text('策略查看功能开发中...')
    
    async def cmd_settings(self, update: Update, context: CallbackContext):
        """处理 /settings 命令"""
        settings_text = """
⚙️ 自动化设置

💬 智能评论：[开启] 每日上限：15 条
👍 自动点赞：[关闭] 每日上限：30 次
🔁 自动 RT: [关闭] 每日上限：10 次
🤖 自动发帖：[关闭]

点击按钮进行设置：
        """
        
        keyboard = [
            [InlineKeyboardButton("💬 修改评论上限", callback_data="settings_comment_limit")],
            [InlineKeyboardButton("👍 切换点赞开关", callback_data="settings_like_toggle")],
            [InlineKeyboardButton("🔁 切换 RT 开关", callback_data="settings_rt_toggle")],
            [InlineKeyboardButton("🤖 自动发帖设置", callback_data="settings_post_toggle")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(settings_text, reply_markup=reply_markup)
    
    async def cmd_llm(self, update: Update, context: CallbackContext):
        """处理 /llm 命令"""
        llm_options = [
            ('anthropic', 'Claude 3.5'),
            ('openai', 'GPT-4'),
            ('groq', 'Llama (Groq)'),
            ('gemini', 'Gemini Pro'),
            ('openrouter', 'OpenRouter'),
            ('nvidia', 'NVIDIA NIM'),
            ('ollama', 'Ollama 本地')
        ]
        
        keyboard = [
            [InlineKeyboardButton(f"{name}", callback_data=f"llm_{provider}")]
            for provider, name in llm_options
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_llm = 'default'
        await update.message.reply_text(
            f'🤖 当前 LLM: {current_llm}\n\n选择供应商：',
            reply_markup=reply_markup
        )
    
    async def callback_handler(self, update: Update, context: CallbackContext):
        """处理 Inline 按钮回调"""
        query = update.callback_query
        data = query.data
        
        if data.startswith('set_niche_'):
            niche = data.replace('set_niche_', '')
            # 更新数据库
            if self.db:
                try:
                    self.db.set_niche(niche)
                except:
                    pass
            # 更新生成器
            if self.generator:
                self.generator.set_niche(niche)
            
            await query.edit_message_text(f'✅ 已切换至 Niche: {niche}')
        
        elif data.startswith('llm_'):
            provider = data.replace('llm_', '')
            # 切换 LLM
            if self.llm_router:
                try:
                    self.llm_router.set_provider(provider)
                except:
                    pass
            
            await query.edit_message_text(f'✅ 已切换 LLM: {provider}')
        
        elif data.startswith('settings_'):
            await query.edit_message_text('设置功能开发中...')
    
    def run(self):
        """运行 Bot"""
        if self.application:
            self.application.run_polling(allowed_updates=['message', 'callback_query'])
        else:
            logger.error("Bot not started. Call start() first.")


def create_bot(token: str, db=None, llm_router=None, generator=None) -> XAgentBot:
    """创建 Bot 实例"""
    bot = XAgentBot(token, db, llm_router, generator)
    bot.start()
    return bot
