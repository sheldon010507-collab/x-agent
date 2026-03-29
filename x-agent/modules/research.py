"""
research.py - 原生异步多平台数据采集模块

【V0 Final 重构版】移除外部 CLI 依赖，实现原生异步采集

功能：
- 原生异步多平台数据采集（Reddit、Hacker News、模拟 X/TikTok/YouTube）
- 不依赖外部 CLI，使用 Python 原生实现
- 支持 aiohttp 异步 HTTP 请求
- 本地缓存机制
- 风险评分计算
- 【增强】并发限制、指数退避重试、超时保护、速率限制感知

支持平台：
- Reddit (通过 PRAW 或直接 API)
- Hacker News (官方 API)
- Google Trends (pytrends)
- X/Twitter (模拟数据，需要 API 密钥)
- TikTok/YouTube (模拟数据，需要爬虫)

版本：V0 Final 增强版（含研究优化）
"""

import asyncio
import hashlib
import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .research_optimization import RateLimitConfig, ConcurrentLimiter, gather_with_timeout
from .deduplicator import ContentDeduplicator

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import praw

    HAS_PRAW = True
except ImportError:
    HAS_PRAW = False

try:
    from pytrends.request import TrendReq

    HAS_PYTRENDS = True
except ImportError:
    HAS_PYTRENDS = False

logger = logging.getLogger(__name__)


class PlatformFetcher:
    """平台数据获取器基类"""

    def __init__(self, config=None):
        self.config = config

    async def fetch(self, niche: str, days: int = 7, timeout: float = 10.0) -> Dict:
        """
        获取平台数据

        Args:
            niche: 研究领域
            days: 回溯天数
            timeout: 请求超时时间（秒）

        Returns:
            平台数据字典
        """
        raise NotImplementedError


class RedditFetcher(PlatformFetcher):
    """Reddit 数据获取器"""

    def __init__(self, config=None):
        super().__init__(config)
        self.reddit = None
        if HAS_PRAW and config:
            try:
                self.reddit = praw.Reddit(
                    client_id=config.reddit_client_id,
                    client_secret=config.reddit_client_secret,
                    user_agent=config.reddit_user_agent or "x-agent/3.0",
                )
                self.reddit.read_only = True
                logger.info("✅ Reddit API 已初始化")
            except Exception as e:
                logger.warning(f"Reddit API 初始化失败: {e}")

    async def fetch(self, niche: str, days: int = 7) -> Dict:
        """获取 Reddit 热门帖子"""
        if not self.reddit:
            return self._mock_data(niche)

        try:
            subreddit_names = self._get_subreddits(niche)
            posts = []

            for sub_name in subreddit_names[:2]:
                try:
                    subreddit = self.reddit.subreddit(sub_name)
                    for post in subreddit.hot(limit=10):
                        posts.append(
                            {
                                "title": post.title,
                                "score": post.score,
                                "url": f"https://reddit.com{post.permalink}",
                                "created_utc": post.created_utc,
                                "num_comments": post.num_comments,
                                "subreddit": sub_name,
                            }
                        )
                except Exception as e:
                    logger.warning(f"获取 r/{sub_name} 失败: {e}")

            return {
                "platform": "reddit",
                "niche": niche,
                "posts": posts[:20],
                "fetched_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Reddit 获取错误: {e}")
            return self._mock_data(niche)

    def _get_subreddits(self, niche: str) -> List[str]:
        """根据 niche 返回相关 subreddit"""
        niche_subs = {
            "ai_tools": ["artificial", "MachineLearning", "OpenAI", "ChatGPT"],
            "crypto": ["CryptoCurrency", "bitcoin", "ethereum", "defi"],
            "fitness": ["fitness", "bodybuilding", "xxfitness", "loseit"],
            "beauty": ["MakeupAddiction", "SkincareAddiction", "Haircare"],
            "adult": ["sex", "AskRedditAfterDark"],
            "humor": ["funny", "meme", "dankmemes"],
            "general": ["AskReddit", "todayilearned", "worldnews"],
        }
        return niche_subs.get(niche, niche_subs["general"])

    def _mock_data(self, niche: str) -> Dict:
        """模拟 Reddit 数据"""
        mock_posts = [
            {
                "title": f"[Mock] Reddit 讨论: {niche} 领域热门话题 #{i}",
                "score": random.randint(100, 5000),
                "url": f"https://reddit.com/r/{niche}/mock_{i}",
                "created_utc": datetime.now().timestamp(),
                "num_comments": random.randint(10, 500),
                "subreddit": niche,
            }
            for i in range(5)
        ]
        return {
            "platform": "reddit",
            "niche": niche,
            "posts": mock_posts,
            "fetched_at": datetime.now().isoformat(),
            "mock": True,
        }


