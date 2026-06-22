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
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "x_agent.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

db = None


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
        self.db_path = db_path or str(DB_PATH)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        logger.info(f"✅ Database initialized at {self.db_path}")

    def _init_schema(self):
        cursor = self.conn.cursor()

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id TEXT PRIMARY KEY,
                trend_id TEXT,
                type TEXT,
                content TEXT,
                status TEXT DEFAULT 'draft',
                publish_result TEXT,
                published_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trend_id) REFERENCES trends(id)
            )
        """)

        cursor.execute("PRAGMA table_info(content)")
        content_columns = {row[1] for row in cursor.fetchall()}
        if "publish_result" not in content_columns:
            cursor.execute("ALTER TABLE content ADD COLUMN publish_result TEXT")
        if "published_at" not in content_columns:
            cursor.execute("ALTER TABLE content ADD COLUMN published_at TEXT")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                username TEXT NOT NULL,
                display_name TEXT DEFAULT '',
                password_hash TEXT DEFAULT '',
                cookies TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                status_detail TEXT DEFAULT '',
                daily_posts INTEGER DEFAULT 0,
                daily_likes INTEGER DEFAULT 0,
                daily_comments INTEGER DEFAULT 0,
                daily_limit_posts INTEGER DEFAULT 10,
                karma_or_followers INTEGER DEFAULT 0,
                account_age_days INTEGER DEFAULT 0,
                reputation_score REAL DEFAULT 100.0,
                last_post_time TEXT,
                last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                platform TEXT NOT NULL,
                action TEXT NOT NULL,
                query TEXT DEFAULT '',
                status TEXT DEFAULT 'running',
                items_found INTEGER DEFAULT 0,
                items_new INTEGER DEFAULT 0,
                items_duplicate INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                duration_seconds REAL DEFAULT 0,
                error_message TEXT DEFAULT '',
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                platform TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                title TEXT DEFAULT '',
                content TEXT DEFAULT '',
                author TEXT DEFAULT '',
                subreddit_or_handle TEXT DEFAULT '',
                upvotes INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                engagement_score REAL DEFAULT 0.0,
                top_comments TEXT DEFAULT '[]',
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                sighting_count INTEGER DEFAULT 1,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                level TEXT DEFAULT 'info',
                platform TEXT NOT NULL,
                account_id TEXT,
                message TEXT NOT NULL,
                resolved INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                report_type TEXT DEFAULT 'multi_platform',
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    # ========== Trends 表操作 ==========

    @db_operation
    def create_trend(self, niche: str, topic: str, source: str, score: float,
                     summary: str = None, citations: Dict = None, url: str = None) -> Dict:
        trend_id = str(uuid.uuid4())
        citations_str = json.dumps(citations) if citations else None
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO trends (id, niche, topic, source, score, summary, citations, url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (trend_id, niche, topic, source, score, summary, citations_str, url),
        )
        self.conn.commit()
        return {"id": trend_id, "niche": niche, "topic": topic, "source": source,
                "score": score, "summary": summary, "citations": citations, "url": url, "status": "new"}

    @db_operation
    def get_trends_by_score(self, min_score: float = 60, limit: int = 20) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM trends WHERE score >= ? AND status = 'new' ORDER BY score DESC LIMIT ?",
            (min_score, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    @db_operation
    def get_trend_by_id(self, trend_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM trends WHERE id = ?", (trend_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @db_operation
    def update_trend_status(self, trend_id: str, status: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE trends SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, trend_id),
        )
        self.conn.commit()

    def get_high_score_trends(self, min_score: float = 80) -> List[Dict]:
        return self.get_trends_by_score(min_score)

    # ========== risk_score 操作 ==========

    @db_operation
    def update_trend_risk_score(self, trend_id: str, risk_score: float) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE trends SET risk_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (risk_score, trend_id),
        )
        self.conn.commit()

    @db_operation
    def get_trends_by_risk(self, max_risk: float = 70, limit: int = 20) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM trends WHERE risk_score < ? AND status = 'new' ORDER BY score DESC LIMIT ?",
            (max_risk, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    @db_operation
    def get_medium_score_trends(self, min_score: float = 60, max_score: float = 79.99) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM trends WHERE score >= ? AND score <= ? AND status = 'new' ORDER BY score DESC",
            (min_score, max_score),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ========== Content 表操作 ==========

    @db_operation
    def create_content(self, trend_id: str, type: str, content: str, status: str = "draft") -> Dict:
        content_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO content (id, trend_id, type, content, status) VALUES (?, ?, ?, ?, ?)",
            (content_id, trend_id, type, content, status),
        )
        self.conn.commit()
        return {"id": content_id, "trend_id": trend_id, "type": type, "content": content, "status": status}

    @db_operation
    def get_content_by_id(self, content_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM content WHERE id = ?", (content_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @db_operation
    def update_content_status(self, content_id: str, status: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE content SET status = ? WHERE id = ?", (status, content_id))
        self.conn.commit()

    @db_operation
    def confirm_content(self, content_id: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE content SET status = ? WHERE id = ?", ("confirmed", content_id))
        self.conn.commit()

    @db_operation
    def get_pending_posts(self, limit: int = 5) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM content WHERE status = ? ORDER BY created_at ASC LIMIT ?",
            ("confirmed", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    @db_operation
    def update_post_status(self, content_id: str, status: str, result: Dict = None) -> None:
        result_json = json.dumps(result or {}, ensure_ascii=False)
        published_at = datetime.now().isoformat() if status == "published" else None
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE content SET status = ?, publish_result = ?, published_at = COALESCE(?, published_at) WHERE id = ?",
            (status, result_json, published_at, content_id),
        )
        self.conn.commit()

    # ========== Accounts 表 ==========

    @db_operation
    def create_account(self, account_data: Dict) -> Dict:
        account_id = account_data.get("id") or str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO accounts
            (id, platform, username, display_name, password_hash, cookies,
             status, status_detail, daily_posts, daily_likes, daily_comments,
             daily_limit_posts, karma_or_followers, account_age_days,
             reputation_score, last_post_time, last_activity, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account_id,
            account_data.get("platform", ""),
            account_data.get("username", ""),
            account_data.get("display_name", ""),
            account_data.get("password_hash", ""),
            account_data.get("cookies", ""),
            account_data.get("status", "active"),
            account_data.get("status_detail", ""),
            account_data.get("daily_posts", 0),
            account_data.get("daily_likes", 0),
            account_data.get("daily_comments", 0),
            account_data.get("daily_limit_posts", 10),
            account_data.get("karma_or_followers", 0),
            account_data.get("account_age_days", 0),
            account_data.get("reputation_score", 100.0),
            account_data.get("last_post_time"),
            account_data.get("last_activity", datetime.now().isoformat()),
            account_data.get("created_at", datetime.now().isoformat()),
        ))
        self.conn.commit()
        return {"id": account_id, **{k: v for k, v in account_data.items() if k != "id"}}

    @db_operation
    def get_all_accounts(self, platform: str = None) -> List[Dict]:
        cursor = self.conn.cursor()
        if platform:
            cursor.execute("SELECT * FROM accounts WHERE platform = ?", (platform,))
        else:
            cursor.execute("SELECT * FROM accounts")
        return [dict(row) for row in cursor.fetchall()]

    @db_operation
    def get_account(self, account_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @db_operation
    def update_account(self, account_id: str, **kwargs) -> Optional[Dict]:
        account = self.get_account(account_id)
        if not account:
            return None
        allowed = {"status", "status_detail", "daily_posts", "daily_likes",
                   "daily_comments", "karma_or_followers", "reputation_score",
                   "last_post_time", "last_activity", "daily_limit_posts"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return account
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [account_id]
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE accounts SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return self.get_account(account_id)

    @db_operation
    def delete_account(self, account_id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    @db_operation
    def reset_daily_counters(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE accounts SET daily_posts = 0, daily_likes = 0, daily_comments = 0")
        self.conn.commit()

    @db_operation
    def increment_account_usage(self, account_id: str, action: str = "posts") -> bool:
        account = self.get_account(account_id)
        if not account:
            return False
        col_map = {"posts": "daily_posts", "likes": "daily_likes", "comments": "daily_comments"}
        col = col_map.get(action)
        if not col:
            return False
        cursor = self.conn.cursor()
        cursor.execute(
            f"UPDATE accounts SET {col} = {col} + 1, last_activity = ? WHERE id = ?",
            (datetime.now().isoformat(), account_id),
        )
        self.conn.commit()
        return True

    # ========== Runs 表 ==========

    @db_operation
    def record_run(self, run_data: Dict) -> Dict:
        run_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO runs (id, account_id, platform, action, query, status,
                              items_found, items_new, items_duplicate,
                              token_count, cost, duration_seconds, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            run_data.get("account_id"),
            run_data.get("platform", ""),
            run_data.get("action", ""),
            run_data.get("query", ""),
            run_data.get("status", "running"),
            run_data.get("items_found", 0),
            run_data.get("items_new", 0),
            run_data.get("items_duplicate", 0),
            run_data.get("token_count", 0),
            run_data.get("cost", 0.0),
            run_data.get("duration_seconds", 0),
            run_data.get("error_message", ""),
        ))
        self.conn.commit()
        return {"id": run_id, **run_data}

    @db_operation
    def update_run(self, run_id: str, **kwargs) -> Optional[Dict]:
        allowed = {"status", "items_found", "items_new", "items_duplicate",
                   "token_count", "cost", "duration_seconds", "error_message"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return self.get_run(run_id)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [run_id]
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE runs SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return self.get_run(run_id)

    @db_operation
    def get_run(self, run_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @db_operation
    def get_runs_by_account(self, account_id: str, limit: int = 50) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM runs WHERE account_id = ? ORDER BY started_at DESC LIMIT ?",
            (account_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    @db_operation
    def get_recent_runs(self, limit: int = 100) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # ========== Findings 表 ==========

    @db_operation
    def store_findings(self, run_id: str, findings: List[Dict]) -> Dict:
        cursor = self.conn.cursor()
        new_count = 0
        dup_count = 0
        for f in findings:
            url = f.get("url", "")
            if not url:
                dup_count += 1
                continue
            cursor.execute("SELECT id FROM findings WHERE url = ?", (url,))
            if cursor.fetchone():
                dup_count += 1
                continue
            finding_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO findings (id, run_id, platform, url, title, content,
                                      author, subreddit_or_handle, upvotes, comment_count,
                                      engagement_score, top_comments, first_seen, last_seen, sighting_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                finding_id, run_id,
                f.get("platform", ""), url,
                f.get("title", ""), f.get("content", ""),
                f.get("author", ""), f.get("subreddit_or_handle", ""),
                f.get("upvotes", 0), f.get("comment_count", 0),
                f.get("engagement_score", 0.0),
                json.dumps(f.get("top_comments", [])),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                1,
            ))
            new_count += 1
        self.conn.commit()
        return {"new": new_count, "duplicate": dup_count}

    @db_operation
    def get_findings_by_run(self, run_id: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM findings WHERE run_id = ? ORDER BY engagement_score DESC",
            (run_id,),
        )
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            if d.get("top_comments"):
                try:
                    d["top_comments"] = json.loads(d["top_comments"])
                except Exception:
                    pass
            results.append(d)
        return results

    # ========== Stats & 其他 ==========

    @db_operation
    def get_stats(self) -> Dict:
        cursor = self.conn.cursor()
        stats = {}
        cursor.execute("SELECT COUNT(*) as c FROM accounts")
        stats["total_accounts"] = cursor.fetchone()["c"]
        cursor.execute("""
            SELECT platform, COUNT(*) as count,
                   SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy
            FROM accounts GROUP BY platform
        """)
        stats["by_platform"] = {
            row["platform"]: {"total": row["count"], "healthy": row["healthy"]}
            for row in cursor.fetchall()
        }
        cursor.execute("SELECT COUNT(*) as c FROM runs")
        stats["total_runs"] = cursor.fetchone()["c"]
        cursor.execute(
            "SELECT COUNT(*) as c FROM runs WHERE started_at >= ?",
            ((datetime.now() - timedelta(days=1)).isoformat(),),
        )
        stats["runs_last_24h"] = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) as c FROM findings")
        stats["total_findings"] = cursor.fetchone()["c"]
        cursor.execute("""
            SELECT COUNT(*) as c, SUM(engagement_score) as total_engagement
            FROM findings WHERE last_seen >= ?
        """, ((datetime.now() - timedelta(days=1)).isoformat(),))
        row = cursor.fetchone()
        stats["findings_last_24h"] = row["c"] or 0
        stats["engagement_last_24h"] = round(row["total_engagement"] or 0, 1)
        cursor.execute("SELECT COUNT(*) as c FROM alerts WHERE resolved = 0")
        stats["active_alerts"] = cursor.fetchone()["c"]
        return stats

    @db_operation
    def get_current_niche(self) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT niche FROM trends ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else None

    @db_operation
    def get_daily_log(self, target_date: date) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as posts_count FROM content WHERE DATE(created_at) = ?",
            (target_date.isoformat(),),
        )
        row = cursor.fetchone()
        if row:
            return {"posts_count": row[0], "comments_count": 0,
                    "likes_count": 0, "rt_count": 0, "top_engagement": 0}
        return None

    @db_operation
    def save_report(self, content: str, report_type: str = "multi_platform",
                    timestamp: datetime = None) -> Dict:
        report_id = str(uuid.uuid4())
        created_at = (timestamp or datetime.now()).isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO reports (id, report_type, content, created_at) VALUES (?, ?, ?, ?)",
            (report_id, report_type, content, created_at),
        )
        self.conn.commit()
        return {
            "id": report_id,
            "report_type": report_type,
            "content": content,
            "created_at": created_at,
        }

    def close(self):
        if self.conn:
            self.conn.close()


db: Optional[Database] = None


def init_database(supabase_url: str = None, supabase_key: str = None) -> Database:
    global db
    db = Database()
    return db


def get_database() -> Database:
    if db is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    return db
