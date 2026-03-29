"""
research_optimization.py - 多源采集优化模块

实现：
- 并发限制（Semaphore）
- 指数退避重试
- 超时保护
- 速率限制感知
"""

import asyncio
import logging
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """速率限制和重试配置"""

    # 各平台的并发限制
    reddit_max_concurrent: int = 2  # Reddit API 严格限制
    hackernews_max_concurrent: int = 5  # HN API 相对宽松
    google_trends_max_concurrent: int = 1  # pytrends 是单线程库
    twitter_max_concurrent: int = 3
    youtube_max_concurrent: int = 3
    default_max_concurrent: int = 2

    # 超时配置（秒）
    request_timeout_secs: float = 10.0  # 单个请求超时
    total_timeout_secs: float = 30.0  # 总操作超时

    # 重试配置
    max_retries: int = 3
    backoff_base: float = 2.0  # 指数退避基数：2^n 秒
    backoff_jitter: float = 0.1  # 随机抖动，避免雷鸣羊群


class OptimizedFetcher:
    """优化后的fetcher基类，支持重试和超时"""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.logger = logging.getLogger(__name__)

    async def fetch_with_retry(
        self,
        fetcher_coro,
        platform_name: str = "unknown",
        timeout: float = None,
        max_retries: int = None,
    ) -> Dict[str, Any]:
        """
        执行fetcher，支持重试和超时

        Args:
            fetcher_coro: 异步协程（fetcher function）
            platform_name: 平台名称（用于日志）
            timeout: 单个请求超时（秒），默认使用config
            max_retries: 最大重试次数，默认使用config

        Returns:
            获取到的数据或mock数据
        """
        timeout = timeout or self.config.request_timeout_secs
        max_retries = max_retries or self.config.max_retries

        for attempt in range(1, max_retries + 1):
            try:
                self.logger.debug(f"[{platform_name}] 尝试 #{attempt}/{max_retries}")

                # 执行fetcher，带超时保护
                result = await asyncio.wait_for(fetcher_coro(), timeout=timeout)

                if attempt > 1:
                    self.logger.info(f"[{platform_name}] 第{attempt}次尝试成功")

                return result

            except asyncio.TimeoutError:
                if attempt < max_retries:
                    # 计算退避时间
                    backoff_time = (self.config.backoff_base ** attempt) + random.uniform(
                        0, self.config.backoff_jitter
                    )
                    self.logger.warning(
                        f"[{platform_name}] 超时，{backoff_time:.1f}秒后重试 (尝试 {attempt}/{max_retries})"
                    )
                    await asyncio.sleep(backoff_time)
                else:
                    self.logger.error(f"[{platform_name}] 超时，已达最大重试次数，使用mock数据")
                    return self._get_mock_data()

            except Exception as e:
                if attempt < max_retries:
                    # 检查是否是可重试的错误
                    if self._is_retryable_error(e):
                        backoff_time = (self.config.backoff_base ** attempt) + random.uniform(
                            0, self.config.backoff_jitter
                        )
                        self.logger.warning(
                            f"[{platform_name}] 错误: {e}，{backoff_time:.1f}秒后重试 (尝试 {attempt}/{max_retries})"
                        )
                        await asyncio.sleep(backoff_time)
                    else:
                        self.logger.error(
                            f"[{platform_name}] 不可重试错误: {e}，使用mock数据"
                        )
                        return self._get_mock_data()
                else:
                    self.logger.error(
                        f"[{platform_name}] 错误: {e}，已达最大重试次数，使用mock数据"
                    )
                    return self._get_mock_data()

        # 应该不会到这里
        return self._get_mock_data()

    def _is_retryable_error(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        retryable_strings = [
            "500",
            "502",
            "503",
            "504",
            "429",  # Rate limit
            "timeout",
            "connection reset",
            "temporary",
        ]
        error_str = str(error).lower()
        return any(s in error_str for s in retryable_strings)

    def _get_mock_data(self) -> Dict[str, Any]:
        """返回mock数据（子类应该实现）"""
        return {"error": "fetch failed, using mock data"}


class ConcurrentLimiter:
    """并发限制管理器"""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self._init_semaphores()

    def _init_semaphores(self):
        """初始化各平台的semaphore"""
        self.semaphores = {
            "reddit": asyncio.Semaphore(self.config.reddit_max_concurrent),
            "hackernews": asyncio.Semaphore(self.config.hackernews_max_concurrent),
            "google_trends": asyncio.Semaphore(self.config.google_trends_max_concurrent),
            "twitter": asyncio.Semaphore(self.config.twitter_max_concurrent),
            "youtube": asyncio.Semaphore(self.config.youtube_max_concurrent),
        }

    async def acquire(self, platform: str) -> None:
        """获取指定平台的信号量"""
        semaphore = self.semaphores.get(platform)
        if semaphore:
            await semaphore.acquire()
        else:
            # 未知平台，使用默认
            semaphore = asyncio.Semaphore(self.config.default_max_concurrent)
            await semaphore.acquire()

    def release(self, platform: str) -> None:
        """释放指定平台的信号量"""
        semaphore = self.semaphores.get(platform)
        if semaphore:
            semaphore.release()

    async def limit_concurrent(
        self, platform: str, coro
    ) -> Any:
        """在并发限制下执行协程"""
        await self.acquire(platform)
        try:
            return await coro
        finally:
            self.release(platform)


async def gather_with_timeout(
    tasks: list, timeout: float = 30.0, return_exceptions: bool = True
) -> list:
    """
    执行多个任务，带整体超时保护

    Args:
        tasks: 任务列表
        timeout: 总超时时间（秒）
        return_exceptions: 是否返回异常而非抛出

    Returns:
        结果列表
    """
    try:
        return await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=return_exceptions),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.error(f"总超时（{timeout}s）, 取消所有任务")
        for task in tasks:
            if isinstance(task, asyncio.Task):
                task.cancel()
        # 返回部分完成的结果
        return [None] * len(tasks)


def exponential_backoff(attempt: int, base: float = 2.0, jitter: bool = True) -> float:
    """
    计算指数退避时间

    Args:
        attempt: 尝试次数（从1开始）
        base: 指数基数（默认2）
        jitter: 是否添加随机抖动

    Returns:
        等待时间（秒）
    """
    wait_time = base ** attempt
    if jitter:
        wait_time += random.uniform(0, 0.1 * wait_time)
    return wait_time
