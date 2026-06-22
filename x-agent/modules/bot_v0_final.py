"""Telegram bot for the v0 Final semi-automatic workflow."""

import inspect
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def create_bot_v0_final(
    token: str,
    db=None,
    llm_router=None,
    generator=None,
    config=None,
    researcher=None,
    scorer=None,
):
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
    """Small but complete semi-automatic Telegram workflow.

    Generated content is always a draft first. A user must click a first
    confirmation button, then a final confirmation button, before the draft is
    marked confirmed in storage.
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
        self.application = None
        self.user_states: Dict[int, Dict[str, Any]] = {}
        self.default_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    async def initialize(self) -> None:
        try:
            from telegram.ext import Application, CallbackQueryHandler, CommandHandler
        except Exception as exc:
            self.application = None
            logger.warning("python-telegram-bot unavailable; using log-only bot: %s", exc)
            return

        if not self.token or self.token in {"unused", "test_bot_token"}:
            self.application = None
            logger.warning("Telegram token is not configured; using log-only bot")
            return

        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("create", self.cmd_create))
        self.application.add_handler(CommandHandler("search", self.cmd_search))
        self.application.add_handler(CommandHandler("report", self.cmd_report))
        self.application.add_handler(CommandHandler("settings", self.cmd_settings))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        logger.info("Telegram Bot application initialized in semi-automatic mode")

    async def _reply(self, update, text: str, **kwargs) -> None:
        if update and getattr(update, "message", None):
            await update.message.reply_text(text, **kwargs)
        else:
            logger.info("[Telegram stub] %s", text[:500])

    async def _call_maybe_async(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    def _user_id(self, update) -> int:
        user = getattr(update, "effective_user", None)
        return int(getattr(user, "id", 0) or 0)

    def _draft_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        research = state.get("research_result") or {}
        marketing = research.get("marketing_analysis") or {}
        summary_parts = [
            state.get("summary") or research.get("summary") or "",
            marketing.get("publisher_brief") or "",
        ]
        return {
            "summary": "\n\n".join(part for part in summary_parts if part),
            "source": state.get("source") or research.get("source") or ",".join(research.get("platforms", [])),
            "score": state.get("score") or research.get("relevance_score") or 50.0,
        }

    async def cmd_start(self, update, context) -> None:
        await self._reply(
            update,
            "X-Agent is running.\n"
            "Commands: /status, /search <keyword>, /create <topic>, /report, /settings",
        )

    async def cmd_status(self, update, context) -> None:
        niche = "general"
        try:
            niche = self.db.get_current_niche() or "general" if self.db else "general"
        except Exception:
            pass
        await self._reply(update, f"X-Agent status: running\nNiche: {niche}\nMode: manual approval")

    async def cmd_search(self, update, context) -> None:
        args = getattr(context, "args", []) or []
        keyword = " ".join(args).strip() or "general"
        await self._reply(update, f"Searching trends for: {keyword}")

        if not self.researcher:
            await self._reply(update, "Researcher is not configured.")
            return

        try:
            result = await self._call_maybe_async(self.researcher.research_topic, keyword, 7)
        except Exception as exc:
            logger.exception("Search failed")
            await self._reply(update, f"Search failed: {exc}")
            return

        self.user_states[self._user_id(update)] = {
            "search_keyword": keyword,
            "research_result": result,
        }

        topics = self._extract_topics(result)[:8]
        if not topics:
            await self._reply(update, "No trend items found.")
            return
        await self._reply(update, "Top trend items:\n" + "\n".join(f"{i}. {t}" for i, t in enumerate(topics, 1)))

    async def cmd_create(self, update, context) -> None:
        user_id = self._user_id(update)
        args = getattr(context, "args", []) or []
        topic = " ".join(args).strip()
        state = self.user_states.get(user_id, {})
        if not topic:
            topic = state.get("search_keyword") or "current trend"

        if not self.generator:
            await self._reply(update, "Generator is not configured.")
            return

        await self._reply(update, f"Generating draft for: {topic}")
        try:
            draft_context = self._draft_context(state)
            result = await self._call_maybe_async(
                self.generator.generate_type_a,
                topic=topic,
                summary=draft_context["summary"],
                source=draft_context["source"],
                score=draft_context["score"],
            )
        except Exception as exc:
            logger.exception("Draft generation failed")
            await self._reply(update, f"Draft generation failed: {exc}")
            return

        content = self._first_content(result)
        content_id = None
        if content and self.db:
            try:
                record = self.db.create_content("telegram-generated", "A", content, status="draft")
                content_id = record.get("id") if record else None
            except Exception as exc:
                logger.warning("Failed to save draft: %s", exc)

        self.user_states[user_id] = {
            **state,
            "draft": content,
            "draft_result": result,
            "content_id": content_id,
            "topic": topic,
        }
        await self._send_draft(update, user_id, content, content_id)

    async def _send_draft(self, update, user_id: int, content: str, content_id: Optional[str]) -> None:
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Confirm publish", callback_data=f"confirm_publish_{user_id}")],
                [InlineKeyboardButton("Regenerate", callback_data=f"regenerate_{user_id}")],
                [InlineKeyboardButton("Skip", callback_data=f"skip_{user_id}")],
            ])
            await update.message.reply_text(
                f"Draft ({content_id or 'not saved'}):\n\n{content or '[empty draft]'}",
                reply_markup=keyboard,
            )
        except Exception:
            await self._reply(update, f"Draft ({content_id or 'not saved'}):\n\n{content or '[empty draft]'}")

    async def button_callback(self, update, context) -> None:
        query = getattr(update, "callback_query", None)
        if not query:
            return
        await query.answer()

        data = getattr(query, "data", "") or ""
        parts = data.rsplit("_", 1)
        action = parts[0]
        user_id = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 0
        state = self.user_states.get(user_id, {})

        if action == "confirm_publish":
            try:
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup

                markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Final confirm", callback_data=f"final_confirm_publish_{user_id}")],
                    [InlineKeyboardButton("Cancel", callback_data=f"skip_{user_id}")],
                ])
                await query.edit_message_text("Second confirmation required before publishing.", reply_markup=markup)
            except Exception:
                await query.edit_message_text("Second confirmation required before publishing.")
            return

        if action == "final_confirm_publish":
            content_id = state.get("content_id")
            if content_id and self.db:
                try:
                    if hasattr(self.db, "confirm_content"):
                        self.db.confirm_content(content_id)
                    else:
                        self.db.update_content_status(content_id, "confirmed")
                except Exception as exc:
                    logger.exception("Confirm failed")
                    await query.edit_message_text(f"Confirm failed: {exc}")
                    return
            await query.edit_message_text(f"Draft confirmed: {content_id or 'not saved'}")
            return

        if action == "regenerate":
            topic = state.get("topic") or state.get("search_keyword") or "current trend"
            fake_update = type("UpdateProxy", (), {"message": query.message, "effective_user": getattr(query, "from_user", None)})()
            fake_context = type("ContextProxy", (), {"args": topic.split()})()
            await self.cmd_create(fake_update, fake_context)
            return

        if action == "skip":
            await query.edit_message_text("Draft skipped.")
            return

    async def cmd_report(self, update, context) -> None:
        if not self.db:
            await self._reply(update, "Database is not configured.")
            return
        try:
            from datetime import date

            log = self.db.get_daily_log(date.today()) or {}
        except Exception as exc:
            await self._reply(update, f"Report failed: {exc}")
            return
        await self._reply(
            update,
            "Today: posts={posts}, comments={comments}, likes={likes}, rt={rt}".format(
                posts=log.get("posts_count", 0),
                comments=log.get("comments_count", 0),
                likes=log.get("likes_count", 0),
                rt=log.get("rt_count", 0),
            ),
        )

    async def cmd_settings(self, update, context) -> None:
        await self._reply(update, "Settings: manual approval is enabled; auto-publish is disabled.")

    async def cmd_help(self, update, context) -> None:
        await self._reply(update, "Use /search <keyword>, then /create <topic>. Drafts require two confirmations.")

    async def send_message(self, chat_id=None, text: str = "", **kwargs) -> None:
        if self.application and chat_id:
            await self.application.bot.send_message(chat_id=chat_id, text=text, **kwargs)
        else:
            logger.info("[Telegram stub] chat_id=%s message=%s", chat_id, text[:500])

    def _extract_topics(self, result: Dict[str, Any]) -> list:
        items = []
        platform_data = result.get("platform_data", result) if isinstance(result, dict) else {}
        for data in platform_data.values() if isinstance(platform_data, dict) else []:
            if not isinstance(data, dict):
                continue
            for post in data.get("posts", [])[:5]:
                title = post.get("title") or post.get("topic") or post.get("text")
                if title:
                    items.append(str(title)[:120])
        return items

    def _first_content(self, result: Dict[str, Any]) -> str:
        if not isinstance(result, dict):
            return str(result or "")
        tweets = result.get("tweets") or []
        if tweets:
            return tweets[0].get("content", "")
        return result.get("content") or result.get("script") or ""
