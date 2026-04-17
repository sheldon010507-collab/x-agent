"""
session.py - 平台会话/cookies 持久化

会话文件存放在 ~/.x-agent/sessions/{platform}_auth.json
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


SUPPORTED_PLATFORMS = ["x", "tiktok", "youtube", "reddit", "hackernews", "google_trends"]

PLATFORM_LOGIN_URLS = {
    "x": "https://x.com/i/flow/login",
    "tiktok": "https://www.tiktok.com/login",
    "youtube": "https://accounts.google.com/signin",
    "reddit": "https://www.reddit.com/login/",
    "hackernews": "https://news.ycombinator.com/login",
    "google_trends": "https://trends.google.com/",
}

PLATFORM_HOMEPAGE = {
    "x": "https://x.com/home",
    "tiktok": "https://www.tiktok.com/",
    "youtube": "https://www.youtube.com/",
    "reddit": "https://www.reddit.com/",
    "hackernews": "https://news.ycombinator.com/",
    "google_trends": "https://trends.google.com/trends/",
}


class SessionManager:
    """管理各平台浏览器会话文件"""

    def __init__(self, sessions_dir: Path = None):
        self.sessions_dir = sessions_dir or (Path.home() / ".x-agent" / "sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def session_path(self, platform: str) -> Path:
        return self.sessions_dir / f"{platform}_auth.json"

    def has_session(self, platform: str) -> bool:
        return self.session_path(platform).exists()

    def get_session(self, platform: str) -> Optional[Path]:
        path = self.session_path(platform)
        return path if path.exists() else None

    def save_session_metadata(self, platform: str, metadata: Dict):
        """保存会话元数据 (登录时间、用户名等)"""
        meta_path = self.sessions_dir / f"{platform}_meta.json"
        metadata["saved_at"] = datetime.now().isoformat()
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def get_session_metadata(self, platform: str) -> Dict:
        meta_path = self.sessions_dir / f"{platform}_meta.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def delete_session(self, platform: str) -> bool:
        path = self.session_path(platform)
        meta_path = self.sessions_dir / f"{platform}_meta.json"
        deleted = False
        if path.exists():
            path.unlink()
            deleted = True
        if meta_path.exists():
            meta_path.unlink()
        return deleted

    def list_sessions(self) -> List[Dict]:
        """列出所有会话状态"""
        result = []
        for platform in SUPPORTED_PLATFORMS:
            session_exists = self.has_session(platform)
            metadata = self.get_session_metadata(platform) if session_exists else {}
            result.append({
                "platform": platform,
                "logged_in": session_exists,
                "saved_at": metadata.get("saved_at"),
                "username": metadata.get("username"),
                "session_file": str(self.session_path(platform)) if session_exists else None,
            })
        return result
