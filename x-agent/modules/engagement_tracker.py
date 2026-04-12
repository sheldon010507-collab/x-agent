"""
engagement_tracker.py - 自动拉取推文互动数据

功能：
  1. 定期同步 X 推文的实时互动数据（点赞、转发、回复、浏览）
  2. 计算 engagement_rate 并存入 posts_analytics 表
  3. 根据 niche 和 type 统计性能数据
  4. 触发学习反馈（高互动/低互动提示）

集成方式：
  - APScheduler 定时任务（每小时）
  - 在 api.py 中的 @app.on_event("startup") 初始化
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EngagementTracker:
    """自动拉取 X 推文互动数据"""

    def __init__(self, db, config):
        """
        初始化追踪器

        Args:
            db: 数据库实例
            config: 配置对象
        """
        self.db = db
        self.config = config
        self.x_automation = None

    async def initialize(self) -> bool:
        """初始化 X 自动化模块"""
        try:
            from modules.x_automation import create_x_automation

            self.x_automation = await create_x_automation(self.config)
            logger.info("✅ EngagementTracker 初始化完成")
            return True
        except Exception as e:
            logger.error(f"❌ EngagementTracker 初始化失败: {e}")
            return False

    async def sync_engagement_data(self, hours_lookback: int = 24) -> Dict:
        """
        定期同步互动数据（由 APScheduler 定时调用）

        流程:
        1. 查询过去 N 小时发布的推文
        2. 逐条拉取最新互动数据（点赞、转发、回复、浏览）
        3. 计算 engagement_rate = (likes + retweets + replies) / views
        4. 存入 posts_analytics 表
        5. 更新 niche_performance 统计
        6. 触发学习反馈

        Args:
            hours_lookback: 回溯小时数，默认24小时

        Returns:
            dict: 同步统计信息
        """
        logger.info(f"🔄 开始同步过去 {hours_lookback} 小时的互动数据...")

        cutoff_time = datetime.now() - timedelta(hours=hours_lookback)

        # 1. 获取待同步的推文
        try:
            recent_posts = await self.db.execute("""
                SELECT id, x_url, niche, type, content, publish_time
                FROM posts
                WHERE platform = 'x'
                  AND status = 'published'
                  AND publish_time > ?
                ORDER BY publish_time DESC
            """, (cutoff_time.isoformat(),))
        except Exception as e:
            logger.error(f"查询待同步推文失败: {e}")
            return {"success": False, "error": str(e)}

        if not recent_posts:
            logger.info("📌 无待同步推文")
            return {"success": True, "synced_count": 0, "message": "暂无数据"}

        logger.info(f"📊 发现 {len(recent_posts)} 条待同步推文")

        synced_count = 0
        failed_count = 0

        for post in recent_posts:
            try:
                post_id = post[0]
                x_url = post[1]
                niche = post[2]
                type_ = post[3]
                content = post[4]
                publish_time = post[5]

                # 2. 拉取互动数据
                metrics = await self._fetch_post_metrics(x_url)
                if not metrics:
                    logger.warning(f"⚠️  无法获取推文 {post_id} 的互动数据")
                    failed_count += 1
                    continue

                # 3. 计算 engagement_rate
                engagement_rate = self._calculate_engagement_rate(metrics)

                # 4. 存入 posts_analytics 表
                analytics_id = f"analytics_{post_id}_{datetime.now().timestamp()}"
                await self.db.execute("""
                    INSERT INTO posts_analytics
                    (id, post_id, platform, content, niche, type, publish_time,
                     likes_count, retweets_count, replies_count, views_count,
                     engagement_rate, last_sync, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analytics_id,
                    post_id,
                    'x',
                    content,
                    niche,
                    type_,
                    publish_time,
                    metrics['likes'],
                    metrics['retweets'],
                    metrics['replies'],
                    metrics['views'],
                    engagement_rate,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ))

                synced_count += 1
                logger.info(
                    f"  ✓ 推文 {post_id[:8]}... "
                    f"(👍 {metrics['likes']}, 🔄 {metrics['retweets']}, "
                    f"💬 {metrics['replies']}, 👀 {metrics['views']}, "
                    f"engagement: {engagement_rate:.2%})"
                )

                # 延迟避免限流
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"同步推文 {post[0]} 失败: {e}")
                failed_count += 1
                continue

        # 5. 更新 niche_performance 统计
        logger.info("📈 更新 niche_performance 统计...")
        await self._update_niche_performance()

        # 6. 触发学习反馈
        logger.info("🧠 触发学习反馈...")
        await self._trigger_learning_feedback()

        result = {
            "success": True,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "total_processed": len(recent_posts),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"✅ 同步完成: {synced_count}/{len(recent_posts)} 成功, "
            f"{failed_count} 失败"
        )

        return result

    async def _fetch_post_metrics(self, post_url: str) -> Optional[Dict]:
        """
        从 X API 或爬虫获取推文互动数据

        Args:
            post_url: 推文 URL (https://x.com/user/status/123456)

        Returns:
            dict: {'likes': int, 'retweets': int, 'replies': int, 'views': int}
        """
        try:
            if not self.x_automation:
                logger.warning("X 自动化未初始化，跳过数据拉取")
                return None

            # 使用 X 自动化爬虫获取
            metrics = await self.x_automation.get_post_metrics(post_url)

            return {
                'likes': metrics.get('favorite_count', 0),
                'retweets': metrics.get('retweet_count', 0),
                'replies': metrics.get('reply_count', 0),
                'views': metrics.get('impression_count', 0),
            }

        except Exception as e:
            logger.warning(f"获取推文指标失败 ({post_url}): {e}")
            return None

    def _calculate_engagement_rate(self, metrics: Dict) -> float:
        """
        计算互动率

        公式: engagement_rate = (likes + retweets + replies) / views

        Args:
            metrics: dict with keys: likes, retweets, replies, views

        Returns:
            float: 互动率 (0.0 ~ 1.0)
        """
        total_engagement = (
            metrics.get('likes', 0)
            + metrics.get('retweets', 0)
            + metrics.get('replies', 0)
        )

        views = metrics.get('views', 0)

        if views == 0:
            return 0.0

        return total_engagement / views

    async def _update_niche_performance(self, days: int = 7) -> bool:
        """
        更新 niche_performance 表

        统计过去 N 天各 niche/type 组合的平均互动率

        Args:
            days: 统计天数，默认7天

        Returns:
            bool: 是否更新成功
        """
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()

            # 查询各 niche/type 的统计数据
            stats = await self.db.execute("""
                SELECT
                    niche,
                    type,
                    COUNT(*) as total_posts,
                    AVG(engagement_rate) as avg_engagement,
                    AVG(likes_count) as avg_likes,
                    AVG(retweets_count) as avg_retweets,
                    AVG(replies_count) as avg_replies
                FROM posts_analytics
                WHERE created_at > ?
                GROUP BY niche, type
                ORDER BY avg_engagement DESC
            """, (cutoff_time,))

            if not stats:
                logger.info("📊 暂无统计数据")
                return False

            # 插入或更新 niche_performance
            for idx, stat in enumerate(stats, 1):
                niche, type_, total, avg_eng, avg_likes, avg_rt, avg_reply = stat

                perf_id = f"perf_{niche}_{type_}_{days}d"

                await self.db.execute("""
                    INSERT OR REPLACE INTO niche_performance
                    (id, niche, type, total_posts, avg_engagement_rate,
                     avg_likes, avg_retweets, avg_replies, engagement_rank,
                     period_days, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    perf_id,
                    niche,
                    type_,
                    int(total),
                    float(avg_eng) if avg_eng else 0.0,
                    float(avg_likes) if avg_likes else 0.0,
                    float(avg_rt) if avg_rt else 0.0,
                    float(avg_reply) if avg_reply else 0.0,
                    idx,  # engagement_rank
                    days,
                    datetime.now().isoformat(),
                ))

            logger.info(f"✅ 更新了 {len(stats)} 个 niche/type 组合的性能数据")
            return True

        except Exception as e:
            logger.error(f"更新 niche_performance 失败: {e}")
            return False

    async def _trigger_learning_feedback(self) -> int:
        """
        根据互动数据生成学习反馈

        规则:
        - 互动率 < 5% → low_engagement 反馈
        - 互动率 > 15% → high_engagement 反馈
        - 用户手动标记的 high/low

        Returns:
            int: 生成的反馈数量
        """
        try:
            # 获取过去7天的性能数据
            stats_7d = await self.db.execute("""
                SELECT id, niche, type, avg_engagement_rate, total_posts
                FROM niche_performance
                WHERE period_days = 7
                  AND last_updated > datetime('now', '-24 hours')
            """)

            if not stats_7d:
                logger.info("📊 暂无性能数据用于学习反馈")
                return 0

            feedback_count = 0

            for stat in stats_7d:
                _, niche, type_, avg_engagement, total_posts = stat

                # 跳过数据不足的情况
                if total_posts < 3:
                    continue

                # 低互动率警告
                if avg_engagement < 0.05:
                    feedback_id = f"feedback_{niche}_{type_}_low_{datetime.now().timestamp()}"

                    await self.db.execute("""
                        INSERT INTO learning_feedback
                        (id, feedback_type, niche, type, engagement_rate,
                         suggested_niche, adjustment_reason, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        feedback_id,
                        'low_engagement',
                        niche,
                        type_,
                        float(avg_engagement),
                        niche,  # 暂时不改变 niche
                        f"{niche}/{type_} 互动率仅 {avg_engagement:.1%}，建议考虑调整语气风格或发布时间",
                        datetime.now().isoformat(),
                    ))

                    feedback_count += 1
                    logger.info(f"  ⚠️  低互动反馈: {niche}/{type_} ({avg_engagement:.1%})")

                # 高互动率提示
                elif avg_engagement > 0.15:
                    feedback_id = f"feedback_{niche}_{type_}_high_{datetime.now().timestamp()}"

                    await self.db.execute("""
                        INSERT INTO learning_feedback
                        (id, feedback_type, niche, type, engagement_rate,
                         adjustment_reason, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        feedback_id,
                        'high_engagement',
                        niche,
                        type_,
                        float(avg_engagement),
                        f"{niche}/{type_} 互动率达 {avg_engagement:.1%}，表现出色！建议优先使用此组合",
                        datetime.now().isoformat(),
                    ))

                    feedback_count += 1
                    logger.info(f"  🎯 高互动反馈: {niche}/{type_} ({avg_engagement:.1%})")

            if feedback_count > 0:
                logger.info(f"✅ 生成 {feedback_count} 条学习反馈")

            return feedback_count

        except Exception as e:
            logger.error(f"生成学习反馈失败: {e}")
            return 0
