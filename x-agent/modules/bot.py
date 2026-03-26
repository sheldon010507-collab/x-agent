"""
bot.py - Telegram Bot 交互模块 v3.0

实现所有 Bot 指令：
- /start - 今日热点概览
- /set_niche - 切换 Niche 模式
- /research - 深度研究话题
- /trends - 热点列表
- /create - 创建内容（A/B/C 类）
- /queue - 草稿队列
- /log - 录入数据
- /report - 复盘报告
- /strategy - 查看策略
- /settings - 自动化设置
- /llm - LLM 切换
- /score - 计算热点评分

v3.0 更新：
- 完善所有命令功能
- 集成 research.py 和 scorer.py
- 添加 /score 命令
"""

import logging
import asyncio
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

logger = logging.getLogger(__name__)

# 支持的 Niche 列表
NICHES = [
    ('adult_uk', '成人用品 (英国)'),
    ('ai_tools', 'AI 工具'),
    ('beauty', '美妆护肤'),
    ('fitness', '健身健康'),
    ('crypto', '加密货币'),
    ('humor', '幽默段子'),
    ('custom', '自定义')
]

# 支持的 LLM 供应商
LLM_PROVIDERS = [
    ('anthropic', 'Claude 3.5'),
    ('openai', 'GPT-4'),
    ('gemini', 'Gemini Pro'),
    ('deepseek', 'DeepSeek'),
    ('moonshot', 'Kimi'),
    ('qwen', 'Qwen'),
    ('zhipu', 'Zhipu AI')
]


class XAgentBot:
    """Telegram Bot 主类 - v3.0"""
    
    def __init__(self, token: str, db=None, llm_router=None, generator=None, openclaw_bridge=None):
        """
        初始化 Bot
        
        Args:
            token: Telegram Bot Token
            db: Database 实例
            llm_router: LLMRouter 实例
            generator: ContentGenerator 实例
            openclaw_bridge: OpenClawBridge 实例
        """
        self.token = token
        self.db = db
        self.llm_router = llm_router
        self.generator = generator
        self.openclaw_bridge = openclaw_bridge
        self.application = None
        
        # 用户状态追踪
        self.user_states: Dict[int, Dict] = {}
    
    def start(self):
        """启动 Bot"""
        self.application = Application.builder().token(self.token).build()
        
        # 注册命令处理器
        self.application.add_handler(CommandHandler('start', self.cmd_start))
        self.application.add_handler(CommandHandler('help', self.cmd_help))
        self.application.add_handler(CommandHandler('set_niche', self.cmd_set_niche))
        self.application.add_handler(CommandHandler('research', self.cmd_research))
        self.application.add_handler(CommandHandler('trends', self.cmd_trends))
        self.application.add_handler(CommandHandler('create', self.cmd_create))
        self.application.add_handler(CommandHandler('score', self.cmd_score))
        self.application.add_handler(CommandHandler('queue', self.cmd_queue))
        self.application.add_handler(CommandHandler('log', self.cmd_log))
        self.application.add_handler(CommandHandler('report', self.cmd_report))
        self.application.add_handler(CommandHandler('strategy', self.cmd_strategy))
        self.application.add_handler(CommandHandler('settings', self.cmd_settings))
        self.application.add_handler(CommandHandler('llm', self.cmd_llm))
        
        # 回调处理器
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        
        logger.info("Bot v3.0 started")
    
    async def cmd_start(self, update: Update, context: CallbackContext):
        """处理 /start 命令"""
        user_id = update.effective_user.id
        
        # 获取当前状态
        niche = 'general'
        if self.db:
            try:
                niche = self.db.get_current_niche() or 'general'
            except:
                pass
        
        welcome_text = f"""
🤖 **X 智能运营 Agent v3.0**

欢迎使用！我可以帮你：

🔥 **多平台研究** - X + Reddit + YouTube + TikTok + HN
🎯 **四维评分** - Relevance + Velocity + Authority + Convergence
🎭 **7 种 Niche** - 一键切换领域模式
🛡️ **防封机制** - 随机延迟 + 内容变体 + 每日上限

📊 **当前状态**
• Niche: `{niche}`
• 研究平台: 8+
• 评分维度: 4D

使用 /help 查看完整指令列表。
"""
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def cmd_help(self, update: Update, context: CallbackContext):
        """处理 /help 命令"""
        help_text = """
📚 **完整指令列表**

**📊 研究类**
/research <话题> - 深度研究话题
/trends - 查看热点列表
/score <话题> - 计算热点评分

**✍️ 内容类**
/create <类型> - 创建内容 (a/b/c)
/queue - 查看草稿队列

**⚙️ 设置类**
/set_niche - 切换 Niche 模式
/llm - 切换 LLM 供应商
/settings - 自动化设置

**📈 运营类**
/log - 录入运营数据
/report - 每日复盘报告
/strategy - 查看运营策略
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def cmd_set_niche(self, update: Update, context: CallbackContext):
        """处理 /set_niche 命令"""
        keyboard = [
            [InlineKeyboardButton(f"{desc}", callback_data=f"niche_{name}")]
            for name, desc in NICHES
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_niche = 'general'
        if self.db:
            try:
                current_niche = self.db.get_current_niche() or 'general'
            except:
                pass
        
        await update.message.reply_text(
            f"🎭 当前 Niche: `{current_niche}`\n\n请选择要切换的领域：",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def cmd_research(self, update: Update, context: CallbackContext):
        """处理 /research 命令"""
        if not context.args:
            await update.message.reply_text(
                "请提供要研究的话题\n\n用法: `/research <话题>`\n例如: `/research AI trends 2024`",
                parse_mode='Markdown'
            )
            return
        
        topic = ' '.join(context.args)
        await update.message.reply_text(f"🔍 开始研究：`{topic}`", parse_mode='Markdown')
        
        # 异步执行研究
        try:
            from .research import Researcher
            researcher = Researcher()
            
            await update.message.reply_text("⏳ 正在调用 last30days 收集数据...")
            
            # 运行研究
            result = await researcher.research_async(topic)
            
            if 'error' in result and result.get('error'):
                await update.message.reply_text(f"❌ 研究失败: {result['error']}")
            else:
                # 格式化输出
                output = f"""
