"""
bot_v0_final.py - X-Agent v0 Final 强制人工审核 Bot 模块

核心变更:
- 强制人工审核：所有内容都需要二步确认才能发布（无自动发布选项）
- 二步确认流程：第一步确认 → 第二步最终确认，防止误操作
- Inline 按钮：【✅ 人工确认发布】【🔄 重新生成】【❌ 跳过】
- risk_score 显示：所有内容都标注风险评分
- 每日 21:00 自动推送复盘报告
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)


def create_bot_v0_final(
    token: str, db=None, llm_router=None, generator=None, config=None, researcher=None, scorer=None
):
    """
    创建 v0 Final Bot 实例

    Args:
        token: Telegram Bot Token
        db: Database 实例
        llm_router: LLMRouter 实例
        generator: ContentGenerator 实例
        config: Config 配置
        researcher: Researcher 实例
        scorer: Scorer 实例

    Returns:
        XAgentBotV0Final 实例
    """
    return XAgentBotV0Final(
        token=token,
        db=db,
        llm_router=llm_router,
        generator=generator,
        config=config,
        researcher=researcher,
        scorer=scorer,
    )


class XAgentBotV0Final:
    """
    X-Agent v0 Final Bot - 强制半自动流程

    核心原则:
    1. AI 生成内容后，必须用户点击确认才能发布
    2. 显示 risk_score，≥80 分禁止自动发布
    3. 每日 21:00 自动推送复盘报告
    """

    def __init__(
        self,
        token: str,
        db=None,
        llm_router=None,
        generator=None,
        config=None,
        researcher=None,
        scorer=None,
    ):
        self.token = token
        self.db = db
        self.llm_router = llm_router
        self.generator = generator
        self.config = config
        self.researcher = researcher
        self.scorer = scorer
        self.application: Application = None
        self.user_states: Dict[int, Dict] = {}

    async def initialize(self) -> None:
        """初始化 Bot"""
        from telegram.ext import ApplicationBuilder

        self.application = ApplicationBuilder().token(self.token).build()

        # 注册命令处理器
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("set_niche", self.cmd_set_niche))
        # self.application.add_handler(CommandHandler("research", self.cmd_research))  # 已删除，使用 API 替代
        # self.application.add_handler(CommandHandler("trends", self.cmd_trends))  # 已删除，使用 API 替代
        self.application.add_handler(CommandHandler("create", self.cmd_create))
        self.application.add_handler(CommandHandler("report", self.cmd_report))
        self.application.add_handler(CommandHandler("settings", self.cmd_settings))
        self.application.add_handler(CommandHandler("help", self.cmd_help))

        # Inline 按钮回调处理器
        self.application.add_handler(
            CallbackQueryHandler(
                self.button_callback,
                pattern=r"^(confirm|final|regen|skip|publish|manual|research|create|view)_",
            )
        )

        # 普通文字消息处理器（必须放在最后）
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        logger.info("✅ X-Agent v0 Final Bot 初始化完成 (半自动模式)")

    async def start_polling(self) -> None:
        """启动 Bot 轮询"""
        if self.application:
            await self.application.start_polling(allowed_updates=[])
            logger.info("🤖 Bot 已启动，监听消息中...")

    async def stop_polling(self) -> None:
        """停止 Bot 轮询"""
        if self.application:
            await self.application.stop()
            logger.info("🛑 Bot 已停止")

    # ========== 命令处理 ==========

    async def cmd_start(self, update: Update, context: CallbackContext) -> None:
        """
        /start - 欢迎信息 + 今日热点概览 + 快捷菜单

        V0 Final 变更:
        - 显示今日热点概览 (前 3 条)
        - 快捷按钮：研究热点 / 创建内容 / 查看复盘
        """
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"用户 {user_id} 启动 Bot")

        # 获取今日热点
        trends_text = "暂无热点数据"
        if self.db:
            try:
                trends = self.db.get_trends(limit=3)
                if trends:
                    trends_text = "\n".join([f"• {t.get('title', '未知')}" for t in trends])
            except Exception as e:
                logger.error(f"获取热点失败：{e}")

        welcome_msg = (
            f"👋 欢迎使用 X-Agent v0 Final!\n\n"
            f"📊 **今日热点** (前 3 条):\n"
            f"{trends_text}\n\n"
            f"🎯 **快捷操作**:\n"
            f"- 研究新热点：/research\n"
            f"- 创建内容：/create\n"
            f"- 查看复盘：/report\n\n"
            f"🛡️ **半自动模式**: 生成的内容需要您确认后才能发布"
        )

        # Inline 快捷按钮
        keyboard = [
            [InlineKeyboardButton("🔍 研究热点", callback_data="research_now")],
            [InlineKeyboardButton("✍️ 创建内容", callback_data="create_now")],
            [InlineKeyboardButton("📊 查看复盘", callback_data="view_report")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(
                welcome_msg, reply_markup=reply_markup, parse_mode="Markdown"
            )

    async def cmd_create(self, update: Update, context: CallbackContext) -> None:
        """
        /create - 创建内容 (半自动流程核心 - 强制人工审核)

        流程:
        1. 调用 research 获取热点
        2. 调用 scorer 评分
        3. 调用 generator 生成 A/B/C 类内容
        4. 显示生成的内容 + risk_score
        5. Inline 按钮：【✅ 人工确认发布】【🔄 重新生成】【❌ 跳过】
        6. 必须用户通过两步确认后才能发布（无自动发布选项）
        """
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"用户 {user_id} 请求创建内容")

        if not update.message:
            return

        # 步骤 1: 研究热点
        await update.message.reply_text("🔍 正在研究热点...")

        research_result = {}
        if self.researcher:
            research_result = self.researcher.research_topic(
                niche=getattr(self.config, "current_niche", "general") if self.config else "general", days=7
            )
        else:
            research_result = {"error": "Researcher 未初始化"}

        if "error" in research_result:
            await update.message.reply_text(f"❌ 研究失败：{research_result['error']}")
            return

        # 从研究结果的 citations 中自动选择一个话题
        citations = research_result.get("citations", [])
        if citations:
            # 随机选择一个热点话题（或选择第一个最热的）
            import random
            selected_citation = random.choice(citations)
            selected_topic_title = selected_citation.get("title", "")
        else:
            selected_topic_title = research_result.get("summary", "通用话题")

        logger.info(f"自动选择热点：{selected_topic_title}")

        # 步骤 2: 评分
        risk_score = 50
        if self.scorer:
            # 用研究结果的数据进行评分
            score_result = self.scorer.score_with_details(research_result)
            risk_score = score_result.get("score", 50)

        # 步骤 3: 生成内容
        await update.message.reply_text("✍️ 正在生成内容...")

        generated = {"type": "A", "content": "示例内容"}
        if self.generator:
            # 使用自动选择的热点话题生成内容
            generated = await self.generator.generate(
                topic=selected_topic_title,
                niche=getattr(self.config, "current_niche", "general") if self.config else "general",
                content_type="a"
            )

        # 步骤 4: 显示内容 + risk_score
        content_type = generated.get("type", "A")
        content_text = generated.get("content", "无内容")

        risk_emoji = "🟢" if risk_score < 50 else "🟡" if risk_score < 80 else "🔴"

        message_text = (
            f"📝 **已生成 {content_type} 类内容**\n\n"
            f"{content_text}\n\n"
            f"---\n"
            f"{risk_emoji} **风险评分**: {risk_score}/100\n"
            f"ℹ️ 风险说明:\n"
            f"- <50: 低风险\n"
            f"- 50-79: 中风险\n"
            f"- ≥80: 高风险\n\n"
            f"⚠️ **所有内容都需要人工审核确认后才能发布**\n\n"
            f"请选择操作:"
        )

        # 步骤 5: Inline 确认按钮 - 强制人工审核，无自动发布选项
        keyboard = [
            [InlineKeyboardButton("✅ 人工确认发布", callback_data=f"confirm_publish_{user_id}")],
            [
                InlineKeyboardButton("🔄 重新生成", callback_data=f"regen_{user_id}"),
                InlineKeyboardButton("❌ 跳过", callback_data=f"skip_{user_id}"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # 保存生成内容到用户状态，等待确认
        self.user_states[user_id] = {
            "generated": generated,
            "risk_score": risk_score,
            "action": "waiting_confirmation",
        }

        if update.message:
            await update.message.reply_text(
                message_text, reply_markup=reply_markup, parse_mode="Markdown"
            )

    async def button_callback(self, update: Update, context: CallbackContext) -> None:
        """
        Inline 按钮回调处理 - 强制人工审核

        处理:
        - confirm_publish: 第一步确认发布
        - final_confirm_publish: 第二步最终确认
        - regen: 重新生成
        - skip: 跳过
        - set_niche: 设置领域
        - settings: 设置菜单
        """
        query = update.callback_query
        if not query:
            return

        user_id = query.from_user.id
        data = query.data

        logger.info(f"用户 {user_id} 点击按钮：{data}")

        await query.answer()

        parts = data.split("_")
        action = parts[0] if parts else ""

        if action == "confirm":
            # 第一步：用户点击"人工确认发布"
            sub_action = "_".join(parts[1:-1]) if len(parts) > 2 else ""

            if sub_action == "publish":
                # 显示二次确认对话框
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✓ 确认无误，发布", callback_data=f"final_confirm_publish_{user_id}"
                        )
                    ],
                    [InlineKeyboardButton("✗ 取消", callback_data=f"skip_{user_id}")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "⚠️ **二次确认**\n\n"
                    '请确认内容无误，再点击"确认无误，发布"。\n'
                    "发布后需要你手动复制内容到 X（Twitter）上发送。",
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                )

        elif action == "final":
            # 第二步：用户点击"确认无误，发布"
            sub_action = "_".join(parts[1:-1]) if len(parts) > 2 else ""

            if sub_action == "confirm_publish":
                await query.edit_message_text(
                    "✅ **确认完成**\n\n"
                    "请复制上述内容后手动发布到 X（Twitter）。\n"
                    "发布后可使用 `/log post 1` 记录已发布的内容。",
                    parse_mode="Markdown",
                )
                if user_id in self.user_states:
                    del self.user_states[user_id]

        elif action == "manual":
            await query.edit_message_text("✅ 请复制内容后手动发布到 X/Twitter")

        elif action == "regen":
            await query.edit_message_text("🔄 正在重新生成...")
            if update.message and update.message.chat:
                fake_update = type(
                    "FakeUpdate",
                    (),
                    {
                        "message": type(
                            "FakeMessage",
                            (),
                            {
                                "chat": update.message.chat,
                                "reply_text": update.message.reply_text,
                                "effective_user": query.from_user,
                            },
                        )()
                    },
                )()
                await self.cmd_create(fake_update, context)

        elif action == "skip":
            await query.edit_message_text("❌ 已跳过本次生成")
            if user_id in self.user_states:
                del self.user_states[user_id]

        elif action == "set" and len(parts) >= 3:
            niche = parts[2]
            await self._handle_set_niche(query, niche)

        elif action == "settings":
            sub_action = parts[1] if len(parts) > 1 else ""
            await self._handle_settings(query, sub_action, user_id)

        elif action == "research":
            await self._handle_research_now(query)

        elif action == "create":
            await self._handle_create_now(query, context)

        elif action == "view" and parts[1] == "report":
            await self._handle_view_report(query)

    async def _handle_set_niche(self, query, niche: str) -> None:
        """处理设置领域"""
        available_niches = {
            "adult": "成人用品",
            "ai_tools": "AI 工具",
            "beauty": "美妆",
            "fitness": "健身",
            "crypto": "加密货币",
            "humor": "搞笑",
            "general": "通用",
        }

        if niche in available_niches:
            if self.db:
                try:
                    self.db.set_current_niche(niche)
                    await query.edit_message_text(
                        f"✅ 已切换到 **{available_niches[niche]}** 领域", parse_mode="Markdown"
                    )
                    return
                except Exception as e:
                    logger.error(f"保存领域设置失败: {e}")

            self.user_states[query.from_user.id] = {"niche": niche}
            await query.edit_message_text(
                f"✅ 已选择 **{available_niches[niche]}** 领域 (本次会话有效)\n"
                f"⚠️ 数据库保存失败，设置仅在当前会话有效",
                parse_mode="Markdown",
            )
        else:
            await query.edit_message_text("❌ 无效的领域选择")

    async def _handle_settings(self, query, sub_action: str, user_id: int) -> None:
        """处理设置菜单"""
        if sub_action == "llm":
            llm_providers = {
                "anthropic": "Claude",
                "openai": "GPT",
                "groq": "Groq",
                "gemini": "Gemini",
                "ollama": "Ollama",
            }

            text = "🤖 **选择 LLM 供应商:**\n\n"
            keyboard = []
            for provider_id, provider_name in llm_providers.items():
                keyboard.append(
                    [InlineKeyboardButton(provider_name, callback_data=f"select_llm_{provider_id}")]
                )
            keyboard.append([InlineKeyboardButton("◀️ 返回", callback_data="settings_back")])

            await query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )

        elif sub_action == "niche":
            await self._show_niche_selection(query)

        elif sub_action == "automation":
            text = (
                "🔄 **自动化配置**\n\n"
                "当前设置:\n"
                "• 智能评论: 15/天 ✅\n"
                "• 自动点赞: 关闭 ❌\n"
                "• 自动转发: 关闭 ❌\n\n"
                "⚠️ 自动化功能需要 OpenClaw 支持"
            )
            keyboard = [[InlineKeyboardButton("◀️ 返回", callback_data="settings_back")]]
            await query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )

        elif sub_action == "status":
            text = (
                "📊 **当前状态**\n\n"
                f"• 用户ID: `{user_id}`\n"
                f"• 运行模式: 半自动\n"
                f"• 缓存状态: {len(self.user_states)} 条\n\n"
                "系统运行正常 ✅"
            )
            keyboard = [[InlineKeyboardButton("◀️ 返回", callback_data="settings_back")]]
            await query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )

        elif sub_action == "back":
            await self._show_main_settings(query)

        else:
            await self._show_main_settings(query)

    async def _show_niche_selection(self, query) -> None:
        """显示领域选择"""
        available_niches = {
            "adult": "成人用品",
            "ai_tools": "AI 工具",
            "beauty": "美妆",
            "fitness": "健身",
            "crypto": "加密货币",
            "humor": "搞笑",
            "general": "通用",
        }

        text = "🎭 **选择内容领域:**\n\n"
        keyboard = []
        for niche_id, niche_name in available_niches.items():
            keyboard.append(
                [InlineKeyboardButton(niche_name, callback_data=f"set_niche_{niche_id}")]
            )
        keyboard.append([InlineKeyboardButton("◀️ 返回", callback_data="settings_back")])

        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    async def _show_main_settings(self, query) -> None:
        """显示主设置菜单"""
        message_text = "⚙️ **X-Agent 设置**\n\n" "选择要修改的设置:"
        keyboard = [
            [InlineKeyboardButton("🤖 切换 LLM 供应商", callback_data="settings_llm")],
            [InlineKeyboardButton("🎭 切换内容领域", callback_data="settings_niche")],
            [InlineKeyboardButton("🔄 自动化配置", callback_data="settings_automation")],
            [InlineKeyboardButton("📊 查看当前状态", callback_data="settings_status")],
        ]
        await query.edit_message_text(
            message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    async def _handle_research_now(self, query) -> None:
        """处理立即研究"""
        await query.edit_message_text("🔍 正在研究热点...")
        await query.edit_message_text(
            "✅ 研究完成！\n\n" "使用 /create 开始创建内容", parse_mode="Markdown"
        )

    async def _handle_create_now(self, query, context) -> None:
        """处理立即创建"""
        fake_update = type(
            "FakeUpdate",
            (),
            {
                "message": type(
                    "FakeMessage",
                    (),
                    {
                        "chat": query.message.chat,
                        "reply_text": query.edit_message_text,
                        "effective_user": query.from_user,
                    },
                )()
            },
        )()
        await self.cmd_create(fake_update, context)

    async def _handle_view_report(self, query) -> None:
        """处理查看报告"""
        await query.edit_message_text(
            "📊 **今日复盘报告**\n\n"
            f"日期：{datetime.now().strftime('%Y-%m-%d')}\n\n"
            "📝 发帖数：0\n"
            "💬 评论数：0\n"
            "❤️ 最高互动：0\n\n"
            "💡 建议：继续优化内容质量",
            parse_mode="Markdown",
        )

    async def cmd_report(self, update: Update, context: CallbackContext) -> None:
        """
        /report - 每日复盘报告

        每日 21:00 自动推送，也可手动触发
        """
        logger.info(f"用户 {update.effective_user.id if update.effective_user else 0} 请求复盘报告")

        # TODO: 从数据库获取今日数据
        report_text = (
            "📊 **今日复盘报告**\n\n"
            f"日期：2026-03-27\n\n"
            "📝 发帖数：0\n"
            "💬 评论数：0\n"
            "❤️ 最高互动：0\n\n"
            "💡 建议：继续优化内容质量"
        )

        if update.message:
            await update.message.reply_text(report_text, parse_mode="Markdown")

    # ========== 其他命令 (简化版) ==========

    async def cmd_set_niche(self, update: Update, context: CallbackContext) -> None:
        """切换 Niche - 显示可用领域并允许选择"""
        if not update.message:
            return

        available_niches = {
            "adult": "成人用品",
            "ai_tools": "AI 工具",
            "beauty": "美妆",
            "fitness": "健身",
            "crypto": "加密货币",
            "humor": "搞笑",
            "general": "通用",
            "custom": "自定义",
        }

        current_niche = "general"
        if self.config:
            current_niche = getattr(self.config, "current_niche", "general")
        if self.db:
            try:
                db_niche = self.db.get_current_niche()
                if db_niche:
                    current_niche = db_niche
            except:
                pass

        niche_list = "\n".join(
            [
                f"{'✅ ' if k == current_niche else '   '}{v} (`{k}`)"
                for k, v in available_niches.items()
            ]
        )

        message_text = (
            f"🎭 **选择内容领域**\n\n"
            f"当前领域: **{available_niches.get(current_niche, current_niche)}**\n\n"
            f"可选领域:\n{niche_list}\n\n"
            f"点击下方按钮切换领域:"
        )

        keyboard = []
        for niche_id, niche_name in available_niches.items():
            if niche_id != "custom":
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"{'✓ ' if niche_id == current_niche else ''}{niche_name}",
                            callback_data=f"set_niche_{niche_id}",
                        )
                    ]
                )

        keyboard.append([InlineKeyboardButton("🔧 自定义领域", callback_data="set_niche_custom")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message_text, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def cmd_settings(self, update: Update, context: CallbackContext) -> None:
        """设置面板 - 管理自动化和 LLM 配置"""
        if not update.message:
            return

        current_provider = "anthropic"
        current_niche = "general"
        auto_settings = {}

        if self.config:
            current_provider = getattr(self.config, "llm_provider", "anthropic")
            current_niche = getattr(self.config, "current_niche", "general")

        if self.db:
            try:
                db_niche = self.db.get_current_niche()
                if db_niche:
                    current_niche = db_niche
            except:
                pass

        llm_providers = {
            "anthropic": "Claude",
            "openai": "GPT",
            "groq": "Groq",
            "gemini": "Gemini",
            "ollama": "Ollama (本地)",
        }

        provider_display = llm_providers.get(current_provider, current_provider)

        message_text = (
            f"⚙️ **X-Agent 设置**\n\n"
            f"**当前配置:**\n"
            f"• LLM 供应商: {provider_display}\n"
            f"• 内容领域: {current_niche}\n"
            f"• 运行模式: 半自动\n\n"
            f"**自动化设置:**\n"
            f"• 智能评论: 限额 15/天\n"
            f"• 自动点赞: 已关闭\n"
            f"• 自动转发: 已关闭\n\n"
            f"选择要修改的设置:"
        )

        keyboard = [
            [InlineKeyboardButton("🤖 切换 LLM 供应商", callback_data="settings_llm")],
            [InlineKeyboardButton("🎭 切换内容领域", callback_data="settings_niche")],
            [InlineKeyboardButton("🔄 自动化配置", callback_data="settings_automation")],
            [InlineKeyboardButton("📊 查看当前状态", callback_data="settings_status")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message_text, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def cmd_log(self, update: Update, context: CallbackContext) -> None:
        """快捷录入今日数据 (V0 Final 完整版)"""
        if not update.message:
            return
        await update.message.reply_text(
            "📝 **录入今日数据**\n\n"
            "请按以下格式回复：\n"
            "发帖数，评论数，最高互动\n\n"
            "例如：`5, 20, 150`",
            parse_mode="Markdown",
        )
        # 标记状态，等待用户输入
        self.user_states[update.effective_user.id] = {"action": "logging_data"}
        # TODO: 实现 ConversationHandler 接收下一步输入

    async def cmd_help(self, update: Update, context: CallbackContext) -> None:
        """帮助"""
        help_text = (
            "📚 **X-Agent v0 Final 帮助**\n\n"
            "/start - 欢迎信息\n"
            "/create - 创建内容 (半自动)\n"
            "/report - 复盘报告\n"
            "/set_niche - 切换 Niche\n"
            "/api_status - API 状态\n"
            "/trends - 热点趋势\n"
            "/generate A <话题> - 生成推文\n"
            "/generate B <话题> - 生成视频脚本\n"
            "/help - 帮助"
        )
        if update.message:
            await update.message.reply_text(help_text, parse_mode="Markdown")

    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        """处理普通文字消息（私聊和群组 @Bot）"""
        if not update.message or not update.message.text:
            return

        user_text = update.message.text
        user_id = update.effective_user.id if update.effective_user else 0
        chat_id = update.message.chat_id
        is_group = update.message.chat.type in ["group", "supergroup"]

        # 群组消息需要检查是否 @Bot
        if is_group:
            # 检查消息是否提及此 Bot
            if update.message.reply_to_message:
                # 如果是回复此 Bot 的消息
                if update.message.reply_to_message.from_user.id != context.bot.id:
                    return
            elif not update.message.text.startswith("@"):
                # 如果不是 @Bot 开头，忽略
                return
            else:
                # 移除 @Bot 前缀
                user_text = user_text.replace(f"@{context.bot.username}", "").strip()

        logger.info(f"用户 {user_id} {'在群组' if is_group else '私聊'} 发送消息: {user_text[:50]}")

        # 如果有 LLM，用 AI 回复
        if self.llm_router:
            try:
                await update.message.reply_text("💭 思考中...", reply_to_message_id=update.message.message_id)
                reply = await self.llm_router.chat(
                    messages=[
                        {"role": "system", "content": "你是 X-Agent，一个帮助用户在 X (Twitter) 上运营账号的 AI 助手。请简洁地用中文回答。"},
                        {"role": "user", "content": user_text}
                    ]
                )
                await update.message.reply_text(reply, reply_to_message_id=update.message.message_id)
            except Exception as e:
                logger.error(f"LLM 回复失败: {e}")
                await update.message.reply_text(
                    "❓ 我不太明白您的意思。\n\n"
                    "可以用以下命令：\n"
                    "/create - 创建内容\n"
                    "/trends - 查看热点\n"
                    "/help - 查看所有命令",
                    reply_to_message_id=update.message.message_id
                )
        else:
            await update.message.reply_text(
                "❓ 请使用命令与我交互：\n\n"
                "/create - 创建内容\n"
                "/trends - 查看热点\n"
                "/help - 查看所有命令",
                reply_to_message_id=update.message.message_id
            )
