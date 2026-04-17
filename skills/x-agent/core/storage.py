"""
storage.py - 本地 JSON 文件存储（替代 Supabase）

数据存储在 ~/.x-agent/data/ 下:
- trends.json     热点数据
- content.json    生成的内容
- reports.json    每日报告
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Storage:
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or (Path.home() / ".x-agent" / "data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load(self, filename: str) -> List[Dict]:
        path = self.data_dir / filename
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save(self, filename: str, data: List[Dict]):
        path = self.data_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    # ---- Trends ----

    def save_trends(self, trend_data: Dict) -> Dict:
        trends = self._load("trends.json")
        trend_data["saved_at"] = datetime.now().isoformat()
        trends.append(trend_data)
        # Keep last 500 entries
        if len(trends) > 500:
            trends = trends[-500:]
        self._save("trends.json", trends)
        return trend_data

    def get_trends(self, niche: str = None, limit: int = 20) -> List[Dict]:
        trends = self._load("trends.json")
        if niche:
            trends = [t for t in trends if t.get("niche") == niche]
        return trends[-limit:]

    # ---- Content ----

    def save_content(self, content_data: Dict) -> Dict:
        contents = self._load("content.json")
        content_data["saved_at"] = datetime.now().isoformat()
        contents.append(content_data)
        if len(contents) > 500:
            contents = contents[-500:]
        self._save("content.json", contents)
        return content_data

    def get_content(self, content_type: str = None, niche: str = None, limit: int = 20) -> List[Dict]:
        contents = self._load("content.json")
        if content_type:
            contents = [c for c in contents if c.get("type") == content_type]
        if niche:
            contents = [c for c in contents if c.get("niche") == niche]
        return contents[-limit:]

    # ---- Reports ----

    def save_report(self, report_data: Dict) -> Dict:
        reports = self._load("reports.json")
        report_data["saved_at"] = datetime.now().isoformat()
        reports.append(report_data)
        if len(reports) > 100:
            reports = reports[-100:]
        self._save("reports.json", reports)
        return report_data

    def get_reports(self, limit: int = 10) -> List[Dict]:
        reports = self._load("reports.json")
        return reports[-limit:]

    # ---- Stats ----

    def get_stats(self) -> Dict:
        trends = self._load("trends.json")
        contents = self._load("content.json")
        reports = self._load("reports.json")
        return {
            "trends_count": len(trends),
            "content_count": len(contents),
            "reports_count": len(reports),
            "data_dir": str(self.data_dir),
        }
