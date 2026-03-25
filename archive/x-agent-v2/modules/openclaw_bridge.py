"""
openclaw_bridge.py - OpenClaw 集成模块

功能：
- 调用 OpenClaw Skills（x-poster, x-smart-commenter）
- 自动发帖
- 智能评论（带随机延迟）
- 点赞/RT 开关控制
"""

import asyncio
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenClawBridge:
    """OpenClaw 桥接器"""
    
    def __init__(self, api_endpoint: str = 'http://localhost:8080'):
        """
        初始化 OpenClaw 桥接器
        
        Args:
            api_endpoint: OpenClaw API 端点
        """
        self.api_endpoint = api_endpoint
        self.auto_like_enabled = False
        self.auto_rt_enabled = False
        self.auto_post_enabled = False
        self.daily_like_limit = 30
        self.daily_rt_limit = 10
        self.daily_post_limit = 10
        self.like_count = 0
        self.rt_count = 0
        self.post_count = 0
    
    async def post_content(self, content: str, media_suggestion: str = None, niche: str = 'general') -> Dict:
        """
        通过 OpenClaw 自动发帖
        
        Args:
            content: 帖子内容
            media_suggestion: 配图建议
            niche: Niche 领域
        
        Returns:
            Dict: 发帖结果
        """
        if not self.auto_post_enabled:
            return {'success': False, 'reason': 'Auto post is disabled'}
        
        if self.post_count >= self.daily_post_limit:
            return {'success': False, 'reason': f'Daily post limit reached: {self.daily_post_limit}'}
        
        try:
            # 调用 x-poster skill
            result = await self._call_x_poster(content, media_suggestion)
            self.post_count += 1
            return result
        except Exception as e:
            logger.error(f"Error posting content: {e}")
            return {'success': False, 'reason': str(e)}
    
    async def _call_x_poster(self, content: str, media_suggestion: str = None) -> Dict:
        """调用 x-poster skill"""
        # 实际实现需要调用 OpenClaw API
        logger.info(f"Posting content via OpenClaw: {content[:50]}...")
        
        # 模拟结果
        return {
            'success': True,
            'post_id': 'mock_post_id',
            'url': 'https://x.com/status/mock_post_id',
            'posted_at': datetime.now().isoformat()
        }
    
    async def comment_on_post(self, post_url: str, comment: str, delay_range: tuple = (10, 30)) -> Dict:
        """
        智能评论（带随机延迟）
        
        Args:
            post_url: 原帖链接
            comment: 评论内容
            delay_range: 随机延迟范围（秒）
        
        Returns:
            Dict: 评论结果
        """
        # 随机延迟防检测
        delay = random.uniform(delay_range[0], delay_range[1])
        logger.info(f"Waiting {delay:.1f}s before commenting...")
        await asyncio.sleep(delay)
        
        try:
            # 调用 x-smart-commenter skill
            result = await self._call_smart_commenter(post_url, comment)
            return result
        except Exception as e:
            logger.error(f"Error commenting: {e}")
            return {'success': False, 'reason': str(e)}
    
    async def _call_smart_commenter(self, post_url: str, comment: str) -> Dict:
        """调用 x-smart-commenter skill"""
        # 实际实现需要调用 OpenClaw API
        logger.info(f"Commenting on {post_url}: {comment[:50]}...")
        
        # 模拟结果
        return {
            'success': True,
            'comment_id': 'mock_comment_id',
            'url': 'https://x.com/status/mock_comment_id',
            'commented_at': datetime.now().isoformat()
        }
    
    async def like_post(self, post_url: str) -> Dict:
        """
        点赞帖子
        
        Args:
            post_url: 帖子链接
        
        Returns:
            Dict: 点赞结果
        """
        if not self.auto_like_enabled:
            return {'success': False, 'reason': 'Auto like is disabled'}
        
        if self.like_count >= self.daily_like_limit:
            return {'success': False, 'reason': f'Daily like limit reached: {self.daily_like_limit}'}
        
        try:
            result = await self._call_like(post_url)
            self.like_count += 1
            return result
        except Exception as e:
            logger.error(f"Error liking post: {e}")
            return {'success': False, 'reason': str(e)}
    
    async def _call_like(self, post_url: str) -> Dict:
        """调用点赞 API"""
        logger.info(f"Liking post: {post_url}")
        
        # 模拟结果
        return {
            'success': True,
            'liked_at': datetime.now().isoformat()
        }
    
    async def retweet_post(self, post_url: str, comment: str = None) -> Dict:
        """
        转发帖子（可选带评论）
        
        Args:
            post_url: 帖子链接
            comment: 引用评论（可选）
        
        Returns:
            Dict: 转发结果
        """
        if not self.auto_rt_enabled:
            return {'success': False, 'reason': 'Auto RT is disabled'}
        
        if self.rt_count >= self.daily_rt_limit:
            return {'success': False, 'reason': f'Daily RT limit reached: {self.daily_rt_limit}'}
        
        try:
            result = await self._call_retweet(post_url, comment)
            self.rt_count += 1
            return result
        except Exception as e:
            logger.error(f"Error retweeting post: {e}")
            return {'success': False, 'reason': str(e)}
    
    async def _call_retweet(self, post_url: str, comment: str = None) -> Dict:
        """调用转发 API"""
        logger.info(f"Retweeting post: {post_url} (with comment: {comment is not None})")
        
        # 模拟结果
        return {
            'success': True,
            'retweeted_at': datetime.now().isoformat(),
            'with_comment': comment is not None
        }
    
    def set_auto_like(self, enabled: bool):
        """设置自动点赞开关"""
        self.auto_like_enabled = enabled
        logger.info(f"Auto like {'enabled' if enabled else 'disabled'}")
    
    def set_auto_rt(self, enabled: bool):
        """设置自动 RT 开关"""
        self.auto_rt_enabled = enabled
        logger.info(f"Auto RT {'enabled' if enabled else 'disabled'}")
    
    def set_auto_post(self, enabled: bool):
        """设置自动发帖开关"""
        self.auto_post_enabled = enabled
        logger.info(f"Auto post {'enabled' if enabled else 'disabled'}")
    
    def set_daily_limits(self, like: int = None, rt: int = None, post: int = None):
        """设置每日上限"""
        if like is not None:
            self.daily_like_limit = like
        if rt is not None:
            self.daily_rt_limit = rt
        if post is not None:
            self.daily_post_limit = post
        
        logger.info(f"Daily limits - Like: {self.daily_like_limit}, RT: {self.daily_rt_limit}, Post: {self.daily_post_limit}")
    
    def reset_daily_counts(self):
        """重置每日计数"""
        self.like_count = 0
        self.rt_count = 0
        self.post_count = 0
        logger.info("Daily counts reset")


async def create_openclaw_bridge(api_endpoint: str = 'http://localhost:8080') -> OpenClawBridge:
    """创建 OpenClaw 桥接器实例"""
    bridge = OpenClawBridge(api_endpoint)
    return bridge
