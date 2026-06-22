"""
scheduler.py - 定时任务模块

【V0 Final】此版本为生产级开源版本

功能：
- 每2小时热点采集
- 21:00复盘报告

版本：V0 Final
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

UK_TIMEZONE = pytz.timezone("Europe/London")


class SchedulerManager:
    """定时任务管理器"""

    def __init__(self, db=None, generator=None, openclaw_bridge=None, bot=None):
        self.scheduler = AsyncIOScheduler(timezone=UK_TIMEZONE)
        self.db = db
        self.generator = generator
        self.openclaw_bridge = openclaw_bridge
        self.bot = bot
        self.running = False

    async def start(self):
        """启动调度器"""
        self._setup_jobs()
        self.scheduler.start()
        self.running = True
        logger.info(f"[Scheduler] 已启动")

    async def stop(self):
        """停止调度器"""
        self.running = False
        self.scheduler.shutdown()
        logger.info("[Scheduler] 已停止")

    def _setup_jobs(self):
        """配置定时任务"""

        # 每2小时采集热点
        self.scheduler.add_job(
            self._job_fetch_trends,
            trigger=IntervalTrigger(hours=2),
            id="fetch_trends",
            replace_existing=True,
        )

        # 每天21:00复盘
        self.scheduler.add_job(
            self._job_daily_review,
            trigger=CronTrigger(hour=21, minute=0, timezone=UK_TIMEZONE),
            id="daily_review",
            replace_existing=True,
        )

        logger.info(f"[Scheduler] 已配置 {len(self.scheduler.get_jobs())} 个任务")

    async def _job_fetch_trends(self):
        """热点采集任务"""
        logger.info("[Scheduler] 开始热点采集")

        try:
            from modules.scorer import score_trends
            from modules.trends import fetch_all_trends

            trends = fetch_all_trends()
            scored = score_trends(trends)

            logger.info(f"[Scheduler] 采集完成: {len(scored)} 条")

        except Exception as e:
            logger.error(f"[Scheduler] 采集失败: {e}")

    async def _job_daily_review(self):
        """每日复盘 — 21:00 搜集热点 + 推送 Top-5 摘要到 Telegram"""
        logger.info("[Scheduler] 开始每日复盘Brief")

        try:
            from modules.research import Researcher
            from modules.scorer import TrendScorer
            from config import config

            researcher = Researcher(config=config)
            result = await researcher.research_async(
                niche="general",
                days=1,
                sources="reddit,hackernews,x",
                timeout_secs=25.0,
            )
            all_posts = []
            for src, data in result.items():
                if isinstance(data, dict) and "posts" in data:
                    all_posts.extend(data["posts"])

            scorer = TrendScorer(db=self.db)
            scored = [scorer.calculate_score(p) for p in all_posts]
            all_posts_with_score = [
                {**p, "score": s} for p, s in zip(all_posts, scored)
            ] if scored else all_posts
            all_posts_with_score.sort(key=lambda x: x.get("score", 0), reverse=True)
            top5 = all_posts_with_score[:5]

            lines = ["📊 Daily Brief — " + datetime.now(UK_TIMEZONE).strftime("%Y-%m-%d")]
            for i, p in enumerate(top5, 1):
                lines.append(f"{i}. {p.get('title','')[:80]} (score:{p.get('score',0):.0f})")

            brief = "\n".join(lines)

            if self.bot:
                chat_id = getattr(self.bot, "default_chat_id", None) or os.environ.get("TELEGRAM_CHAT_ID")
                if chat_id:
                    await self.bot.send_message(chat_id=chat_id, text=brief)
                else:
                    logger.info(f"[Daily Brief] {brief[:200]}...")
            else:
                logger.info(f"[Daily Brief] {brief[:200]}...")

            logger.info(f"[Scheduler] 复盘完成: {len(top5)} 条摘要")

        except Exception as e:
            logger.error(f"[Scheduler] 复盘失败: {e}")


def create_scheduler(db=None, generator=None, openclaw_bridge=None, bot=None) -> SchedulerManager:
    """创建调度器"""
    return SchedulerManager(db=db, generator=generator, openclaw_bridge=openclaw_bridge, bot=bot)
