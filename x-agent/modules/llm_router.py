"""
llm_router.py - 多供应商 LLM 统一路由器 (v3)
支持 7 个供应商：Anthropic, OpenAI, Groq, Gemini, OpenRouter, NVIDIA NIM, Ollama
实现统一接口，根据配置动态切换
实现 /llm 指令的底层切换逻辑
"""
import logging
import asyncio
from typing import List, Dict, Optional, Union
from abc import ABC, abstractmethod
import os

logger = logging.getLogger(__name__)

# ============ 供应商配置 ============
PROVIDER_MODELS = {
    'anthropic': ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'],
    'openai': ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    'groq': ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768'],
    'gemini': ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash'],
    'openrouter': ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o', 'meta-llama/llama-3.1-70b-instruct'],
    'nvidia': ['meta/llama-3.1-405b-instruct', 'meta/llama-3.1-70b-instruct', 'mistralai/mistral-large'],
    'ollama': ['llama3.2', 'llama3.1', 'mistral', 'gemma2']
}

PROVIDER_BASE_URLS = {
    'openrouter': 'https://openrouter.ai/api/v1',
    'nvidia': 'https://integrate.api.nvidia.com/v1',
    'ollama': 'http://localhost:11434/v1'
}

# ============ 基类 ============
class LLMProvider(ABC):
    """LLM 供应商基类"""
    
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式：[{"role": "system|user|assistant", "content": "内容"}]
            **kwargs: 额外参数 (model, temperature, max_tokens 等)
        
        Returns:
            str: 回复内容
        """
        pass
    
    @abstractmethod
    async def generate_json(self, messages: List[Dict], **kwargs) -> Dict:
        """
        生成 JSON 格式回复
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
        
        Returns:
            Dict: 解析后的 JSON 对象
        """
        pass
    
    def _parse_json_response(self, text: str) -> Dict:
        """解析 JSON 响应"""
        import json
        # 尝试提取 JSON 代码块
        text = text.strip()
        if text.startswith('```json') and text.endswith('```'):
            text = text[7:-3].strip()
        elif text.startswith('```') and text.endswith('```'):
            text = text[3:-3].strip()
        
        return json.loads(text)


# ============ Anthropic Provider ============
class AnthropicProvider(LLMProvider):
    """Anthropic (Claude) 供应商"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.default_model = 'claude-3-5-sonnet-20241022'
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        import anthropic
        
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        model = kwargs.get("model", self.default_model)
        
        # 分离 system 消息
        system = ""
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat_messages.append({"role": m["role"], "content": m["content"]})
        
        # 构建请求参数
        params = {
            "model": model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": chat_messages
        }
        
        if system:
            params["system"] = system
        
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        
        response = await client.messages.create(**params)
        return response.content[0].text
    
    async def generate_json(self, messages: List[Dict], **kwargs) -> Dict:
        # 添加 JSON 格式要求
        system_msg = "You are a helpful assistant that responds in valid JSON format. Do not include any markdown or explanation, only valid JSON."
        
        # 检查是否已有 system 消息
        has_system = any(m["role"] == "system" for m in messages)
        if not has_system:
            messages = [{"role": "system", "content": system_msg}] + messages
        
        response = await self.chat(messages, **kwargs)
        return self._parse_json_response(response)


# ============ OpenAI Compatible Provider (OpenAI, OpenRouter, NVIDIA NIM, Ollama) ============
class OpenAICompatibleProvider(LLMProvider):
    """OpenAI 兼容接口供应商"""
    
    def __init__(self, api_key: str, base_url: str, default_model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        model = kwargs.get("model", self.default_model)
        
        # 构建请求参数
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096)
        }
        
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        
        response = await client.chat.completions.create(**params)
        return response.choices[0].message.content
    
    async def generate_json(self, messages: List[Dict], **kwargs) -> Dict:
        # 添加 JSON 格式要求
        system_msg = "You are a helpful assistant that responds in valid JSON format. Do not include any markdown or explanation, only valid JSON."
        
        # 检查是否已有 system 消息
        has_system = any(m["role"] == "system" for m in messages)
        if not has_system:
            messages = [{"role": "system", "content": system_msg}] + messages
        
        # 强制使用 JSON 模式（如果支持）
        kwargs['response_format'] = {"type": "json_object"}
        
        response = await self.chat(messages, **kwargs)
        return self._parse_json_response(response)


