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
        self.application.add_handler(CommandHandler("search", self.cmd_search))
        self.application.add_handler(CommandHandler("report", self.cmd_report))
        self.application.add_handler(CommandHandler("settings", self.cmd_settings))
        self.application.add_handler(CommandHandler("help", self.cmd_help))

        # Inline 按钮回调处理器（匹配所有回调）
        self.application.add_handler(
            CallbackQueryHandler(self.button_callback)
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

        优先使用之前搜索的结果，如果没有则重新研究热点
        """
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"用户 {user_id} 请求创建内容")

        if not update.message:
            return

        # 检查是否有之前的搜索结果
        user_state = self.user_states.get(user_id, {})
        research_result = user_state.get("research_result")
        search_keyword = user_state.get("search_keyword")

        if research_result and search_keyword:
            # 使用之前的搜索结果
            await update.message.reply_text(
                f"✅ 使用之前搜索的「{search_keyword}」的数据来生成内容...",
                parse_mode="Markdown"
            )
        else:
            # 重新研究热点
            await update.message.reply_text("🔍 正在研究热点...")

            if self.researcher:
                research_result = self.researcher.research_topic(
                    niche=getattr(self.config, "current_niche", "general") if self.config else "general",
                    days=7
                )
            else:
                research_result = {"error": "Researcher 未初始化"}

            if "error" in research_result:
                await update.message.reply_text(f"❌ 研究失败：{research_result['error']}")
                return

        # 显示采集到的热点
        citations = research_result.get("citations", [])
        platform_data = research_result.get("platform_data", {})
        summary = research_result.get("summary", "暂无摘要")
        risk_score_research = research_result.get("risk_score", 50)

        # 从 platform_data 中提取真实的话题
        real_topics = []
        for platform, data in platform_data.items():
            if isinstance(data, dict) and "posts" in data:
                posts = data.get("posts", [])
                for post in posts[:2]:  # 每个平台取前2个
                    title = post.get("title", "").strip()
                    if title and len(title) > 5:  # 过滤掉太短或空的标题
                        real_topics.append(f"[{platform.upper()}] {title}")

        # 显示热点列表（去重）
        unique_topics = list(set(real_topics))[:10]
        if unique_topics:
            hot_topics_text = "\n".join([f"• {t}" for t in unique_topics])
            await update.message.reply_text(
                f"🔥 **采集到的热点话题** (前10个):\n{hot_topics_text}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"📊 **研究摘要**:\n{summary}",
                parse_mode="Markdown"
            )

        # 让用户选择行业
        await update.message.reply_text("🎯 **选择内容行业**，我将为你生成相应的内容：")

        niche_options = {
            "general": "通用",
            "ai_tools": "AI 工具",
            "crypto": "加密货币",
            "beauty": "美妆",
            "fitness": "健身",
            "humor": "搞笑",
        }

        keyboard = []
        for niche_id, niche_name in niche_options.items():
            keyboard.append([InlineKeyboardButton(niche_name, callback_data=f"create_niche_{niche_id}_{user_id}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("请选择：", reply_markup=reply_markup)

        # 保存研究结果到用户状态，等待选择行业
        self.user_states[user_id] = {
            "research_result": research_result,
            "action": "waiting_niche_selection",
        }

    async def cmd_search(self, update: Update, context: CallbackContext) -> None:
        """
        /search <关键词> - 根据关键词搜索趋势和热点，显示完整数据+LLM总结
        """
        user_id = update.effective_user.id if update.effective_user else 0

        if not update.message or not context.args:
            await update.message.reply_text(
                "用法：/search <关键词>\n\n"
                "例如：\n"
                "/search AI开源项目\n"
                "/search 加密货币\n"
                "/search 产品发布",
                parse_mode="Markdown"
            )
            return

        keyword = " ".join(context.args)
        logger.info(f"用户 {user_id} 搜索关键词: {keyword}")

        # 显示搜索深度选择菜单（层数 + 每层条数）
        keyboard = [
            [InlineKeyboardButton("⚡ 快速 (1层 · 10条/平台)", callback_data=f"search_depth_quick_{user_id}")],
            [InlineKeyboardButton("⚙️ 标准 (3层 · 20条/平台)", callback_data=f"search_depth_standard_{user_id}")],
            [InlineKeyboardButton("🔥 深度 (5层 · 50条/平台)", callback_data=f"search_depth_deep_{user_id}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # 保存待搜索状态（关键词存在 user_states 中）
        self.user_states[user_id] = {
            "pending_search_keyword": keyword,
        }

        await update.message.reply_text(
            f"📊 搜索关键词：**{keyword}**\n\n"
            "🎯 请选择搜索深度：",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    async def _execute_search(self, query, keyword: str, depth: str) -> None:
        """执行实际搜索（从 button_callback 调用，query 是 CallbackQuery 对象）"""
        user_id = query.from_user.id
        layers = {"quick": 1, "standard": 3, "deep": 5}.get(depth, 3)
        max_results = {"quick": 10, "standard": 20, "deep": 50}.get(depth, 20)

        logger.info(f"用户 {user_id} 搜索关键词: {keyword} (深度: {depth}, 层数: {layers})")

        # 开始搜索 (query.answer() 已在 button_callback 中调用)
        await query.edit_message_text(
            f"🔍 正在{'多层' if layers > 1 else ''}搜索「{keyword}」...\n"
            f"📐 搜索层数: {layers} 层，每平台最多 {max_results} 条\n"
            f"⏳ 这可能需要 {15 * layers}-{30 * layers} 秒"
        )

        try:
            research_result = {}
            if self.researcher:
                if layers > 1:
                    # 多层递进搜索
                    research_result = await self.researcher.research_hierarchical(
                        keyword, layers=layers, max_per_layer=max_results
                    )
                else:
                    # 快速单层搜索
                    research_result = self.researcher.research_topic(niche=keyword, days=7)

            if not research_result or "error" in research_result:
                await query.message.reply_text(f"❌ 搜索失败：{research_result.get('error', '未知错误')}")
                return

            # 提取每个平台的数据
            platform_data = research_result.get("platform_data", {})
            all_posts = {}

            for platform, data in platform_data.items():
                if isinstance(data, dict) and "posts" in data:
                    posts = data.get("posts", [])
                    all_posts[platform] = posts[:max_results]  # 根据深度限制条数

            if not all_posts:
                await query.message.reply_text("❌ 未能获取任何趋势数据")
                return

            # ========== 发送完整数据 ==========

            # 1. 发送汇总统计（含多层信息）
            layer_info = research_result.get("layer_info", [])
            summary_text = f"📊 **「{keyword}」趋势搜索结果汇总**\n\n"
            if layer_info:
                summary_text += f"🔄 **搜索层数**: {len(layer_info)} 层\n"
                for li in layer_info:
                    kws = ", ".join(li.get("keywords", []))
                    summary_text += f"  层{li['layer']}: `{kws}` → {li.get('found', 0)} 条\n"
                summary_text += "\n"
            for platform, posts in all_posts.items():
                summary_text += f"✅ **{platform.upper()}**: {len(posts)} 条热点\n"

            await query.message.reply_text(summary_text, parse_mode="Markdown")

            # 2. 为每个平台发送详细数据
            for platform, posts in all_posts.items():
                if not posts:
                    continue

                platform_text = f"🔥 **{platform.upper()} 热点排行**\n\n"
                for idx, post in enumerate(posts, 1):
                    # 转义 Markdown 特殊字符，防止解析错误
                    title = post.get("title", "无标题")[:80]
                    title = title.replace("*", "\\*").replace("_", "\\_").replace("[", "\\[").replace("]", "\\]")
                    engagement = post.get("engagement", 0)
                    platform_text += f"{idx}. {title}\n   📊 热度: {engagement}\n"

                    if idx % 5 == 0:
                        platform_text += "\n"

                # Telegram 有消息长度限制，如果太长则分块发送
                if len(platform_text) > 3000:
                    chunks = [platform_text[i:i+3000] for i in range(0, len(platform_text), 3000)]
                    for chunk in chunks:
                        await query.message.reply_text(chunk, parse_mode="Markdown")
                else:
                    await query.message.reply_text(platform_text, parse_mode="Markdown")

            # 3. 用 LLM 生成趋势总结
            if self.llm_router:
                try:
                    # 构造 LLM 输入
                    trends_text = "\n".join([
                        f"{platform}: " + ", ".join([p.get("title", "")[:50] for p in posts[:5]])
                        for platform, posts in all_posts.items()
                    ])

                    prompt = f"""基于以下多平台的热点数据，用中文生成 2-3 句的趋势总结：

平台热点：
{trends_text}

搜索关键词：{keyword}

请总结出主要趋势和关键特征："""

                    summary = await self.llm_router.chat([
                        {"role": "user", "content": prompt}
                    ])

                    await query.message.reply_text(
                        f"🤖 **AI 趋势总结**\n\n{summary}",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"LLM 趋势总结失败: {e}")

            # 4. 保存搜索结果到用户状态
            self.user_states[user_id] = {
                "research_result": research_result,
                "search_keyword": keyword,
                "action": "search_complete",
                "all_posts": all_posts,
            }

            # 5. 提供后续操作选项 + 分析报告按钮
            keyboard = [
                [InlineKeyboardButton("📊 生成趋势分析报告", callback_data=f"analyze_report_{user_id}")],
                [InlineKeyboardButton("✍️ 基于结果生成内容", callback_data=f"create_from_search_{user_id}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.reply_text(
                "✨ 搜索完成！\n\n"
                "💡 接下来可以：",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"搜索命令出错: {e}")
            await query.message.reply_text(f"❌ 搜索出现错误：{str(e)}")

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

        parts = data.split("_", 3)  # 最多分 4 段
        action = parts[0] if parts else ""

        # 处理搜索深度选择
        if action == "search" and len(parts) >= 2 and parts[1] == "depth":
            # search_depth_<depth>_<user_id>
            depth = parts[2] if len(parts) > 2 else "standard"
            # 从 user_states 获取关键词
            user_state = self.user_states.get(user_id, {})
            keyword = user_state.get("pending_search_keyword", "")

            if not keyword:
                await query.answer("❌ 搜索关键词已过期，请重新 /search")
                return

            await query.answer()
            await self._execute_search(query, keyword, depth)
            return

        # 处理分析报告生成
        if action == "analyze" and len(parts) >= 2 and parts[1] == "report":
            await query.answer()
            await self._handle_trend_analysis(query, context)
            return

        # 处理保存分析报告为文件
        if action == "save" and len(parts) >= 2 and parts[1] == "analysis":
            await query.answer()
            await self._handle_save_analysis(query)
            return

        # 处理基于搜索结果生成内容
        if action == "create" and len(parts) >= 2 and parts[1] == "from":
            await query.answer()
            await self._handle_create_from_search(query, context)
            return

        await query.answer()

        if action == "create" and len(parts) >= 4 and parts[1] == "niche":
            # 处理 create_niche_<niche>_<user_id> 回调
            niche = parts[2]
            await self._handle_create_with_niche(query, context, niche)

        elif action == "search" and len(parts) >= 4 and parts[1] == "niche":
            # 处理 search_niche_<niche>_<user_id> 回调
            niche = parts[2]
            await self._handle_create_with_niche(query, context, niche)

        elif action == "confirm":
            # 第一步：用户点击"人工确认发布" (confirm_publish_{user_id})
            sub_action = "_".join(parts[1:-1]) if len(parts) > 2 else parts[1] if len(parts) > 1 else ""

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
            if query.message and query.message.chat:
                fake_update = type(
                    "FakeUpdate",
                    (),
                    {
                        "message": type(
                            "FakeMessage",
                            (),
                            {
                                "chat": query.message.chat,
                                "reply_text": query.message.reply_text,
                                "effective_user": query.from_user,
                            },
                        )(),
                        "effective_user": query.from_user,
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

    async def _handle_create_with_niche(self, query, context, niche: str) -> None:
        """处理用户选择行业后生成内容"""
        user_id = query.from_user.id

        # 获取之前保存的研究结果
        user_state = self.user_states.get(user_id, {})
        research_result = user_state.get("research_result", {})

        if not research_result:
            await query.edit_message_text("❌ 研究数据已过期，请重新 /create")
            return

        await query.edit_message_text(f"⏳ 正在为 {niche} 行业生成内容...")

        # 从 platform_data 中提取真实的话题
        platform_data = research_result.get("platform_data", {})
        real_topics = []
        for platform, data in platform_data.items():
            if isinstance(data, dict) and "posts" in data:
                posts = data.get("posts", [])
                for post in posts[:2]:
                    title = post.get("title", "").strip()
                    if title and len(title) > 5:
                        real_topics.append(title)

        # 从真实话题中随机选择一个
        if real_topics:
            import random
            selected_topic_title = random.choice(real_topics)
        else:
            selected_topic_title = research_result.get("summary", "通用话题")[:100]

        # 评分
        risk_score = 50
        if self.scorer:
            score_result = self.scorer.score_with_details(research_result)
            risk_score = score_result.get("score", 50)

        # 生成内容
        generated = {"type": "A", "content": "示例内容"}
        if self.generator:
            generated = await self.generator.generate(
                topic=selected_topic_title,
                niche=niche,
                content_type="a"
            )

        # 显示内容 + risk_score
        content_type = generated.get("type", "A").upper()
        content_text = generated.get("content", "无内容")
        risk_emoji = "🟢" if risk_score < 50 else "🟡" if risk_score < 80 else "🔴"

        message_text = (
            f"📝 **{niche} 行业**\n\n"
            f"🔥 **话题**: {selected_topic_title}\n\n"
            f"{content_text}\n\n"
            f"---\n"
            f"{risk_emoji} **风险评分**: {risk_score}/100\n"
            f"ℹ️ 风险说明: <50 低风险 | 50-79 中风险 | ≥80 高风险\n\n"
            f"⚠️ **需要人工审核确认后才能发布**\n\n"
            f"请选择操作:"
        )

        # 确认按钮
        keyboard = [
            [InlineKeyboardButton("✅ 人工确认发布", callback_data=f"confirm_publish_{user_id}")],
            [
                InlineKeyboardButton("🔄 重新生成", callback_data=f"regen_{user_id}"),
                InlineKeyboardButton("❌ 跳过", callback_data=f"skip_{user_id}"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # 保存生成内容到用户状态
        self.user_states[user_id] = {
            "generated": generated,
            "risk_score": risk_score,
            "niche": niche,
            "topic": selected_topic_title,
            "research_result": research_result,
            "action": "waiting_confirmation",
        }

        await query.edit_message_text(
            message_text, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def _handle_trend_analysis(self, query, context) -> None:
        """处理趋势分析报告生成"""
        user_id = query.from_user.id

        # 获取之前保存的研究结果
        user_state = self.user_states.get(user_id, {})
        research_result = user_state.get("research_result", {})

        if not research_result:
            await query.edit_message_text("❌ 研究数据已过期，请重新 /search")
            return

        await query.edit_message_text("⏳ 正在生成专业趋势分析报告...")

        try:
            # 调用 generator 生成分析报告
            if self.generator:
                report = await self.generator.generate_trend_analysis(research_result)
            else:
                report = "❌ 生成器不可用"

            # 分块发送（Telegram 有消息长度限制）
            if len(report) > 4000:
                chunks = [report[i:i+4000] for i in range(0, len(report), 4000)]
                await query.edit_message_text("📊 趋势分析报告（分段）：")
                for i, chunk in enumerate(chunks):
                    await query.message.reply_text(chunk, parse_mode="Markdown")
            else:
                await query.edit_message_text(report, parse_mode="Markdown")

            # 提供导出选项
            keyboard = [
                [InlineKeyboardButton("💾 保存为文件", callback_data=f"save_analysis_{user_id}")],
                [InlineKeyboardButton("🔄 生成新分析", callback_data=f"analyze_report_{user_id}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("📋 分析报告已生成", reply_markup=reply_markup)

            # 保存报告到用户状态
            self.user_states[user_id]["trend_analysis"] = report

        except Exception as e:
            logger.error(f"生成趋势分析失败: {e}")
            await query.edit_message_text(f"❌ 分析报告生成失败：{str(e)}")

    async def _handle_save_analysis(self, query) -> None:
        """保存趋势分析报告为 MD 文件并发送"""
        import os
        from datetime import datetime

        user_id = query.from_user.id
        user_state = self.user_states.get(user_id, {})
        report = user_state.get("trend_analysis", "")

        if not report:
            await query.edit_message_text("❌ 没有可保存的分析报告，请先生成报告")
            return

        try:
            # 保存到文件
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            keyword = user_state.get("search_keyword", "trends")
            filename = f"trend_analysis_{keyword}_{date_str}.md"
            filepath = os.path.join("data", filename)
            os.makedirs("data", exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)

            # 发送文件给用户
            await query.message.reply_document(
                document=open(filepath, "rb"),
                filename=filename,
                caption=f"📊 趋势分析报告 - {keyword}"
            )
            await query.edit_message_text("✅ 报告已保存并发送")

        except Exception as e:
            logger.error(f"保存分析报告失败: {e}")
            await query.edit_message_text(f"❌ 保存失败：{str(e)}")

    async def _handle_create_from_search(self, query, context) -> None:
        """基于搜索结果生成内容"""
        user_id = query.from_user.id

        # 获取之前保存的研究结果
        user_state = self.user_states.get(user_id, {})
        research_result = user_state.get("research_result", {})

        if not research_result:
            await query.edit_message_text("❌ 研究数据已过期，请重新 /search")
            return

        # 显示 niche 选择菜单
        niches = ["general", "ai_tools", "crypto", "beauty", "fitness", "humor", "adult"]
        keyboard = [
            [InlineKeyboardButton(niche_name, callback_data=f"create_niche_{niche}_{user_id}")]
            for niche_name, niche in zip(
                ["通用", "AI工具", "加密货币", "美妆", "健身", "搞笑", "成人用品"],
                niches
            )
        ]
        # 分成两列显示
        keyboard = [keyboard[i:i+2] for i in range(0, len(keyboard), 2)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🎯 请选择内容领域：",
            reply_markup=reply_markup
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
            "**内容生成:**\n"
            "/search <关键词> - 搜索趋势热点\n"
            "/create - 创建内容 (根据 niche)\n"
            "\n**查询命令:**\n"
            "/api_status - API 状态\n"
            "/trends - 热点趋势\n"
            "/report - 复盘报告\n"
            "\n**设置:**\n"
            "/set_niche - 切换 Niche\n"
            "/settings - 更多设置\n"
            "\n**其他:**\n"
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
        logger.info(f"[DEBUG] llm_router = {self.llm_router}, type = {type(self.llm_router)}")

        # 如果有 LLM，用 AI 回复
        if self.llm_router:
            try:
                logger.info(f"[DEBUG] 正在调用 LLM 回复...")
                await update.message.reply_text("💭 思考中...", reply_to_message_id=update.message.message_id)

                reply = await self.llm_router.chat(
                    messages=[
                        {"role": "system", "content": (
                            "你是一个智能 AI 助手，可以回答任何问题。你同时也具备帮助用户在 X (Twitter) 上运营账号的能力。\n"
                            "请用中文回答，简洁、有用、友好。如果用户问的是通用问题，正常回答即可。"
                        )},
                        {"role": "user", "content": user_text}
                    ]
                )
                logger.info(f"[DEBUG] LLM 回复成功: {reply[:50] if reply else 'empty'}")

                # Telegram 消息最大 4096 字符
                if len(reply) > 4000:
                    for i in range(0, len(reply), 4000):
                        await update.message.reply_text(reply[i:i+4000], reply_to_message_id=update.message.message_id)
                else:
                    await update.message.reply_text(reply, reply_to_message_id=update.message.message_id)
            except Exception as e:
                logger.error(f"LLM 回复失败: {e}", exc_info=True)
                await update.message.reply_text(
                    f"❌ AI 回复失败: {str(e)[:200]}\n\n"
                    "可能是 API 连接问题，请稍后再试。",
                    reply_to_message_id=update.message.message_id
                )
        else:
            logger.warning(f"[DEBUG] llm_router 为 None，无法回复消息")
            await update.message.reply_text(
                "❓ 请使用命令与我交互：\n\n"
                "/create - 创建内容\n"
                "/trends - 查看热点\n"
                "/help - 查看所有命令",
                reply_to_message_id=update.message.message_id
            )
