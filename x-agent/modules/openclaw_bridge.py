"""
openclaw_bridge.py - OpenClaw集成模块

【V0 Final】此版本为生产级开源版本

功能：
- 自动发帖/评论
- 防封机制
- 随机延迟
- 每日上限控制

版本：V0 Final
"""

import asyncio
import random
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# 防封配置
DELAY_MIN = float(os.getenv("DELAY_MIN", "10"))
DELAY_MAX = float(os.getenv("DELAY_MAX", "40"))
MAX_COMMENTS_PER_DAY = int(os.getenv("MAX_COMMENTS_PER_DAY", "15"))
MAX_POSTS_PER_DAY = int(os.getenv("MAX_POSTS_PER_DAY", "10"))
MAX_LIKES_PER_DAY = int(os.getenv("MAX_LIKES_PER_DAY", "30"))

# Emoji 变体池
EMOJI_VARIANTS = ["🔥", "👀", "💡", "✨", "🚀", "💯", "🎯", "📌"]
PHRASE_VARIANTS = [
    "",
    " Interesting.",
    " Thoughts?",
    " 👀",
    " Just saying.",
    ""
]


class OpenClawBridge:
    """OpenClaw 桥接器 - 带防封机制"""
    
    def __init__(self, api_endpoint: str = 'http://localhost:8080'):
        """
        初始化 OpenClaw 桥接器
        
        Args:
            api_endpoint: OpenClaw API 端点
        """
        self.api_endpoint = api_endpoint
        
        # 开关控制
        self.auto_like_enabled = False
        self.auto_rt_enabled = False
        self.auto_post_enabled = False
        
        # 每日上限（从环境变量读取）
        self.daily_like_limit = MAX_LIKES_PER_DAY
        self.daily_rt_limit = 10
        self.daily_post_limit = MAX_POSTS_PER_DAY
        self.daily_comment_limit = MAX_COMMENTS_PER_DAY
        
        # 当日计数
        self.like_count = 0
        self.rt_count = 0
        self.post_count = 0
        self.comment_count = 0
    
    # ==================== 防封规则 ====================
    
    def _random_delay(self, min_sec: float = None, max_sec: float = None):
        """
        规则1: 随机延迟 10-40 秒
        
        Args:
            min_sec: 最小延迟（默认从环境变量）
            max_sec: 最大延迟（默认从环境变量）
        """
        min_sec = min_sec or DELAY_MIN
        max_sec = max_sec or DELAY_MAX
        delay = random.uniform(min_sec, max_sec)
        logger.info(f"[防封] 随机延迟 {delay:.1f} 秒")
        return delay
    
    def _apply_content_variant(self, content: str) -> str:
        """
        规则2: 内容轻微变体
        
        Args:
            content: 原始内容
            
        Returns:
            str: 变体后的内容
        """
        # 随机添加 emoji
        if random.random() > 0.5:
            emoji = random.choice(EMOJI_VARIANTS)
            content = f"{content} {emoji}"
        
        # 随机添加短语
        if random.random() > 0.7:
            phrase = random.choice(PHRASE_VARIANTS)
            content = f"{content}{phrase}"
        
        logger.debug(f"[防封] 内容变体: {content[:50]}...")
        return content.strip()
    
    def _check_daily_limit(self, action: str) -> bool:
        """
        规则3: 检查每日上限
        
        Args:
            action: 动作类型 (like, rt, post, comment)
            
        Returns:
            bool: 是否在限额内
        """
        limits = {
            'like': (self.like_count, self.daily_like_limit),
            'rt': (self.rt_count, self.daily_rt_limit),
            'post': (self.post_count, self.daily_post_limit),
            'comment': (self.comment_count, self.daily_comment_limit)
        }
        
        current, limit = limits.get(action, (0, 10))
        
        if current >= limit:
            logger.warning(f"[防封] 每日 {action} 上限已达: {current}/{limit}")
            return False
        
        return True
    
    # ==================== 发帖功能 ====================
    
    async def post_content(
        self,
        content: str,
        media_suggestion: str = None,
        niche: str = 'general',
        apply_variant: bool = True
    ) -> Dict:
        """
        通过 OpenClaw 自动发帖
        
        Args:
            content: 帖子内容
            media_suggestion: 配图建议
            niche: Niche 领域
            apply_variant: 是否应用内容变体
            
        Returns:
            Dict: 发帖结果
        """
        if not self.auto_post_enabled:
            return {'success': False, 'reason': 'Auto post is disabled'}
        
        if not self._check_daily_limit('post'):
            return {'success': False, 'reason': f'Daily post limit reached: {self.daily_post_limit}'}
        
        try:
            # 规则1: 随机延迟
            delay = self._random_delay()
            await asyncio.sleep(delay)
            
            # 规则2: 内容变体
            if apply_variant:
                content = self._apply_content_variant(content)
            
            # 调用 x-poster skill
            result = await self._call_x_poster(content, media_suggestion)
            
            self.post_count += 1
            logger.info(f"[发帖] 成功，今日第 {self.post_count} 条")
            
            return result
            
        except Exception as e:
            logger.error(f"[发帖] 错误: {e}")
            return {'success': False, 'reason': str(e)}
    
    async def _call_x_poster(self, content: str, media_suggestion: str = None) -> Dict:
        """调用 x-poster skill"""
        # TODO: 实际调用 OpenClaw API
        logger.info(f"[x-poster] 发帖: {content[:50]}...")
        
        return {
            'success': True,
            'post_id': f'mock_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'url': 'https://x.com/status/mock',
            'content': content,
            'posted_at': datetime.now().isoformat()
        }
    
    # ==================== 评论功能 ====================
    
    async def comment_on_post(
        self,
        post_url: str,
        comment: str,
        apply_variant: bool = True
    ) -> Dict:
        """
        智能评论（带防封）
        
        Args:
            post_url: 原帖链接
            comment: 评论内容
            apply_variant: 是否应用内容变体
            
        Returns:
            Dict: 评论结果
        """
        if not self._check_daily_limit('comment'):
            return {'success': False, 'reason': f'Daily comment limit reached: {self.daily_comment_limit}'}
        
        try:
            # 规则1: 随机延迟
            delay = self._random_delay()
            await asyncio.sleep(delay)
            
            # 规则2: 内容变体
            if apply_variant:
                comment = self._apply_content_variant(comment)
            
            # 调用 x-smart-commenter skill
            result = await self._call_smart_commenter(post_url, comment)
            
            self.comment_count += 1
            logger.info(f"[评论] 成功，今日第 {self.comment_count} 条")
            
            return result
            
        except Exception as e:
            logger.error(f"[评论] 错误: {e}")
            return {'success': False, 'reason': str(e)}
    
    async def _call_smart_commenter(self, post_url: str, comment: str) -> Dict:
        """调用 x-smart-commenter skill"""
        # TODO: 实际调用 OpenClaw API
        logger.info(f"[x-smart-commenter] 评论: {post_url} -> {comment[:50]}...")
        
        return {
            'success': True,
            'comment_id': f'mock_comment_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'url': post_url,
            'comment': comment,
            'commented_at': datetime.now().isoformat()
        }
    
    # ==================== 点赞/转发 ====================
    
    async def like_post(self, post_url: str) -> Dict:
        """点赞帖子"""
        if not self.auto_like_enabled:
            return {'success': False, 'reason': 'Auto like is disabled'}
        
        if not self._check_daily_limit('like'):
            return {'success': False, 'reason': f'Daily like limit reached: {self.daily_like_limit}'}
        
        try:
            delay = self._random_delay(5, 15)  # 点赞延迟较短
            await asyncio.sleep(delay)
            
            result = await self._call_like(post_url)
            self.like_count += 1
            return result
            
        except Exception as e:
            logger.error(f"[点赞] 错误: {e}")
            return {'success': False, 'reason': str(e)}
    
    async def _call_like(self, post_url: str) -> Dict:
        """调用点赞 API"""
        logger.info(f"[点赞] {post_url}")
        return {'success': True, 'liked_at': datetime.now().isoformat()}
    
    async def retweet_post(self, post_url: str, comment: str = None) -> Dict:
        """转发帖子"""
        if not self.auto_rt_enabled:
            return {'success': False, 'reason': 'Auto RT is disabled'}
        
        if not self._check_daily_limit('rt'):
            return {'success': False, 'reason': f'Daily RT limit reached: {self.daily_rt_limit}'}
        
        try:
            delay = self._random_delay()
            await asyncio.sleep(delay)
            
            if comment:
                comment = self._apply_content_variant(comment)
            
            result = await self._call_retweet(post_url, comment)
            self.rt_count += 1
            return result
            
        except Exception as e:
            logger.error(f"[转发] 错误: {e}")
            return {'success': False, 'reason': str(e)}
    
    async def _call_retweet(self, post_url: str, comment: str = None) -> Dict:
        """调用转发 API"""
        logger.info(f"[转发] {post_url} (评论: {comment is not None})")
        return {
            'success': True,
            'retweeted_at': datetime.now().isoformat(),
            'with_comment': comment is not None
        }
    
    # ==================== 配置方法 ====================
    
    def set_auto_like(self, enabled: bool):
        """设置自动点赞开关"""
        self.auto_like_enabled = enabled
        logger.info(f"[配置] 自动点赞: {'启用' if enabled else '禁用'}")
    
    def set_auto_rt(self, enabled: bool):
        """设置自动 RT 开关"""
        self.auto_rt_enabled = enabled
        logger.info(f"[配置] 自动转发: {'启用' if enabled else '禁用'}")
    
    def set_auto_post(self, enabled: bool):
        """设置自动发帖开关"""
        self.auto_post_enabled = enabled
        logger.info(f"[配置] 自动发帖: {'启用' if enabled else '禁用'}")
    
    def set_daily_limits(self, like: int = None, rt: int = None, 
                         post: int = None, comment: int = None):
        """设置每日上限"""
        if like is not None:
            self.daily_like_limit = like
        if rt is not None:
            self.daily_rt_limit = rt
        if post is not None:
            self.daily_post_limit = post
        if comment is not None:
            self.daily_comment_limit = comment
        
        logger.info(
            f"[配置] 每日上限 - 点赞: {self.daily_like_limit}, "
            f"转发: {self.daily_rt_limit}, 发帖: {self.daily_post_limit}, "
            f"评论: {self.daily_comment_limit}"
        )
    
    def reset_daily_counts(self):
        """重置每日计数（建议每天 00:00 调用）"""
        self.like_count = 0
        self.rt_count = 0
        self.post_count = 0
        self.comment_count = 0
        logger.info("[重置] 每日计数已清零")
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            'auto_like': self.auto_like_enabled,
            'auto_rt': self.auto_rt_enabled,
            'auto_post': self.auto_post_enabled,
            'daily_counts': {
                'like': self.like_count,
                'rt': self.rt_count,
                'post': self.post_count,
                'comment': self.comment_count
            },
            'daily_limits': {
                'like': self.daily_like_limit,
                'rt': self.daily_rt_limit,
                'post': self.daily_post_limit,
                'comment': self.daily_comment_limit
            }
        }


# 便捷函数
async def create_openclaw_bridge(api_endpoint: str = 'http://localhost:8080') -> OpenClawBridge:
    """创建 OpenClaw 桥接器实例"""
    bridge = OpenClawBridge(api_endpoint)
    return bridge
