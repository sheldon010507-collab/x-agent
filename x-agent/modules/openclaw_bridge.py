"""
openclaw_bridge.py - X (Twitter) 集成模块

【V1 Browser Automation】使用 Playwright 无头浏览器自动化 X

功能：
- 浏览器自动化发帖/评论/点赞
- 防封机制（随机延迟、内容变体）
- 每日上限控制
- Session 管理（登录状态持久化）

版本：V1 - Browser Automation Edition
"""

import asyncio
import logging
import os
import random
from datetime import datetime
from typing import Dict, List, Optional

from .x_automation import XAutomation, create_x_automation

logger = logging.getLogger(__name__)


# 防封配置
DELAY_MIN = float(os.getenv("DELAY_MIN", "10"))
DELAY_MAX = float(os.getenv("DELAY_MAX", "40"))
MAX_COMMENTS_PER_DAY = int(os.getenv("MAX_COMMENTS_PER_DAY", "15"))
MAX_POSTS_PER_DAY = int(os.getenv("MAX_POSTS_PER_DAY", "10"))
MAX_LIKES_PER_DAY = int(os.getenv("MAX_LIKES_PER_DAY", "30"))

# Emoji 变体池
EMOJI_VARIANTS = ["🔥", "👀", "💡", "✨", "🚀", "💯", "🎯", "📌"]
PHRASE_VARIANTS = ["", " Interesting.", " Thoughts?", " 👀", " Just saying.", ""]


