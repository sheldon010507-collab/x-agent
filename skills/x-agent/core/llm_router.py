"""
llm_router.py - LLM 多供应商路由模块
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        pass


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        model = kwargs.get("model", "claude-sonnet-4-20250514")

        system = ""
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat_messages.append({"role": m["role"], "content": m["content"]})

        response = await client.messages.create(
            model=model,
            max_tokens=4096,
            system=system if system else None,
            messages=chat_messages,
        )
        return response.content[0].text


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        model = kwargs.get("model", "gpt-4o")

        response = await client.chat.completions.create(
            model=model, messages=messages, max_tokens=4096
        )
        return response.choices[0].message.content


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=self.api_key)
        model = kwargs.get("model", "llama-3.3-70b-versatile")

        response = await client.chat.completions.create(
            model=model, messages=messages, max_tokens=4096
        )
        return response.choices[0].message.content


class LLMRouter:
    def __init__(self, config):
        self.config = config
        self.provider = self._get_provider()

    def _get_provider(self) -> LLMProvider:
        name = self.config.llm.provider.lower()

        if name == "anthropic":
            return AnthropicProvider(self.config.llm.anthropic_api_key)
        elif name == "openai":
            return OpenAIProvider(self.config.llm.openai_api_key)
        elif name == "groq":
            return GroqProvider(self.config.llm.groq_api_key)
        elif name == "openrouter":
            return OpenAIProvider(
                self.config.llm.openrouter_api_key,
                self.config.llm.openrouter_base_url,
            )
        elif name == "nvidia":
            return OpenAIProvider(
                self.config.llm.nvidia_nim_api_key,
                self.config.llm.nvidia_nim_base_url,
            )
        elif name == "ollama":
            return OpenAIProvider(
                "ollama", self.config.llm.ollama_base_url + "/v1"
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {name}")

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        return await self.provider.chat(messages, **kwargs)

    async def generate_json(self, prompt: str, system: str = "", **kwargs) -> Dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        raw = await self.chat(messages, **kwargs)
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group())
        raise ValueError("No valid JSON found in LLM response")


_default_router: Optional[LLMRouter] = None


def get_llm(config=None) -> LLMRouter:
    global _default_router
    if config:
        return LLMRouter(config)
    if _default_router is None:
        from .config import Config

        _default_router = LLMRouter(Config())
    return _default_router
