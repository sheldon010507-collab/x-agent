"""
database.py - 数据库操作模块

【V0 Final】此版本为生产级开源版本

功能：
- CRUD封装
- risk_score字段
- 状态流转

版本：V0 Final
"""

import functools
import logging
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

try:
    from supabase import Client, create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None
    create_client = None

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """数据库操作异常"""

    pass


def db_operation(method):
    """数据库操作装饰器 — 统一捕获 Supabase 异常并记录日志"""

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"[DB] {method.__name__} failed: {e}", exc_info=True)
            raise DatabaseError(f"操作失败 ({method.__name__}): {e}") from e

    return wrapper


class Database:
    """Supabase 数据库操作类"""

    def __init__(self, supabase_url: str, supabase_key: str):
        """初始化数据库连接"""
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "Supabase SDK not installed. Install with: pip install supabase"
            )
        self.client: Client = create_client(supabase_url, supabase_key)

    # ========== Trends 表操作 ==========

    @db_operation
    def create_trend(
        self,
        niche: str,
        topic: str,
        source: str,
        score: float,
        summary: str = None,
        citations: Dict = None,
        url: str = None,
    ) -> Dict:
        """创建新的热点记录"""
        data = {
            "id": str(uuid.uuid4()),
            "niche": niche,
            "topic": topic,
            "source": source,
            "score": score,
            "summary": summary,
            "citations": citations,
            "url": url,
            "status": "new",
        }
        result = self.client.table("trends").insert(data).execute()
        return result.data[0] if result.data else None

    @db_operation
    def get_trends_by_score(self, min_score: float = 60, limit: int = 20) -> List[Dict]:
        """获取高于指定分数的热点（按分数降序）"""
        result = (
            self.client.table("trends")
            .select("*")
            .gte("score", min_score)
            .eq("status", "new")
            .order("score", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    @db_operation
    def get_trend_by_id(self, trend_id: str) -> Optional[Dict]:
        """根据 ID 获取热点"""
        result = self.client.table("trends").select("*").eq("id", trend_id).execute()
        return result.data[0] if result.data else None

    @db_operation
    def update_trend_status(self, trend_id: str, status: str) -> None:
        """更新热点状态"""
        self.client.table("trends").update({"status": status}).eq("id", trend_id).execute()

    def get_high_score_trends(self, min_score: float = 80) -> List[Dict]:
        """获取高分热点（≥80 分，用于立即推送）"""
        return self.get_trends_by_score(min_score)

    # ========== V0 Final: risk_score 操作 ==========

    @db_operation
    def update_trend_risk_score(self, trend_id: str, risk_score: float) -> None:
        """更新热点风险评分 (V0 Final)"""
        self.client.table("trends").update({"risk_score": risk_score}).eq("id", trend_id).execute()

    @db_operation
    def get_trends_by_risk(self, max_risk: float = 70, limit: int = 20) -> List[Dict]:
        """获取低风险热点 (V0 Final: risk_score < 70 为低风险，所有内容都需人工审核)"""
        result = (
            self.client.table("trends")
            .select("*")
            .lt("risk_score", max_risk)
            .eq("status", "new")
            .order("score", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    @db_operation
    def get_medium_score_trends(
        self, min_score: float = 60, max_score: float = 79.99
    ) -> List[Dict]:
        """获取中等分数热点（60-79 分，用于每日汇总）"""
        result = (
            self.client.table("trends")
            .select("*")
            .gte("score", min_score)
            .lt("score", max_score)
            .eq("status", "new")
            .order("score", desc=True)
            .execute()
        )
        return result.data

    # ========== Content Queue 表操作 ==========

    @db_operation
    def create_content(
        self,
        trend_id: str,
        type: str,
        content: str,
        media_suggestion: str = None,
        status: str = "draft",
    ) -> Dict:
        """创建内容草稿"""
        data = {
            "id": str(uuid.uuid4()),
            "trend_id": trend_id,
            "type": type,
            "content": content,
            "media_suggestion": media_suggestion,
            "status": status,
        }
        result = self.client.table("content_queue").insert(data).execute()
        return result.data[0] if result.data else None

    @db_operation
    def get_content_queue(self, status: str = "draft", limit: int = 20) -> List[Dict]:
        """获取待发布内容队列"""
        result = (
            self.client.table("content_queue")
            .select("*")
            .eq("status", status)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    @db_operation
    def update_content_status(self, content_id: str, status: str) -> None:
        """更新内容状态"""
        self.client.table("content_queue").update({"status": status}).eq("id", content_id).execute()

    # ========== V0 Final: 内容状态流转 (draft → confirmed/rejected/published) ==========

    @db_operation
    def confirm_content(self, content_id: str) -> None:
        """确认内容发布 (V0 Final: draft → confirmed)"""
        self.client.table("content_queue").update(
            {"status": "confirmed", "confirmed_at": datetime.now().isoformat()}
        ).eq("id", content_id).execute()

    @db_operation
    def reject_content(self, content_id: str) -> None:
        """拒绝内容 (V0 Final: draft → rejected)"""
        self.client.table("content_queue").update(
            {"status": "rejected", "rejected_at": datetime.now().isoformat()}
        ).eq("id", content_id).execute()

    @db_operation
    def publish_content(self, content_id: str) -> None:
        """标记内容已发布 (V0 Final: confirmed → published)"""
        self.client.table("content_queue").update(
            {"status": "published", "published_at": datetime.now().isoformat()}
        ).eq("id", content_id).execute()

    @db_operation
    def create_content_with_risk(
        self,
        trend_id: str,
        type: str,
        content: str,
        media_suggestion: str = None,
        risk_score: float = 50.0,
    ) -> Dict:
        """创建带风险评分的内容草稿 (V0 Final)"""
        data = {
            "id": str(uuid.uuid4()),
            "trend_id": trend_id,
            "type": type,
            "content": content,
            "media_suggestion": media_suggestion,
            "risk_score": risk_score,
            "status": "draft",
        }
        result = self.client.table("content_queue").insert(data).execute()
        return result.data[0] if result.data else None

    # ========== Daily Log 表操作 ==========

    @db_operation
    def create_daily_log(
        self,
        date: date,
        posts_count: int = 0,
        comments_count: int = 0,
        likes_count: int = 0,
        rt_count: int = 0,
        top_engagement: int = 0,
        notes: str = None,
    ) -> Dict:
        """创建每日记录"""
        data = {
            "id": str(uuid.uuid4()),
            "date": date.isoformat(),
            "posts_count": posts_count,
            "comments_count": comments_count,
            "likes_count": likes_count,
            "rt_count": rt_count,
            "top_engagement": top_engagement,
            "notes": notes,
        }
        result = self.client.table("daily_log").insert(data).execute()
        return result.data[0] if result.data else None

    @db_operation
    def get_daily_log(self, date: date) -> Optional[Dict]:
        """获取指定日期的记录"""
        result = self.client.table("daily_log").select("*").eq("date", date.isoformat()).execute()
        return result.data[0] if result.data else None

    @db_operation
    def update_daily_log(self, date: date, **kwargs) -> None:
        """更新每日记录"""
        self.client.table("daily_log").update(kwargs).eq("date", date.isoformat()).execute()

    # ========== Niche 表操作 ==========

    @db_operation
    def get_current_niche(self) -> Optional[str]:
        """获取当前激活的 Niche"""
        result = self.client.table("niche").select("name").eq("is_active", True).execute()
        return result.data[0]["name"] if result.data else None

    @db_operation
    def set_niche(self, niche_name: str, voice_file: str = None) -> None:
        """切换 Niche"""
        # 先停用所有 Niche
        self.client.table("niche").update({"is_active": False}).execute()

        # 激活指定 Niche
        data = {
            "name": niche_name,
            "is_active": True,
            "voice_file": voice_file or f"{niche_name}.md",
        }

        # 检查是否存在
        result = self.client.table("niche").select("id").eq("name", niche_name).execute()

        if result.data:
            self.client.table("niche").update(
                {"is_active": True, "voice_file": data["voice_file"]}
            ).eq("name", niche_name).execute()
        else:
            self.client.table("niche").insert(data).execute()

    # ========== Automation Settings 表操作 ==========

    @db_operation
    def get_automation_settings(self) -> Dict:
        """获取自动化设置"""
        result = (
            self.client.table("automation_settings")
            .select("*")
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

        return self.create_default_automation_settings()

    @db_operation
    def create_default_automation_settings(self) -> Dict:
        """创建默认自动化设置"""
        data = {
            "id": str(uuid.uuid4()),
            "auto_comment": True,
            "comment_daily_limit": 15,
            "auto_like": False,
            "auto_rt": False,
            "like_daily_limit": 30,
            "rt_daily_limit": 10,
            "updated_at": datetime.now().isoformat(),
        }
        result = self.client.table("automation_settings").insert(data).execute()
        return result.data[0] if result.data else data

    @db_operation
    def update_automation_settings(self, **kwargs) -> Dict:
        """更新自动化设置"""
        current = self.get_automation_settings()
        current_id = current.get("id")

        update_data = {k: v for k, v in kwargs.items() if k != "id"}
        update_data["updated_at"] = datetime.now().isoformat()

        self.client.table("automation_settings").update(update_data).eq("id", current_id).execute()

        return self.get_automation_settings()

    # ========== Strategy 表操作 ==========

    @db_operation
    def get_current_strategy(self, niche: str) -> Optional[Dict]:
        """获取当前 Niche 的策略"""
        result = (
            self.client.table("strategy")
            .select("*")
            .eq("niche", niche)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    @db_operation
    def create_strategy(self, niche: str, version: int, content: str) -> Dict:
        """创建新策略版本"""
        data = {"id": str(uuid.uuid4()), "niche": niche, "version": version, "content": content}
        result = self.client.table("strategy").insert(data).execute()
        return result.data[0] if result.data else None

    # ========== 统计查询 ==========

    @db_operation
    def get_today_stats(self, date: date = None) -> Dict:
        """获取今日统计"""
        if date is None:
            date = datetime.now().date()

        # 内容生成统计
        content_result = (
            self.client.table("content_queue")
            .select("type, status")
            .gte("created_at", date.isoformat())
            .execute()
        )

        # 热点统计
        trends_result = (
            self.client.table("trends")
            .select("score, status")
            .gte("created_at", date.isoformat())
            .execute()
        )

        return {
            "content_generated": len(content_result.data),
            "trends_found": len(trends_result.data),
            "high_score_trends": len([t for t in trends_result.data if t.get("score", 0) >= 80]),
        }


# 全局数据库实例（延迟初始化）
db: Optional[Database] = None


def init_database(supabase_url: str, supabase_key: str) -> Database:
    """初始化数据库连接"""
    global db
    db = Database(supabase_url, supabase_key)
    return db


def get_database() -> Database:
    """获取数据库实例"""
    if db is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    return db