class OpenClawBridge:
    """X (Twitter) 自动化桥接器 - 浏览器自动化版本"""

    def __init__(self, api_endpoint: str = "http://localhost:8080"):
        """
        初始化 X 自动化桥接器

        Args:
            api_endpoint: OpenClaw API 端点（暂未使用，保持兼容性）
        """
        self.api_endpoint = api_endpoint
        self.x_automation: Optional[XAutomation] = None
        self.initialized = False

        # 开关控制
        self.auto_like_enabled = False
        self.auto_rt_enabled = False
        self.auto_post_enabled = False
        self.auto_comment_enabled = True

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

    # ==================== 每日限制检查 ====================

    def _check_daily_limit(self, action: str) -> bool:
        """
        规则3: 检查每日上限

        Args:
            action: 动作类型 (like, rt, post, comment)

        Returns:
            bool: 是否在限额内
        """
        limits = {
            "like": (self.like_count, self.daily_like_limit),
            "rt": (self.rt_count, self.daily_rt_limit),
            "post": (self.post_count, self.daily_post_limit),
            "comment": (self.comment_count, self.daily_comment_limit),
        }

        current, limit = limits.get(action, (0, 10))

        if current >= limit:
            logger.warning(f"[防封] 每日 {action} 上限已达: {current}/{limit}")
            return False

        return True

    # ==================== 发帖功能 ====================

    async def initialize(self) -> bool:
        """初始化 X 自动化"""
        try:
            self.x_automation = await create_x_automation()
            self.initialized = self.x_automation.logged_in

            if self.initialized:
                logger.info("✅ X 自动化已初始化并登录")
            else:
                logger.warning("⚠️ X 自动化已初始化，但未登录（需要手动登录）")

            return True
        except Exception as e:
            logger.error(f"初始化 X 自动化失败: {e}")
            return False

    async def login_x(self, email: str, password: str, phone: Optional[str] = None) -> bool:
        """
        登录 X 账号

        Args:
            email: 邮箱或用户名
            password: 密码
            phone: 可选，如果需要电话验证

        Returns:
            bool: 登录成功
        """
        if not self.x_automation:
            logger.error("X 自动化未初始化")
            return False

        success = await self.x_automation.login(email, password, phone)
        self.initialized = success
        return success

    async def post_content(
        self,
        content: str,
        media_suggestion: str = None,
        niche: str = "general",
        apply_variant: bool = True,
    ) -> Dict:
        """
        通过浏览器自动化发帖到 X

        Args:
            content: 帖子内容
            media_suggestion: 配图建议（暂未支持）
            niche: Niche 领域
            apply_variant: 是否应用内容变体

        Returns:
            Dict: 发帖结果
        """
        if not self.auto_post_enabled:
            return {"success": False, "reason": "Auto post is disabled"}

        if not self.initialized or not self.x_automation:
            return {"success": False, "reason": "X 自动化未初始化或未登录"}

        if not self._check_daily_limit("post"):
            return {
                "success": False,
                "reason": f"Daily post limit reached: {self.daily_post_limit}",
            }

        try:
            # 调用 X 自动化发帖
            result = await self.x_automation.post(content, apply_variant=apply_variant)

            if result.get("success"):
                self.post_count += 1
                logger.info(f"[发帖] 成功，今日第 {self.post_count} 条")

            return result

        except Exception as e:
            logger.error(f"[发帖] 错误: {e}")
            return {"success": False, "reason": str(e)}

    # ==================== 点赞/转发 ====================

    async def like_post(self, post_url: str) -> Dict:
        """点赞 X 帖子"""
        if not self.auto_like_enabled:
            return {"success": False, "reason": "Auto like is disabled"}

        if not self.initialized or not self.x_automation:
            return {"success": False, "reason": "X 自动化未初始化或未登录"}

        if not self._check_daily_limit("like"):
            return {
                "success": False,
                "reason": f"Daily like limit reached: {self.daily_like_limit}",
            }

        try:
            result = await self.x_automation.like(post_url)
            if result.get("success"):
                self.like_count += 1
                logger.info(f"[点赞] 成功，今日第 {self.like_count} 个")
            return result

        except Exception as e:
            logger.error(f"[点赞] 错误: {e}")
            return {"success": False, "reason": str(e)}

    async def retweet_post(self, post_url: str, comment: str = None) -> Dict:
        """转发 X 帖子"""
        if not self.auto_rt_enabled:
            return {"success": False, "reason": "Auto RT is disabled"}

        if not self.initialized or not self.x_automation:
            return {"success": False, "reason": "X 自动化未初始化或未登录"}

        if not self._check_daily_limit("rt"):
            return {"success": False, "reason": f"Daily RT limit reached: {self.daily_rt_limit}"}

        try:
            result = await self.x_automation.retweet(post_url, comment)
            if result.get("success"):
                self.rt_count += 1
                logger.info(f"[转发] 成功，今日第 {self.rt_count} 条")
            return result

        except Exception as e:
            logger.error(f"[转发] 错误: {e}")
            return {"success": False, "reason": str(e)}

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

    def set_daily_limits(
        self, like: int = None, rt: int = None, post: int = None, comment: int = None
    ):
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
        x_status = self.x_automation.get_status() if self.x_automation else {}

        return {
            "initialized": self.initialized,
            "x_logged_in": self.x_automation.logged_in if self.x_automation else False,
            "auto_settings": {
                "auto_like": self.auto_like_enabled,
                "auto_rt": self.auto_rt_enabled,
                "auto_post": self.auto_post_enabled,
                "auto_comment": self.auto_comment_enabled,
            },
            "daily_counts": {
                "like": self.like_count,
                "rt": self.rt_count,
                "post": self.post_count,
                "comment": self.comment_count,
            },
            "daily_limits": {
                "like": self.daily_like_limit,
                "rt": self.daily_rt_limit,
                "post": self.daily_post_limit,
                "comment": self.daily_comment_limit,
            },
            "x_automation": x_status,
        }

    async def close(self) -> None:
        """关闭浏览器"""
        if self.x_automation:
            await self.x_automation.close()


# 便捷函数
async def create_openclaw_bridge(api_endpoint: str = "http://localhost:8080") -> OpenClawBridge:
    """创建 OpenClaw 桥接器实例"""
    bridge = OpenClawBridge(api_endpoint)
    return bridge
