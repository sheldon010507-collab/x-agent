"""
config.py - X-Agent Skill 配置模块（精简版）

只保留 LLM 和 Niche 相关配置，去掉 Telegram/Supabase/Playwright
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

try:
    from dotenv import load_dotenv

    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


@dataclass
class LLMConfig:
    """LLM 供应商配置"""

    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"

    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    nvidia_nim_api_key: Optional[str] = None

    # Base URLs
    ollama_base_url: str = "http://localhost:11434"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    nvidia_nim_base_url: str = "https://integrate.api.nvidia.com/v1"

    def get_api_key(self, provider: str = None) -> Optional[str]:
        if provider is None:
            provider = self.provider
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
        if provider is None:
            provider = self.provider
        urls = {
            "openrouter": self.openrouter_base_url,
            "nvidia": self.nvidia_nim_base_url,
            "ollama": self.ollama_base_url,
        }
        return urls.get(provider, "")

    def get_available_providers(self) -> list:
        providers = []
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.openai_api_key:
            providers.append("openai")
        if self.groq_api_key:
            providers.append("groq")
        if self.gemini_api_key:
            providers.append("gemini")
        if self.openrouter_api_key:
            providers.append("openrouter")
        if self.nvidia_nim_api_key:
            providers.append("nvidia")
        providers.append("ollama")
        return providers


AVAILABLE_NICHES = {
    "adult": "成人用品",
    "ai_tools": "AI 工具",
    "beauty": "美妆",
    "fitness": "健身",
    "crypto": "加密货币",
    "humor": "搞笑",
    "general": "通用",
    "custom": "自定义",
}


class Config:
    """X-Agent Skill 配置"""

    def __init__(self, env_path: str = None):
        if HAS_DOTENV:
            if env_path:
                load_dotenv(Path(env_path))
            else:
                load_dotenv()

        self.llm = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "anthropic"),
            model=os.getenv("LLM_MODEL", "claude-sonnet-4-20250514"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            nvidia_nim_api_key=os.getenv("NVIDIA_NIM_API_KEY"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            openrouter_base_url=os.getenv(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
            nvidia_nim_base_url=os.getenv(
                "NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"
            ),
        )

        self.niche: str = os.getenv("X_AGENT_NICHE", "general")

        # Reddit 配置（可选）
        self.reddit_client_id: Optional[str] = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret: Optional[str] = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent: str = os.getenv("REDDIT_USER_AGENT", "x-agent/3.0")

        # 数据目录
        self.data_dir = Path(
            os.getenv("X_AGENT_DATA_DIR", str(Path.home() / ".x-agent" / "data"))
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def set_niche(self, niche: str) -> bool:
        if niche in AVAILABLE_NICHES:
            self.niche = niche
            return True
        return False

    def get_status(self) -> Dict:
        return {
            "llm_provider": self.llm.provider,
            "llm_model": self.llm.model,
            "available_providers": self.llm.get_available_providers(),
            "niche": self.niche,
            "data_dir": str(self.data_dir),
            "reddit_configured": bool(self.reddit_client_id),
        }