# ============ Groq Provider ============
class GroqProvider(LLMProvider):
    """Groq 供应商"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.default_model = 'llama-3.3-70b-versatile'
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        from groq import AsyncGroq
        
        client = AsyncGroq(api_key=self.api_key)
        model = kwargs.get("model", self.default_model)
        
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096)
        }
        
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        
        response = await client.chat.completions.create(**params)
        return response.choices[0].message.content
    
    async def generate_json(self, messages: List[Dict], **kwargs) -> Dict:
        system_msg = "You are a helpful assistant that responds in valid JSON format. Do not include any markdown or explanation, only valid JSON."
        
        has_system = any(m["role"] == "system" for m in messages)
        if not has_system:
            messages = [{"role": "system", "content": system_msg}] + messages
        
        response = await self.chat(messages, **kwargs)
        return self._parse_json_response(response)


# ============ Gemini Provider ============
class GeminiProvider(LLMProvider):
    """Google Gemini 供应商"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.default_model = 'gemini-2.0-flash-exp'
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(kwargs.get("model", self.default_model))
        
        # 转换消息格式
        chat_history = []
        system_instruction = None
        
        for m in messages:
            if m["role"] == "system":
                system_instruction = m["content"]
            elif m["role"] == "user":
                chat_history.append({"role": "user", "parts": [m["content"]]})
            elif m["role"] == "assistant":
                chat_history.append({"role": "model", "parts": [m["content"]]})
        
        # 如果有 system instruction，添加到第一条消息
        if system_instruction:
            if chat_history and chat_history[0]["role"] == "user":
                chat_history[0]["parts"].insert(0, f"{system_instruction}\n\n")
            else:
                chat_history.insert(0, {"role": "user", "parts": [system_instruction]})
        
        # 生成回复
        response = await model.generate_content_async(
            contents=chat_history,
            generation_config=genai.GenerationConfig(
                max_output_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7)
            )
        )
        
        return response.text
    
    async def generate_json(self, messages: List[Dict], **kwargs) -> Dict:
        system_msg = "You are a helpful assistant that responds in valid JSON format. Do not include any markdown or explanation, only valid JSON."
        
        has_system = any(m["role"] == "system" for m in messages)
        if not has_system:
            messages = [{"role": "system", "content": system_msg}] + messages
        
        response = await self.chat(messages, **kwargs)
        return self._parse_json_response(response)