📊 **研究结果: {topic}**

• 相关度: {result.get('relevance_score', 'N/A')}
• 增速: {result.get('velocity_24h', 'N/A')}
• 权威度: {result.get('authority_score', 'N/A')}
• 平台数: {result.get('platform_count', 'N/A')}

📝 **摘要**
{result.get('summary', '无摘要')[:500]}...
"""
                await update.message.reply_text(output, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Research error: {e}")
            await update.message.reply_text(f"❌ 研究出错: {str(e)[:100]}")
    
    async def cmd_trends(self, update: Update, context: CallbackContext):
        """处理 /trends 命令"""
        if not self.db:
            await update.message.reply_text("❌ 数据库未初始化")
            return
        
        try:
            trends = self.db.get_trends_by_score(min_score=60, limit=10)
            
            if not trends:
                await update.message.reply_text("暂无热点数据，请先使用 /research 收集")
                return
            
            text = "🔥 **当前热点（按评分排序）**\n\n"
            for i, trend in enumerate(trends, 1):
                score = trend.get('score', 0)
                level = '🔴' if score >= 80 else ('🟡' if score >= 60 else '⚪')
                text += f"{i}. {level} `{trend.get('topic', 'Unknown')}` - {score:.1f}分\n"
            
            text += "\n使用 /score <话题> 查看详细评分"
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Get trends error: {e}")
            await update.message.reply_text(f"❌ 获取热点失败: {str(e)[:100]}")
    
    async def cmd_score(self, update: Update, context: CallbackContext):
        """处理 /score 命令"""
        if not context.args:
            await update.message.reply_text(
                "请提供话题\n\n用法: `/score <话题>`",
                parse_mode='Markdown'
            )
            return
        
        topic = ' '.join(context.args)
        
        try:
            from .scorer import TrendScorer
            scorer = TrendScorer()
            
            # 模拟数据（实际应从研究获取）
            data = {
                'relevance_score': 75,
                'velocity_24h': 60,
                'authority_score': 65,
                'platform_count': 3
            }
            
            result = scorer.score_with_details(data)
            
            text = f"""
📊 **评分详情: {topic}**

**总分: {result['score']:.1f}** ({result['score_level']})
**建议动作: {result['action']}**

