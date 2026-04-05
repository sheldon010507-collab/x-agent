"""
llm_router.py - LLM路由模块

【V0 Final】此版本为生产级开源版本

功能：
- 多模型支持
- 自动降级

版本：V0 Final
"""

import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ============ 基类 ============


class LLMProvider(ABC):
    """LLM 供应商基类"""

    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送聊天请求"""
        pass


# ============ Anthropic ============


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        model = kwargs.get("model", "claude-3-5-sonnet-20241022")

        system = ""
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat_messages.append({"role": m["role"], "content": m["content"]})

        response = await client.messages.create(
            model=model, max_tokens=4096, system=system if system else None, messages=chat_messages
        )

        return response.content[0].text


# ============ OpenAI (兼容 OpenRouter, NVIDIA NIM, Ollama) ============


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


# ============ Groq ============


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


# ============ LLM 路由器 ============


class LLMRouter:
    """LLM 路由器"""

    def __init__(self, config):
        self.config = config
        self.provider = self._get_provider()

    def _get_provider(self) -> LLMProvider:
        provider_name = self.config.llm.provider.lower()

        if provider_name == "anthropic":
            return AnthropicProvider(self.config.llm.anthropic_api_key)

        elif provider_name == "openai":
            return OpenAIProvider(self.config.llm.openai_api_key)

        elif provider_name == "groq":
            return GroqProvider(self.config.llm.groq_api_key)

        elif provider_name == "openrouter":
            return OpenAIProvider(
                self.config.llm.openrouter_api_key, self.config.llm.openrouter_base_url
            )

        elif provider_name == "nvidia":
            return OpenAIProvider(
                self.config.llm.nvidia_nim_api_key, self.config.llm.nvidia_nim_base_url
            )

        elif provider_name == "ollama":
            return OpenAIProvider("ollama", self.config.llm.ollama_base_url + "/v1")

        else:
            raise ValueError(f"不支持的 LLM 供应商: {provider_name}")

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送聊天请求"""
        # 自动使用 config 中配置的模型，调用方可覆盖
        if "model" not in kwargs and hasattr(self.config, "llm") and self.config.llm.model:
            kwargs["model"] = self.config.llm.model
        return await self.provider.chat(messages, **kwargs)

    async def generate_json(self, prompt: str, system: str = "", **kwargs) -> Dict:
        """调用 LLM 并解析 JSON 响应"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        raw = await self.chat(messages, **kwargs)
        # 提取 JSON（处理 markdown 代码块包裹的情况）
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group())
        raise ValueError("LLM 响应中未找到有效 JSON")


# ============ 便捷函数 ============

_default_router: Optional[LLMRouter] = None


def get_llm(config=None) -> LLMRouter:
    """获取 LLM 路由器"""
    global _default_router
    if config:
        return LLMRouter(config)
    if _default_router is None:
        from config import config as cfg

        _default_router = LLMRouter(cfg)
    return _default_router
