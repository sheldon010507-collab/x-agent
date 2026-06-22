"""Telegram command handlers that proxy requests to the X-Agent API."""

import logging

logger = logging.getLogger(__name__)


class BotAPICommands:
    def __init__(self, api_client=None):
        self.api = api_client

    async def _reply(self, update, text: str) -> None:
        if update and getattr(update, "message", None):
            await update.message.reply_text(text)
        else:
            logger.info(text)

    async def cmd_api_status(self, update, context):
        if not self.api:
            await self._reply(update, "API client is not configured.")
            return
        data = await self.api.get_status()
        if "error" in data:
            await self._reply(update, f"API status failed: {data['error']}")
            return
        await self._reply(
            update,
            "API status: {service} {version}\nLLM: {llm_provider}\nNiche: {niche}".format(
                service=data.get("service", "unknown"),
                version=data.get("version", ""),
                llm_provider=data.get("llm_provider", "unknown"),
                niche=data.get("niche", "general"),
            ),
        )

    async def cmd_api_trends(self, update, context):
        if not self.api:
            await self._reply(update, "API client is not configured.")
            return
        args = getattr(context, "args", []) or []
        niche = args[0] if args else "general"
        data = await self.api.get_trends(niche=niche, days=7)
        trends = data.get("trends", [])
        if "error" in data:
            await self._reply(update, f"Trend lookup failed: {data['error']}")
            return
        if not trends:
            await self._reply(update, f"No trends found for {niche}.")
            return
        lines = [f"Top trends for {niche}:"]
        for idx, item in enumerate(trends[:5], 1):
            title = item.get("topic") or item.get("title") or item.get("text") or "Untitled"
            score = item.get("score", 0)
            lines.append(f"{idx}. {title[:90]} (score: {score:.0f})")
        await self._reply(update, "\n".join(lines))

    async def cmd_api_generate(self, update, context):
        if not self.api:
            await self._reply(update, "API client is not configured.")
            return
        args = getattr(context, "args", []) or []
        content_type = args[0].upper() if args else "A"
        topic = " ".join(args[1:]) if len(args) > 1 else "current trend"
        data = await self.api.create_content("general", content_type, topic)
        if "error" in data:
            await self._reply(update, f"Content generation failed: {data['error']}")
            return
        result = data.get("result", {})
        content = ""
        if content_type == "A" and result.get("tweets"):
            content = result["tweets"][0].get("content", "")
        else:
            content = result.get("script") or result.get("content", "")
        await self._reply(
            update,
            f"Draft created: {data.get('content_id') or 'not saved'}\n\n{content[:1000]}",
        )

    async def cmd_api_report(self, update, context):
        if not self.api:
            await self._reply(update, "API client is not configured.")
            return
        args = getattr(context, "args", []) or []
        data = await self.api.get_report(args[0] if args else None)
        if "error" in data:
            await self._reply(update, f"Report lookup failed: {data['error']}")
            return
        await self._reply(
            update,
            "Report {date}: posts={posts}, comments={comments}, likes={likes}, rt={rt}".format(
                date=data.get("date", ""),
                posts=data.get("posts_count", 0),
                comments=data.get("comments_count", 0),
                likes=data.get("likes_count", 0),
                rt=data.get("rt_count", 0),
            ),
        )

    async def handle_api_callback(self, update, context):
        query = getattr(update, "callback_query", None)
        if query:
            await query.answer()
        logger.info("API callback received")
