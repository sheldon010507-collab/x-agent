"""
database.py - 本地 SQLite 数据库模块

功能：
- 使用 SQLite 进行本地存储
- CRUD 封装
- risk_score 字段
- 状态流转

版本：V0 Final (Local SQLite)
"""

import functools
import json
import logging
import sqlite3
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 数据库文件路径
DB_PATH = Path(__file__).parent.parent / "data" / "x_agent.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class DatabaseError(Exception):
    """数据库操作异常"""

    pass


def db_operation(method):
    """数据库操作装饰器 — 统一捕获异常并记录日志"""

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
    """本地 SQLite 数据库操作类"""

    def __init__(self, db_path: str = None):
        """初始化数据库连接"""
        self.db_path = db_path or str(DB_PATH)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        logger.info(f"✅ Database initialized at {self.db_path}")

    def _init_schema(self):
        """初始化数据库结构"""
        cursor = self.conn.cursor()

        # Trends 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trends (
                id TEXT PRIMARY KEY,
                niche TEXT NOT NULL,
                topic TEXT NOT NULL,
                source TEXT,
                score REAL,
                summary TEXT,
                citations TEXT,
                url TEXT,
                status TEXT DEFAULT 'new',
                risk_score REAL DEFAULT 50,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Content 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id TEXT PRIMARY KEY,
                trend_id TEXT,
                type TEXT,
                content TEXT,
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trend_id) REFERENCES trends(id)
            )
        """)

        self.conn.commit()

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
        trend_id = str(uuid.uuid4())
        citations_str = json.dumps(citations) if citations else None

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO trends (id, niche, topic, source, score, summary, citations, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (trend_id, niche, topic, source, score, summary, citations_str, url))

        self.conn.commit()

        return {
            "id": trend_id,
            "niche": niche,
            "topic": topic,
            "source": source,
            "score": score,
            "summary": summary,
            "citations": citations,
            "url": url,
            "status": "new",
        }

    @db_operation
    def get_trends_by_score(self, min_score: float = 60, limit: int = 20) -> List[Dict]:
        """获取高于指定分数的热点（按分数降序）"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM trends
            WHERE score >= ? AND status = 'new'
            ORDER BY score DESC
            LIMIT ?
        """, (min_score, limit))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @db_operation
    def get_trend_by_id(self, trend_id: str) -> Optional[Dict]:
        """根据 ID 获取热点"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM trends WHERE id = ?", (trend_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @db_operation
    def update_trend_status(self, trend_id: str, status: str) -> None:
        """更新热点状态"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE trends SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, trend_id),
        )
        self.conn.commit()

    def get_high_score_trends(self, min_score: float = 80) -> List[Dict]:
        """获取高分热点（≥80 分，用于立即推送）"""
        return self.get_trends_by_score(min_score)

    # ========== risk_score 操作 ==========

    @db_operation
    def update_trend_risk_score(self, trend_id: str, risk_score: float) -> None:
        """更新热点风险评分"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE trends SET risk_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (risk_score, trend_id),
        )
        self.conn.commit()

    @db_operation
    def get_trends_by_risk(self, max_risk: float = 70, limit: int = 20) -> List[Dict]:
        """获取低风险热点"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM trends
            WHERE risk_score < ? AND status = 'new'
            ORDER BY score DESC
            LIMIT ?
        """, (max_risk, limit))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @db_operation
    def get_medium_score_trends(
        self, min_score: float = 60, max_score: float = 79.99
    ) -> List[Dict]:
        """获取中等分数热点（60-79 分）"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM trends
            WHERE score >= ? AND score <= ? AND status = 'new'
            ORDER BY score DESC
        """, (min_score, max_score))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ========== Content 表操作 ==========

    @db_operation
    def create_content(
        self, trend_id: str, type: str, content: str, status: str = "draft"
    ) -> Dict:
        """创建内容"""
        content_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO content (id, trend_id, type, content, status)
            VALUES (?, ?, ?, ?, ?)
        """, (content_id, trend_id, type, content, status))

        self.conn.commit()
        return {"id": content_id, "trend_id": trend_id, "type": type, "content": content, "status": status}

    @db_operation
    def get_content_by_id(self, content_id: str) -> Optional[Dict]:
        """根据 ID 获取内容"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM content WHERE id = ?", (content_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @db_operation
    def update_content_status(self, content_id: str, status: str) -> None:
        """更新内容状态"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE content SET status = ? WHERE id = ?", (status, content_id))
        self.conn.commit()

    # ========== 其他操作 ==========

    @db_operation
    def get_current_niche(self) -> Optional[str]:
        """获取当前 Niche（返回最近的一条）"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT niche FROM trends ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else None

    @db_operation
    def get_stats(self, start_date: date = None) -> Dict:
        """获取统计数据"""
        cursor = self.conn.cursor()

        date_filter = ""
        params = []
        if start_date:
            date_filter = "WHERE created_at >= ?"
            params.append(start_date.isoformat())

        cursor.execute(f"""
            SELECT
                COUNT(*) as content_generated,
                (SELECT COUNT(*) FROM trends {date_filter}) as trends_found,
                (SELECT COUNT(*) FROM trends WHERE score >= 80 {date_filter}) as high_score_trends
            FROM content {date_filter}
        """, params if start_date else [])

        row = cursor.fetchone()
        return {
            "content_generated": row[0] if row else 0,
            "trends_found": row[1] if row else 0,
            "high_score_trends": row[2] if row else 0,
        }

    @db_operation
    def confirm_content(self, content_id: str) -> None:
        """确认内容发布（draft → confirmed）"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE content SET status = ? WHERE id = ?",
            ("confirmed", content_id),
        )
        self.conn.commit()

    @db_operation
    def get_daily_log(self, target_date: date) -> Optional[Dict]:
        """获取指定日期的每日日报"""
        cursor = self.conn.cursor()
        date_str = target_date.isoformat()

        cursor.execute("""
            SELECT
                COUNT(*) as posts_count,
                0 as comments_count,
                0 as likes_count,
                0 as rt_count,
                0 as top_engagement
            FROM content
            WHERE DATE(created_at) = ?
        """, (date_str,))

        row = cursor.fetchone()
        if row:
            return {
                "posts_count": row[0],
                "comments_count": row[1],
                "likes_count": row[2],
                "rt_count": row[3],
                "top_engagement": row[4],
            }
        return None

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


# 全局数据库实例（延迟初始化）
db: Optional[Database] = None


def init_database(supabase_url: str = None, supabase_key: str = None) -> Database:
    """初始化数据库连接"""
    global db
    db = Database()
    return db


def get_database() -> Database:
    """获取数据库实例"""
    if db is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    return db
