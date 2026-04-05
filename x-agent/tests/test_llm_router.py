"""
test_llm_router.py - LLM 路由模块测试

使用 unittest.mock 模拟 API 调用，完全离线运行。
测试供应商选择逻辑、接口委托和异常处理。
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.llm_router import (
    AnthropicProvider,
    GroqProvider,
    LLMRouter,
    OpenAIProvider,
)


def make_config(**kwargs):
    """创建带默认值的 mock config"""
    config = MagicMock()
    # LLM 配置通过 config.llm 子对象访问
    config.llm.provider = kwargs.get("llm_provider", "anthropic")
    config.llm.anthropic_api_key = kwargs.get("anthropic_api_key", "sk-test-anthropic")
    config.llm.openai_api_key = kwargs.get("openai_api_key", "sk-test-openai")
    config.llm.groq_api_key = kwargs.get("groq_api_key", "gsk-test-groq")
    config.llm.openrouter_api_key = kwargs.get("openrouter_api_key", "or-test")
    config.llm.openrouter_base_url = "https://openrouter.ai/api/v1"
    config.llm.nvidia_nim_api_key = kwargs.get("nvidia_api_key", "nvapi-test")
    config.llm.nvidia_nim_base_url = "https://integrate.api.nvidia.com/v1"
    config.llm.ollama_base_url = kwargs.get("ollama_base_url", "http://localhost:11434")
    config.llm.model = kwargs.get("model", "claude-3-5-sonnet-20241022")
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

        # The chat method auto-injects model from config.llm.model
        router.provider.chat.assert_called_once_with(messages, model="claude-3-5-sonnet-20241022")
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


def _can_import(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _can_import("anthropic"), reason="anthropic not installed")
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


@pytest.mark.skipif(not _can_import("openai"), reason="openai not installed")
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


@pytest.mark.skipif(not _can_import("groq"), reason="groq not installed")
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
        mock_client.chat.completions.create = AsyncMock(return_value=mock_client)

        with patch("groq.AsyncGroq", return_value=mock_client):
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            result = await provider.chat([{"role": "user", "content": "hi"}])

        assert result == "Groq response"


class TestGenerateJson:
    """generate_json 方法测试"""

    @pytest.mark.asyncio
    async def test_generate_json_parses_plain_json(self):
        """LLM 直接返回 JSON 字符串时能正确解析"""
        router = LLMRouter(make_config())
        router.chat = AsyncMock(return_value='{"key": "value", "num": 42}')

        result = await router.generate_json("give me json")

        assert result == {"key": "value", "num": 42}

    @pytest.mark.asyncio
    async def test_generate_json_handles_code_block(self):
        """LLM 返回 ```json 代码块时能正确提取"""
        router = LLMRouter(make_config())
        router.chat = AsyncMock(return_value='Here is the result:\n```json\n{"tweets": []}\n```')

        result = await router.generate_json("give me tweets")

        assert result == {"tweets": []}

    @pytest.mark.asyncio
    async def test_generate_json_with_system_prompt(self):
        """system 参数应作为 system 消息传入 chat"""
        router = LLMRouter(make_config())
        router.chat = AsyncMock(return_value='{"ok": true}')

        await router.generate_json("prompt text", system="you are helpful")

        call_args = router.chat.call_args
        messages = call_args[0][0]
        assert messages[0] == {"role": "system", "content": "you are helpful"}
        assert messages[1] == {"role": "user", "content": "prompt text"}

    @pytest.mark.asyncio
    async def test_generate_json_raises_on_no_json(self):
        """LLM 返回非 JSON 内容时应抛出 ValueError"""
        router = LLMRouter(make_config())
        router.chat = AsyncMock(return_value="Sorry, I cannot help with that.")

        with pytest.raises(ValueError, match="未找到有效 JSON"):
            await router.generate_json("prompt")
