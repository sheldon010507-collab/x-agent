"""
X-Agent v3 - 模块包
延迟导入，避免依赖问题
"""

__all__ = [
    # Database
    'Database',
    'init_database',
    'get_database',
    'database_exists',
    
    # LLM Router
    'LLMRouter',
    'get_llm_router',
    'switch_llm_provider',
    
    # Scorer
    'TrendScorer',
    'calculate_trend_score',
    'batch_calculate_scores',
    
    # Generator
    'ContentGenerator',
    'generate_content',
]

# 延迟导入
def __getattr__(name):
    if name in ['Database', 'init_database', 'get_database', 'database_exists']:
        from .database import Database, init_database, get_database, database_exists
        if name == 'Database':
            return Database
        elif name == 'init_database':
            return init_database
        elif name == 'get_database':
            return get_database
        elif name == 'database_exists':
            return database_exists
    elif name in ['LLMRouter', 'get_llm_router', 'switch_llm_provider']:
        from .llm_router import LLMRouter, get_llm_router, switch_llm_provider
        if name == 'LLMRouter':
            return LLMRouter
        elif name == 'get_llm_router':
            return get_llm_router
        elif name == 'switch_llm_provider':
            return switch_llm_provider
    elif name in ['TrendScorer', 'calculate_trend_score', 'batch_calculate_scores']:
        from .scorer import TrendScorer, calculate_trend_score, batch_calculate_scores
        if name == 'TrendScorer':
            return TrendScorer
        elif name == 'calculate_trend_score':
            return calculate_trend_score
        elif name == 'batch_calculate_scores':
            return batch_calculate_scores
    elif name in ['ContentGenerator', 'generate_content']:
        from .generator import ContentGenerator, generate_content
        if name == 'ContentGenerator':
            return ContentGenerator
        elif name == 'generate_content':
            return generate_content
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
