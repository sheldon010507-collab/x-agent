"""
config_validator.py - 配置验证模块

功能：
- 启动时检查.env 必填项
- 检查 OpenClaw daemon 连接
- 检查 Supabase 连接
- 检查 LLM API Key 有效性
- 提供配置状态报告
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, env_path: str = None):
        """
        初始化验证器
        
        Args:
            env_path: .env 文件路径，默认为项目根目录
        """
        if env_path is None:
            env_path = Path(__file__).parent.parent / '.env'
        self.env_path = Path(env_path)
        
        # 必填配置项
        self.required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'SUPABASE_URL',
            'SUPABASE_KEY',
        ]
        
        # 可选但推荐的配置项
        self.recommended_vars = [
            'ANTHROPIC_API_KEY',
            'OPENAI_API_KEY',
            'GROQ_API_KEY',
            'GEMINI_API_KEY',
            'OPENROUTER_API_KEY',
            'NVIDIA_NIM_API_KEY',
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET',
        ]
        
        # 验证结果
        self.validation_results: Dict[str, bool] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_env_file(self) -> bool:
        """
        验证 .env 文件是否存在且包含必要配置
        
        Returns:
            bool: 是否通过验证
        """
        logger.info("[ConfigValidator] 开始验证 .env 文件")
        
        # 检查 .env 文件是否存在
        if not self.env_path.exists():
            error_msg = f".env 文件不存在：{self.env_path}"
            logger.error(f"[ConfigValidator] {error_msg}")
            self.errors.append(error_msg)
            return False
        
        # 加载 .env 文件
        load_dotenv(self.env_path)
        
        all_passed = True
        
        # 检查必填项
        for var in self.required_vars:
            value = os.getenv(var)
            if value and value.strip():
                self.validation_results[var] = True
                logger.debug(f"[ConfigValidator] ✓ {var} 已配置")
            else:
                self.validation_results[var] = False
                error_msg = f"缺少必要配置：{var}"
                self.errors.append(error_msg)
                logger.error(f"[ConfigValidator] {error_msg}")
                all_passed = False
        
        # 检查推荐项
        for var in self.recommended_vars:
            value = os.getenv(var)
            if value and value.strip():
                self.validation_results[var] = True
                logger.debug(f"[ConfigValidator] ✓ {var} 已配置")
            else:
                self.validation_results[var] = False
                # 不加入错误，只记录警告
                self.warnings.append(f"未配置推荐项：{var}")
                logger.warning(f"[ConfigValidator] 未配置推荐项：{var}")
        
        logger.info(f"[ConfigValidator] .env 验证完成：{'通过' if all_passed else '失败'}")
        return all_passed
    
    async def validate_supabase_connection(self) -> bool:
        """
        验证 Supabase 连接
        
        Returns:
            bool: 连接是否成功
        """
        logger.info("[ConfigValidator] 验证 Supabase 连接")
        
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                logger.warning("[ConfigValidator] Supabase 配置缺失，跳过连接测试")
                return False
            
            # 尝试连接
            from supabase import create_client
            client = create_client(supabase_url, supabase_key)
            
            # 简单查询测试表是否存在
            result = client.table('trends').select('id').limit(1).execute()
            
            logger.info("[ConfigValidator] ✓ Supabase 连接成功")
            self.validation_results['supabase_connection'] = True
            return True
            
        except Exception as e:
            logger.error(f"[ConfigValidator] ✗ Supabase 连接失败：{e}")
            self.validation_results['supabase_connection'] = False
            self.errors.append(f"Supabase 连接失败：{str(e)}")
            return False
    
    async def validate_openclaw_connection(self) -> bool:
        """
        验证 OpenClaw daemon 连接
        
        Returns:
            bool: 连接是否成功
        """
        logger.info("[ConfigValidator] 验证 OpenClaw 连接")
        
        try:
            from .openclaw_bridge import create_openclaw_bridge
            api_endpoint = os.getenv('OPENCLAW_API_ENDPOINT', 'http://localhost:8080')
            bridge = await create_openclaw_bridge(api_endpoint)
            
            logger.info(f"[ConfigValidator] ✓ OpenClaw 桥接器初始化成功 (端点：{api_endpoint})")
            self.validation_results['openclaw_connection'] = True
            return True
            
        except Exception as e:
            logger.warning(f"[ConfigValidator] OpenClaw 连接失败（可选组件）: {e}")
            self.validation_results['openclaw_connection'] = False
            self.warnings.append(f"OpenClaw 连接失败：{str(e)}")
            return False
    
    async def validate_llm_provider(self, provider: str = None) -> bool:
        """
        验证 LLM 供应商配置
        
        Returns:
            bool: 是否有至少一个可用的 LLM 供应商
        """
        logger.info("[ConfigValidator] 验证 LLM 供应商")
        
        try:
            config_vars = {
                'anthropic': 'ANTHROPIC_API_KEY',
                'openai': 'OPENAI_API_KEY',
                'groq': 'GROQ_API_KEY',
                'gemini': 'GEMINI_API_KEY',
                'openrouter': 'OPENROUTER_API_KEY',
                'nvidia': 'NVIDIA_NIM_API_KEY',
            }
            
            available_providers = []
            for prov, env_var in config_vars.items():
                api_key = os.getenv(env_var)
                if api_key and api_key.strip():
                    available_providers.append(prov)
            
            # 检查 Ollama（本地部署，无需 API Key）
            ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            available_providers.append('ollama')
            
            if available_providers:
                logger.info(f"[ConfigValidator] ✓ 可用 LLM 供应商：{', '.join(available_providers)}")
                self.validation_results['llm_provider'] = True
                return True
            else:
                logger.error("[ConfigValidator] ✗ 无可用的 LLM 供应商")
                self.errors.append("未配置任何 LLM 供应商的 API Key")
                self.validation_results['llm_provider'] = False
                return False
                
        except Exception as e:
            logger.error(f"[ConfigValidator] LLM 验证失败：{e}")
            self.validation_results['llm_provider'] = False
            self.errors.append(f"LLM 验证失败：{str(e)}")
            return False
    
    async def validate_all(self) -> Dict:
        """
        执行所有验证
        
        Returns:
            Dict: 验证结果报告
        """
        logger.info("[ConfigValidator] 开始全面配置验证")
        
        report = {
            'env_valid': False,
            'supabase_valid': False,
            'openclaw_valid': False,
            'llm_valid': False,
            'all_passed': False,
            'errors': [],
            'warnings': [],
            'summary': ''
        }
        
        # 1. 验证 .env 文件
        report['env_valid'] = self.validate_env_file()
        
        # 2. 如果 .env 验证通过，继续验证连接
        if report['env_valid']:
            # 验证 Supabase
            report['supabase_valid'] = await self.validate_supabase_connection()
            
            # 验证 OpenClaw（可选）
            report['openclaw_valid'] = await self.validate_openclaw_connection()
            
            # 验证 LLM
            report['llm_valid'] = await self.validate_llm_provider()
        
        # 汇总错误和警告
        report['errors'] = self.errors
        report['warnings'] = self.warnings
        
        # 判断是否全部通过
        critical_passed = (
            report['env_valid'] and
            report['supabase_valid'] and
            report['llm_valid']
        )
        report['all_passed'] = critical_passed
        
        # 生成摘要
        if report['all_passed']:
            report['summary'] = "✅ 所有关键配置验证通过"
        else:
            failed = []
            if not report['env_valid']:
                failed.append(".env 配置")
            if not report['supabase_valid']:
                failed.append("Supabase 连接")
            if not report['llm_valid']:
                failed.append("LLM 供应商")
            report['summary'] = f"❌ 验证失败：{', '.join(failed)}"
        
        logger.info(f"[ConfigValidator] 验证完成：{report['summary']}")
        return report
    
    def get_validation_status(self) -> str:
        """
        获取验证状态文本
        
        Returns:
            str: 状态文本
        """
        status_lines = []
        
        # .env 状态
        if self.validation_results.get('env_valid', False):
            status_lines.append("✅ .env 配置完整")
        else:
            status_lines.append("❌ .env 配置缺失")
        
        # Supabase 状态
        if self.validation_results.get('supabase_connection', False):
            status_lines.append("✅ Supabase 连接正常")
        elif 'supabase_connection' in self.validation_results:
            status_lines.append("❌ Supabase 连接失败")
        
        # OpenClaw 状态
        if self.validation_results.get('openclaw_connection', False):
            status_lines.append("✅ OpenClaw 已连接")
        elif 'openclaw_connection' in self.validation_results:
            status_lines.append("⚠️ OpenClaw 未连接（可选）")
        
        # LLM 状态
        if self.validation_results.get('llm_provider', False):
            status_lines.append("✅ LLM 供应商可用")
        elif 'llm_provider' in self.validation_results:
            status_lines.append("❌ 无可用 LLM 供应商")
        
        return "\n".join(status_lines)


# ============ 便捷函数 ============

async def validate_config(env_path: str = None) -> Dict:
    """
    便捷函数：验证配置
    
    Args:
        env_path: .env 文件路径
        
    Returns:
        Dict: 验证结果
    """
    validator = ConfigValidator(env_path)
    return await validator.validate_all()


async def check_and_report(env_path: str = None) -> Tuple[bool, str]:
    """
    检查配置并生成报告
    
    Args:
        env_path: .env 文件路径
        
    Returns:
        Tuple[bool, str]: (是否通过，报告文本)
    """
    validator = ConfigValidator(env_path)
    report = await validator.validate_all()
    status_text = validator.get_validation_status()
    return report['all_passed'], status_text


def validate_env_only(env_path: str = None) -> bool:
    """
    仅验证 .env 文件（同步版本）
    
    Args:
        env_path: .env 文件路径
        
    Returns:
        bool: 是否通过验证
    """
    validator = ConfigValidator(env_path)
    return validator.validate_env_file()
