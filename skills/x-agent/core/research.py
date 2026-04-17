"""
research.py - 多平台浏览器采集协调器（含多层搜索 + engagement 排序）

特性：
- 自定义 query 透传到各平台 scrapers
- 多层级联过滤 (refines): 每层在前一层结果上继续缩小
- 全文匹配：标题 + 正文 + 描述 + 作者
- Engagement-based 排序：按真实点赞/转发/浏览量排序
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .browser import BrowserManager
from .deduplicator import ContentDeduplicator
from .scrapers import get_scraper
from .scorer import PostScorer
from .search import cascade_with_trace

logger = logging.getLogger(__name__)


class Researcher:
    """通过浏览器自动化跨平台采集真实数据"""

    def __init__(self, config=None, headless: bool = True):
        self.config = config
        self.browser = BrowserManager(headless=headless)
        self.deduplicator = ContentDeduplicator(threshold=0.75)
        self.post_scorer = PostScorer()

        if config and hasattr(config, "data_dir"):
            self.cache_dir = config.data_dir / "research"
        else:
            self.cache_dir = Path.home() / ".x-agent" / "data" / "research"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def research_async(
        self,
        niche: str,
        days: int = 7,
        sources: str = "x,reddit,hackernews,google_trends,youtube,tiktok",
        timeout_secs: float = 60.0,
        limit_per_source: int = 20,
        query: Optional[str] = None,
        refines: Optional[List[str]] = None,
        rank_by: str = "engagement",
    ) -> Dict:
        """
        多平台研究

        Args:
            niche: 预定义 niche
            query: 用户自定义关键词（覆盖 niche 默认查询）
            refines: 多层级联过滤词列表（在抓取后逐层缩小）
            rank_by: 'engagement' | 'velocity' | 'recent'
        """
        source_list = [s.strip().lower() for s in sources.split(",")]
        refines = refines or []

        try:
            await self.browser.start()
            tasks = []
            for src in source_list:
                try:
                    scraper = get_scraper(src, self.browser)
                except ValueError:
                    logger.warning(f"Unknown source: {src}")
                    continue
                tasks.append(self._safe_fetch(scraper, niche, days, limit_per_source, query))

            if not tasks:
                return self._empty_result(niche, "No valid sources")

            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout_secs,
                )
            except asyncio.TimeoutError:
                return self._empty_result(niche, f"Total timeout ({timeout_secs}s)")
        finally:
            await self.browser.stop()

        # 收集每平台 posts
        platform_data: Dict[str, Dict] = {}
        platform_sources: List[str] = []
        all_posts: List[Dict] = []
        filter_traces: List[Dict] = []

        for r in results:
            if isinstance(r, Exception):
                logger.warning(f"Scraper exception: {r}")
                continue
            if not isinstance(r, dict):
                continue
            src = r.get("platform", "unknown")
            posts = r.get("posts", [])

            # 1. 多层级联过滤（按平台分别做）
            if refines:
                trace = cascade_with_trace(posts, refines)
                posts = trace["posts"]
                filter_traces.append({"platform": src, "trace": trace["trace"]})

            # 2. 用 PostScorer 标注 engagement
            scored_posts = self.post_scorer.rank_posts(posts, src, by=rank_by)

            r["posts"] = scored_posts
            r["original_count"] = len(r.get("posts", []))
            platform_data[src] = r
            platform_sources.append(src)
            all_posts.extend(scored_posts)

        # 3. 全平台合并后再去重
        if all_posts:
            all_posts = self.deduplicator.deduplicate_batch(
                all_posts, content_key="text", score_key="engagement_score"
            )

        # 4. 全平台合并后按 engagement 排序
        sort_key = "engagement_score" if rank_by != "velocity" else "velocity_per_hour"
        all_posts_ranked = sorted(all_posts, key=lambda p: p.get(sort_key, 0), reverse=True)

        # 5. 提取 top 引用
        top_citations = [
            {
                "platform": p.get("platform"),
                "title": p.get("title", ""),
                "url": p.get("url", ""),
                "engagement_score": p.get("engagement_score", 0),
                "velocity_per_hour": p.get("velocity_per_hour", 0),
                "age_hours": p.get("age_hours", 0),
            }
            for p in all_posts_ranked[:10]
        ]

        # 6. 计算趋势级指标
        total_posts = len(all_posts_ranked)
        total_engagement = sum(p.get("engagement_score", 0) for p in all_posts_ranked)
        avg_velocity = (
            sum(p.get("velocity_per_hour", 0) for p in all_posts_ranked) / total_posts
            if total_posts
            else 0
        )

        metrics = self._calc_metrics(platform_data, total_posts, total_engagement, avg_velocity)
        risk_score = self._calc_risk(metrics)

        result = {
            "niche": niche,
            "query": query,
            "refines": refines,
            "days": days,
            "sources": sources,
            "rank_by": rank_by,
            "relevance_score": metrics["relevance"],
            "velocity_24h": metrics["velocity"],
            "authority_score": metrics["authority"],
            "engagement_score": metrics["engagement"],
            "platform_count": metrics["platform_count"],
            "platform_sources": platform_sources,
            "risk_score": risk_score,
            "total_posts": total_posts,
            "total_engagement": round(total_engagement, 1),
            "avg_velocity_per_hour": round(avg_velocity, 2),
            "summary": self._summary(platform_data, metrics, risk_score, refines),
            "filter_traces": filter_traces,
            "top_posts": all_posts_ranked[:10],
            "citations": top_citations,
            "platforms": list(platform_data.keys()),
            "platform_data": platform_data,
            "created_at": datetime.now().isoformat(),
        }

        # 缓存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        cache_path = self.cache_dir / f"research_{niche}_{timestamp}.json"
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        except Exception:
            pass

        return result

    async def _safe_fetch(
        self, scraper, niche: str, days: int, limit: int, query: Optional[str] = None
    ) -> Dict:
        try:
            return await scraper.fetch_trends(niche, days=days, limit=limit, query=query)
        except Exception as e:
            logger.warning(f"[{scraper.PLATFORM}] failed: {e}")
            return {
                "platform": scraper.PLATFORM,
                "niche": niche,
                "posts": [],
                "error": str(e),
                "fetched_at": datetime.now().isoformat(),
            }

    def research_topic(
        self,
        niche: str,
        days: int = 7,
        sources: str = "x,reddit,hackernews,google_trends,youtube,tiktok",
        query: Optional[str] = None,
        refines: Optional[List[str]] = None,
    ) -> Dict:
        return asyncio.run(
            self.research_async(
                niche, days, sources, query=query, refines=refines
            )
        )

    def _calc_metrics(
        self, platform_data: Dict, total_posts: int, total_engagement: float, avg_velocity: float
    ) -> Dict:
        """基于真实数据的趋势指标（不再只看 post 数量）"""
        # relevance：综合考虑帖子数 + 互动数
        relevance = min(100.0, 30.0 + (total_posts / 5) * 5 + (total_engagement / 1000) * 10)

        # velocity：基于平均每小时 engagement
        # 100 engagement/hour ≈ velocity 50; 1000 engagement/hour ≈ velocity 100
        velocity = min(100.0, 20.0 + (avg_velocity / 20))

        # engagement_score：归一化的总互动
        engagement_score = min(100.0, total_engagement / 100)

        # authority：每个非错误平台 +10，最低 50
        authority = 50.0
        for data in platform_data.values():
            if isinstance(data, dict) and not data.get("error") and data.get("posts"):
                authority += 10
        authority = min(100.0, authority)

        platform_count = len([p for p, d in platform_data.items() if not d.get("error")])

        return {
            "relevance": round(relevance, 1),
            "velocity": round(velocity, 1),
            "authority": round(authority, 1),
            "engagement": round(engagement_score, 1),
            "platform_count": platform_count,
        }

    def _calc_risk(self, metrics: Dict) -> float:
        risk = 30.0
        if metrics["velocity"] > 80:
            risk += 20
        elif metrics["velocity"] > 60:
            risk += 10
        if metrics["platform_count"] < 2:
            risk += 15
        elif metrics["platform_count"] < 3:
            risk += 8
        if metrics["authority"] < 40:
            risk += 10
        elif metrics["authority"] < 60:
            risk += 5
        return round(min(100.0, max(0.0, risk)), 1)

    def _summary(self, platform_data, metrics, risk_score, refines: List[str] = None):
        n = len([p for p, d in platform_data.items() if not d.get("error") and d.get("posts")])
        s = f"Found content on {n} platform(s)"
        if refines:
            s += f" after {len(refines)} refinement(s) [{', '.join(refines)}]"
        s += ". "
        if metrics["velocity"] > 60:
            s += "🔥 High velocity - act now. "
        elif metrics["velocity"] > 40:
            s += "Moderate velocity. "
        else:
            s += "Low velocity. "
        s += f"Total engagement: {metrics['engagement']:.0f}. "
        if risk_score >= 80:
            s += "⚠️ HIGH RISK."
        elif risk_score >= 50:
            s += "🟡 Medium risk."
        else:
            s += "✅ Low risk."
        return s

    def _empty_result(self, niche: str, error: str = None) -> Dict:
        return {
            "niche": niche,
            "relevance_score": 0.0,
            "velocity_24h": 0.0,
            "authority_score": 0.0,
            "engagement_score": 0.0,
            "platform_count": 0,
            "risk_score": 100.0,
            "summary": f"Research failed: {error}" if error else "No data",
            "citations": [],
            "platforms": [],
            "created_at": datetime.now().isoformat(),
        }

    def search_cached(
        self,
        queries: List[str],
        niche: Optional[str] = None,
        limit: int = 50,
    ) -> Dict:
        """
        在缓存的研究结果中级联搜索（不重新抓取）

        Args:
            queries: 级联过滤词列表
            niche: 限制 niche
            limit: 最多返回的帖子数

        Returns:
            匹配结果
        """
        from .storage import Storage

        storage = Storage(self.config.data_dir if self.config else None)
        cached_trends = storage.get_trends(niche=niche, limit=20)

        # 把所有缓存里的 posts 收集起来
        all_posts: List[Dict] = []
        for trend in cached_trends:
            for platform, data in trend.get("platform_data", {}).items():
                if isinstance(data, dict):
                    for post in data.get("posts", []):
                        post.setdefault("platform", platform)
                        all_posts.append(post)

        # 去重
        all_posts = self.deduplicator.deduplicate_batch(
            all_posts, content_key="text", score_key="engagement_score"
        )

        # 级联过滤
        trace = cascade_with_trace(all_posts, queries)

        # 按 engagement 排序
        sorted_posts = sorted(
            trace["posts"], key=lambda p: p.get("engagement_score", 0), reverse=True
        )

        return {
            "queries": queries,
            "niche_filter": niche,
            "total_cached_trends": len(cached_trends),
            "filter_trace": trace["trace"],
            "matched_posts": sorted_posts[:limit],
        }
