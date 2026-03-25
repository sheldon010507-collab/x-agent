"""
scheduler.py - 定时任务模块

功能：
- 每 2 小时自动采集热点
- 每日 21:00 自动复盘报告
- 自动评论任务调度
- 使用 APScheduler 实现
- 英国时区 (Europe/London)
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger(__name__)

# 英国时区
UK_TIMEZONE = pytz.timezone("Europe/London")


class SchedulerManager:
    """定时任务管理器"""
    
    def __init__(self, db=None, generator=None, openclaw_bridge=None, 
                 research_module=None, trends_module=None, bot=None):
        """
        初始化调度器
        
        Args:
            db: 数据库实例
            generator: 生成器实例
            openclaw_bridge: OpenClaw 桥接器
            research_module: 研究模块
            trends_module: 趋势模块
            bot: Bot 实例
        """
        self.scheduler = AsyncIOScheduler(timezone=UK_TIMEZONE)
        self.db = db
        self.generator = generator
        self.openclaw_bridge = openclaw_bridge
        self.research_module = research_module
        self.trends_module = trends_module
        self.bot = bot
        self.running = False
        
        # 任务 ID 前缀
        self.task_prefix = "x_agent_v3"
        
        # 任务状态
        self.last_fetch_time = None
        self.last_review_time = None
        self.last_comment_time = None
    
    async def start(self):
        """启动调度器"""
        self._setup_jobs()
        self.scheduler.start()
        self.running = True
        logger.info(f"[Scheduler] 已启动 (时区：{UK_TIMEZONE})")
    
    async def stop(self):
        """停止调度器"""
        self.running = False
        self.scheduler.shutdown(wait=False)
        logger.info("[Scheduler] 已停止")
    
    def _setup_jobs(self):
        """配置定时任务"""
        jobs_added = 0
        
        # 1. 每 2 小时自动采集热点
        try:
            self.scheduler.add_job(
                self._job_fetch_trends,
                trigger=IntervalTrigger(hours=2),
                id=f"{self.task_prefix}_fetch_trends",
                replace_existing=True,
                name="热点采集"
            )
            jobs_added += 1
            logger.info("[Scheduler] 已添加热点采集任务 (每 2 小时)")
        except Exception as e:
            logger.error(f"[Scheduler] 添加热点采集任务失败：{e}")
        
        # 2. 每日 21:00 自动复盘报告
        try:
            self.scheduler.add_job(
                self._job_daily_review,
                trigger=CronTrigger(hour=21, minute=0, timezone=UK_TIMEZONE),
                id=f"{self.task_prefix}_daily_review",
                replace_existing=True,
                name="每日复盘"
            )
            jobs_added += 1
            logger.info("[Scheduler] 已添加每日复盘任务 (21:00 UK)")
        except Exception as e:
            logger.error(f"[Scheduler] 添加每日复盘任务失败：{e}")
        
        # 3. 自动评论任务（每 30 分钟检查一次）
        try:
            self.scheduler.add_job(
                self._job_auto_comment,
                trigger=IntervalTrigger(minutes=30),
                id=f"{self.task_prefix}_auto_comment",
                replace_existing=True,
                name="自动评论"
            )
            jobs_added += 1
            logger.info("[Scheduler] 已添加自动评论任务 (每 30 分钟)")
        except Exception as e:
            logger.error(f"[Scheduler] 添加自动评论任务失败：{e}")
        
        # 4. 每日 00:00 重置计数器
        try:
            self.scheduler.add_job(
                self._job_reset_counts,
                trigger=CronTrigger(hour=0, minute=0, timezone=UK_TIMEZONE),
                id=f"{self.task_prefix}_reset_counts",
                replace_existing=True,
                name="重置计数"
            )
            jobs_added += 1
            logger.info("[Scheduler] 已添加重置计数任务 (00:00 UK)")
        except Exception as e:
            logger.error(f"[Scheduler] 添加重置计数任务失败：{e}")
        
        logger.info(f"[Scheduler] 共配置 {jobs_added} 个任务")
    
    # ============ 任务处理函数 ============
    
    async def _job_fetch_trends(self):
        """热点采集任务"""
        logger.info("[Scheduler] 开始热点采集任务")
        self.last_fetch_time = datetime.now(UK_TIMEZONE)
        
        try:
            if self.trends_module is None:
                logger.warning("[Scheduler] 趋势模块未加载")
                return
            
            # 调用趋势模块采集
            from . import trends
            
            all_trends = trends.fetch_all_trends()
            logger.info(f"[Scheduler] 采集完成：{len(all_trends)} 条")
            
            # 保存到数据库
            if self.db:
                self.db.save_trends(all_trends)
            
            # 通知（可选）
            if self.bot:
                await self._send_notification(
                    f"📊 热点采集完成\n"
                    f"时间：{self.last_fetch_time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"数量：{len(all_trends)} 条"
                )
            
        except Exception as e:
            logger.error(f"[Scheduler] 热点采集失败：{e}")
            if self.bot:
                await self._send_notification(f"❌ 热点采集失败：{str(e)}")
    
    async def _job_daily_review(self):
        """每日复盘任务"""
        logger.info("[Scheduler] 开始每日复盘任务")
        self.last_review_time = datetime.now(UK_TIMEZONE)
        
        try:
            if self.generator is None:
                logger.warning("[Scheduler] 生成器模块未加载")
                return
            
            # 生成复盘报告
            today = datetime.now(UK_TIMEZONE).strftime("%Y-%m-%d")
            
            # 获取今日统计
            stats = self._get_daily_stats()
            
            # 获取错过的热点
            missed_trends = self._get_missed_trends()
            
            # 生成报告
            report = await self.generator.generate_daily_review(
                date=today,
                niche="adult",
                stats=stats,
                missed_trends=missed_trends
            )
            
            logger.info(f"[Scheduler] 复盘完成")
            
            # 发送报告
            if self.bot:
                await self._send_notification(
                    f"📝 每日复盘报告\n"
                    f"日期：{today}\n\n"
                    f"{report}"
                )
            
        except Exception as e:
            logger.error(f"[Scheduler] 每日复盘失败：{e}")
            if self.bot:
                await self._send_notification(f"❌ 每日复盘失败：{str(e)}")
    
    async def _job_auto_comment(self):
        """自动评论任务"""
        logger.info("[Scheduler] 开始自动评论任务")
        self.last_comment_time = datetime.now(UK_TIMEZONE)
        
        try:
            if self.openclaw_bridge is None:
                logger.warning("[Scheduler] OpenClaw 桥接器未加载")
                return
            
            # 获取待评论的帖子（从数据库或队列）
            posts_to_comment = self._get_posts_to_comment()
            
            if not posts_to_comment:
                logger.info("[Scheduler] 无待评论帖子")
                return
            
            # 执行评论（限制数量）
            max_comments = 5  # 每次最多评论 5 条
            commented = 0
            
            for post in posts_to_comment[:max_comments]:
                if self.openclaw_bridge.comment_count >= self.openclaw_bridge.daily_comment_limit:
                    logger.info("[Scheduler] 达到每日评论上限")
                    break
                
                result = await self.openclaw_bridge.comment_on_post(
                    post_url=post['url'],
                    comment=post['comment'],
                    niche=post.get('niche', 'general')
                )
                
                if result.get('success'):
                    commented += 1
                    logger.info(f"[Scheduler] 评论成功：{post['url'][:50]}...")
                else:
                    logger.warning(f"[Scheduler] 评论失败：{result.get('reason')}")
            
            logger.info(f"[Scheduler] 自动评论完成：{commented}/{len(posts_to_comment[:max_comments])}")
            
        except Exception as e:
            logger.error(f"[Scheduler] 自动评论失败：{e}")
    
    async def _job_reset_counts(self):
        """重置计数器任务"""
        logger.info("[Scheduler] 开始重置每日计数")
        
        try:
            if self.openclaw_bridge:
                self.openclaw_bridge.reset_daily_counts()
            
            logger.info("[Scheduler] 计数已重置")
            
        except Exception as e:
            logger.error(f"[Scheduler] 重置计数失败：{e}")
    
    # ============ 辅助函数 ============
    
    def _get_daily_stats(self) -> Dict:
        """获取每日统计"""
        # 从数据库获取统计
        if self.db:
            return self.db.get_daily_stats()
        return {}
    
    def _get_missed_trends(self) -> List:
        """获取错过的热点"""
        # 从数据库获取错过的热点
        if self.db:
            return self.db.get_missed_trends()
        return []
    
    def _get_posts_to_comment(self) -> List[Dict]:
        """获取待评论的帖子"""
        # 从数据库或队列获取
        if self.db:
            return self.db.get_posts_to_comment()
        return []
    
    async def _send_notification(self, message: str):
        """发送通知"""
        if self.bot:
            try:
                await self.bot.send_message(message)
            except Exception as e:
                logger.error(f"[Scheduler] 发送通知失败：{e}")
    
    # ============ 任务管理 ============
    
    def add_job(self, func: Callable, trigger: str = 'interval', 
                **trigger_args) -> str:
        """
        添加自定义任务
        
        Args:
            func: 任务函数
            trigger: 触发器类型 ('interval', 'cron', 'date')
            trigger_args: 触发器参数
        
        Returns:
            str: 任务 ID
        """
        job_id = f"{self.task_prefix}_{func.__name__}"
        
        if trigger == 'interval':
            trigger_obj = IntervalTrigger(**trigger_args)
        elif trigger == 'cron':
            trigger_obj = CronTrigger(**trigger_args)
        elif trigger == 'date':
            trigger_obj = DateTrigger(**trigger_args)
        else:
            raise ValueError(f"不支持的触发器类型：{trigger}")
        
        self.scheduler.add_job(
            func,
            trigger=trigger_obj,
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"[Scheduler] 添加自定义任务：{job_id}")
        return job_id
    
    def remove_job(self, job_id: str):
        """移除任务"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"[Scheduler] 移除任务：{job_id}")
        except Exception as e:
            logger.warning(f"[Scheduler] 移除任务失败：{e}")
    
    def get_job_status(self, job_id: str) -> Dict:
        """获取任务状态"""
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            }
        return {'error': 'Job not found'}
    
    def get_all_jobs(self) -> List[Dict]:
        """获取所有任务状态"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            })
        return jobs
    
    def pause_job(self, job_id: str):
        """暂停任务"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"[Scheduler] 暂停任务：{job_id}")
        except Exception as e:
            logger.warning(f"[Scheduler] 暂停任务失败：{e}")
    
    def resume_job(self, job_id: str):
        """恢复任务"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"[Scheduler] 恢复任务：{job_id}")
        except Exception as e:
            logger.warning(f"[Scheduler] 恢复任务失败：{e}")


def create_scheduler(db=None, generator=None, openclaw_bridge=None,
                    research_module=None, trends_module=None, bot=None) -> SchedulerManager:
    """创建调度器实例"""
    return SchedulerManager(
        db=db,
        generator=generator,
        openclaw_bridge=openclaw_bridge,
        research_module=research_module,
        trends_module=trends_module,
        bot=bot
    )
