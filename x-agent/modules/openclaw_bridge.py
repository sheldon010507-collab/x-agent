"""
openclaw_bridge.py - OpenClaw 桥接模块

功能：
- 调用 OpenClaw Skills（x-poster, x-smart-commenter）
- 自动发帖（带随机延迟 8-25 秒）
- 智能评论（带随机延迟 10-30 秒）
- 内容变体防重复
- 每日限额控制
- 防封机制
"""

import asyncio
import random
import logging
import hashlib
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path

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
        self.running = False
        
        # 功能开关
        self.auto_post_enabled = False
        self.auto_comment_enabled = False
        
        # 每日限额
        self.daily_post_limit = 10
        self.daily_comment_limit = 50
        
        # 计数器（内存中）
        self.post_count = 0
        self.comment_count = 0
        
        # 防重复：已发布内容哈希
        self.posted_hashes: Set[str] = set()
        
        # 防封：延迟范围
        self.post_delay_range = (8, 25)  # 发帖延迟 8-25 秒
        self.comment_delay_range = (10, 30)  # 评论延迟 10-30 秒
        
        # 数据持久化路径
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir.mkdir(exist_ok=True)
        self.posted_hashes_file = self.data_dir / 'posted_hashes.txt'
        
        # 加载已发布哈希
        self._load_posted_hashes()
    
    def _load_posted_hashes(self):
        """加载已发布内容哈希"""
        if self.posted_hashes_file.exists():
            try:
                with open(self.posted_hashes_file, 'r') as f:
                    self.posted_hashes = set(line.strip() for line in f if line.strip())
                logger.info(f"[OpenClaw] 加载 {len(self.posted_hashes)} 条已发布哈希")
            except Exception as e:
                logger.warning(f"[OpenClaw] 加载哈希失败：{e}")
                self.posted_hashes = set()
    
    def _save_posted_hash(self, content_hash: str):
        """保存已发布内容哈希"""
        self.posted_hashes.add(content_hash)
        try:
            with open(self.posted_hashes_file, 'a') as f:
                f.write(f"{content_hash}\n")
        except Exception as e:
            logger.warning(f"[OpenClaw] 保存哈希失败：{e}")
    
    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希（用于防重复）"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _is_duplicate(self, content: str) -> bool:
        """检查内容是否重复"""
        content_hash = self._generate_content_hash(content)
        return content_hash in self.posted_hashes
    
    def _create_content_variant(self, content: str) -> str:
        """
        创建内容变体（防重复）
        
        策略：
        - 添加随机表情
        - 调整标点符号
        - 添加随机空格/换行
        """
        import random
        
        variants = [
            # 添加随机表情
            lambda c: c + " " + random.choice(["🔥", "💡", "✨", "🚀", "💪", ""]),
            # 调整句尾标点
            lambda c: c.rstrip('.,!?.') + random.choice(["", ".", "!", "?"]),
            # 添加换行
            lambda c: c.replace(" ", "  ", random.randint(0, 2)),
        ]
        
        variant = content
        for transform in random.sample(variants, random.randint(1, 2)):
            variant = transform(variant)
        
        return variant
    
    async def _random_delay(self, delay_range: tuple, action: str = "action"):
        """
        随机延迟（防封机制）
        
        Args:
            delay_range: 延迟范围 (min, max) 秒
            action: 操作类型（用于日志）
        """
        delay = random.uniform(delay_range[0], delay_range[1])
        logger.info(f"[OpenClaw] {action} 延迟 {delay:.1f} 秒")
        await asyncio.sleep(delay)
    
    async def post_content(self, content: str, media_suggestion: str = None, 
                          niche: str = 'general', create_variant: bool = True) -> Dict:
        """
        通过 OpenClaw 自动发帖
        
        Args:
            content: 帖子内容
            media_suggestion: 配图建议
            niche: Niche 领域
            create_variant: 是否创建变体防重复
        
        Returns:
            Dict: 发帖结果
        """
        if not self.auto_post_enabled:
            return {'success': False, 'reason': 'Auto post is disabled'}
        
        if self.post_count >= self.daily_post_limit:
            return {'success': False, 'reason': f'Daily post limit reached: {self.daily_post_limit}'}
        
        # 检查重复
        if self._is_duplicate(content):
            if create_variant:
                # 创建变体
                original_content = content
                for _ in range(3):  # 最多尝试 3 次
                    variant = self._create_content_variant(content)
                    if not self._is_duplicate(variant):
                        content = variant
                        logger.info(f"[OpenClaw] 创建内容变体")
                        break
                else:
                    return {'success': False, 'reason': 'Content is duplicate, no variant available'}
            else:
                return {'success': False, 'reason': 'Content is duplicate'}
        
        # 随机延迟（防封）
        await self._random_delay(self.post_delay_range, "发帖")
        
        try:
            # 调用 x-poster skill
            result = await self._call_x_poster(content, media_suggestion, niche)
            
            if result.get('success'):
                self.post_count += 1
                # 保存哈希防止重复
                self._save_posted_hash(self._generate_content_hash(content))
            
            return result
        except Exception as e:
            logger.error(f"[OpenClaw] 发帖失败：{e}")
            return {'success': False, 'reason': str(e)}
    
    async def _call_x_poster(self, content: str, media_suggestion: str = None, 
                            niche: str = 'general') -> Dict:
        """
        调用 x-poster skill
        
        通过 OpenClaw message 工具发送技能调用请求
        """
        logger.info(f"[OpenClaw] 调用 x-poster: {content[:50]}...")
        
        # 实际实现：通过 OpenClaw API 调用 skill
        # 这里使用 exec 调用 OpenClaw CLI
        import subprocess
        import json
        
        try:
            # 构建技能调用命令
            # 注意：实际使用时需要正确的 OpenClaw 命令格式
            skill_call = {
                'skill': 'x-poster',
                'action': 'post',
                'content': content,
                'niche': niche,
            }
            
            if media_suggestion:
                skill_call['media'] = media_suggestion
            
            # 调用 OpenClaw（示例）
            # 实际命令需要根据 OpenClaw 的 CLI 格式调整
            cmd = ['openclaw', 'skill', 'x-poster', '--action', 'post', 
                   '--content', content, '--niche', niche]
            
            # 模拟结果（实际使用时替换为真实调用）
            logger.info(f"[OpenClaw] 模拟调用 x-poster skill")
            
            return {
                'success': True,
                'post_id': f'post_{datetime.now().timestamp()}',
                'url': f'https://x.com/status/{datetime.now().timestamp()}',
                'posted_at': datetime.now().isoformat(),
                'content': content,
                'niche': niche,
            }
            
        except Exception as e:
            logger.error(f"[OpenClaw] x-poster 调用失败：{e}")
            return {'success': False, 'reason': str(e)}
    
    async def comment_on_post(self, post_url: str, comment: str, 
                             niche: str = 'general', delay_range: tuple = None) -> Dict:
        """
        智能评论（带随机延迟）
        
        Args:
            post_url: 原帖链接
            comment: 评论内容
            niche: Niche 领域
            delay_range: 随机延迟范围（秒），默认 (10, 30)
        
        Returns:
            Dict: 评论结果
        """
        if not self.auto_comment_enabled:
            return {'success': False, 'reason': 'Auto comment is disabled'}
        
        if self.comment_count >= self.daily_comment_limit:
            return {'success': False, 'reason': f'Daily comment limit reached: {self.daily_comment_limit}'}
        
        # 使用指定延迟范围或默认值
        delay = delay_range or self.comment_delay_range
        
        # 随机延迟（防封）
        await self._random_delay(delay, "评论")
        
        try:
            # 调用 x-smart-commenter skill
            result = await self._call_smart_commenter(post_url, comment, niche)
            
            if result.get('success'):
                self.comment_count += 1
            
            return result
        except Exception as e:
            logger.error(f"[OpenClaw] 评论失败：{e}")
            return {'success': False, 'reason': str(e)}
    
    async def _call_smart_commenter(self, post_url: str, comment: str, 
                                   niche: str = 'general') -> Dict:
        """
        调用 x-smart-commenter skill
        
        通过 OpenClaw message 工具发送技能调用请求
        """
        logger.info(f"[OpenClaw] 调用 x-smart-commenter: {post_url}")
        
        try:
            # 构建技能调用命令
            skill_call = {
                'skill': 'x-smart-commenter',
                'action': 'comment',
                'post_url': post_url,
                'comment': comment,
                'niche': niche,
            }
            
            # 调用 OpenClaw（示例）
            logger.info(f"[OpenClaw] 模拟调用 x-smart-commenter skill")
            
            return {
                'success': True,
                'comment_id': f'comment_{datetime.now().timestamp()}',
                'url': f'{post_url}/status/{datetime.now().timestamp()}',
                'commented_at': datetime.now().isoformat(),
                'post_url': post_url,
                'comment': comment,
            }
            
        except Exception as e:
            logger.error(f"[OpenClaw] x-smart-commenter 调用失败：{e}")
            return {'success': False, 'reason': str(e)}
    
    def set_auto_post(self, enabled: bool):
        """设置自动发帖开关"""
        self.auto_post_enabled = enabled
        logger.info(f"[OpenClaw] 自动发帖 {'已启用' if enabled else '已禁用'}")
    
    def set_auto_comment(self, enabled: bool):
        """设置自动评论开关"""
        self.auto_comment_enabled = enabled
        logger.info(f"[OpenClaw] 自动评论 {'已启用' if enabled else '已禁用'}")
    
    def set_daily_limits(self, post: int = None, comment: int = None):
        """设置每日上限"""
        if post is not None:
            self.daily_post_limit = post
        if comment is not None:
            self.daily_comment_limit = comment
        
        logger.info(f"[OpenClaw] 每日限额 - 发帖：{self.daily_post_limit}, 评论：{self.daily_comment_limit}")
    
    def reset_daily_counts(self):
        """重置每日计数"""
        self.post_count = 0
        self.comment_count = 0
        logger.info("[OpenClaw] 每日计数已重置")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'post_count': self.post_count,
            'comment_count': self.comment_count,
            'daily_post_limit': self.daily_post_limit,
            'daily_comment_limit': self.daily_comment_limit,
            'posted_hashes_count': len(self.posted_hashes),
            'auto_post_enabled': self.auto_post_enabled,
            'auto_comment_enabled': self.auto_comment_enabled,
        }


async def create_openclaw_bridge(api_endpoint: str = 'http://localhost:8080') -> OpenClawBridge:
    """创建 OpenClaw 桥接器实例"""
    bridge = OpenClawBridge(api_endpoint)
    return bridge
