"""
database.py - Supabase 数据库操作封装 (v3)
实现 6 张表的完整 CRUD: trends, content_queue, daily_log, strategy, automation_settings, llm_config
"""
from supabase import create_client, Client
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import uuid
import os


class Database:
    """Supabase 数据库操作类"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        初始化数据库连接
        
        Args:
            supabase_url: Supabase URL (可选，默认从环境变量读取)
            supabase_key: Supabase Key (可选，默认从环境变量读取)
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and Key are required")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    # ========== Trends 表操作 ==========
    
    def create_trend(self, niche: str, topic: str, source: str, score: float, 
                     summary: str = None, citations: Dict = None, url: str = None,
                     relevance: float = None, velocity: float = None, 
                     authority: float = None, convergence: float = None) -> Dict:
        """
        创建新的热点记录
        
        Args:
            niche: Niche 领域
            topic: 话题
            source: 来源
            score: 综合评分 (0-100)
            summary: 摘要
            citations: 引用信息
            url: 原始链接
            relevance: 相关性分数 (可选)
            velocity: 增速分数 (可选)
            authority: 权威性分数 (可选)
            convergence: 汇聚性分数 (可选)
        """
        data = {
            'id': str(uuid.uuid4()),
            'niche': niche,
            'topic': topic,
            'source': source,
            'score': score,
            'summary': summary,
            'citations': citations,
            'url': url,
            'relevance': relevance,
            'velocity': velocity,
            'authority': authority,
            'convergence': convergence,
            'status': 'new',
            'created_at': datetime.now().isoformat()
        }
        
        result = self.client.table('trends').insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_trends_by_score(self, min_score: float = 60, limit: int = 20, 
                            niche: str = None) -> List[Dict]:
        """
        获取高于指定分数的热点（按分数降序）
        
        Args:
            min_score: 最低分数
            limit: 返回数量限制
            niche: Niche 过滤 (可选)
        """
        query = self.client.table('trends')\
            .select('*')\
            .gte('score', min_score)\
            .eq('status', 'new')\
            .order('score', desc=True)\
            .limit(limit)
        
        if niche:
            query = query.eq('niche', niche)
        
        result = query.execute()
        return result.data
    
    def get_trend_by_id(self, trend_id: str) -> Optional[Dict]:
        """根据 ID 获取热点"""
        result = self.client.table('trends')\
            .select('*')\
            .eq('id', trend_id)\
            .execute()
        return result.data[0] if result.data else None
    
    def update_trend_status(self, trend_id: str, status: str) -> None:
        """更新热点状态"""
        self.client.table('trends')\
            .update({'status': status, 'updated_at': datetime.now().isoformat()})\
            .eq('id', trend_id)\
            .execute()
    
    def get_high_score_trends(self, min_score: float = 80, niche: str = None) -> List[Dict]:
        """获取高分热点（≥80 分，用于立即推送）"""
        return self.get_trends_by_score(min_score, niche=niche)
    
    def get_medium_score_trends(self, min_score: float = 60, max_score: float = 79.99, 
                                niche: str = None) -> List[Dict]:
        """获取中等分数热点（60-79 分，用于每日汇总）"""
        query = self.client.table('trends')\
            .select('*')\
            .gte('score', min_score)\
            .lt('score', max_score)\
            .eq('status', 'new')\
            .order('score', desc=True)
        
        if niche:
            query = query.eq('niche', niche)
        
        result = query.execute()
        return result.data
    
    def delete_trend(self, trend_id: str) -> None:
        """删除热点记录"""
        self.client.table('trends')\
            .delete()\
            .eq('id', trend_id)\
            .execute()
    
    # ========== Content Queue 表操作 ==========
    
    def create_content(self, trend_id: str, type: str, content: str, 
                       media_suggestion: str = None, status: str = 'draft',
                       niche: str = None) -> Dict:
        """
        创建内容草稿
        
        Args:
            trend_id: 关联的热点 ID
            type: 内容类型 (A/B/C)
            content: 内容文本
            media_suggestion: 配图建议关键词
            status: 状态 (draft/published/discarded)
            niche: Niche 领域
        """
        data = {
            'id': str(uuid.uuid4()),
            'trend_id': trend_id,
            'type': type,
            'content': content,
            'media_suggestion': media_suggestion,
            'status': status,
            'niche': niche,
            'created_at': datetime.now().isoformat()
        }
        
        result = self.client.table('content_queue').insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_content_queue(self, status: str = 'draft', limit: int = 20,
                          niche: str = None, type: str = None) -> List[Dict]:
        """
        获取待发布内容队列
        
        Args:
            status: 状态过滤
            limit: 返回数量限制
            niche: Niche 过滤
            type: 类型过滤 (A/B/C)
        """
        query = self.client.table('content_queue')\
            .select('*')\
            .eq('status', status)\
            .order('created_at', desc=True)\
            .limit(limit)
        
        if niche:
            query = query.eq('niche', niche)
        
        if type:
            query = query.eq('type', type)
        
        result = query.execute()
        return result.data
    
    def update_content_status(self, content_id: str, status: str) -> None:
        """更新内容状态"""
        self.client.table('content_queue')\
            .update({'status': status, 'updated_at': datetime.now().isoformat()})\
            .eq('id', content_id)\
            .execute()
    
    def delete_content(self, content_id: str) -> None:
        """删除内容"""
        self.client.table('content_queue')\
            .delete()\
            .eq('id', content_id)\
            .execute()
    
    # ========== Daily Log 表操作 ==========
    
    def create_daily_log(self, date: date = None, posts_count: int = 0, 
                         comments_count: int = 0, likes_count: int = 0, 
                         rt_count: int = 0, top_engagement: int = 0, 
                         notes: str = None, niche: str = None) -> Dict:
        """创建每日记录"""
        if date is None:
            date = datetime.now().date()
        
        data = {
            'id': str(uuid.uuid4()),
            'date': date.isoformat(),
            'posts_count': posts_count,
            'comments_count': comments_count,
            'likes_count': likes_count,
            'rt_count': rt_count,
            'top_engagement': top_engagement,
            'notes': notes,
            'niche': niche,
            'created_at': datetime.now().isoformat()
        }
        
        result = self.client.table('daily_log').insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_daily_log(self, date: date = None) -> Optional[Dict]:
        """获取指定日期的记录"""
        if date is None:
            date = datetime.now().date()
        
        result = self.client.table('daily_log')\
            .select('*')\
            .eq('date', date.isoformat())\
            .execute()
        return result.data[0] if result.data else None
    
    def update_daily_log(self, date: date = None, **kwargs) -> None:
        """更新每日记录"""
        if date is None:
            date = datetime.now().date()
        
        # 移除只读字段
        kwargs.pop('id', None)
        kwargs.pop('date', None)
        kwargs['updated_at'] = datetime.now().isoformat()
        
        self.client.table('daily_log')\
            .update(kwargs)\
            .eq('date', date.isoformat())\
            .execute()
    
    def get_daily_logs_range(self, start_date: date, end_date: date = None) -> List[Dict]:
        """获取日期范围内的日志"""
        if end_date is None:
            end_date = datetime.now().date()
        
        result = self.client.table('daily_log')\
            .select('*')\
            .gte('date', start_date.isoformat())\
            .lte('date', end_date.isoformat())\
            .order('date', desc=True)\
            .execute()
        return result.data
    
    # ========== Strategy 表操作 ==========
    
    def get_current_strategy(self, niche: str) -> Optional[Dict]:
        """获取当前 Niche 的策略"""
        result = self.client.table('strategy')\
            .select('*')\
            .eq('niche', niche)\
            .order('version', desc=True)\
            .limit(1)\
            .execute()
        return result.data[0] if result.data else None
    
    def create_strategy(self, niche: str, version: int, content: str, 
                        description: str = None) -> Dict:
        """创建新策略版本"""
        data = {
            'id': str(uuid.uuid4()),
            'niche': niche,
            'version': version,
            'content': content,
            'description': description,
            'created_at': datetime.now().isoformat()
        }
        
        result = self.client.table('strategy').insert(data).execute()
        return result.data[0] if result.data else None
    
    def update_strategy(self, niche: str, version: int, **kwargs) -> None:
        """更新策略"""
        # 移除只读字段
        kwargs.pop('id', None)
        kwargs.pop('niche', None)
        kwargs.pop('version', None)
        kwargs['updated_at'] = datetime.now().isoformat()
        
        self.client.table('strategy')\
            .update(kwargs)\
            .eq('niche', niche)\
            .eq('version', version)\
            .execute()
    
    def list_strategies(self, niche: str = None) -> List[Dict]:
        """列出所有策略（可按 Niche 过滤）"""
        query = self.client.table('strategy')\
            .select('*')\
            .order('niche')\
            .order('version', desc=True)
        
        if niche:
            query = query.eq('niche', niche)
        
        result = query.execute()
        return result.data
    
    # ========== Automation Settings 表操作 ==========
    
    def get_automation_settings(self) -> Dict:
        """获取自动化设置"""
        result = self.client.table('automation_settings')\
            .select('*')\
            .order('updated_at', desc=True)\
            .limit(1)\
            .execute()
        
        if result.data:
            return result.data[0]
        
        # 如果不存在，创建默认设置
        return self.create_default_automation_settings()
    
    def create_default_automation_settings(self) -> Dict:
        """创建默认自动化设置"""
        data = {
            'id': str(uuid.uuid4()),
            'auto_comment': True,
            'comment_daily_limit': 15,
            'auto_like': False,
            'auto_rt': False,
            'like_daily_limit': 30,
            'rt_daily_limit': 10,
            'auto_post': False,
            'post_schedule_enabled': False,
            'updated_at': datetime.now().isoformat()
        }
        
        result = self.client.table('automation_settings').insert(data).execute()
        return result.data[0] if result.data else data
    
    def update_automation_settings(self, **kwargs) -> Dict:
        """更新自动化设置"""
        # 获取当前设置
        current = self.get_automation_settings()
        current_id = current.get('id')
        
        # 更新字段
        update_data = {k: v for k, v in kwargs.items() if k not in ['id', 'updated_at']}
        update_data['updated_at'] = datetime.now().isoformat()
        
        self.client.table('automation_settings')\
            .update(update_data)\
            .eq('id', current_id)\
            .execute()
        
        return self.get_automation_settings()
    
    # ========== LLM Config 表操作 ==========
    
    def get_llm_config(self) -> Dict:
        """获取当前 LLM 配置"""
        result = self.client.table('llm_config')\
            .select('*')\
            .eq('is_active', True)\
            .execute()
        
        if result.data:
            return result.data[0]
        
        # 如果不存在，创建默认配置
        return self.create_default_llm_config()
    
    def create_default_llm_config(self) -> Dict:
        """创建默认 LLM 配置"""
        data = {
            'id': str(uuid.uuid4()),
            'provider': 'anthropic',
            'model': 'claude-3-5-sonnet-20241022',
            'is_active': True,
            'temperature': 0.7,
            'max_tokens': 4096,
            'created_at': datetime.now().isoformat()
        }
        
        result = self.client.table('llm_config').insert(data).execute()
        return result.data[0] if result.data else data
    
    def set_llm_config(self, provider: str, model: str = None, 
                       temperature: float = None, max_tokens: int = None) -> Dict:
        """
        设置 LLM 配置
        
        Args:
            provider: LLM 供应商 (anthropic/openai/groq/gemini/openrouter/nvidia/ollama)
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
        """
        # 先停用所有配置
        self.client.table('llm_config')\
            .update({'is_active': False})\
            .execute()
        
        # 构建配置数据
        data = {
            'provider': provider,
            'is_active': True,
            'updated_at': datetime.now().isoformat()
        }
        
        if model:
            data['model'] = model
        
        if temperature is not None:
            data['temperature'] = temperature
        
        if max_tokens is not None:
            data['max_tokens'] = max_tokens
        
        # 检查是否存在该供应商配置
        result = self.client.table('llm_config')\
            .select('id')\
            .eq('provider', provider)\
            .execute()
        
        if result.data:
            # 更新现有配置
            self.client.table('llm_config')\
                .update(data)\
                .eq('provider', provider)\
                .execute()
        else:
            # 插入新配置
            data['id'] = str(uuid.uuid4())
            data['created_at'] = datetime.now().isoformat()
            self.client.table('llm_config').insert(data).execute()
        
        return self.get_llm_config()
    
    def list_llm_configs(self) -> List[Dict]:
        """列出所有 LLM 配置"""
        result = self.client.table('llm_config')\
            .select('*')\
            .order('provider')\
            .execute()
        return result.data
    
    # ========== 统计查询 ==========
    
    def get_today_stats(self, date: date = None, niche: str = None) -> Dict:
        """获取今日统计"""
        if date is None:
            date = datetime.now().date()
        
        date_str = date.isoformat()
        
        # 内容生成统计
        content_query = self.client.table('content_queue')\
            .select('type, status')\
        
        if niche:
            content_query = content_query.eq('niche', niche)
        
        content_result = content_query.execute()
        
        # 热点统计
        trends_query = self.client.table('trends')\
            .select('score, status')
        
        if niche:
            trends_query = trends_query.eq('niche', niche)
        
        trends_result = trends_query.execute()
        
        return {
            'date': date_str,
            'niche': niche,
            'content_generated': len(content_result.data),
            'trends_found': len(trends_result.data),
            'high_score_trends': len([t for t in trends_result.data if t.get('score', 0) >= 80]),
            'medium_score_trends': len([t for t in trends_result.data if 60 <= t.get('score', 0) < 80])
        }
    
    def get_niche_stats(self, niche: str) -> Dict:
        """获取特定 Niche 的统计信息"""
        # 热点统计
        trends_result = self.client.table('trends')\
            .select('score, status')\
            .eq('niche', niche)\
            .execute()
        
        # 内容统计
        content_result = self.client.table('content_queue')\
            .select('type, status')\
            .eq('niche', niche)\
            .execute()
        
        return {
            'niche': niche,
            'total_trends': len(trends_result.data),
            'high_score_trends': len([t for t in trends_result.data if t.get('score', 0) >= 80]),
            'total_content': len(content_result.data),
            'published_content': len([c for c in content_result.data if c.get('status') == 'published'])
        }


# 全局数据库实例（延迟初始化）
_db: Optional[Database] = None


def init_database(supabase_url: str = None, supabase_key: str = None) -> Database:
    """
    初始化数据库连接
    
    Args:
        supabase_url: Supabase URL (可选，默认从环境变量读取)
        supabase_key: Supabase Key (可选，默认从环境变量读取)
    """
    global _db
    _db = Database(supabase_url, supabase_key)
    return _db


def get_database() -> Database:
    """获取数据库实例"""
    if _db is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    return _db


def database_exists() -> bool:
    """检查数据库是否已初始化"""
    return _db is not None
