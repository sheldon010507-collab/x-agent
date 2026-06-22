"""
Dashboard 多账号监控系统
FastAPI + WebSocket + SQLite 持久化 + 实时数据可视化

升级要点:
- 集成 SQLite 持久化 (accounts/runs/findings/alerts)
- 集成质量遥测 (quality_telemetry)
- 真实 account pool 基于 DB
- 升级 Dashboard 前端 (历史图表、活动日志、账号卡片)
"""
import asyncio
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="X-Agent Dashboard", version="2.0.0")

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

class Platform(str, Enum):
    REDDIT = "reddit"
    X = "x"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    HACKERNEWS = "hackernews"

class AccountStatus(str, Enum):
    HEALTHY = "healthy"
    RATE_LIMITED = "rate_limited"
    SUSPENDED = "suspended"
    COOLDOWN = "cooldown"
    LOGIN_REQUIRED = "login_required"
    ERROR = "error"

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class SystemAlert:
    id: str
    level: AlertLevel
    platform: Platform
    account_id: str
    message: str
    created_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level.value,
            "platform": self.platform.value,
            "account_id": self.account_id,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "resolved": self.resolved,
        }

# ---------------------------------------------------------------------------
# DB-backed Account Pool
# ---------------------------------------------------------------------------

class AccountPool:
    """多平台账号池 — 基于 SQLite 持久化"""

    def __init__(self, db=None):
        self._db = db
        self._alerts: List[SystemAlert] = []
        self._alert_counter = 0

    def set_db(self, db) -> None:
        self._db = db

    # ----- 账号 CRUD -----

    def add_account(self, account) -> Dict:
        db_account = {
            "id": account.id,
            "platform": account.platform.value if hasattr(account.platform, "value") else account.platform,
            "username": account.username,
            "display_name": getattr(account, "display_name", ""),
            "status": getattr(account, "status", AccountStatus.HEALTHY).value if hasattr(getattr(account, "status", AccountStatus.HEALTHY), "value") else str(getattr(account, "status", "active")),
            "status_detail": getattr(account, "status_detail", ""),
            "daily_posts": getattr(account, "daily_posts", 0),
            "daily_likes": getattr(account, "daily_likes", 0),
            "daily_comments": getattr(account, "daily_comments", 0),
            "daily_limit_posts": getattr(account, "daily_limit_posts", 10),
            "karma_or_followers": getattr(account, "karma_or_followers", 0),
            "account_age_days": getattr(account, "account_age_days", 0),
            "reputation_score": getattr(account, "reputation_score", 100.0),
            "last_activity": datetime.now().isoformat(),
        }
        if self._db:
            try:
                self._db.create_account(db_account)
            except Exception as e:
                logger.warning(f"DB create_account failed: {e}")
        logger.info(f"Account added: {db_account['platform']}/{db_account['username']}")
        return db_account

    def get_all_accounts(self) -> List[Dict]:
        if self._db:
            try:
                return self._db.get_all_accounts()
            except Exception as e:
                logger.warning(f"DB get_all_accounts failed: {e}")
        return []

    def get_account(self, account_id: str) -> Optional[Dict]:
        if self._db:
            try:
                return self._db.get_account(account_id)
            except Exception as e:
                logger.warning(f"DB get_account failed: {e}")
        return None

    def get_accounts_by_platform(self, platform: str) -> List[Dict]:
        if self._db:
            try:
                return self._db.get_all_accounts(platform=platform)
            except Exception as e:
                logger.warning(f"DB get_accounts_by_platform failed: {e}")
        return [a for a in self.get_all_accounts() if a.get("platform") == platform]

    def update_account(self, account_id: str, **kwargs) -> Optional[Dict]:
        if self._db:
            try:
                result = self._db.update_account(account_id, **kwargs)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"DB update_account failed: {e}")
        return None

    def remove_account(self, account_id: str) -> bool:
        if self._db:
            try:
                return self._db.delete_account(account_id)
            except Exception as e:
                logger.warning(f"DB delete_account failed: {e}")
        return False

    def record_run(self, run_data: Dict) -> Dict:
        if self._db:
            try:
                self._db.record_run(run_data)
            except Exception as e:
                logger.warning(f"DB record_run failed: {e}")
        return run_data

    def store_findings(self, run_id: str, findings: List[Dict]) -> Dict:
        result = {"new": 0, "duplicate": 0}
        if self._db:
            try:
                result = self._db.store_findings(run_id, findings)
            except Exception as e:
                logger.warning(f"DB store_findings failed: {e}")
        return result

    def get_recent_runs(self, limit: int = 50) -> List[Dict]:
        if self._db:
            try:
                return self._db.get_recent_runs(limit)
            except Exception as e:
                logger.warning(f"DB get_recent_runs failed: {e}")
        return []

    def get_runs_by_account(self, account_id: str, limit: int = 20) -> List[Dict]:
        if self._db:
            try:
                return self._db.get_runs_by_account(account_id, limit)
            except Exception as e:
                logger.warning(f"DB get_runs_by_account failed: {e}")
        return []

    def get_findings_by_run(self, run_id: str) -> List[Dict]:
        if self._db:
            try:
                return self._db.get_findings_by_run(run_id)
            except Exception as e:
                logger.warning(f"DB get_findings_by_run failed: {e}")
        return []

    # ----- 限额管理 -----

    def increment_usage(self, account_id: str, action: str = "posts") -> bool:
        if self._db:
            try:
                return self._db.increment_account_usage(account_id, action)
            except Exception as e:
                logger.warning(f"DB increment_usage failed: {e}")
        return False

    def reset_daily_counters(self) -> None:
        if self._db:
            try:
                self._db.reset_daily_counters()
            except Exception as e:
                logger.warning(f"DB reset_daily_counters failed: {e}")

    # ----- 告警管理 -----

    def add_alert(self, level: AlertLevel, platform: Platform, account_id: str, message: str) -> SystemAlert:
        self._alert_counter += 1
        alert = SystemAlert(
            id=f"alert_{self._alert_counter}_{uuid.uuid4().hex[:8]}",
            level=level, platform=platform, account_id=account_id, message=message,
        )
        self._alerts.append(alert)
        if self._db:
            try:
                cursor = self._db.conn.cursor()
                cursor.execute(
                    "INSERT INTO alerts (id, level, platform, account_id, message) VALUES (?, ?, ?, ?, ?)",
                    (alert.id, alert.level.value, platform.value if hasattr(platform, "value") else str(platform),
                     account_id, message),
                )
                self._db.conn.commit()
            except Exception as e:
                logger.warning(f"DB insert alert failed: {e}")
        logger.warning(f"[{level.value}] {platform}/{account_id}: {message}")
        return alert

    def get_alerts(self, resolved: Optional[bool] = None) -> List[SystemAlert]:
        alerts = self._alerts
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def resolve_alert(self, alert_id: str) -> bool:
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.resolved = True
                return True
        return False

    def get_platform_summary(self) -> Dict[str, Any]:
        accounts = self.get_all_accounts()
        summary = defaultdict(lambda: {"total": 0, "healthy": 0, "rate_limited": 0,
                                        "suspended": 0, "total_posts_today": 0, "total_likes_today": 0})
        for a in accounts:
            p = a.get("platform", "unknown")
            summary[p]["total"] += 1
            s = a.get("status", "active")
            if s == "healthy":
                summary[p]["healthy"] += 1
            elif s == "rate_limited":
                summary[p]["rate_limited"] += 1
            elif s == "suspended":
                summary[p]["suspended"] += 1
            summary[p]["total_posts_today"] += a.get("daily_posts", 0)
            summary[p]["total_likes_today"] += a.get("daily_likes", 0)
        return dict(summary)

    def get_stats(self) -> Dict[str, Any]:
        try:
            return self._db.get_stats()
        except Exception:
            return {}