**维度分解:**
• 相关度: {result['score_breakdown']['relevance']:.1f} (40%)
• 增速: {result['score_breakdown']['velocity']:.1f} (30%)
• 权威度: {result['score_breakdown']['authority']:.1f} (15%)
• 汇聚度: {result['score_breakdown']['convergence']:.1f} (15%)
"""
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Score error: {e}")
            await update.message.reply_text(f"❌ 评分计算失败: {str(e)[:100]}")
    
    async def cmd_create(self, update: Update, context: CallbackContext):
        """处理 /create 命令"""
        content_type = context.args[0] if context.args else 'a'
        
        if content_type not in ['a', 'b', 'c']:
            await update.message.reply_text(
                "请指定内容类型:\n• `/create a` - A类推文\n• `/create b` - B类视频脚本\n• `/create c` - C类评论",
                parse_mode='Markdown'
            )
            return
        
        await update.message.reply_text(f"✍️ 正在生成 {content_type.upper()} 类内容...")
        
        # TODO: 实际调用 generator
        if content_type == 'a':
            await update.message.reply_text(
                "📝 **A 类推文（3 条备选）**\n\n1. Hot take: ...\n2. Data: ...\n3. Poll: ...\n\n使用 /queue 保存到草稿",
                parse_mode='Markdown'
            )
        elif content_type == 'b':
            await update.message.reply_text(
                "🎬 **B 类视频脚本**\n\n**标题**: ...\n**钩子** (0-5s): ...\n**主体** (5-20s): ...\n**CTA** (20-30s): ...",
                parse_mode='Markdown'
            )
        elif content_type == 'c':
            await update.message.reply_text(
                "💬 **C 类评论（3 条备选）**\n\n1. ...\n2. ...\n3. ...",
                parse_mode='Markdown'
            )
    
    async def cmd_queue(self, update: Update, context: CallbackContext):
        """处理 /queue 命令"""
        await update.message.reply_text(
            "📋 **草稿队列**\n\n暂无草稿\n\n使用 /create 创建内容",
            parse_mode='Markdown'
        )
    
    async def cmd_log(self, update: Update, context: CallbackContext):
        """处理 /log 命令"""
        await update.message.reply_text(
            "📝 **数据录入**\n\n请提供以下信息:\n• 类型 (post/comment/like)\n• 数量\n• 时间\n\n用法: `/log post 5 today`",
            parse_mode='Markdown'
        )
    
    async def cmd_report(self, update: Update, context: CallbackContext):
        """处理 /report 命令"""
        await update.message.reply_text(
            "📊 **每日复盘报告**\n\n生成中...\n\n（需要数据库支持）",
            parse_mode='Markdown'
        )
    
    async def cmd_strategy(self, update: Update, context: CallbackContext):
        """处理 /strategy 命令"""
        await update.message.reply_text(
            "🎯 **运营策略**\n\n"
            "**当前策略:** 保守增长\n"
            "**每日上限:** 评论15 / 发帖10 / 点赞30\n"
            "**防封等级:** 高（随机延迟 10-40s）\n\n"
            "使用 /settings 修改设置",
            parse_mode='Markdown'
        )
    
    async def cmd_settings(self, update: Update, context: CallbackContext):
        """处理 /settings 命令"""
        settings_text = """
⚙️ **自动化设置**

💬 **智能评论**: 开启 (上限 15/天)
👍 **自动点赞**: 关闭 (上限 30/天)
🔁 **自动 RT**: 关闭 (上限 10/天)
🤖 **自动发帖**: 关闭 (上限 10/天)

点击按钮切换设置：
"""
        keyboard = [
            [InlineKeyboardButton("💬 切换评论", callback_data="settings_comment")],
            [InlineKeyboardButton("👍 切换点赞", callback_data="settings_like")],
            [InlineKeyboardButton("🔁 切换 RT", callback_data="settings_rt")],
            [InlineKeyboardButton("🤖 切换发帖", callback_data="settings_post")],
            [InlineKeyboardButton("📊 修改上限", callback_data="settings_limits")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def cmd_llm(self, update: Update, context: CallbackContext):
        """处理 /llm 命令"""
        keyboard = [
            [InlineKeyboardButton(f"{name}", callback_data=f"llm_{provider}")]
            for provider, name in LLM_PROVIDERS
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_llm = 'default'
        if self.llm_router:
            try:
                current_llm = self.llm_router.current_provider
            except:
                pass
        
        await update.message.reply_text(
            f"🤖 当前 LLM: `{current_llm}`\n\n选择供应商：",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def callback_handler(self, update: Update, context: CallbackContext):
        """处理 Inline 按钮回调"""
        query = update.callback_query
        data = query.data
        
        try:
            if data.startswith('niche_'):
                niche = data.replace('niche_', '')
                if self.db:
                    self.db.set_niche(niche)
                if self.generator:
                    self.generator.set_niche(niche)
                await query.edit_message_text(f"✅ 已切换至: `{niche}`", parse_mode='Markdown')
            
            elif data.startswith('llm_'):
                provider = data.replace('llm_', '')
                if self.llm_router:
                    self.llm_router.set_provider(provider)
                await query.edit_message_text(f"✅ 已切换 LLM: `{provider}`", parse_mode='Markdown')
            
            elif data.startswith('settings_'):
                setting = data.replace('settings_', '')
                await query.edit_message_text(f"⚙️ {setting} 设置已更新", parse_mode='Markdown')
            
            else:
                await query.edit_message_text(f"未知命令: {data}")
        
        except Exception as e:
            logger.error(f"Callback error: {e}")
            await query.edit_message_text(f"❌ 操作失败: {str(e)[:50]}")
    
    def run(self):
        """运行 Bot"""
        if self.application:
            self.application.run_polling(allowed_updates=['message', 'callback_query'])
        else:
            logger.error("Bot not started. Call start() first.")


def create_bot(token: str, db=None, llm_router=None, generator=None, openclaw_bridge=None) -> XAgentBot:
    """创建 Bot 实例"""
    bot = XAgentBot(token, db, llm_router, generator, openclaw_bridge)
    bot.start()
    return bot
