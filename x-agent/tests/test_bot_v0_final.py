from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.bot_v0_final import XAgentBotV0Final


class DummyMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append((text, kwargs))


@pytest.mark.asyncio
async def test_create_saves_draft_before_confirmation():
    db = MagicMock()
    db.create_content.return_value = {"id": "content-1"}
    generator = MagicMock()
    generator.generate_type_a = AsyncMock(return_value={"tweets": [{"content": "draft text"}]})
    bot = XAgentBotV0Final("unused", db=db, generator=generator)

    message = DummyMessage()
    update = SimpleNamespace(message=message, effective_user=SimpleNamespace(id=123))
    context = SimpleNamespace(args=["test", "topic"])

    await bot.cmd_create(update, context)

    db.create_content.assert_called_once_with(
        "telegram-generated", "A", "draft text", status="draft"
    )
    assert bot.user_states[123]["content_id"] == "content-1"
    assert any("draft text" in reply[0] for reply in message.replies)


@pytest.mark.asyncio
async def test_create_passes_marketing_brief_from_research_to_generator():
    generator = MagicMock()
    generator.generate_type_a = AsyncMock(return_value={"tweets": [{"content": "draft text"}]})
    bot = XAgentBotV0Final("unused", generator=generator)
    bot.user_states[123] = {
        "search_keyword": "ai_tools",
        "research_result": {
            "summary": "Users want cheaper monitoring.",
            "source": "reddit,youtube",
            "relevance_score": 72,
            "marketing_analysis": {
                "publisher_brief": "Lead with the cost pain, then offer a checklist.",
            },
        },
    }

    message = DummyMessage()
    update = SimpleNamespace(message=message, effective_user=SimpleNamespace(id=123))
    context = SimpleNamespace(args=[])

    await bot.cmd_create(update, context)

    call_kwargs = generator.generate_type_a.await_args.kwargs
    assert "Users want cheaper monitoring." in call_kwargs["summary"]
    assert "Lead with the cost pain" in call_kwargs["summary"]
    assert call_kwargs["source"] == "reddit,youtube"
    assert call_kwargs["score"] == 72


@pytest.mark.asyncio
async def test_final_confirm_marks_content_confirmed():
    db = MagicMock()
    bot = XAgentBotV0Final("unused", db=db)
    bot.user_states[123] = {"content_id": "content-1"}

    query = SimpleNamespace(
        data="final_confirm_publish_123",
        answer=AsyncMock(),
        edit_message_text=AsyncMock(),
    )
    update = SimpleNamespace(callback_query=query)

    await bot.button_callback(update, SimpleNamespace())

    db.confirm_content.assert_called_once_with("content-1")
    query.edit_message_text.assert_awaited_once()
