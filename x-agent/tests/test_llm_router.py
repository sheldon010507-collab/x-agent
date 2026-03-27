"""
test_llm_router.py - LLM 路由模块测试

使用 unittest.mock 模拟 API 调用，完全离线运行。
测试供应商选择逻辑、接口委托和异常处理。
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.llm_router import (
    LLMRouter,
    AnthropicProvider,
    OpenAIProvider,
    GroqProvider,
)


def make_config(**kwargs):
    """创建带默认值的 mock config"""
    config = MagicMock()
    config.llm_provider = kwargs.get("llm_provider", "anthropic")
    config.anthropic_api_key = kwargs.get("anthropic_api_key", "sk-test-anthropic")
    config.openai_api_key = kwargs.get("openai_api_key", "sk-test-openai")
    config.groq_api_key = kwargs.get("groq_api_key", "gsk-test-groq")
    config.openrouter_api_key = kwargs.get("openrouter_api_key", "or-test")
    config.nvidia_api_key = kwargs.get("nvidia_api_key", "nvapi-test")
    config.ollama_base_url = kwargs.get("ollama_base_url", "http://localhost:11434/v1")
    return config


class TestLLMRouterProviderSelection:
    """供应商选择测试"""

    def test_anthropic_provider_selected(self):
        router = LLMRouter(make_config(llm_provider="anthropic"))
        assert isinstance(router.provider, AnthropicProvider)

    def test_openai_provider_selected(self):
        router = LLMRouter(make_config(llm_provider="openai"))
        assert isinstance(router.provider, OpenAIProvider)

    def test_groq_provider_selected(self):
        router = LLMRouter(make_config(llm_provider="groq"))
        assert isinstance(router.provider, GroqProvider)

    def test_openrouter_uses_openai_compatible(self):
        """OpenRouter 使用 OpenAI 兼容接口"""
        router = LLMRouter(make_config(llm_provider="openrouter"))
        assert isinstance(router.provider, OpenAIProvider)

    def test_nvidia_uses_openai_compatible(self):
        """NVIDIA NIM 使用 OpenAI 兼容接口"""
        router = LLMRouter(make_config(llm_provider="nvidia"))
        assert isinstance(router.provider, OpenAIProvider)

    def test_ollama_uses_openai_compatible(self):
        """Ollama 使用 OpenAI 兼容接口"""
        router = LLMRouter(make_config(llm_provider="ollama"))
        assert isinstance(router.provider, OpenAIProvider)

    def test_unsupported_provider_raises_value_error(self):
        with pytest.raises(ValueError, match="不支持的 LLM 供应商"):
            LLMRouter(make_config(llm_provider="unknown_xyz"))


class TestLLMRouterChat:
    """chat 方法委托测试"""

    @pytest.mark.asyncio
    async def test_chat_delegates_to_provider(self):
        router = LLMRouter(make_config())
        router.provider = MagicMock()
        router.provider.chat = AsyncMock(return_value="mocked response")

        messages = [{"role": "user", "content": "hello"}]
        result = await router.chat(messages)

        router.provider.chat.assert_called_once_with(messages)
        assert result == "mocked response"

    @pytest.mark.asyncio
    async def test_chat_passes_kwargs_to_provider(self):
        router = LLMRouter(make_config())
        router.provider = MagicMock()
        router.provider.chat = AsyncMock(return_value="response")

        await router.chat([{"role": "user", "content": "hi"}], model="claude-3-opus")

        router.provider.chat.assert_called_once_with(
            [{"role": "user", "content": "hi"}],
            model="claude-3-opus",
        )


class TestAnthropicProvider:
    """AnthropicProvider 单元测试"""

    @pytest.mark.asyncio
    async def test_system_message_extracted_separately(self):
        """system 消息应从列表中提取，单独传给 Anthropic API"""
        provider = AnthropicProvider("test-key")
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hi there!")]

        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            result = await provider.chat(messages)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        # system 应单独传递
        assert call_kwargs.get("system") == "You are helpful"
        # messages 中不应包含 system
        for msg in call_kwargs.get("messages", []):
            assert msg.get("role") != "system"
        assert result == "Hi there!"

    @pytest.mark.asyncio
    async def test_returns_text_content(self):
        provider = AnthropicProvider("test-key")
        messages = [{"role": "user", "content": "test"}]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello from Claude")]

        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            result = await provider.chat(messages)

        assert result == "Hello from Claude"

    @pytest.mark.asyncio
    async def test_default_model_used(self):
        provider = AnthropicProvider("test-key")
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="response")]

        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            await provider.chat([{"role": "user", "content": "hi"}])

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "model" in call_kwargs
        assert "claude" in call_kwargs["model"]


class TestOpenAIProvider:
    """OpenAIProvider 单元测试"""

    @pytest.mark.asyncio
    async def test_chat_returns_message_content(self):
        provider = OpenAIProvider("sk-test")

        mock_choice = MagicMock()
        mock_choice.message.content = "OpenAI response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            result = await provider.chat([{"role": "user", "content": "hi"}])

        assert result == "OpenAI response"

    @pytest.mark.asyncio
    async def test_custom_base_url_passed(self):
        """自定义 base_url（用于 OpenRouter/Ollama）应被传递"""
        provider = OpenAIProvider("or-key", base_url="https://openrouter.ai/api/v1")

        mock_choice = MagicMock()
        mock_choice.message.content = "response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client) as mock_cls:
            await provider.chat([{"role": "user", "content": "hi"}])

        mock_cls.assert_called_once_with(
            api_key="or-key",
            base_url="https://openrouter.ai/api/v1",
        )


class TestGroqProvider:
    """GroqProvider 单元测试"""

    @pytest.mark.asyncio
    async def test_chat_returns_message_content(self):
        provider = GroqProvider("gsk-test")

        mock_choice = MagicMock()
        mock_choice.message.content = "Groq response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("groq.AsyncGroq", return_value=mock_client):
            result = await provider.chat([{"role": "user", "content": "hi"}])

        assert result == "Groq response"
