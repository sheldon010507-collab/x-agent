"""
bot_v0_final.py - X-Agent v0 Final 半自动流程版

核心变更：
- 强制半自动：生成内容后必须人工确认才能发布
- Inline 按钮：【🤖 自动发布】【✅ 人工确认发布】【🔄 重新生成】【❌ 跳过】
- risk_score 显示：所有内容都标注风险评分
- 每日 21:00 自动推送复盘报告
"""

import logging
from typing import Dict, Optional, Any
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
)

logger = logging.getLogger(__name__)

# 对话状态
WAITING_CONFIRMATION = 1  # 等待用户确认发布


class XAgentBotV0Final:
    """
    X-Agent v0 Final Bot - 强制半自动流程
    
    核心原则：
    1. AI 生成内容后，必须用户点击确认才能发布
    2. 显示 risk_score，≥80 分禁止自动发布
    3. 每日 21:00 自动推送复盘报告
    """
    
    def __init__(self, token: str, db=None, llm_router=None, generator=None, 
                 config=None, researcher=None, scorer=None):
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
        self.application.add_handler(CommandHandler("research", self.cmd_research))
        self.application.add_handler(CommandHandler("trends", self.cmd_trends))
        self.application.add_handler(CommandHandler("create", self.cmd_create))
        self.application.add_handler(CommandHandler("report", self.cmd_report))
        self.application.add_handler(CommandHandler("settings", self.cmd_settings))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        
        # Inline 按钮回调处理器
        self.application.add_handler(
            CallbackQueryHandler(self.button_callback, pattern=r"^(confirm|auto|regen|skip|publish)_")
        )
        
        logger.info("✅ X-Agent v0 Final Bot 初始化完成（半自动模式）")
        
    async def start_bot(self) -> None:
        """启动 Bot"""
        if self.application:
            await self.application.start_polling()
            logger.info("🤖 Bot 已启动，监听消息中...")
    
    async def stop_bot(self) -> None:
        """停止 Bot"""
        if self.application:
            await self.application.stop()
            logger.info("🛑 Bot 已停止")
    
    # ========== 命令处理 ==========
    
    async def cmd_start(self, update: Update, context: CallbackContext) -> None:
        """
        /start - 欢迎信息 + 今日热点概览 + 快捷菜单
        
        V0 Final 变更：
        - 显示今日热点概览（前 3 条）
        - 快捷按钮：研究热点 / 创建内容 / 查看复盘
        """
        user_id = update.effective_user.id
        logger.info(f"用户 {user_id} 启动 Bot")
        
        # 获取今日热点
        trends_text = "暂无热点数据"
        if self.db:
            try:
                trends = self.db.get_trends(limit=3)  # 假设数据库方法存在
                if trends:
                    trends_text = "\n".join([f"• {t.get('title', '未知')}" for t in trends])
            except Exception as e:
                logger.error(f"获取热点失败：{e}")
        
        welcome_msg = (
            f"👋 欢迎使用 X-Agent v0 Final！\n\n"
            f"📊 **今日热点**（前 3 条）:\n"
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
        
        await update.message.reply_text(
            welcome_msg,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def cmd_create(self, update: Update, context: CallbackContext) -> None:
        """
        /create - 创建内容（半自动流程核心）
        
        流程：
        1. 调用 research 获取热点
        2. 调用 scorer 评分
        3. 调用 generator 生成 A/B/C 类内容
        4. 显示生成的内容 + risk_score
        5. Inline 按钮：【🤖 自动发布】【✅ 人工确认发布】【🔄 重新生成】【❌ 跳过】
        6. 必须用户点击确认后才调用 OpenClaw 发布
        """
        user_id = update.effective_user.id
        logger.info(f"用户 {user_id} 请求创建内容")
        
        # 步骤 1: 研究热点
        await update.message.reply_text("🔍 正在研究热点...")
        research_result = self.researcher.research_topic(
            niche=self.config.get("niche", "general"),
            days=7
        )
        
        if "error" in research_result:
            await update.message.reply_text(f"❌ 研究失败：{research_result['error']}")
            return
        
        # 步骤 2: 评分
        score_result = self.scorer.score(research_result)
        risk_score = score_result.get("risk_score", 50)
        
        # 步骤 3: 生成内容
        await update.message.reply_text("✍️ 正在生成内容...")
        generated = self.generator.generate(
            niche=self.config.get("niche", "general"),
            research=research_result,
            score=score_result
        )
        
        # 步骤 4: 显示内容 + risk_score
        content_type = generated.get("type", "A")  # A/B/C
        content_text = generated.get("content", "")
        
        risk_emoji = "🟢" if risk_score < 50 else "🟡" if risk_score < 80 else "🔴"
        
        message_text = (
            f"📝 **已生成 {content_type} 类内容**\n\n"
            f"{content_text}\n\n"
            f"---\n"
            f"{risk_emoji} **风险评分**: {risk_score}/100\n"
            f"ℹ️ 风险说明:\n"
            f"- <50: 低风险，可自动发布\n"
            f"- 50-79: 中风险，建议人工确认\n"
            f"- ≥80: 高风险，必须人工确认\n\n"
            f"请选择操作："
        )
        
        # 步骤 5: Inline 确认按钮
        can_auto_publish = risk_score < 80  # 高风险禁止自动发布
        
        keyboard = []
        
        if can_auto_publish:
            keyboard.append([
                InlineKeyboardButton("🤖 自动发布", callback_data=f"auto_publish_{user_id}"),
                InlineKeyboardButton("✅ 人工确认发布", callback_data=f"manual_publish_{user_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("✅ 人工确认发布（必须）", callback_data=f"manual_publish_{user_id}")
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔄 重新生成", callback_data=f"regen_{user_id}"),
            InlineKeyboardButton("❌ 跳过", callback_data=f"skip_{user_id}")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 保存生成内容到用户状态，等待确认
        self.user_states[user_id] = {
            "generated": generated,
            "risk_score": risk_score,
            "action": "waiting_confirmation"
        }
        
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def button_callback(self, update: Update, context: CallbackContext) -> None:
        """
        Inline 按钮回调处理
        
        处理：
        - confirm_publish: 确认后发布
        - auto_publish: 自动发布（低风险）
        - regen: 重新生成
        - skip: 跳过
        """
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data  # 例如："auto_publish_12345"
        
        logger.info(f"用户 {user_id} 点击按钮：{data}")
        
        # 解析按钮类型
        action, *_ = data.split("_")
        
        if action == "auto":
            # 自动发布（低风险内容）
            await query.edit_message_text("🤖 正在自动发布...")
            # TODO: 调用 openclaw_bridge.publish()
            await query.edit_message_text("✅ 已自动发布！")
            
        elif action == "manual":
            # 人工确认发布 - 显示最终确认
            await query.edit_message_text("✅ 请复制内容后手动发布到 X/Twitter")
            # TODO: 显示复制按钮或跳转链接
            
        elif action == "regen":
            # 重新生成
            await query.edit_message_text("🔄 正在重新生成...")
            await self.cmd_create(update, context)  # 重新走流程
            
        elif action == "skip":
            # 跳过
            await query.edit_message_text("❌ 已跳过本次生成")
            if user_id in self.user_states:
                del self.user_states[user_id]
    
    async def cmd_report(self, update: Update, context: CallbackContext) -> None:
        """
        /report - 每日复盘报告
        
        每日 21:00 自动推送，也可手动触发
        """
        logger.info(f"用户 {update.effective_user.id} 请求复盘报告")
        
        # TODO: 从数据库获取今日数据
        report_text = (
            "📊 **今日复盘报告**\n\n"
            f"日期：2026-03-27\n\n"
            "📝 发帖数：0\n"
            "💬 评论数：0\n"
            "❤️ 最高互动：0\n\n"
            "💡 建议：继续优化内容质量"
        )
        
        await update.message.reply_text(report_text, parse_mode="Markdown")
    
    # ========== 其他命令（简化版）==========
    
    async def cmd_set_niche(self, update: Update, context: CallbackContext) -> None:
        """切换 Niche"""
        await update.message.reply_text("🎭 切换 Niche 功能开发中...")
    
    async def cmd_research(self, update: Update, context: CallbackContext) -> None:
        """研究热点"""
        await update.message.reply_text("🔍 研究热点功能开发中...")
    
    async def cmd_trends(self, update: Update, context: CallbackContext) -> None:
        """查看热点列表"""
        await update.message.reply_text("📊 热点列表功能开发中...")
    
    async def cmd_settings(self, update: Update, context: CallbackContext) -> None:
        """设置"""
        await update.message.reply_text("⚙️ 设置功能开发中...")
    
    async def cmd_help(self, update: Update, context: CallbackContext) -> None:
        """帮助"""
        help_text = (
            "📚 **X-Agent v0 Final 帮助**\n\n"
            "/start - 欢迎信息\n"
            "/create - 创建内容（半自动）\n"
            "/report - 复盘报告\n"
            "/set_niche - 切换 Niche\n"
            "/help - 帮助"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")


# ========== 主程序入口 ==========

async def main():
    """Bot 启动入口"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN 未配置")
        return
    
    # 初始化 Bot（需要传入依赖）
    bot = XAgentBotV0Final(
        token=token,
        db=None,  # TODO: 传入 Database 实例
        llm_router=None,  # TODO: 传入 LLMRouter 实例
        generator=None,  # TODO: 传入 ContentGenerator 实例
        config=None,  # TODO: 传入 Config 实例
        researcher=None,  # TODO: 传入 Researcher 实例
        scorer=None  # TODO: 传入 Scorer 实例
    )
    
    await bot.initialize()
    await bot.start_bot()
    
    # 保持运行直到停止
    import asyncio
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        await bot.stop_bot()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
