"""
config.py - X-Agent v3 配置管理模块

功能：
- 从 .env 文件加载配置
- 支持多 LLM 供应商配置
- 支持 Niche 配置
- 支持自动化参数配置
- 配置验证
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """LLM 供应商配置"""
    provider: str = 'anthropic'
    model: str = 'claude-3-5-sonnet-20241022'
    
    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    nvidia_nim_api_key: Optional[str] = None
    
    # Base URLs
    ollama_base_url: str = 'http://localhost:11434'
    openrouter_base_url: str = 'https://openrouter.ai/api/v1'
    nvidia_nim_base_url: str = 'https://integrate.api.nvidia.com/v1'
    
    def get_api_key(self, provider: str = None) -> Optional[str]:
        """获取指定供应商的 API Key"""
        if provider is None:
            provider = self.provider
        
        key_map = {
            'anthropic': self.anthropic_api_key,
            'openai': self.openai_api_key,
            'groq': self.groq_api_key,
            'gemini': self.gemini_api_key,
            'openrouter': self.openrouter_api_key,
            'nvidia': self.nvidia_nim_api_key,
        }
        return key_map.get(provider)
    
    def get_base_url(self, provider: str = None) -> str:
        """获取指定供应商的基础 URL"""
        if provider is None:
            provider = self.provider
        
        if provider == 'openrouter':
            return self.openrouter_base_url
        elif provider == 'nvidia':
            return self.nvidia_nim_base_url
        elif provider == 'ollama':
            return self.ollama_base_url
        else:
            return ''
    
    def get_available_providers(self) -> list:
        """返回已配置 API Key 的供应商列表"""
        providers = []
        if self.anthropic_api_key:
            providers.append('anthropic')
        if self.openai_api_key:
            providers.append('openai')
        if self.groq_api_key:
            providers.append('groq')
        if self.gemini_api_key:
            providers.append('gemini')
        if self.openrouter_api_key:
            providers.append('openrouter')
        if self.nvidia_nim_api_key:
            providers.append('nvidia')
        # Ollama 本地部署，始终可用
        providers.append('ollama')
        return providers
    
    def set_provider(self, provider: str) -> bool:
        """切换 LLM 供应商"""
        valid_providers = ['anthropic', 'openai', 'groq', 'gemini', 'openrouter', 'nvidia', 'ollama']
        if provider in valid_providers:
            self.provider = provider
            return True
        return False


@dataclass
class AutomationConfig:
    """自动化配置"""
    # 智能评论
    auto_comment_enabled: bool = True
    auto_comment_limit: int = 15
    
    # 自动点赞
    auto_like_enabled: bool = False
    auto_like_limit: int = 30
    
    # 自动转发
    auto_rt_enabled: bool = False
    auto_rt_limit: int = 10
    
    # 自动发帖
    auto_post_enabled: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'auto_comment_enabled': self.auto_comment_enabled,
            'auto_comment_limit': self.auto_comment_limit,
            'auto_like_enabled': self.auto_like_enabled,
            'auto_like_limit': self.auto_like_limit,
            'auto_rt_enabled': self.auto_rt_enabled,
            'auto_rt_limit': self.auto_rt_limit,
            'auto_post_enabled': self.auto_post_enabled,
        }


@dataclass
class NicheConfig:
    """Niche 配置"""
    current_niche: str = 'general'
    
    # 内置 Niche 列表
    AVAILABLE_NICHES = {
        'adult': '成人用品',
        'ai_tools': 'AI 工具',
        'beauty': '美妆',
        'fitness': '健身',
        'crypto': '加密货币',
        'humor': '搞笑',
        'general': '通用',
        'custom': '自定义',
    }
    
    def get_niche_name(self, niche_id: str) -> str:
        """获取 Niche 显示名称"""
        return self.AVAILABLE_NICHES.get(niche_id, niche_id)
    
    def get_available_niches(self) -> list:
        """获取所有可用的 Niche 列表"""
        return [(k, v) for k, v in self.AVAILABLE_NICHES.items()]
    
    def set_niche(self, niche: str) -> bool:
        """切换 Niche"""
        if niche in self.AVAILABLE_NICHES:
            self.current_niche = niche
            return True
        return False


class Config:
    """主配置类"""
    
    def __init__(self, env_path: str = None):
        """
        初始化配置
        
        Args:
            env_path: .env 文件路径，默认为当前目录的 .env
        """
        # 加载 .env 文件
        if env_path is None:
            env_path = Path(__file__).parent / '.env'
        else:
            env_path = Path(env_path)
        
        if env_path.exists():
            load_dotenv(env_path)
        
        # Telegram 配置
        self.telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id: str = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # LLM 配置
        self.llm = LLMConfig(
            provider=os.getenv('LLM_PROVIDER', 'anthropic'),
            model=os.getenv('LLM_MODEL', 'claude-3-5-sonnet-20241022'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            groq_api_key=os.getenv('GROQ_API_KEY'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            openrouter_api_key=os.getenv('OPENROUTER_API_KEY'),
            nvidia_nim_api_key=os.getenv('NVIDIA_NIM_API_KEY'),
            ollama_base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            openrouter_base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1'),
            nvidia_nim_base_url=os.getenv('NVIDIA_NIM_BASE_URL', 'https://integrate.api.nvidia.com/v1'),
        )
        
        # Niche 配置
        self.niche = NicheConfig()
        
        # 自动化配置
        self.automation = AutomationConfig()
        
        # Supabase 配置
        self.supabase_url: str = os.getenv('SUPABASE_URL', '')
        self.supabase_key: str = os.getenv('SUPABASE_KEY', '')
        
        # Reddit 配置
        self.reddit_client_id: Optional[str] = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_client_secret: Optional[str] = os.getenv('REDDIT_CLIENT_SECRET')
        self.reddit_user_agent: str = os.getenv('REDDIT_USER_AGENT', 'x-agent/3.0')
        
        # OpenClaw 配置
        self.openclaw_api_endpoint: str = os.getenv('OPENCLAW_API_ENDPOINT', 'http://localhost:8080')
        
        # 加密密钥
        self.encryption_key: Optional[str] = os.getenv('ENCRYPTION_KEY')
        
        # 验证配置
        self._validate()
    
    def _validate(self) -> None:
        """验证必要配置是否存在"""
        required = {
            'TELEGRAM_BOT_TOKEN': self.telegram_bot_token,
            'SUPABASE_URL': self.supabase_url,
            'SUPABASE_KEY': self.supabase_key,
        }
        
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"缺少必要配置：{', '.join(missing)}")
        
        # 验证至少有一个 LLM 供应商配置
        if not self.llm.get_available_providers():
            raise ValueError("至少需要配置一个 LLM 供应商的 API Key")
    
    def get_llm_key(self, provider: str = None) -> Optional[str]:
        """获取指定供应商的 API Key"""
        return self.llm.get_api_key(provider)
    
    def get_base_url(self, provider: str = None) -> str:
        """获取指定供应商的基础 URL"""
        return self.llm.get_base_url(provider)
    
    def set_llm_provider(self, provider: str) -> bool:
        """切换 LLM 供应商"""
        return self.llm.set_provider(provider)
    
    def set_niche(self, niche: str) -> bool:
        """切换 Niche"""
        return self.niche.set_niche(niche)
    
    def get_automation_settings(self) -> Dict[str, Any]:
        """获取自动化设置"""
        return self.automation.to_dict()


# 全局配置实例
config = Config()