# 全局账号池实例
account_pool = AccountPool()

# ---------------------------------------------------------------------------
# WebSocket 连接管理
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WS client connected (total: {len(self.active_connections)})")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WS client disconnected (total: {len(self.active_connections)})")

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        await websocket.send_json(message)

manager = ConnectionManager()

# ---------------------------------------------------------------------------
# FastAPI 路由
# ---------------------------------------------------------------------------

@app.get("/")
async def dashboard():
    static_index = Path(__file__).parent / "static" / "index.html"
    if static_index.exists():
        return FileResponse(static_index)
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/api/accounts")
async def list_accounts(platform: Optional[str] = None):
    accounts = account_pool.get_accounts_by_platform(platform) if platform else account_pool.get_all_accounts()
    return {"accounts": accounts, "total": len(accounts)}

@app.get("/api/accounts/{account_id}")
async def get_account(account_id: str):
    account = account_pool.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@app.post("/api/accounts/{account_id}/status")
async def update_account_status(account_id: str, status: str, detail: str = ""):
    account = account_pool.update_account(account_id, status=status, status_detail=detail)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await manager.broadcast({"type": "account_update", "data": account})
    return account

@app.get("/api/summary")
async def get_summary():
    return {
        "platforms": account_pool.get_platform_summary(),
        "total_accounts": len(account_pool.get_all_accounts()),
        "stats": account_pool.get_stats(),
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/api/alerts")
async def get_alerts(resolved: Optional[bool] = None):
    alerts = account_pool.get_alerts(resolved)
    return {"alerts": [a.to_dict() for a in alerts], "total": len(alerts)}

@app.post("/api/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    if account_pool.resolve_alert(alert_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Alert not found")

@app.post("/api/reset-daily")
async def reset_daily():
    account_pool.reset_daily_counters()
    return {"success": True, "message": "Daily counters reset"}

@app.get("/api/runs")
async def get_runs(platform: Optional[str] = None, account_id: Optional[str] = None, limit: int = 50):
    """获取最近的 run 记录"""
    runs = account_pool.get_recent_runs(limit)
    if platform:
        runs = [r for r in runs if r.get("platform") == platform]
    if account_id:
        runs = [r for r in runs if r.get("account_id") == account_id]
    return {"runs": runs[:limit], "total": len(runs)}

@app.get("/api/runs/{run_id}/findings")
async def get_run_findings(run_id: str):
    findings = account_pool.get_findings_by_run(run_id)
    return {"findings": findings, "total": len(findings)}

@app.get("/api/posts")
async def get_posts(platform: Optional[str] = None, account_id: Optional[str] = None, days: int = 7, limit: int = 50):
    """获取最近发现/发布的帖子列表"""
    runs = account_pool.get_recent_runs(limit=limit * 3)
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    posts = []
    for run in runs:
        if run.get("started_at", "") < cutoff:
            continue
        if platform and run.get("platform") != platform:
            continue
        if account_id and run.get("account_id") != account_id:
            continue
        findings = account_pool.get_findings_by_run(run["id"])
        for f in findings:
            posts.append({
                "id": f.get("id", ""),
                "run_id": run["id"],
                "account_id": run.get("account_id", ""),
                "platform": run.get("platform", ""),
                "title": f.get("title", ""),
                "url": f.get("url", ""),
                "upvotes": f.get("upvotes", 0),
                "comments": f.get("comment_count", 0),
                "engagement": f.get("engagement_score", 0),
                "posted_at": run.get("started_at", ""),
                "status": run.get("status", ""),
                "author": f.get("author", ""),
                "subreddit": f.get("subreddit_or_handle", ""),
            })
    posts.sort(key=lambda p: p.get("posted_at", ""), reverse=True)
    return {"posts": posts[:limit], "total": len(posts)}

# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await manager.send_personal(websocket, {
            "type": "init",
            "data": {
                "accounts": account_pool.get_all_accounts(),
                "summary": account_pool.get_platform_summary(),
                "stats": account_pool.get_stats(),
                "alerts": [a.to_dict() for a in account_pool.get_alerts(resolved=False)[:10]],
                "recent_runs": account_pool.get_recent_runs(20),
                "dm_messages": [],
            }
        })
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action", "")

            if action == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
            elif action == "refresh":
                await manager.send_personal(websocket, {
                    "type": "update",
                    "data": {
                        "accounts": account_pool.get_all_accounts(),
                        "summary": account_pool.get_platform_summary(),
                        "stats": account_pool.get_stats(),
                        "recent_runs": account_pool.get_recent_runs(20),
                    }
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# DM / 消息监控 API
# ---------------------------------------------------------------------------

@app.get("/api/dm/{platform}")
async def get_dms(platform: str, limit: int = 20):
    """获取指定平台的 DM/消息列表。platform: x | reddit"""
    try:
        from .dm_monitor import AggregatedDMMonitor
        monitor = AggregatedDMMonitor()
        if platform == "all":
            messages = await monitor.fetch_all(limit_per_platform=limit)
        elif platform == "x":
            messages = await monitor.x.fetch_dms(limit=limit)
        elif platform == "reddit":
            from .dm_monitor import RedditDMMonitor
            rd_monitor = RedditDMMonitor()
            messages = await rd_monitor.fetch_dms(limit=limit)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")
        return {"messages": messages, "total": len(messages), "platform": platform}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DM fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dm/{platform}/refresh")
async def refresh_dms(platform: str):
    """手动触发 DM 刷新，结果通过 WebSocket 推送"""
    try:
        from .dm_monitor import AggregatedDMMonitor
        monitor = AggregatedDMMonitor()
        if platform == "all":
            messages = await monitor.fetch_all(limit_per_platform=20)
        elif platform == "x":
            messages = await monitor.x.fetch_dms(limit=20)
        elif platform == "reddit":
            from .dm_monitor import RedditDMMonitor
            rd_monitor = RedditDMMonitor()
            messages = await rd_monitor.fetch_dms(limit=20)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown: {platform}")

        await manager.broadcast({
            "type": "dm_update",
            "data": {"platform": platform, "messages": messages, "count": len(messages)},
        })
        return {"success": True, "count": len(messages)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DM refresh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# 后台任务
# ---------------------------------------------------------------------------

async def update_account_status_task():
    """定期检查账号状态并推送更新"""
    while True:
        try:
            accounts = account_pool.get_all_accounts()
            for account in accounts:
                posts = account.get("daily_posts", 0)
                limit = account.get("daily_limit_posts", 10)
                if posts >= limit:
                    account_pool.update_account(account["id"], status="cooldown")
                    account_pool.add_alert(
                        AlertLevel.WARNING,
                        Platform(account.get("platform", "reddit")),
                        account["id"],
                        f"Daily limit reached ({posts}/{limit})",
                    )
                elif posts >= limit * 0.85:
                    account_pool.add_alert(
                        AlertLevel.WARNING,
                        Platform(account.get("platform", "reddit")),
                        account["id"],
                        f"Near daily limit ({posts}/{limit})",
                    )

            telemetry_stats = {}
            try:
                from modules.quality_telemetry import telemetry as _tel
                telemetry_stats = _tel.global_stats()
            except ImportError:
                pass

            await manager.broadcast({
                "type": "update",
                "data": {
                    "accounts": accounts,
                    "summary": account_pool.get_platform_summary(),
                    "stats": account_pool.get_stats(),
                    "telemetry": telemetry_stats,
                    "recent_runs": account_pool.get_recent_runs(20),
                    "timestamp": datetime.now().isoformat(),
                }
            })
        except Exception as e:
            logger.error(f"Status update error: {e}")
        await asyncio.sleep(60)

# ---------------------------------------------------------------------------
# Dashboard HTML - 升级版 v2
# ---------------------------------------------------------------------------

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>X-Agent Dashboard v2</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
:root {
  --bg-primary: #0b1120;
  --bg-card: #151e32;
  --bg-card-hover: #1c2844;
  --bg-input: #1a2438;
  --text-primary: #e8edf5;
  --text-secondary: #7b8ba5;
  --accent: #6366f1;
  --accent-hover: #818cf8;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #06b6d4;
  --border: #1e2d4a;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans SC', sans-serif; background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; }
.header { background: var(--bg-card); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 50; }
.header h1 { font-size: 1.4rem; background: linear-gradient(135deg, var(--accent), #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header-right { display: flex; align-items: center; gap: 1rem; }
.ws-badge { display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; padding: 4px 12px; border-radius: 9999px; }
.ws-connected { background: rgba(34,197,94,0.15); color: var(--success); }
.ws-disconnected { background: rgba(239,68,68,0.15); color: var(--danger); }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-live { background: var(--success); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.4; } }
.btn { padding: 6px 14px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 500; transition: all 0.2s; }
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-ghost { background: transparent; color: var(--text-secondary); border: 1px solid var(--border); }
.btn-ghost:hover { background: var(--bg-card-hover); color: var(--text-primary); }
.container { padding: 1.5rem 2rem; max-width: 1600px; margin: 0 auto; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
.card { background: var(--bg-card); border-radius: 10px; padding: 1.25rem; border: 1px solid var(--border); transition: all 0.2s; }
.card:hover { border-color: var(--accent); }
.card-title { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-secondary); margin-bottom: 0.5rem; }
.metric { font-size: 2rem; font-weight: 700; }
.metric-sub { font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem; }
.section { margin-bottom: 2rem; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.section-title { font-size: 1.1rem; font-weight: 600; display: flex; align-items: center; gap: 0.5rem; }
.platform-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
.platform-card { background: var(--bg-card); border-radius: 10px; padding: 1.25rem; border: 1px solid var(--border); }
.platform-card h3 { font-size: 0.85rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
.account-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0; border-bottom: 1px solid var(--border); }
.account-item:last-child { border-bottom: none; }
.avatar { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; flex-shrink: 0; }
.account-info { flex: 1; min-width: 0; }
.account-name { font-weight: 600; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.account-meta { font-size: 0.75rem; color: var(--text-secondary); display: flex; gap: 0.75rem; }
.badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 10px; border-radius: 9999px; font-size: 0.7rem; font-weight: 600; }
.badge-healthy { background: rgba(34,197,94,0.15); color: var(--success); }
.badge-warning { background: rgba(245,158,11,0.15); color: var(--warning); }
.badge-danger { background: rgba(239,68,68,0.15); color: var(--danger); }
.badge-info { background: rgba(6,182,212,0.15); color: var(--info); }
.badge-neutral { background: rgba(123,139,165,0.15); color: var(--text-secondary); }
.progress { height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; margin-top: 4px; }
.progress-fill { height: 100%; border-radius: 2px; transition: width 0.5s ease; }
.tr-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.tr-table th { text-align: left; padding: 0.6rem; color: var(--text-secondary); font-weight: 500; border-bottom: 1px solid var(--border); font-size: 0.75rem; text-transform: uppercase; }
.tr-table td { padding: 0.6rem; border-bottom: 1px solid var(--border); }
.tr-table tr:hover td { background: var(--bg-card-hover); }
select.filter-select { background: var(--bg-input); color: var(--text-primary); border: 1px solid var(--border); padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; }
.tabs { display: flex; gap: 0; border-bottom: 1px solid var(--border); margin-bottom: 1rem; }
.tab { padding: 0.5rem 1rem; cursor: pointer; font-size: 0.85rem; color: var(--text-secondary); border-bottom: 2px solid transparent; transition: all 0.2s; }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab:hover { color: var(--text-primary); }
.hidden { display: none !important; }
.alert-panel { position: fixed; top: 70px; right: 20px; width: 360px; max-height: 60vh; overflow-y: auto; background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; z-index: 100; display: none; box-shadow: 0 10px 40px rgba(0,0,0,0.4); }
.alert-item { padding: 0.75rem; margin: 0.5rem; border-radius: 8px; font-size: 0.8rem; border-left: 3px solid; }
.alert-warning { background: rgba(245,158,11,0.08); border-color: var(--warning); }
.alert-critical { background: rgba(239,68,68,0.08); border-color: var(--danger); }
.alert-info { background: rgba(6,182,212,0.08); border-color: var(--info); }
.alert-ts { font-size: 0.7rem; color: var(--text-secondary); margin-top: 4px; }
.empty-state { text-align: center; padding: 3rem; color: var(--text-secondary); }
.health-bar { width: 60px; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.health-fill { height: 100%; border-radius: 3px; }
canvas { max-height: 250px; }

.dm-grid { display: flex; flex-direction: column; gap: 0.5rem; }
.dm-card { background: var(--bg-input); border: 1px solid var(--border); border-radius: 8px;
  padding: 0.75rem 1rem; display: flex; gap: 0.75rem; transition: border-color 0.2s; cursor: pointer; }
.dm-card:hover { border-color: var(--accent); }
.dm-avatar { width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-weight: 700; font-size: 0.85rem; flex-shrink: 0; }
.dm-body { flex: 1; min-width: 0; }
.dm-sender { font-weight: 600; font-size: 0.85rem; }
.dm-preview { font-size: 0.8rem; color: var(--text-secondary); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; margin-top: 2px; }
.dm-meta { font-size: 0.7rem; color: var(--text-secondary); margin-top: 4px;
  display: flex; gap: 0.75rem; }
.dm-badge { font-size: 0.65rem; padding: 2px 8px; border-radius: 9999px; font-weight: 600; }
.dm-unread { background: rgba(99,102,241,0.2); color: var(--accent); }
.dm-read { background: rgba(123,139,165,0.1); color: var(--text-secondary); }
.dm-x { background: rgba(29,161,242,0.15); color: #1da1f2; }
.dm-reddit { background: rgba(255,69,0,0.15); color: #ff4500; }
.dm-empty-state { text-align: center; padding: 2rem; color: var(--text-secondary); }

</style>
</head>
<body>

<div class="header">
  <div>
    <h1>🤖 X-Agent Dashboard</h1>
  </div>
  <div class="header-right">
    <span id="ws-status" class="ws-badge ws-disconnected"><span class="dot" style="background:var(--danger)"></span> Offline</span>
    <button class="btn btn-ghost" onclick="toggleAlerts()">🔔 <span id="alert-count">0</span></button>
    <button class="btn btn-primary" onclick="refreshData()">🔄 Refresh</button>
  </div>
</div>

<div class="alert-panel" id="alert-panel">
  <div style="padding:1rem;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;">
    <strong>⚠️ Alerts</strong>
    <button class="btn btn-ghost" onclick="toggleAlerts()" style="padding:2px 8px;">✕</button>
  </div>
  <div id="alerts-list"></div>
</div>

<div class="container">
  <!-- 概览卡片 -->
  <div class="grid" id="overview-cards"></div>

  <!-- 平台活动 + 遥测 -->
  <div class="section">
    <div class="grid" style="grid-template-columns: 2fr 1fr;">
      <div class="card">
        <div class="section-header"><h3 class="section-title">📈 Activity (7 days)</h3></div>
        <canvas id="activityChart"></canvas>
      </div>
      <div class="card">
        <div class="section-header"><h3 class="section-title">💊 Health</h3></div>
        <canvas id="healthChart"></canvas>
      </div>
    </div>
  </div>

  <!-- Tabs: Accounts / Runs -->
  <div class="section">
    <div class="tabs">
      <div class="tab active" onclick="switchTab('accounts')">👥 Accounts</div>
      <div class="tab" onclick="switchTab('runs')">⏱ Recent Runs</div>
          <div class="tab" onclick="switchTab('runs')">⏱ Recent Runs</div>
<div class="tab" onclick="switchTab('posts')">📝 Posts</div>
<div class="tab" onclick="switchTab('messages')">💬 Messages</div>
    </div>

    <!-- 账号 tab -->
    <div id="tab-accounts">
      <div class="card">
        <div class="section-header">
          <h3 class="section-title">📋 Account Status</h3>
          <div style="display:flex;gap:0.5rem;">
            <select class="filter-select" id="platform-filter" onchange="renderAccounts()">
              <option value="all">All Platforms</option>
              <option value="reddit">Reddit</option>
              <option value="x">X/Twitter</option>
              <option value="instagram">Instagram</option>
              <option value="tiktok">TikTok</option>
              <option value="youtube">YouTube</option>
              <option value="hackernews">HackerNews</option>
            </select>
          </div>
        </div>
        <div id="accounts-list"></div>
      </div>
    </div>

    <!-- Runs tab -->
    
<div id="tab-messages" class="hidden">
<div class="card">
<div class="section-header">
<h3 class="section-title">💬 Messages</h3>
<div style="display:flex;gap:0.5rem;">
<select class="filter-select" id="dm-platform-filter" onchange="loadMessages()">
<option value="all">All Platforms</option>
<option value="x">X / Twitter</option>
<option value="reddit">Reddit</option>
</select>
<button class="btn btn-primary" onclick="refreshMessages()">🔄 Refresh DMs</button>
</div>
</div>
<div class="dm-grid" id="messages-container"></div>
<div class="empty-state" id="dm-empty" style="display:none;">
No messages found. Click <strong>Refresh DMs</strong> to fetch.
</div>
</div>
</div>
<div id="tab-runs" class="hidden">
      <div class="card">
        <div class="section-header">
          <h3 class="section-title">⏱ Recent Runs</h3>
          <select class="filter-select" id="run-platform-filter" onchange="renderRuns()">
            <option value="all">All Platforms</option>
            <option value="reddit">Reddit</option>
            <option value="x">X/Twitter</option>
          </select>
        </div>

<div id="tab-posts" class="hidden">
<div class="card">
<div class="section-header">
<h3 class="section-title">📝 Posts & Findings</h3>
<div style="display:flex;gap:0.5rem;">
<select class="filter-select" id="post-platform-filter" onchange="renderPosts()">
<option value="all">All Platforms</option>
<option value="reddit">Reddit</option>
<option value="x">X/Twitter</option>
</select>
<select class="filter-select" id="post-account-filter" onchange="renderPosts()">
<option value="all">All Accounts</option>
</select>
</div>
</div>
<div style="overflow-x:auto;">
<table class="tr-table" id="posts-table">
<thead><tr><th>Time</th><th>Platform</th><th>Account</th><th>Title</th><th>Score</th><th>Comments</th><th>Author</th><th>Source</th></tr></thead>
<tbody id="posts-tbody"></tbody>
</table>
</div>
</div>
</div>

        <div style="overflow-x:auto;">
          <table class="tr-table" id="runs-table">
            <thead><tr><th>Time</th><th>Platform</th><th>Account</th><th>Action</th><th>Query</th><th>Status</th><th>New/Dup</th><th>Dur</th></tr></thead>
            <tbody id="runs-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const PLATFORM_COLORS = {
  reddit: '#ff4500', x: '#1da1f2', instagram: '#e1306c',
  tiktok: '#000000', youtube: '#ff0000', hackernews: '#ff6600', unknown: '#6366f1'

function switchTab(t) {
    currentTab = t;
    const tabs = ['accounts', 'runs', 'posts', 'messages'];
    tabs.forEach((name, i) => {
        const tabEl = document.querySelectorAll('.tab')[i];
        if (tabEl) tabEl.classList.toggle('active', name === t);
    });
    document.getElementById('tab-accounts').classList.toggle('hidden', t !== 'accounts');
    document.getElementById('tab-runs').classList.toggle('hidden', t !== 'runs');
    const postsTab = document.getElementById('tab-posts');
    if (postsTab) postsTab.classList.toggle('hidden', t !== 'posts');
    if (t === 'posts') renderPosts();
    const msgTab = document.getElementById('tab-messages');
    if (msgTab) msgTab.classList.toggle('hidden', t !== 'messages');
    if (t === 'messages') loadMessages();
}

async function loadMessages() {
    const filter = document.getElementById('dm-platform-filter').value;
    const container = document.getElementById('messages-container');
    const empty = document.getElementById('dm-empty');
    try {
        const r = await fetch(`/api/dm/${filter}`);
        const d = await r.json();
        const msgs = d.messages || [];
        if (!msgs.length) {
            container.innerHTML = '';
            empty.style.display = 'block';
            return;
        }
        empty.style.display = 'none';
        container.innerHTML = msgs.map(m => {
            const platformBadge = `<span class="dm-badge dm-${m.platform}">${m.platform.toUpperCase()}</span>`;
            const unreadBadge = m.unread ? '<span class="dm-badge dm-unread">Unread</span>' : '<span class="dm-badge dm-read">Read</span>';
            const avatarColor = m.platform === 'x' ? '#1da1f2' : '#ff4500';
            const avatar = `<div class="dm-avatar" style="background:${avatarColor}20;color:${avatarColor}">${(m.sender || '?')[0].toUpperCase()}</div>`;
            return `<div class="dm-card" onclick="window.open('${m.url}','_blank')">
                ${avatar}
                <div class="dm-body">
                    <div class="dm-sender">${m.sender} ${platformBadge} ${unreadBadge}</div>
                    <div class="dm-preview">${m.preview || '(no content)'}</div>
                    <div class="dm-meta">
                        <span>${m.timestamp ? new Date(m.timestamp).toLocaleString() : ''}</span>
                        ${m.account_id ? `<span>${m.account_id}</span>` : ''}
                    </div>
                </div>
            </div>`;
        }).join('');
    } catch (e) {
        console.error('loadMessages error:', e);
        container.innerHTML = '<div class="dm-empty-state">Failed to load messages</div>';
    }
}

async function refreshMessages() {
    const filter = document.getElementById('dm-platform-filter').value;
    try {
        const r = await fetch(`/api/dm/${filter}/refresh`, {method: 'POST'});
        const d = await r.json();
        if (d.success) loadMessages();
    } catch (e) {
        console.error('refreshMessages error:', e);
    }
}

};
const PLATFORM_ICONS = {
  reddit: '🔴', x: '🐦', instagram: '📸', tiktok: '🎵', youtube: '▶️', hackernews: '🟠'
};

let ws = null;
let activityChart = null;
let healthChart = null;
let currentTab = 'accounts';

function platformLabel(p) { return (PLATFORM_ICONS[p] || '⚪') + ' ' + (p || 'unknown').toUpperCase(); }
function statusBadge(s) {
  const m = { healthy: 'badge-healthy', rate_limited: 'badge-warning', suspended: 'badge-danger', cooldown: 'badge-info', login_required: 'badge-neutral', error: 'badge-danger', active: 'badge-healthy' };
  return `<span class="badge ${m[s] || 'badge-neutral'}">${s || 'unknown'}</span>`;
}
function progressColor(pct) { return pct > 80 ? 'var(--danger)' : pct > 50 ? 'var(--warning)' : 'var(--success)'; }
function healthColor(score) { return score >= 80 ? 'var(--success)' : score >= 50 ? 'var(--warning)' : 'var(--danger)'; }
function ts(s) { return s ? new Date(s).toLocaleString() : 'N/A'; }

function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(proto + '//' + location.host + '/ws');
  ws.onopen = () => {
    document.getElementById('ws-status').innerHTML = '<span class="dot dot-live"></span> Live';
    document.getElementById('ws-status').className = 'ws-badge ws-connected';
  };
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'init' || msg.type === 'update') renderDashboard(msg.data);
  };
  ws.onclose = () => {
    document.getElementById('ws-status').innerHTML = '<span class="dot" style="background:var(--danger)"></span> Offline';
    document.getElementById('ws-status').className = 'ws-badge ws-disconnected';
    setTimeout(connectWS, 3000);
  };
  ws.onerror = (err) => console.error('WS error', err);
}


function renderDashboard(data) {
  renderOverview(data);
  renderAccounts();
  renderPosts();
  renderRuns();
  updateAlerts(data.alerts || []);
  updateCharts(data);
}

function renderOverview(data) {
  const accounts = (data && data.accounts) || [];
  const summary = (data && data.summary) || {};
  const stats = (data && data.stats) || {};
  const tel = (data && data.telemetry) || {};
  let totalPosts = 0, healthy = 0;
  accounts.forEach(a => { totalPosts += (a.daily_posts || 0); if (a.status === 'healthy') healthy++; });
  const successRate = tel.global_success_rate != null ? (tel.global_success_rate * 100).toFixed(1) + '%' : 'N/A';
  document.getElementById('overview-cards').innerHTML = `
    <div class="card"><div class="card-title">Total Accounts</div><div class="metric">${accounts.length}</div><div class="metric-sub"><span class="badge badge-healthy">${healthy} healthy</span></div></div>
    <div class="card"><div class="card-title">Posts Today</div><div class="metric" style="color:var(--accent)">${totalPosts}</div><div class="metric-sub">Across all platforms</div></div>
    <div class="card"><div class="card-title">Success Rate</div><div class="metric" style="color:var(--success)">${successRate}</div><div class="metric-sub">${tel.total_runs || 0} runs tracked</div></div>
    <div class="card"><div class="card-title">Avg Health</div><div class="metric" style="color:${healthColor(tel.avg_health_score || 100)}">${tel.avg_health_score != null ? tel.avg_health_score : 'N/A'}</div><div class="metric-sub">${tel.accounts_with_issues || 0} accounts need attention</div></div>
    <div class="card"><div class="card-title">Findings</div><div class="metric" style="color:var(--info)">${stats.total_findings || 0}</div><div class="metric-sub">${stats.runs_last_24h || 0} runs today</div></div>
    <div class="card"><div class="card-title">Active Alerts</div><div class="metric" style="color:var(--warning)">${stats.active_alerts || 0}</div><div class="metric-sub">Requires attention</div></div>
  `;
}

function renderAccounts() {
  let accounts = [];
  try { const r = await fetch('/api/accounts'); const d = await r.json(); accounts = d.accounts || []; } catch(e) { return; }
  const filter = document.getElementById('platform-filter').value;
  if (filter !== 'all') accounts = accounts.filter(a => a.platform === filter);

  if (!accounts.length) {
    document.getElementById('accounts-list').innerHTML = '<div class="empty-state">No accounts configured. Add accounts via API or config.</div>';
    return;
  }

  // Group by platform
  const groups = {};
  accounts.forEach(a => {
    if (!groups[a.platform]) groups[a.platform] = [];
    groups[a.platform].push(a);
  });

  let html = '';
  for (const [plat, items] of Object.entries(groups)) {
    html += `<div class="platform-card"><h3>${platformLabel(plat)} (${items.length})</h3>`;
    items.forEach(a => {
      const pct = Math.min(((a.daily_posts || 0) / Math.max(a.daily_limit_posts || 10, 1)) * 100, 100);
      html += `
        <div class="account-item">
          <div class="avatar" style="background:${PLATFORM_COLORS[plat] || '#6366f1'}20;color:${PLATFORM_COLORS[plat] || '#6366f1'}">${(a.username || '?')[0].toUpperCase()}</div>
          <div class="account-info">
            <div class="account-name">${a.username} <span style="font-weight:400;color:var(--text-secondary)">${a.display_name ? '(' + a.display_name + ')' : ''}</span></div>
            <div class="account-meta">
              ${statusBadge(a.status)}
              <span>Posts: ${a.daily_posts || 0}/${a.daily_limit_posts || 10}</span>
              <span>Health: <span style="color:${healthColor(a.reputation_score || 0)}">${(a.reputation_score || 0).toFixed(0)}</span></span>
              <span>Activity: ${ts(a.last_activity)}</span>
            </div>
            <div class="progress"><div class="progress-fill" style="width:${pct}%;background:${progressColor(pct)}"></div></div>
          </div>
        </div>`;
    });
    html += '</div>';
  }
  document.getElementById('accounts-list').innerHTML = html;
}


async function renderPosts() {
  const pfilter = document.getElementById('post-platform-filter').value;
  const afilter = document.getElementById('post-account-filter').value;
  let url = '/api/posts?days=7&limit=50';
  if (pfilter !== 'all') url += '&platform=' + pfilter;
  if (afilter !== 'all') url += '&account_id=' + afilter;
  try {
    const r = await fetch(url);
    const d = await r.json();
    const posts = d.posts || [];
    const tbody = document.getElementById('posts-tbody');
    if (!posts.length) { tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-secondary)">No posts found</td></tr>'; return; }
    tbody.innerHTML = posts.map(p => `
      <tr>
        <td style="white-space:nowrap">${ts(p.posted_at)}</td>
        <td>${platformLabel(p.platform)}</td>
        <td>${p.account_id || '-'}</td>
        <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"><a href="${p.url}" target="_blank" style="color:var(--accent);text-decoration:none">${p.title || '(no title)'}</a></td>
        <td>${p.upvotes || 0}</td>
        <td>${p.comments || 0}</td>
        <td>${p.author || '-'}</td>
        <td>${p.subreddit ? 'r/' + p.subreddit : '-'}</td>
      </tr>
    `).join('');
  } catch (e) { console.error('renderPosts error:', e); }
}

function renderRuns() {
  fetch('/api/runs' + (document.getElementById('run-platform-filter').value !== 'all' ? '?platform=' + document.getElementById('run-platform-filter').value : ''))
    .then(r => r.json()).then(data => {
      const runs = data.runs || [];
      const tbody = document.getElementById('runs-tbody');
      if (!runs.length) { tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-secondary)">No runs yet</td></tr>'; return; }
      tbody.innerHTML = runs.map(r => `
        <tr>
          <td style="white-space:nowrap">${ts(r.started_at)}</td>
          <td>${platformLabel(r.platform)}</td>
          <td>${r.account_id || '-'}</td>
          <td><span class="badge badge-neutral">${r.action}</span></td>
          <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.query || '-'}</td>
          <td>${r.status === 'completed' ? '<span class="badge badge-healthy">completed</span>' : r.status === 'failed' ? '<span class="badge badge-danger">failed</span>' : '<span class="badge badge-info">' + r.status + '</span>'}</td>
          <td>${r.items_new || 0} / ${r.items_duplicate || 0}</td>
          <td>${r.duration_seconds ? r.duration_seconds.toFixed(1) + 's' : '-'}</td>
        </tr>
      `).join('');
    });
}

function updateAlerts(alerts) {
  const unread = alerts.filter(a => !a.resolved).length;
  document.getElementById('alert-count').textContent = unread;
  if (!alerts.length) {
    document.getElementById('alerts-list').innerHTML = '<div style="padding:1rem;color:var(--text-secondary);font-size:0.85rem">No alerts</div>';
    return;
  }
  document.getElementById('alerts-list').innerHTML = alerts.slice(0, 20).map(a => {
    const cls = a.level === 'critical' ? 'alert-critical' : a.level === 'warning' ? 'alert-warning' : 'alert-info';
    return `<div class="alert-item ${cls}"><strong>${a.platform.toUpperCase()}/${a.account_id}</strong><br>${a.message}<div class="alert-ts">${ts(a.created_at)}</div></div>`;
  }).join('');
}

function toggleAlerts() {
  const p = document.getElementById('alert-panel');
  p.style.display = p.style.display === 'none' ? 'block' : 'none';
  if (p.style.display === 'block') fetchAlerts();
}
async function fetchAlerts() {
  const r = await fetch('/api/alerts'); const d = await r.json(); updateAlerts(d.alerts || []);
}

function updateCharts(data) {
  // Activity chart
  const actCtx = document.getElementById('activityChart').getContext('2d');
  const runs = (data && data.recent_runs) || [];
  // Build last-7-day buckets
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    days.push({ label: d.toLocaleDateString('en', {weekday:'short'}), date: d.toISOString().slice(0,10), found: 0, new: 0 });
  }
  runs.forEach(r => {
    if (!r.started_at) return;
    const rd = r.started_at.slice(0, 10);
    const bucket = days.find(d => d.date === rd);
    if (bucket) { bucket.found += r.items_found || 0; bucket.new += r.items_new || 0; }
  });
  if (activityChart) activityChart.destroy();
  activityChart = new Chart(actCtx, {
    type: 'bar',
    data: {
      labels: days.map(d => d.label),
      datasets: [
        { label: 'Found', data: days.map(d => d.found), backgroundColor: '#6366f1' },
        { label: 'New', data: days.map(d => d.new), backgroundColor: '#22c55e' },
      ]
    },
    options: { responsive: true, plugins: { legend: { labels: { color: '#7b8ba5' } } }, scales: { y: { beginAtZero: true, grid: { color: '#1e2d4a' }, ticks: { color: '#7b8ba5' } }, x: { grid: { color: '#1e2d4a' }, ticks: { color: '#7b8ba5' } } } }
  });

  // Health chart
  const healthCtx = document.getElementById('healthChart').getContext('2d');
  const summary = (data && data.summary) || {};
  const labels = []; const healthy = []; const issues = [];
  for (const [plat, s] of Object.entries(summary)) {
    labels.push(plat.toUpperCase());
    healthy.push(s.healthy || 0);
    issues.push((s.total || 0) - (s.healthy || 0));
  }
  if (healthChart) healthChart.destroy();
  if (labels.length) {
    healthChart = new Chart(healthCtx, {
      type: 'doughnut',
      data: {
        labels: ['Healthy', 'Issues'],
        datasets: [{ data: labels.length ? [healthy.reduce((a,b)=>a+b,0), issues.reduce((a,b)=>a+b,0)] : [0,0], backgroundColor: ['#22c55e', '#ef4444'], borderWidth: 0 }]
      },
      options: { responsive: true, plugins: { legend: { labels: { color: '#7b8ba5' } } } }
    });
  }
}

async function refreshData() {
  try {
    const [accRes, sumRes] = await Promise.all([fetch('/api/accounts'), fetch('/api/summary')]);
    const accData = await accRes.json(); const sumData = await sumRes.json();
    renderDashboard({ accounts: accData.accounts, summary: sumData.platforms, stats: sumData.stats, recent_runs: [] });
  } catch (err) { console.error('Refresh error:', err); }
}

document.addEventListener('DOMContentLoaded', () => {
  connectWS();
  refreshData();
  setInterval(refreshData, 30000);
});
</script>
</body>
</html>'''

# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------

def init_sample_accounts():
    """初始化示例账号（实际应从数据库/配置文件读取）"""
    from dashboard.app import Platform
    samples = [
        ("reddit_1", Platform.REDDIT, "xagent_research1", "Research Bot 1", 10),
        ("reddit_2", Platform.REDDIT, "xagent_research2", "Research Bot 2", 10),
        ("reddit_3", Platform.REDDIT, "xagent_research3", "Research Bot 3", 10),
        ("x_1", Platform.X, "xagent_poster", "X Content Bot", 10),
        ("ig_1", Platform.INSTAGRAM, "xagent_visual", "Visual Bot", 5),
        ("tt_1", Platform.TIKTOK, "xagent_shorts", "Shorts Bot", 3),
        ("yt_1", Platform.YOUTUBE, "xagent_longform", "Longform Bot", 2),
    ]
    for acc_id, platform, username, display, limit in samples:
        # 仅在 account 不存在时创建
        existing = account_pool.get_account(acc_id)
        if not existing:
            account_pool.add_account(_make_account(acc_id, platform, username, display, limit))

def _make_account(acc_id, platform, username, display, daily_limit):
    fake = type('Account', (), {})()
    fake.id = acc_id
    fake.platform = platform
    fake.username = username
    fake.display_name = display
    fake.status = "active"
    fake.status_detail = "No live account status collected yet"
    fake.daily_posts = 0
    fake.daily_likes = 0
    fake.daily_comments = 0
    fake.daily_limit_posts = daily_limit
    fake.karma_or_followers = 0
    fake.account_age_days = 0
    fake.reputation_score = 0.0
    fake.last_post_time = None
    fake.last_activity = datetime.now().isoformat()
    fake.created_at = datetime.now().isoformat()
    return fake

if __name__ == "__main__":
    import uvicorn
    print("X-Agent Dashboard v2 Starting...")
    init_sample_accounts()
    uvicorn.run(app, host="0.0.0.0", port=8080)