class HackerNewsFetcher(PlatformFetcher):
    """Hacker News 数据获取器"""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    async def fetch(self, niche: str, days: int = 7) -> Dict:
        """获取 HN 热门故事"""
        if not HAS_AIOHTTP:
            return self._mock_data(niche)

        try:
            async with aiohttp.ClientSession() as session:
                # 获取 top stories IDs
                async with session.get(f"{self.BASE_URL}/topstories.json") as resp:
                    story_ids = await resp.json()

                # 获取前 20 个故事的详情
                posts = []
                for story_id in story_ids[:20]:
                    try:
                        async with session.get(f"{self.BASE_URL}/item/{story_id}.json") as resp:
                            story = await resp.json()
                            if story:
                                posts.append(
                                    {
                                        "title": story.get("title", ""),
                                        "score": story.get("score", 0),
                                        "url": story.get(
                                            "url",
                                            f"https://news.ycombinator.com/item?id={story_id}",
                                        ),
                                        "by": story.get("by", "unknown"),
                                        "time": story.get("time", 0),
                                        "descendants": story.get("descendants", 0),
                                    }
                                )
                    except Exception as e:
                        logger.debug(f"获取 HN story {story_id} 失败: {e}")

                return {
                    "platform": "hackernews",
                    "niche": niche,
                    "posts": posts,
                    "fetched_at": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Hacker News 获取错误: {e}")
            return self._mock_data(niche)

    def _mock_data(self, niche: str) -> Dict:
        """模拟 HN 数据"""
        mock_posts = [
            {
                "title": f"[Mock] Show HN: 关于 {niche} 的新项目",
                "score": random.randint(50, 500),
                "url": f"https://news.ycombinator.com/item?id=mock_{i}",
                "by": f"user_{i}",
                "time": int(datetime.now().timestamp()),
                "descendants": random.randint(0, 100),
            }
            for i in range(5)
        ]
        return {
            "platform": "hackernews",
            "niche": niche,
            "posts": mock_posts,
            "fetched_at": datetime.now().isoformat(),
            "mock": True,
        }


class GoogleTrendsFetcher(PlatformFetcher):
    """Google Trends 数据获取器"""

    def __init__(self, config=None):
        super().__init__(config)
        self.pytrends = None
        if HAS_PYTRENDS:
            try:
                self.pytrends = TrendReq(hl="en-US", tz=360)
                logger.info("✅ Google Trends 已初始化")
            except Exception as e:
                logger.warning(f"Google Trends 初始化失败: {e}")

    async def fetch(self, niche: str, days: int = 7) -> Dict:
        """获取 Google Trends 数据"""
        if not self.pytrends:
            return self._mock_data(niche)

        try:
            # 在线程池中运行同步的 pytrends
            loop = asyncio.get_event_loop()

            keywords = self._get_keywords(niche)

            def get_trends():
                try:
                    self.pytrends.build_payload(keywords, timeframe=f"now {days}-d")
                    interest = self.pytrends.interest_over_time()
                    related = self.pytrends.related_queries()
                    return interest, related
                except Exception as e:
                    logger.error(f"pytrends 错误: {e}")
                    return None, None

            interest, related = await loop.run_in_executor(None, get_trends)

            trends_data = {
                "platform": "google_trends",
                "niche": niche,
                "keywords": keywords,
                "fetched_at": datetime.now().isoformat(),
            }

            if interest is not None and not interest.empty:
                trends_data["interest_over_time"] = interest.to_dict()

            if related:
                trends_data["related_queries"] = {
                    k: {"top": v.get("top", []), "rising": v.get("rising", [])}
                    for k, v in related.items()
                    if v
                }

            return trends_data

        except Exception as e:
            logger.error(f"Google Trends 获取错误: {e}")
            return self._mock_data(niche)

    def _get_keywords(self, niche: str) -> List[str]:
        """根据 niche 返回相关关键词"""
        niche_keywords = {
            "ai_tools": ["ChatGPT", "AI tools", "artificial intelligence"],
            "crypto": ["Bitcoin", "cryptocurrency", "blockchain"],
            "fitness": ["workout", "fitness", "gym"],
            "beauty": ["skincare", "makeup", "beauty"],
            "adult": ["relationships", "dating"],
            "humor": ["memes", "funny", "jokes"],
            "general": ["news", "trending", "popular"],
        }
        return niche_keywords.get(niche, niche_keywords["general"])

    def _mock_data(self, niche: str) -> Dict:
        """模拟 Google Trends 数据"""
        return {
            "platform": "google_trends",
            "niche": niche,
            "keywords": self._get_keywords(niche),
            "interest_over_time": {niche: [random.randint(20, 100) for _ in range(7)]},
            "related_queries": {
                niche: {
                    "top": [f"{niche} tip {i}" for i in range(5)],
                    "rising": [f"{niche} trend 2024" for _ in range(3)],
                }
            },
            "fetched_at": datetime.now().isoformat(),
            "mock": True,
        }


class SimulatedPlatformFetcher(PlatformFetcher):
    """模拟平台数据获取器（X/TikTok/YouTube）"""

    async def fetch(self, niche: str, days: int = 7, platform: str = "x") -> Dict:
        """生成模拟数据"""
        mock_posts = [
            {
                "title": f"[Mock {platform.upper()}] {niche} 领域热门内容 #{i}",
                "engagement": random.randint(100, 10000),
                "url": f"https://{platform}.com/mock_{i}",
                "author": f"@{niche}_creator_{i}",
                "created_at": datetime.now().isoformat(),
                "tags": [niche, "trending", "viral"],
            }
            for i in range(5)
        ]

        return {
            "platform": platform,
            "niche": niche,
            "posts": mock_posts,
            "fetched_at": datetime.now().isoformat(),
            "mock": True,
        }


class Researcher:
    """研究员 - 负责多平台数据采集

    【V0 Final 重构版】原生异步实现，不依赖外部 CLI
    """

    def __init__(self, config=None, rate_limit_config: Optional[RateLimitConfig] = None):
        """初始化研究员

        Args:
            config: Config 实例
            rate_limit_config: 速率限制配置（可选）
        """
        self.config = config
        self.cache_dir = Path("data/research")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 初始化各平台获取器
        self.reddit_fetcher = RedditFetcher(config)
        self.hn_fetcher = HackerNewsFetcher(config)
        self.trends_fetcher = GoogleTrendsFetcher(config)
        self.simulated_fetcher = SimulatedPlatformFetcher(config)

        # 初始化优化模块
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.concurrent_limiter = ConcurrentLimiter(self.rate_limit_config)
        self.deduplicator = ContentDeduplicator(threshold=0.75)

        logger.info("✅ Researcher 初始化完成 (原生异步模式 + 优化)")

    async def research_async(
        self,
        niche: str,
        days: int = 7,
        sources: str = "x,reddit,youtube,web,tiktok,hackernews",
        timeout_secs: float = 30.0,
    ) -> Dict:
        """异步研究方法 - 并行获取多平台数据（带超时保护）

        Args:
            niche: 研究领域/话题
            days: 回溯天数 (1-30)
            sources: 数据源，逗号分隔
            timeout_secs: 总超时时间（秒），默认30秒

        Returns:
            Dict: 研究结果
        """
        logger.info(f"开始异步研究: {niche}, days={days}, sources={sources}, timeout={timeout_secs}s")

        source_list = [s.strip().lower() for s in sources.split(",")]

        # 创建并行任务（带并发限制）
        tasks = []
        task_sources = []

        async def limited_fetch(platform: str, fetcher, niche: str, days: int) -> tuple:
            """限制并发的获取函数"""
            try:
                # 获取信号量
                await self.concurrent_limiter.acquire(platform)
                try:
                    # 执行获取（带超时）
                    result = await asyncio.wait_for(
                        fetcher.fetch(niche, days, timeout=self.rate_limit_config.request_timeout_secs),
                        timeout=self.rate_limit_config.request_timeout_secs,
                    )
                    return platform, result
                finally:
                    self.concurrent_limiter.release(platform)
            except asyncio.TimeoutError:
                logger.warning(f"[{platform}] 超时（{self.rate_limit_config.request_timeout_secs}s）")
                return platform, {"error": "timeout", "platform": platform}
            except Exception as e:
                logger.warning(f"[{platform}] 错误: {e}")
                return platform, {"error": str(e), "platform": platform}

        if "reddit" in source_list:
            tasks.append(limited_fetch("reddit", self.reddit_fetcher, niche, days))

        if "hackernews" in source_list or "hn" in source_list:
            tasks.append(limited_fetch("hackernews", self.hn_fetcher, niche, days))

        if "web" in source_list or "google_trends" in source_list:
            tasks.append(limited_fetch("google_trends", self.trends_fetcher, niche, days))

        # 模拟平台（X/TikTok/YouTube）
        for platform in ["x", "twitter"]:
            if platform in source_list:
                tasks.append(limited_fetch("x", self.simulated_fetcher, niche, days))
                break

        for platform in ["tiktok"]:
            if platform in source_list:
                tasks.append(limited_fetch("tiktok", self.simulated_fetcher, niche, days))
                break

        for platform in ["youtube", "yt"]:
            if platform in source_list:
                tasks.append(limited_fetch("youtube", self.simulated_fetcher, niche, days))
                break

        # 并行执行（带总超时保护）
        if not tasks:
            logger.warning("没有有效的数据源")
            return self._empty_result(niche)

        try:
            results = await gather_with_timeout(tasks, timeout=timeout_secs, return_exceptions=False)
        except Exception as e:
            logger.error(f"并行获取失败: {e}")
            return self._empty_result(niche, str(e))

        # 合并结果
        platform_data = {}
        citations = []
        total_posts = 0
        platform_sources = []

        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                source, data = result
            else:
                logger.warning(f"意外的结果格式: {result}")
                continue

            if isinstance(data, dict):
                platform_data[source] = data
                platform_sources.append(source)

                # 跳过错误数据
                if "error" in data:
                    logger.warning(f"{source} 返回错误: {data.get('error')}")
                    continue

                posts = data.get("posts", [])
                total_posts += len(posts)

                # 提取citations并去重
                for post in posts[:3]:
                    citation = {
                        "platform": source,
                        "title": post.get("title", ""),
                        "url": post.get("url", ""),
                        "text": post.get("text", post.get("title", "")),
                    }
                    citations.append(citation)

        # 【新增】使用去重器清理citations
        if citations:
            unique_citations = self.deduplicator.deduplicate_batch(
                citations, content_key="text", score_key="score"
            )
            logger.info(
                f"去重: {len(citations)} citations → {len(unique_citations)} unique"
            )
            citations = unique_citations

        # 计算指标
        metrics = self._calculate_metrics(platform_data, total_posts)

        # 计算风险评分
        risk_score = self._calculate_risk_score(metrics)

        result = {
            "niche": niche,
            "days": days,
            "sources": sources,
            "relevance_score": metrics["relevance"],
            "velocity_24h": metrics["velocity"],
            "authority_score": metrics["authority"],
            "platform_count": metrics["platform_count"],
            "platform_sources": platform_sources,  # 【新增】用于平台多样性计算
            "risk_score": risk_score,
            "total_posts": total_posts,
            "summary": self._generate_summary(platform_data, metrics, risk_score),
            "citations": citations[:10],
            "platforms": list(platform_data.keys()),
            "platform_data": platform_data,
            "created_at": datetime.now().isoformat(),
        }

        # 本地缓存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        cache_path = self.cache_dir / f"research_{niche}_{timestamp}.json"
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"研究结果已缓存: {cache_path}")
        except Exception as e:
            logger.warning(f"缓存失败: {e}")

        return result

    def research_topic(
        self, niche: str, days: int = 7, sources: str = "x,reddit,youtube,web,tiktok,hackernews"
    ) -> Dict:
        """同步版本的研究方法（兼容旧接口）

        Args:
            niche: 研究领域/话题
            days: 回溯天数
            sources: 数据源

        Returns:
            Dict: 研究结果
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # 如果事件循环已在运行，创建新的
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.research_async(niche, days, sources))
                return future.result()
        else:
            return loop.run_until_complete(self.research_async(niche, days, sources))

    def _calculate_metrics(self, platform_data: Dict, total_posts: int) -> Dict:
        """计算综合指标

        Args:
            platform_data: 各平台数据
            total_posts: 总帖子数

        Returns:
            Dict: 指标字典
        """
        # 相关度：基于关键词匹配（简化计算）
        relevance = min(100.0, 50.0 + (total_posts / 10) * 5)

        # 增速：基于帖子数量估算
        velocity = min(100.0, 20.0 + (total_posts / 5) * 10)

        # 权威度：基于平台数据质量
        authority = 50.0
        for platform, data in platform_data.items():
            if isinstance(data, dict) and not data.get("mock"):
                authority += 10
        authority = min(100.0, authority)

        # 平台数
        platform_count = len(
            [p for p in platform_data if not isinstance(platform_data.get(p), Exception)]
        )

        return {
            "relevance": round(relevance, 1),
            "velocity": round(velocity, 1),
            "authority": round(authority, 1),
            "platform_count": platform_count,
        }

    def _calculate_risk_score(self, metrics: Dict) -> float:
        """计算风险评分

        风险评分逻辑：
        - velocity 过高 (+20风险)
        - 平台数过少 (+15风险)
        - authority 过低 (+10风险)

        risk_score 越低越安全，< 70 才可自动发布

        Args:
            metrics: 指标数据

        Returns:
            float: 风险评分 (0-100)，越低越安全
        """
        base_risk = 30.0

        velocity = metrics.get("velocity", 0)
        platform_count = metrics.get("platform_count", 1)
        authority = metrics.get("authority", 50)

        # 增速过高增加风险
        if velocity > 80:
            base_risk += 20
        elif velocity > 60:
            base_risk += 10

        # 平台数过少增加风险
        if platform_count < 2:
            base_risk += 15
        elif platform_count < 3:
            base_risk += 8

        # 权威度过低增加风险
        if authority < 40:
            base_risk += 10
        elif authority < 60:
            base_risk += 5

        return round(min(100.0, max(0.0, base_risk)), 1)

    def _generate_summary(
        self, platform_data: Dict, metrics: Dict, risk_score: float = None
    ) -> str:
        """生成研究摘要

        Args:
            platform_data: 各平台数据
            metrics: 指标数据
            risk_score: 风险评分

        Returns:
            str: 摘要文本
        """
        platforms = list(platform_data.keys())
        summary = f"在 {len(platforms)} 个平台发现了相关内容。"

        if metrics["velocity"] > 60:
            summary += "话题热度较高，建议及时跟进。"
        elif metrics["velocity"] > 40:
            summary += "话题处于中等热度，可以适度参与。"
        else:
            summary += "话题热度一般，需要更多内容优化。"

        risk = risk_score if risk_score is not None else metrics.get("risk_score", 50)

        if risk >= 80:
            summary += " ⚠️ 风险较高，建议人工审核。"
        elif risk >= 50:
            summary += " 🟡 存在中等风险，请谨慎发布。"
        else:
            summary += " ✅ 风险较低，可考虑自动发布。"

        return summary

    def _empty_result(self, niche: str, error: str = None) -> Dict:
        """空结果

        Args:
            niche: 研究领域
            error: 错误信息

        Returns:
            Dict: 空结果
        """
        return {
            "niche": niche,
            "relevance_score": 0.0,
            "velocity_24h": 0.0,
            "authority_score": 0.0,
            "platform_count": 0,
            "risk_score": 100.0,
            "summary": f"研究失败: {error}" if error else "无数据",
            "citations": [],
            "platforms": [],
            "created_at": datetime.now().isoformat(),
            "error": error,
        }

    async def research_batch(self, niches: List[str], days: int = 7) -> List[Dict]:
        """批量研究多个领域

        Args:
            niches: 领域列表
            days: 回溯天数

        Returns:
            List[Dict]: 研究结果列表
        """
        tasks = [self.research_async(niche, days) for niche in niches]
        return await asyncio.gather(*tasks)


# 便捷函数
def research_topic(
    niche: str, days: int = 7, sources: str = "x,reddit,youtube,web,tiktok,hackernews"
) -> Dict:
    """便捷函数：研究单个话题

    Args:
        niche: 研究领域
        days: 回溯天数
        sources: 数据源

    Returns:
        Dict: 研究结果
    """
    researcher = Researcher()
    return researcher.research_topic(niche, days, sources)


async def research_batch(niches: List[str], days: int = 7) -> List[Dict]:
    """便捷函数：批量研究

    Args:
        niches: 领域列表
        days: 回溯天数

    Returns:
        List[Dict]: 研究结果列表
    """
    researcher = Researcher()
    return await researcher.research_batch(niches, days)
