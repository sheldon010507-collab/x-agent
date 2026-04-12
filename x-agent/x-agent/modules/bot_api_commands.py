"""
bot_api_commands.py - Bot API 控制命令

为 Telegram Bot 添加通过 HTTP API 控制 X-Agent 的命令
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import logging
from typing import Optional

from .api_client import XAgentAPIClient

logger = logging.getLogger(__name__)


class BotAPICommands:
    """Bot API 命令处理器"""

    def __init__(self, api_client: Optional[XAgentAPIClient] = None):
        """
        初始化

        Args:
            api_client: X-Agent API 客户端实例
        """
        self.api = api_client or XAgentAPIClient()

    async def cmd_api_status(self, update: Update, context: CallbackContext):
        """检查 API 状态"""
        chat_id = update.effective_chat.id

        try:
            status = await self.api.get_status()

            if "error" in status:
                await context.bot.send_message(
                    chat_id, f"❌ API 离线：{status['error']}"
                )
            else:
                msg = f"""
✅ **API 状态正常**

🔧 服务：{status.get('service', 'unknown')}
📦 版本：{status.get('version', 'unknown')}
🎯 细分领域：{status.get('niche', 'unknown')}
⚙️ LLM：{status.get('llm_provider', 'unknown')}
⏰ 时间：{status.get('timestamp', 'unknown')}
                """
                await context.bot.send_message(chat_id, msg, parse_mode="Markdown")

        except Exception as e:
            await context.bot.send_message(
                chat_id, f"❌ 获取状态失败：{str(e)}"
            )

    async def cmd_api_trends(self, update: Update, context: CallbackContext):
        """获取热点趋势"""
        chat_id = update.effective_chat.id

        # 获取参数 /trends [niche] [days]
        args = context.args
        niche = args[0] if args else "general"
        days = int(args[1]) if len(args) > 1 else 7

        try:
            await context.bot.send_chat_action(chat_id, "typing")

            trends_data = await self.api.get_trends(niche, days)

            if "error" in trends_data:
                await context.bot.send_message(
                    chat_id, f"❌ 获取趋势失败：{trends_data['error']}"
                )
                return

            trends = trends_data.get("trends", [])

            if not trends:
                await context.bot.send_message(
                    chat_id,
                    f"📊 **热点趋势**\n\n暂无 {niche} 细分领域的热点数据",
                    parse_mode="Markdown",
                )
                return

            msg = f"📊 **{niche} 细分领域热点趋势**（最近 {days} 天）\n\n"
            for i, trend in enumerate(trends[:10], 1):  # 最多显示 10 条
                score = trend.get("score", 0)
                topic = trend.get("topic", "Unknown")
                msg += f"{i}. {topic} (评分: {score})\n"

            await context.bot.send_message(chat_id, msg, parse_mode="Markdown")

        except Exception as e:
            await context.bot.send_message(
                chat_id, f"❌ 获取趋势失败：{str(e)}"
            )

    async def cmd_api_generate(self, update: Update, context: CallbackContext):
        """生成内容

        用法：/generate <type> <topic>
        type: A (推文) 或 B (视频脚本)
        """
        chat_id = update.effective_chat.id

        if len(context.args) < 2:
            await context.bot.send_message(
                chat_id,
                "❌ 用法：/generate <A|B> <话题>\n\nA = 推文\nB = 视频脚本",
            )
            return

        content_type = context.args[0].upper()
        topic = " ".join(context.args[1:])

        if content_type not in ["A", "B"]:
            await context.bot.send_message(chat_id, "❌ 类型只能是 A（推文）或 B（视频脚本）")
            return

        try:
            await context.bot.send_chat_action(chat_id, "typing")

            result = await self.api.create_content("general", content_type, topic)

            if "error" in result:
                await context.bot.send_message(
                    chat_id, f"❌ 生成失败：{result['error']}"
                )
                return

            content_id = result.get("content_id")
            generated = result.get("result", {})
            status = result.get("status", "draft")

            type_name = "推文" if content_type == "A" else "视频脚本"

            msg = f"✅ **{type_name}生成成功**\n\n"
            msg += f"📝 ID: `{content_id}`\n"
            msg += f"📌 状态: {status}\n"
            msg += f"📚 话题: {topic}\n\n"

            # 显示生成的内容
            if content_type == "A":
                tweets = generated.get("tweets", [])
                msg += f"**生成的推文数：{len(tweets)}**\n\n"
                for i, tweet in enumerate(tweets[:3], 1):  # 显示前 3 条
                    msg += f"{i}. {tweet.get('content', 'N/A')[:100]}...\n\n"
            else:
                msg += "✨ 视频脚本已生成\n"

            # 添加批准按钮
            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ 批准发布",
                        callback_data=f"approve_{content_id}",
                    ),
                    InlineKeyboardButton(
                        "❌ 删除", callback_data=f"delete_{content_id}"
                    ),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id, msg, parse_mode="Markdown", reply_markup=reply_markup
            )

        except Exception as e:
            await context.bot.send_message(
                chat_id, f"❌ 生成内容失败：{str(e)}"
            )

    async def cmd_api_report(self, update: Update, context: CallbackContext):
        """获取每日报告

        用法：/report [YYYY-MM-DD]
        """
        chat_id = update.effective_chat.id

        date = context.args[0] if context.args else None

        try:
            await context.bot.send_chat_action(chat_id, "typing")

            report = await self.api.get_report(date)

            if "error" in report:
                await context.bot.send_message(
                    chat_id, f"❌ 获取报告失败：{report['error']}"
                )
                return

            msg = f"""
📊 **每日报告**

📅 日期: {report.get('date', 'N/A')}
📝 帖子数: {report.get('posts_count', 0)}
💬 评论数: {report.get('comments_count', 0)}
❤️ 点赞数: {report.get('likes_count', 0)}
🔄 转发数: {report.get('rt_count', 0)}
⭐ 最高互动: {report.get('top_engagement', 0)}
            """

            await context.bot.send_message(chat_id, msg, parse_mode="Markdown")

        except Exception as e:
            await context.bot.send_message(
                chat_id, f"❌ 获取报告失败：{str(e)}"
            )

    async def handle_api_callback(self, update: Update, context: CallbackContext):
        """处理 API 相关的回调（按钮点击）"""
        query = update.callback_query
        data = query.data

        try:
            if data.startswith("approve_"):
                content_id = data.replace("approve_", "")
                await context.bot.send_chat_action(query.message.chat_id, "typing")

                result = await self.api.approve_content(content_id)

                if "error" in result:
                    await query.answer(f"❌ 批准失败：{result['error']}", show_alert=True)
                else:
                    await query.answer("✅ 内容已批准发布", show_alert=True)
                    # 编辑消息，移除按钮
                    await query.edit_message_text(
                        text=query.message.text + "\n\n✅ **已批准发布**"
                    )

            elif data.startswith("delete_"):
                content_id = data.replace("delete_", "")
                await query.answer("❌ 内容已删除", show_alert=True)
                await query.edit_message_text(
                    text=query.message.text + "\n\n❌ **已删除**"
                )

        except Exception as e:
            await query.answer(f"❌ 操作失败：{str(e)}", show_alert=True)
