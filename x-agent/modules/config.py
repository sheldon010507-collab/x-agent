"""
config.py - 配置加载模块
负责从 .env 文件加载配置并验证
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Config:
    """配置加载和验证类"""

    def __init__(self):
        # 加载 .env 文件
        env_path = Path(__file__).parent / ".env"
        load_dotenv(env_path)

        # Telegram
        self.telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

        # LLM 供应商配置
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
        self.llm_model: str = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")

        # LLM API Keys
        self.anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
        self.gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.openrouter_api_key: Optional[str] = os.getenv("OPENROUTER_API_KEY")
        self.nvidia_nim_api_key: Optional[str] = os.getenv("NVIDIA_NIM_API_KEY")
        self.ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # OpenRouter / NVIDIA NIM 基础 URL
        self.openrouter_base_url: str = os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        )
        self.nvidia_nim_base_url: str = os.getenv(
            "NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"
        )

        # Supabase
        self.supabase_url: str = os.getenv("SUPABASE_URL", "")
        self.supabase_key: str = os.getenv("SUPABASE_KEY", "")

        # Reddit
        self.reddit_client_id: Optional[str] = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret: Optional[str] = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent: str = os.getenv("REDDIT_USER_AGENT", "x-agent/2.0")

        # OpenClaw
        self.openclaw_api_endpoint: str = os.getenv(
            "OPENCLAW_API_ENDPOINT", "http://localhost:8080"
        )

        # 加密密钥
        self.encryption_key: Optional[str] = os.getenv("ENCRYPTION_KEY")

        # 验证必要配置
        self._validate()

    def _validate(self) -> None:
        """验证必要配置是否存在"""
        required = {
            "TELEGRAM_BOT_TOKEN": self.telegram_bot_token,
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_KEY": self.supabase_key,
        }

        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"缺少必要配置：{', '.join(missing)}")

        # 验证至少有一个 LLM 供应商配置
        llm_keys = {
            "ANTHROPIC_API_KEY": self.anthropic_api_key,
            "OPENAI_API_KEY": self.openai_api_key,
            "GROQ_API_KEY": self.groq_api_key,
            "GEMINI_API_KEY": self.gemini_api_key,
            "OPENROUTER_API_KEY": self.openrouter_api_key,
            "NVIDIA_NIM_API_KEY": self.nvidia_nim_api_key,
        }

        # 如果默认供应商不可用，检查是否有其他供应商
        default_key = f"{self.llm_provider.upper()}_API_KEY"
        if not llm_keys.get(default_key) and not any(llm_keys.values()):
            raise ValueError("至少需要配置一个 LLM 供应商的 API Key")

    def get_llm_key(self, provider: str = None) -> Optional[str]:
        """获取指定供应商的 API Key"""
        if provider is None:
            provider = self.llm_provider

        key_map = {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "groq": self.groq_api_key,
            "gemini": self.gemini_api_key,
            "openrouter": self.openrouter_api_key,
            "nvidia": self.nvidia_nim_api_key,
        }

        return key_map.get(provider)

    def get_base_url(self, provider: str = None) -> str:
        """获取指定供应商的基础 URL"""
        if provider is None:
            provider = self.llm_provider

        if provider == "openrouter":
            return self.openrouter_base_url
        elif provider == "nvidia":
            return self.nvidia_nim_base_url
        elif provider == "ollama":
            return self.ollama_base_url
        else:
            # 其他供应商使用默认 URL
            return ""


# 全局配置实例
config = Config()
