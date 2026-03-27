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
        """每日复盘任务"""
        logger.info("[Scheduler] 开始每日复盘")

        try:
            from modules.generator import generate_daily_review

            today = datetime.now(UK_TIMEZONE).strftime("%Y-%m-%d")
            report = await generate_daily_review(
                date=today, niche="adult", stats={}, missed_trends=[]
            )

            logger.info(f"[Scheduler] 复盘完成")

        except Exception as e:
            logger.error(f"[Scheduler] 复盘失败: {e}")


def create_scheduler(db=None, generator=None, openclaw_bridge=None, bot=None) -> SchedulerManager:
    """创建调度器"""
    return SchedulerManager(db=db, generator=generator, openclaw_bridge=openclaw_bridge, bot=bot)
