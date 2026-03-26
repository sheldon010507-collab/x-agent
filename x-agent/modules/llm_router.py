"""
llm_router.py - 多供应商 LLM 统一路由器
支持: OpenAI, Anthropic, Groq, Gemini, OpenRouter, NVIDIA NIM, Ollama
"""

import logging
import asyncio
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

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
            model=model,
            max_tokens=4096,
            system=system if system else None,
            messages=chat_messages
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
            model=model,
            messages=messages,
            max_tokens=4096
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
            model=model,
            messages=messages,
            max_tokens=4096
        )
        
        return response.choices[0].message.content


# ============ LLM 路由器 ============

class LLMRouter:
    """LLM 路由器"""
    
    def __init__(self, config):
        self.config = config
        self.provider = self._get_provider()
    
    def _get_provider(self) -> LLMProvider:
        provider_name = getattr(self.config, 'llm_provider', 'anthropic').lower()
        
        if provider_name == "anthropic":
            return AnthropicProvider(self.config.anthropic_api_key)
        
        elif provider_name == "openai":
            return OpenAIProvider(self.config.openai_api_key)
        
        elif provider_name == "groq":
            return GroqProvider(self.config.groq_api_key)
        
        elif provider_name == "openrouter":
            return OpenAIProvider(
                self.config.openrouter_api_key,
                "https://openrouter.ai/api/v1"
            )
        
        elif provider_name == "nvidia":
            return OpenAIProvider(
                self.config.nvidia_api_key,
                "https://integrate.api.nvidia.com/v1"
            )
        
        elif provider_name == "ollama":
            return OpenAIProvider(
                "ollama",
                getattr(self.config, 'ollama_base_url', 'http://localhost:11434/v1')
            )
        
        else:
            raise ValueError(f"不支持的 LLM 供应商: {provider_name}")
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送聊天请求"""
        return await self.provider.chat(messages, **kwargs)


# ============ 便捷函数 ============

_default_router: Optional[LLMRouter] = None


def get_llm(config=None) -> LLMRouter:
    """获取 LLM 路由器"""
    global _default_router
    if config:
        return LLMRouter(config)
    if _default_router is None:
        from modules.config import config as cfg
        _default_router = LLMRouter(cfg)
    return _default_router
