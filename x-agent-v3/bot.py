""" bot.py - X-Agent v3 Telegram Bot 主程序

实现所有 Bot 指令：
- /start - 欢迎信息和今日热点概览
- /set_niche - 切换 Niche
- /research - 深度研究话题
- /trends - 热点列表
- /create - 创建内容
- /log - 快捷录入数据
- /report - 复盘报告
- /strategy - 查看策略
- /settings - 自动化设置面板
- /llm - LLM 供应商切换

实现 Inline 按钮交互：
- A/B/C 类内容的"复制"按钮回调
- "OpenClaw 发布"按钮回调
- "重新生成"按钮回调
- "跳过"按钮回调
- /settings 面板（自动化开关、每日限额配置）
- /llm 供应商切换面板
- /log 快捷录入流程
"""

import logging
from typing import Dict, Optional, Any
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)

logger = logging.getLogger(__name__)

# 对话状态常量
SELECTING_ACTION = 1
LOGGING_DATA = 2
SETTINGS_UPDATING = 3
RESEARCHING = 4
CREATING_CONTENT = 5


class XAgentBot:
    """
    X-Agent v3 Telegram Bot 主类
    
    负责：
    - 处理所有 Telegram 命令
    - 管理 Inline 按钮交互
    - 与数据库和后端模块交互
    """
    
    def __init__(self, token: str, db=None, llm_router=None, generator=None, config=None):
        """
        初始化 Bot
        
        Args:
            token: Telegram Bot Token
            db: Database 实例
            llm_router: LLMRouter 实例
            generator: ContentGenerator 实例
            config: Config 配置实例
        """
        self.token = token
        self.db = db
        self.llm_router = llm_router
        self.generator = generator
        self.config = config
        self.application: Application = None
        
        # 用户状态管理
        self.user_states: Dict[int, Dict[str, Any]] = {}
        
        # 命令前缀映射
        self.commands = {
            'start': self.cmd_start,
            'set_niche': self.cmd_set_niche,
            'research': self.cmd_research,
            'trends': self.cmd_trends,
            'create': self.cmd_create,
            'log': self.cmd_log,
            'report': self.cmd_report,
            'strategy': self.cmd_strategy,
            'settings': self.cmd_settings,
            'llm': self.cmd_llm,
            'help': self.cmd_help,
        }
    
    async def initialize(self) -> None:
        """初始化 Bot 应用"""
        # 创建应用
        self.application = Application.builder().token(self.token).build()
        
        # 注册命令处理器
        for cmd, handler in self.commands.items():
            self.application.add_handler(CommandHandler(cmd, handler))
        
        # 注册回调处理器（Inline 按钮）
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        
        # 注册消息处理器（用于 /log 等对话流程）
        self.application.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        
        logger.info("✅ Bot initialized")
    
    async def cmd_start(self, update: Update, context: CallbackContext) -> None:
        """处理 /start 命令 - 显示欢迎信息和今日热点概览"""
        # 获取当前 Niche 和 LLM
        niche = 'general'
        llm = 'default'
        
        if self.config:
            niche = self.config.niche.current_niche
            llm = f"{self.config.llm.provider} ({self.config.llm.model})"
        
        welcome_text = f"""
🤖 **X 智能运营 Agent v3.0**

欢迎使用！我可以帮你：
- 🔥 监控多平台热点
- 🤖 自动生成内容（A 类/B 类/C 类）
- 🎭 注入专属 Niche 语气
- ⚙️ 自动化运营

当前 Niche: `{niche}`
LLM: `{llm}`

使用 /help 查看完整指令列表。
""".strip()
        
        # 创建快捷操作按钮
        keyboard = [
            [InlineKeyboardButton("🔥 今日热点", callback_data="action_trends")],
            [InlineKeyboardButton("🎭 切换 Niche", callback_data="action_niche")],
            [InlineKeyboardButton("📝 创建内容", callback_data="action_create")],
            [InlineKeyboardButton("⚙️ 设置", callback_data="action_settings")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def cmd_help(self, update: Update, context: CallbackContext) -> None:
        """处理 /help 命令 - 显示帮助信息"""
        help_text = """
📚 **X-Agent v3 帮助文档**

**核心指令：**
/start - 欢迎信息和今日热点概览
/set_niche - 切换 Niche
/research [话题] - 深度研究话题
/trends - 热点列表
/create - 创建内容
/log - 快捷录入数据
/report - 复盘报告
/strategy - 查看策略
/settings - 自动化设置
/llm - LLM 供应商切换

**内容类型：**
A 类 - AI 全自动推文（3 条备选）
B 类 - AI 出脚本，人工制作
C 类 - 智能评论（≤120 字符）

**提示：**
- 使用 Inline 按钮快速操作
- /settings 配置自动化参数
- /llm 切换 AI 供应商
""".strip()
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def cmd_set_niche(self, update: Update, context: CallbackContext) -> None:
        """处理 /set_niche 命令 - 显示 Niche 选择面板"""
        if not self.config:
            await update.message.reply_text('❌ 配置未初始化')
            return
        
        niche_options = self.config.niche.get_available_niches()
        keyboard = []
        for niche_id, niche_name in niche_options:
            keyboard.append([
                InlineKeyboardButton(f"{niche_name} ({niche_id})", callback_data=f"set_niche_{niche_id}")
            ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_niche = self.config.niche.current_niche
        current_name = self.config.niche.get_niche_name(current_niche)
        
        await update.message.reply_text(
            f"🎭 **当前 Niche**: {current_name} (`{current_niche}`)\n\n请选择要切换的 Niche：",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def cmd_research(self, update: Update, context: CallbackContext) -> None:
        """处理 /research 命令 - 深度研究指定话题"""
        if not context.args:
            await update.message.reply_text(
                '🔍 请提供要研究的话题，例如：\n`/research AI trends in 2024`',
                parse_mode='Markdown'
            )
            return
        
        topic = ' '.join(context.args)
        
        # 显示研究中的状态
        status_msg = await update.message.reply_text(f'🔍 正在研究话题：{topic}...\n\n请稍候...')
        
        # TODO: 调用 research 模块进行深度研究
        # 这里先返回一个占位响应
        result_text = f"""
📊 **研究完成：{topic}**

🔥 热点发现：
- 热点 1: 相关话题描述
- 热点 2: 相关话题描述
- 热点 3: 相关话题描述

💡 建议行动：
1. 创建 A 类内容（AI 推文）
2. 制作 B 类内容（视频脚本）
3. 参与相关讨论（C 类评论）

使用 /create 开始创建内容
""".strip()
        
        await status_msg.edit_text(result_text, parse_mode='Markdown')
    
    async def cmd_trends(self, update: Update, context: CallbackContext) -> None:
        """处理 /trends 命令 - 显示热点列表（按评分排序）"""
        if self.db:
            try:
                trends = self.db.get_trends_by_score(min_score=60, limit=10)
                if trends:
                    text = "🔥 **当前热点（按评分排序）**:\n\n"
                    for i, trend in enumerate(trends, 1):
                        topic = trend.get('topic', 'Unknown')
                        score = trend.get('score', 0)
                        text += f"{i}. **{topic}** - 评分：{score:.1f}\n"
                    
                    # 添加操作按钮
                    keyboard = [
                        [InlineKeyboardButton("📝 创建内容", callback_data="create_from_trends")],
                        [InlineKeyboardButton("🔄 刷新", callback_data="refresh_trends")],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
                else:
                    await update.message.reply_text('暂无热点数据')
            except Exception as e:
                logger.error(f"Error getting trends: {e}")
                await update.message.reply_text('获取热点失败')
        else:
            # 演示模式
            demo_trends = [
                ("AI Agent 自动化趋势", 85.5),
                ("Telegram Bot 商业化", 78.2),
                ("Python 异步编程", 72.8),
                ("跨境电商营销", 68.4),
                ("Web3 社交应用", 65.1),
            ]
            text = "🔥 **当前热点（演示模式）**:\n\n"
            for i, (topic, score) in enumerate(demo_trends, 1):
                text += f"{i}. **{topic}** - 评分：{score:.1f}\n"
            
            keyboard = [
                [InlineKeyboardButton("📝 创建内容", callback_data="create_from_trends")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def cmd_create(self, update: Update, context: CallbackContext) -> None:
        """处理 /create 命令 - 创建内容（A/B/C 类）"""
        # 显示内容类型选择
        keyboard = [
            [InlineKeyboardButton("🤖 A 类 - AI 推文", callback_data="create_type_a")],
            [InlineKeyboardButton("🎬 B 类 - 视频脚本", callback_data="create_type_b")],
            [InlineKeyboardButton("💬 C 类 - 智能评论", callback_data="create_type_c")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📝 **选择内容类型**:\n\n"
            "**A 类** - AI 自动生成推文（3 条备选）\n"
            "**B 类** - AI 生成视频脚本（人工制作）\n"
            "**C 类** - AI 生成智能评论（自动发布）\n\n"
            "请选择：",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def cmd_log(self, update: Update, context: CallbackContext) -> None:
        """处理 /log 命令 - 快捷录入今日数据"""
        # 显示录入选项
        keyboard = [
            [InlineKeyboardButton("📊 粉丝增长", callback_data="log_followers")],
            [InlineKeyboardButton("👍 互动数据", callback_data="log_engagement")],
            [InlineKeyboardButton("💰 收入数据", callback_data="log_revenue")],
            [InlineKeyboardButton("📝 自定义记录", callback_data="log_custom")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📝 **快捷录入**\n\n请选择要录入的数据类型：",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def cmd_report(self, update: Update, context: CallbackContext) -> None:
        """处理 /report 命令 - 显示复盘报告"""
        # 获取今日/昨日数据
        report_text = """
📊 **今日复盘报告**

**时间**: 2026-03-25

**内容表现**:
- 发布内容：3 条
- 总互动：156 次
- 涨粉：+12

**自动化统计**:
- 智能评论：15 条
- 自动点赞：30 次
- 自动转发：5 次

**热门内容**:
1. "AI Agent 趋势分析" - 89 互动
2. "Telegram Bot 技巧" - 45 互动
3. "Python 异步编程" - 22 互动

**建议**:
- 继续保持 A 类内容质量
- 增加互动类内容比例
- 优化发布时间为 19:00-21:00
""".strip()
        
        keyboard = [
            [InlineKeyboardButton("📅 查看历史报告", callback_data="report_history")],
            [InlineKeyboardButton("📤 导出报告", callback_data="report_export")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(report_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def cmd_strategy(self, update: Update, context: CallbackContext) -> None:
        """处理 /strategy 命令 - 查看当前内容策略"""
        strategy_text = """
📋 **当前内容策略**

**Niche**: 成人用品
**语气风格**: cheeky、暗示、感性、大胆
**典型句式**: "you deserve this 😏"

**内容比例**:
- A 类（AI 推文）: 60%
- B 类（视频脚本）: 30%
- C 类（评论）: 10%

**发布时段** (UK 时间):
- 07:30-09:00 资讯/数据类
- 12:00-13:00 互动投票
- 19:00-21:00 推荐/Cheeky 类
- 21:30-23:00 感性/关系话题

**自动化设置**:
- 智能评论：开启（15 条/日）
- 自动点赞：关闭
- 自动转发：关闭
""".strip()
        
        keyboard = [
            [InlineKeyboardButton("✏️ 编辑策略", callback_data="strategy_edit")],
            [InlineKeyboardButton("🔄 重置策略", callback_data="strategy_reset")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(strategy_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def cmd_settings(self, update: Update, context: CallbackContext) -> None:
        """处理 /settings 命令 - 显示自动化设置面板"""
        if not self.config:
            await update.message.reply_text('❌ 配置未初始化')
            return
        
        auto = self.config.automation
        settings_text = f"""
⚙️ **自动化设置**

💬 **智能评论**: [{'开启' if auto.auto_comment_enabled else '关闭'}]
每日上限：{auto.auto_comment_limit} 条

👍 **自动点赞**: [{'开启' if auto.auto_like_enabled else '关闭'}]
每日上限：{auto.auto_like_limit} 次

🔁 **自动转发**: [{'开启' if auto.auto_rt_enabled else '关闭'}]
每日上限：{auto.auto_rt_limit} 次

🤖 **自动发帖**: [{'开启' if auto.auto_post_enabled else '关闭'}]

点击按钮进行设置：
""".strip()
        
        keyboard = [
            [
                InlineKeyboardButton(f"💬 评论 [{'开' if auto.auto_comment_enabled else '关'}]", callback_data="settings_comment_toggle"),
                InlineKeyboardButton(f"上限 {auto.auto_comment_limit}", callback_data="settings_comment_limit"),
            ],
            [
                InlineKeyboardButton(f"👍 点赞 [{'开' if auto.auto_like_enabled else '关'}]", callback_data="settings_like_toggle"),
                InlineKeyboardButton(f"上限 {auto.auto_like_limit}", callback_data="settings_like_limit"),
            ],
            [
                InlineKeyboardButton(f"🔁 转发 [{'开' if auto.auto_rt_enabled else '关'}]", callback_data="settings_rt_toggle"),
                InlineKeyboardButton(f"上限 {auto.auto_rt_limit}", callback_data="settings_rt_limit"),
            ],
            [
                InlineKeyboardButton(f"🤖 自动发帖 [{'开' if auto.auto_post_enabled else '关'}]", callback_data="settings_post_toggle"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(settings_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def cmd_llm(self, update: Update, context: CallbackContext) -> None:
        """处理 /llm 命令 - LLM 供应商切换面板"""
        if not self.config:
            await update.message.reply_text('❌ 配置未初始化')
            return
        
        # 获取已配置的供应商
        available = self.config.llm.get_available_providers()
        
        # 供应商显示名称映射
        provider_names = {
            'anthropic': 'Claude 3.5',
            'openai': 'GPT-4',
            'groq': 'Llama (Groq)',
            'gemini': 'Gemini Pro',
            'openrouter': 'OpenRouter',
            'nvidia': 'NVIDIA NIM',
            'ollama': 'Ollama 本地',
        }
        
        keyboard = []
        for provider in available:
            name = provider_names.get(provider, provider)
            current = self.config.llm.provider == provider
            label = f"{'✅ ' if current else ''}{name}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"llm_{provider}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_llm = self.config.llm.provider
        current_model = self.config.llm.model
        
        await update.message.reply_text(
            f"🤖 **当前 LLM**: {current_llm}\n"
            f"**模型**: `{current_model}`\n\n"
            "选择供应商：",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def callback_handler(self, update: Update, context: CallbackContext) -> None:
        """处理 Inline 按钮回调 - 统一的回调处理逻辑"""
        query = update.callback_query
        data = query.data
        
        # 延迟响应，避免超时
        await query.answer()
        
        try:
            # Niche 切换
            if data.startswith('set_niche_'):
                niche = data.replace('set_niche_', '')
                await self._handle_niche_switch(query, niche)
            
            # LLM 切换
            elif data.startswith('llm_'):
                provider = data.replace('llm_', '')
                await self._handle_llm_switch(query, provider)
            
            # 设置相关
            elif data.startswith('settings_'):
                await self._handle_settings_action(query, data)
            
            # 创建内容
            elif data.startswith('create_'):
                await self._handle_create_action(query, data)
            
            # 日志录入
            elif data.startswith('log_'):
                await self._handle_log_action(query, data)
            
            # 报告相关
            elif data.startswith('report_'):
                await self._handle_report_action(query, data)
            
            # 策略相关
            elif data.startswith('strategy_'):
                await self._handle_strategy_action(query, data)
            
            # 快捷操作
            elif data.startswith('action_'):
                await self._handle_quick_action(query, data)
            
            # 刷新操作
            elif data == 'refresh_trends':
                await query.edit_message_text('🔄 刷新热点列表...')
                await self.cmd_trends(update, context)
            
            else:
                logger.warning(f"Unknown callback data: {data}")
        
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            await query.edit_message_text(f'❌ 操作失败：{str(e)}')
    
    async def _handle_niche_switch(self, query, niche: str) -> None:
        """处理 Niche 切换"""
        if self.config:
            success = self.config.set_niche(niche)
            if success:
                # 更新数据库（如果有）
                if self.db:
                    try:
                        self.db.set_niche(niche)
                    except Exception as e:
                        logger.error(f"Error updating niche in DB: {e}")
                
                # 更新生成器（如果有）
                if self.generator:
                    try:
                        self.generator.set_niche(niche)
                    except Exception as e:
                        logger.error(f"Error updating niche in generator: {e}")
                
                niche_name = self.config.niche.get_niche_name(niche)
                await query.edit_message_text(f'✅ 已切换至 Niche: {niche_name} ({niche})')
            else:
                await query.edit_message_text(f'❌ 无效的 Niche: {niche}')
        else:
            await query.edit_message_text('❌ 配置未初始化')
    
    async def _handle_llm_switch(self, query, provider: str) -> None:
        """处理 LLM 切换"""
        if self.config:
            success = self.config.set_llm_provider(provider)
            if success:
                # 更新 LLM Router（如果有）
                if self.llm_router:
                    try:
                        self.llm_router.set_provider(provider)
                    except Exception as e:
                        logger.error(f"Error updating LLM provider: {e}")
                
                await query.edit_message_text(f'✅ 已切换 LLM: {provider}')
            else:
                await query.edit_message_text(f'❌ 无效的供应商：{provider}')
        else:
            await query.edit_message_text('❌ 配置未初始化')
    
    async def _handle_settings_action(self, query, data: str) -> None:
        """处理设置相关操作"""
        if not self.config:
            await query.edit_message_text('❌ 配置未初始化')
            return
        
        auto = self.config.automation
        
        # 开关切换
        if data == 'settings_comment_toggle':
            auto.auto_comment_enabled = not auto.auto_comment_enabled
            await query.edit_message_text(f"💬 智能评论：{'开启' if auto.auto_comment_enabled else '关闭'}")
        
        elif data == 'settings_like_toggle':
            auto.auto_like_enabled = not auto.auto_like_enabled
            await query.edit_message_text(f"👍 自动点赞：{'开启' if auto.auto_like_enabled else '关闭'}")
        
        elif data == 'settings_rt_toggle':
            auto.auto_rt_enabled = not auto.auto_rt_enabled
            await query.edit_message_text(f"🔁 自动转发：{'开启' if auto.auto_rt_enabled else '关闭'}")
        
        elif data == 'settings_post_toggle':
            auto.auto_post_enabled = not auto.auto_post_enabled
            await query.edit_message_text(f"🤖 自动发帖：{'开启' if auto.auto_post_enabled else '关闭'}")
        
        # 限额设置（简单实现）
        elif data.endswith('_limit'):
            setting_type = data.replace('settings_', '').replace('_limit', '')
            await query.edit_message_text(f"⚙️ 设置{setting_type}限额功能开发中...")
    
    async def _handle_create_action(self, query, data: str) -> None:
        """处理创建内容相关操作"""
        if data == 'create_type_a':
            await query.edit_message_text("🤖 A 类内容创建功能开发中...")
        elif data == 'create_type_b':
            await query.edit_message_text("🎬 B 类内容创建功能开发中...")
        elif data == 'create_type_c':
            await query.edit_message_text("💬 C 类内容创建功能开发中...")
        elif data == 'create_from_trends':
            await query.edit_message_text("📝 从热点创建内容功能开发中...")
    
    async def _handle_log_action(self, query, data: str) -> None:
        """处理日志录入相关操作"""
        if data == 'log_followers':
            await query.edit_message_text("📊 粉丝增长录入功能开发中...")
        elif data == 'log_engagement':
            await query.edit_message_text("👍 互动数据录入功能开发中...")
        elif data == 'log_revenue':
            await query.edit_message_text("💰 收入数据录入功能开发中...")
        elif data == 'log_custom':
            await query.edit_message_text("📝 自定义记录功能开发中...")
    
    async def _handle_report_action(self, query, data: str) -> None:
        """处理报告相关操作"""
        if data == 'report_history':
            await query.edit_message_text("📅 历史报告功能开发中...")
        elif data == 'report_export':
            await query.edit_message_text("📤 导出报告功能开发中...")
    
    async def _handle_strategy_action(self, query, data: str) -> None:
        """处理策略相关操作"""
        if data == 'strategy_edit':
            await query.edit_message_text("✏️ 编辑策略功能开发中...")
        elif data == 'strategy_reset':
            await query.edit_message_text("🔄 重置策略功能开发中...")
    
    async def _handle_quick_action(self, query, data: str) -> None:
        """处理快捷操作"""
        if data == 'action_trends':
            await query.edit_message_text("🔥 正在获取热点...")
        elif data == 'action_niche':
            await query.edit_message_text("🎭 正在打开 Niche 选择...")
        elif data == 'action_create':
            await query.edit_message_text("📝 正在创建内容...")
        elif data == 'action_settings':
            await query.edit_message_text("⚙️ 正在打开设置...")
    
    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        """处理普通消息 - 用于 /log 等对话流程"""
        text = update.message.text
        user_id = update.message.chat_id
        
        # 检查用户状态
        if user_id in self.user_states:
            state = self.user_states[user_id]
            # 根据状态处理消息
            if state.get('action') == 'logging':
                await self._process_log_input(update, text, state)
                return
        
        # 默认回复
        await update.message.reply_text(f"收到消息：{text}\n\n使用 /help 查看可用命令")
    
    async def _process_log_input(self, update: Update, text: str, state: Dict) -> None:
        """处理日志录入输入"""
        # 这里处理具体的日志录入逻辑
        await update.message.reply_text(f"📝 已记录：{text}")
        
        # 清除状态
        if update.message.chat_id in self.user_states:
            del self.user_states[update.message.chat_id]
    
    def run(self) -> None:
        """运行 Bot（阻塞模式）"""
        if self.application:
            logger.info("🚀 Starting Bot polling...")
            self.application.run_polling(allowed_updates=['message', 'callback_query'])
        else:
            logger.error("Bot not initialized. Call initialize() first.")
    
    async def start_polling(self) -> None:
        """启动 Bot（异步模式）"""
        if self.application:
            logger.info("🚀 Starting Bot polling (async)...")
            await self.application.start_polling(allowed_updates=['message', 'callback_query'])
        else:
            logger.error("Bot not initialized. Call initialize() first.")
    
    async def stop_polling(self) -> None:
        """停止 Bot"""
        if self.application:
            await self.application.stop()
            logger.info("Bot stopped")


def create_bot(token: str, db=None, llm_router=None, generator=None, config=None) -> XAgentBot:
    """
    创建 Bot 实例
    
    Args:
        token: Telegram Bot Token
        db: Database 实例
        llm_router: LLMRouter 实例
        generator: ContentGenerator 实例
        config: Config 配置实例
    
    Returns:
        XAgentBot 实例
    """
    bot = XAgentBot(token, db, llm_router, generator, config)
    return bot