# ============ LLM 路由器 ============
class LLMRouter:
    """
    LLM 路由器 - 统一接口，动态切换供应商
    
    使用方法:
    ```python
    # 从配置初始化
    router = LLMRouter(config)
    
    # 或直接传入参数
    router = LLMRouter(
        provider='anthropic',
        api_key='sk-xxx',
        model='claude-3-5-sonnet-20241022'
    )
    
    # 发送消息
    response = await router.chat([
        {"role": "user", "content": "Hello!"}
    ])
    
    # 生成 JSON
    json_response = await router.generate_json([
        {"role": "user", "content": "Return {\"answer\": 42}"}
    ])
    ```
    """
    
    def __init__(self, config=None, provider: str = None, api_key: str = None, 
                 model: str = None, base_url: str = None):
        """
        初始化 LLM 路由器
        
        Args:
            config: 配置对象（可选，从 config 模块导入）
            provider: LLM 供应商名称 (anthropic/openai/groq/gemini/openrouter/nvidia/ollama)
            api_key: API Key (可选，默认从环境变量读取)
            model: 模型名称 (可选)
            base_url: 基础 URL (可选，用于自定义端点)
        """
        # 从 config 对象读取配置
        if config:
            self.provider_name = getattr(config, 'llm_provider', 'anthropic').lower()
            self.api_key = self._get_api_key(self.provider_name, config)
            self.model = getattr(config, 'llm_model', None)
            self.base_url = self._get_base_url(self.provider_name, config)
        else:
            # 直接传入参数
            self.provider_name = provider or 'anthropic'
            self.api_key = api_key or self._get_env_api_key(self.provider_name)
            self.model = model
            self.base_url = base_url
        
        # 如果没有指定模型，使用该供应商的默认模型
        if not self.model:
            self.model = PROVIDER_MODELS.get(self.provider_name, [''])[0]
        
        # 初始化供应商实例
        self.provider = self._create_provider()
    
    def _get_env_api_key(self, provider: str) -> str:
        """从环境变量获取 API Key"""
        env_keys = {
            'anthropic': 'ANTHROPIC_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'groq': 'GROQ_API_KEY',
            'gemini': 'GEMINI_API_KEY',
            'openrouter': 'OPENROUTER_API_KEY',
            'nvidia': 'NVIDIA_NIM_API_KEY',
            'ollama': 'ollama'  # Ollama 不需要 API Key
        }
        
        env_name = env_keys.get(provider, '')
        if env_name and env_name != 'ollama':
            return os.getenv(env_name, '')
        return ''
    
    def _get_api_key(self, provider: str, config) -> str:
        """从 config 对象获取 API Key"""
        key_mapping = {
            'anthropic': getattr(config, 'anthropic_api_key', ''),
            'openai': getattr(config, 'openai_api_key', ''),
            'groq': getattr(config, 'groq_api_key', ''),
            'gemini': getattr(config, 'gemini_api_key', ''),
            'openrouter': getattr(config, 'openrouter_api_key', ''),
            'nvidia': getattr(config, 'nvidia_api_key', ''),
            'ollama': 'ollama'
        }
        return key_mapping.get(provider, '')
    
    def _get_base_url(self, provider: str, config) -> str:
        """获取基础 URL"""
        if provider in PROVIDER_BASE_URLS:
            return PROVIDER_BASE_URLS[provider]
        
        # 检查 config 中是否有自定义 URL
        url_mapping = {
            'openrouter': getattr(config, 'openrouter_base_url', None),
            'nvidia': getattr(config, 'nvidia_base_url', None),
            'ollama': getattr(config, 'ollama_base_url', 'http://localhost:11434/v1')
        }
        
        return url_mapping.get(provider, None) or PROVIDER_BASE_URLS.get(provider, None)
    
    def _create_provider(self) -> LLMProvider:
        """创建供应商实例"""
        if self.provider_name == 'anthropic':
            return AnthropicProvider(self.api_key)
        elif self.provider_name == 'openai':
            return OpenAICompatibleProvider(self.api_key, 'https://api.openai.com/v1', self.model or 'gpt-4o')
        elif self.provider_name == 'groq':
            return GroqProvider(self.api_key)
        elif self.provider_name == 'gemini':
            return GeminiProvider(self.api_key)
        elif self.provider_name == 'openrouter':
            return OpenAICompatibleProvider(
                self.api_key,
                self.base_url or PROVIDER_BASE_URLS['openrouter'],
                self.model or 'anthropic/claude-3.5-sonnet'
            )
        elif self.provider_name == 'nvidia':
            return OpenAICompatibleProvider(
                self.api_key,
                self.base_url or PROVIDER_BASE_URLS['nvidia'],
                self.model or 'meta/llama-3.1-405b-instruct'
            )
        elif self.provider_name == 'ollama':
            return OpenAICompatibleProvider(
                'ollama',  # Ollama 不需要 API Key
                self.base_url or 'http://localhost:11434/v1',
                self.model or 'llama3.2'
            )
        else:
            raise ValueError(f"不支持的 LLM 供应商：{self.provider_name}")
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数 (model, temperature, max_tokens 等)
        
        Returns:
            str: 回复内容
        """
        if 'model' not in kwargs:
            kwargs['model'] = self.model
        
        return await self.provider.chat(messages, **kwargs)
    
    async def generate_json(self, messages: List[Dict], **kwargs) -> Dict:
        """
        生成 JSON 格式回复
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
        
        Returns:
            Dict: 解析后的 JSON 对象
        """
        if 'model' not in kwargs:
            kwargs['model'] = self.model
        
        return await self.provider.generate_json(messages, **kwargs)
    
    def switch_provider(self, provider: str, api_key: str = None, model: str = None):
        """
        动态切换供应商
        
        Args:
            provider: 新的供应商名称
            api_key: 新的 API Key (可选)
            model: 新的模型 (可选)
        """
        self.provider_name = provider
        if api_key:
            self.api_key = api_key
        if model:
            self.model = model
        
        self.provider = self._create_provider()
    
    def get_current_provider(self) -> str:
        """获取当前供应商"""
        return self.provider_name
    
    def get_available_providers(self) -> List[str]:
        """获取可用供应商列表"""
        return list(PROVIDER_MODELS.keys())
    
    def get_available_models(self, provider: str = None) -> List[str]:
        """
        获取可用模型列表
        
        Args:
            provider: 供应商名称 (可选，默认当前供应商)
        """
        if provider:
            return PROVIDER_MODELS.get(provider, [])
        return PROVIDER_MODELS.get(self.provider_name, [])


# ============ 全局实例 ============
_default_router: Optional[LLMRouter] = None


def get_llm_router(config=None, provider: str = None, api_key: str = None, 
                   model: str = None) -> LLMRouter:
    """
    获取 LLM 路由器实例
    
    Args:
        config: 配置对象
        provider: 供应商名称
        api_key: API Key
        model: 模型名称
    
    Returns:
        LLMRouter: LLM 路由器实例
    """
    global _default_router
    
    if config or provider:
        return LLMRouter(config, provider, api_key, model)
    
    if _default_router is None:
        from modules.config import config as cfg
        _default_router = LLMRouter(cfg)
    
    return _default_router


def switch_llm_provider(provider: str, api_key: str = None, model: str = None) -> LLMRouter:
    """
    切换 LLM 供应商（用于 /llm 指令）
    
    Args:
        provider: 供应商名称
        api_key: API Key (可选)
        model: 模型 (可选)
    
    Returns:
        LLMRouter: 更新后的路由器
    """
    global _default_router
    
    if _default_router is None:
        _default_router = LLMRouter(provider=provider, api_key=api_key, model=model)
    else:
        _default_router.switch_provider(provider, api_key, model)
    
    return _default_router


# 便捷函数
async def chat(messages: List[Dict], **kwargs) -> str:
    """便捷聊天函数"""
    router = get_llm_router()
    return await router.chat(messages, **kwargs)


async def generate_json(messages: List[Dict], **kwargs) -> Dict:
    """便捷 JSON 生成函数"""
    router = get_llm_router()
    return await router.generate_json(messages, **kwargs)
