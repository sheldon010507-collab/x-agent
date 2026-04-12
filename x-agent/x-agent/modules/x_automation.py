"""
x_automation.py - X (Twitter) 浏览器自动化模块

使用 Playwright 无头浏览器自动化 X 平台：
- 登录和 session 管理
- 自动发帖（带内容变体和随机延迟）
- 自动评论
- 自动点赞/转发
- 防封机制：随机延迟 + 内容变体 + 每日上限

版本：v1.0.0 - Browser Automation Edition
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    from playwright.async_api import Browser, BrowserContext, Page, async_playwright

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    Browser = None
    BrowserContext = None
    Page = None
    async_playwright = None

logger = logging.getLogger(__name__)

# 防封配置
DELAY_MIN = float(os.getenv("DELAY_MIN", "10"))
DELAY_MAX = float(os.getenv("DELAY_MAX", "40"))
MAX_POSTS_PER_DAY = int(os.getenv("MAX_POSTS_PER_DAY", "10"))
MAX_COMMENTS_PER_DAY = int(os.getenv("MAX_COMMENTS_PER_DAY", "15"))
MAX_LIKES_PER_DAY = int(os.getenv("MAX_LIKES_PER_DAY", "30"))

# Session 文件位置
X_SESSION_DIR = Path.home() / ".x-agent" / "sessions"
X_SESSION_FILE = X_SESSION_DIR / "x_auth_state.json"
X_COOKIES_FILE = X_SESSION_DIR / "x_cookies.json"

# 内容变体池
EMOJI_VARIANTS = ["🔥", "👀", "💡", "✨", "🚀", "💯", "🎯", "📌", "⚡", "🎉"]
PHRASE_VARIANTS = [
    "",
    " Interesting.",
    " Thoughts?",
    " 👀",
    " Just saying.",
    " 💭",
    " What do you think?",
]


class XAutomation:
    """X (Twitter) 浏览器自动化类"""

    def __init__(self):
        """初始化 X 自动化"""
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logged_in = False

        # 每日计数
        self.post_count = 0
        self.comment_count = 0
        self.like_count = 0

        # 创建 session 目录
        X_SESSION_DIR.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> bool:
        """
        初始化浏览器

        Returns:
            bool: 初始化成功
        """
        if not HAS_PLAYWRIGHT:
            logger.error(
                "❌ playwright 未安装，请运行: pip install playwright && playwright install"
            )
            return False
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)

            # 尝试加载已保存的 session
            if await self._load_session():
                logger.info("✅ 已加载保存的 X session")
                self.logged_in = True
                return True
            else:
                logger.info("⚠️ 未找到已保存的 session，需要手动登录")
                return False

        except Exception as e:
            logger.error(f"初始化浏览器失败: {e}")
            return False

    async def _load_session(self) -> bool:
        """
        加载已保存的 session

        Returns:
            bool: 加载成功
        """
        try:
            if not X_SESSION_FILE.exists():
                logger.debug(f"Session 文件不存在: {X_SESSION_FILE}")
                return False

            # 加载存储的状态
            with open(X_SESSION_FILE, "r") as f:
                state = json.load(f)

            self.context = await self.browser.new_context(storage_state=state)
            self.page = await self.context.new_page()

            # 验证登录状态
            await self.page.goto("https://x.com/home", wait_until="networkidle", timeout=10000)

            # 检查是否仍然登录（通过检查主页是否加载）
            logged_in = await self.page.locator('a[href="/home"]').is_visible()

            if logged_in:
                logger.info("✅ Session 有效，已验证登录状态")
                self.logged_in = True
                return True
            else:
                logger.warning("⚠️ Session 已过期，需要重新登录")
                return False

        except Exception as e:
            logger.error(f"加载 session 失败: {e}")
            return False

    async def login(self, email: str, password: str, phone: Optional[str] = None) -> bool:
        """
        登录 X 账号

        Args:
            email: 账号邮箱
            password: 密码
            phone: 可选，如果账号需要验证

        Returns:
            bool: 登录成功
        """
        try:
            if not self.browser:
                logger.error("浏览器未初始化")
                return False

            # 创建新 context 用于登录
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

            logger.info("开始登录 X...")

            # 访问 X 登录页面
            await self.page.goto("https://x.com/i/flow/login", wait_until="networkidle")

            # 输入邮箱/用户名
            email_input = await self.page.locator('input[autocomplete="username"]')
            await email_input.fill(email)
            await self.page.locator('button:has-text("Next")').click()

            # 等待密码输入框出现
            await asyncio.sleep(1)

            # 输入密码
            password_input = await self.page.locator('input[type="password"]')
            await password_input.fill(password)

            # 点击登录按钮
            login_button = await self.page.locator('button:has-text("Log in")')
            await login_button.click()

            # 等待登录完成
            await self.page.wait_for_url("**/home", timeout=30000)

            logger.info("✅ 登录成功！")

            # 保存 session
            await self._save_session()

            self.logged_in = True
            return True

        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False

    async def _save_session(self) -> None:
        """保存当前 session 到文件"""
        try:
            if not self.context:
                logger.error("Context 不存在，无法保存 session")
                return

            # 保存浏览器存储状态（包括 cookies）
            storage_state = await self.context.storage_state(path=str(X_SESSION_FILE))

            logger.info(f"✅ Session 已保存到: {X_SESSION_FILE}")

        except Exception as e:
            logger.error(f"保存 session 失败: {e}")

    async def post(
        self,
        content: str,
        media_urls: Optional[list] = None,
        apply_variant: bool = True,
    ) -> Dict:
        """
        发布推文

        Args:
            content: 推文内容
            media_urls: 图片 URL 列表（可选）
            apply_variant: 是否应用内容变体

        Returns:
            Dict: 发帖结果
        """
        if not self.logged_in or not self.page:
            return {"success": False, "reason": "未登录"}

        if not self._check_daily_limit("post"):
            return {
                "success": False,
                "reason": f"超过每日发帖限额: {MAX_POSTS_PER_DAY}",
            }

        try:
            # 随机延迟
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            logger.info(f"[防封] 延迟 {delay:.1f}s...")
            await asyncio.sleep(delay)

            # 应用内容变体
            if apply_variant:
                content = self._apply_content_variant(content)

            # 导航到主页
            await self.page.goto("https://x.com/home", wait_until="networkidle")

            # 找到发帖输入框
            tweet_composer = await self.page.locator('[data-testid="tweetTextarea_0"]')
            if not await tweet_composer.is_visible():
                logger.warning("发帖输入框不可见，尝试点击发帖按钮...")
                await self.page.locator('a[href="/compose/tweet"]').click()
                await asyncio.sleep(1)
                tweet_composer = await self.page.locator('[data-testid="tweetTextarea_0"]')

            # 输入内容
            await tweet_composer.fill(content)
            await asyncio.sleep(0.5)

            # 点击发帖按钮
            post_button = await self.page.locator('button[data-testid="tweetButtonInline"]')
            await post_button.click()

            # 等待发帖完成
            await asyncio.sleep(2)

            logger.info(f"✅ 推文已发布，内容: {content[:50]}...")

            self.post_count += 1

            return {
                "success": True,
                "content": content,
                "posted_at": datetime.now().isoformat(),
                "count": self.post_count,
            }

        except Exception as e:
            logger.error(f"发帖失败: {e}")
            return {"success": False, "reason": str(e)}

    async def comment(self, tweet_url: str, comment: str, apply_variant: bool = True) -> Dict:
        """
        评论推文

        Args:
            tweet_url: 推文 URL
            comment: 评论内容
            apply_variant: 是否应用内容变体

        Returns:
            Dict: 评论结果
        """
        if not self.logged_in or not self.page:
            return {"success": False, "reason": "未登录"}

        if not self._check_daily_limit("comment"):
            return {
                "success": False,
                "reason": f"超过每日评论限额: {MAX_COMMENTS_PER_DAY}",
            }

        try:
            # 随机延迟
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            await asyncio.sleep(delay)

            # 应用内容变体
            if apply_variant:
                comment = self._apply_content_variant(comment)

            # 打开推文
            await self.page.goto(tweet_url, wait_until="networkidle")

            # 找到评论输入框
            reply_box = await self.page.locator('[data-testid="tweetTextarea_0"]')
            await reply_box.fill(comment)
            await asyncio.sleep(0.5)

            # 点击回复按钮
            reply_button = await self.page.locator('button[data-testid="tweetButtonInline"]')
            await reply_button.click()

            # 等待完成
            await asyncio.sleep(2)

            logger.info(f"✅ 评论已发布")

            self.comment_count += 1

            return {
                "success": True,
                "comment": comment,
                "commented_at": datetime.now().isoformat(),
                "count": self.comment_count,
            }

        except Exception as e:
            logger.error(f"评论失败: {e}")
            return {"success": False, "reason": str(e)}

    async def like(self, tweet_url: str) -> Dict:
        """点赞推文"""
        if not self.logged_in or not self.page:
            return {"success": False, "reason": "未登录"}

        if not self._check_daily_limit("like"):
            return {
                "success": False,
                "reason": f"超过每日点赞限额: {MAX_LIKES_PER_DAY}",
            }

        try:
            delay = random.uniform(5, 15)  # 点赞延迟较短
            await asyncio.sleep(delay)

            await self.page.goto(tweet_url, wait_until="networkidle")

            # 找到点赞按钮
            like_button = await self.page.locator('[data-testid="like"]')
            await like_button.click()

            logger.info(f"✅ 已点赞: {tweet_url}")

            self.like_count += 1

            return {
                "success": True,
                "liked_at": datetime.now().isoformat(),
                "count": self.like_count,
            }

        except Exception as e:
            logger.error(f"点赞失败: {e}")
            return {"success": False, "reason": str(e)}

    async def retweet(self, tweet_url: str, comment: Optional[str] = None) -> Dict:
        """转发推文"""
        if not self.logged_in or not self.page:
            return {"success": False, "reason": "未登录"}

        try:
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            await asyncio.sleep(delay)

            await self.page.goto(tweet_url, wait_until="networkidle")

            # 找到转发按钮
            rt_button = await self.page.locator('[data-testid="retweet"]')
            await rt_button.click()

            logger.info(f"✅ 已转发: {tweet_url}")

            return {
                "success": True,
                "retweeted_at": datetime.now().isoformat(),
                "with_comment": comment is not None,
            }

        except Exception as e:
            logger.error(f"转发失败: {e}")
            return {"success": False, "reason": str(e)}

    def _apply_content_variant(self, content: str) -> str:
        """
        应用内容变体（防止重复检测）

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

        return content.strip()

    def _check_daily_limit(self, action: str) -> bool:
        """
        检查每日上限

        Args:
            action: 动作类型 (post, comment, like)

        Returns:
            bool: 是否在限额内
        """
        limits = {
            "post": (self.post_count, MAX_POSTS_PER_DAY),
            "comment": (self.comment_count, MAX_COMMENTS_PER_DAY),
            "like": (self.like_count, MAX_LIKES_PER_DAY),
        }

        current, limit = limits.get(action, (0, 10))

        if current >= limit:
            logger.warning(f"[防封] 每日 {action} 上限已达: {current}/{limit}")
            return False

        return True

    async def reset_daily_counts(self) -> None:
        """重置每日计数（每天 00:00 调用）"""
        self.post_count = 0
        self.comment_count = 0
        self.like_count = 0
        logger.info("✅ 每日计数已重置")

    async def close(self) -> None:
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")

    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            "logged_in": self.logged_in,
            "daily_counts": {
                "posts": self.post_count,
                "comments": self.comment_count,
                "likes": self.like_count,
            },
            "daily_limits": {
                "posts": MAX_POSTS_PER_DAY,
                "comments": MAX_COMMENTS_PER_DAY,
                "likes": MAX_LIKES_PER_DAY,
            },
            "session_file": str(X_SESSION_FILE),
        }


# 便捷函数
async def create_x_automation() -> XAutomation:
    """创建 X 自动化实例"""
    automation = XAutomation()
    await automation.initialize()
    return automation
