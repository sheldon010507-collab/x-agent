"""
safety.py - 安全机制：每日动作限制 + 随机延迟 + 内容变体
"""

import asyncio
import json
import logging
import random
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# 每个平台的每日上限
DEFAULT_DAILY_LIMITS = {
    "x": {"post": 5, "comment": 15, "like": 30, "retweet": 10},
    "tiktok": {"post": 3, "comment": 10, "like": 30, "follow": 10},
    "youtube": {"post": 2, "comment": 10, "like": 30, "subscribe": 5},
}


class SafetyGuard:
    """每日动作配额追踪 + 延迟控制"""

    def __init__(self, data_dir: Path = None, limits: Dict = None):
        self.data_dir = data_dir or (Path.home() / ".x-agent" / "data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.counter_file = self.data_dir / "action_counters.json"
        self.limits = limits or DEFAULT_DAILY_LIMITS

    def _load_counters(self) -> Dict:
        if not self.counter_file.exists():
            return {}
        try:
            with open(self.counter_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_counters(self, counters: Dict):
        with open(self.counter_file, "w", encoding="utf-8") as f:
            json.dump(counters, f, ensure_ascii=False, indent=2)

    def _today_key(self) -> str:
        return date.today().isoformat()

    def can_perform(self, platform: str, action: str) -> bool:
        """检查是否还能执行该动作"""
        limit = self.limits.get(platform, {}).get(action)
        if limit is None:
            return True  # 无限制
        used = self.get_used(platform, action)
        return used < limit

    def get_used(self, platform: str, action: str) -> int:
        """获取今日已使用次数"""
        counters = self._load_counters()
        today = self._today_key()
        return counters.get(today, {}).get(platform, {}).get(action, 0)

    def record_action(self, platform: str, action: str):
        """记录一次动作"""
        counters = self._load_counters()
        today = self._today_key()
        counters.setdefault(today, {}).setdefault(platform, {})
        counters[today][platform][action] = counters[today][platform].get(action, 0) + 1
        # 清理 7 天前的数据
        self._cleanup_old(counters)
        self._save_counters(counters)

    def _cleanup_old(self, counters: Dict):
        cutoff = (datetime.now().date()).toordinal() - 7
        keys_to_remove = []
        for k in counters.keys():
            try:
                if date.fromisoformat(k).toordinal() < cutoff:
                    keys_to_remove.append(k)
            except ValueError:
                keys_to_remove.append(k)
        for k in keys_to_remove:
            del counters[k]

    def get_status(self) -> Dict:
        """返回所有平台所有动作的配额状态"""
        result = {}
        for platform, actions in self.limits.items():
            result[platform] = {}
            for action, limit in actions.items():
                used = self.get_used(platform, action)
                result[platform][action] = {
                    "used": used,
                    "limit": limit,
                    "remaining": max(0, limit - used),
                }
        return result

    @staticmethod
    async def random_delay(min_sec: float = 10.0, max_sec: float = 40.0):
        """动作之间的随机延迟"""
        delay = random.uniform(min_sec, max_sec)
        logger.info(f"Sleeping {delay:.1f}s before next action")
        await asyncio.sleep(delay)

    @staticmethod
    async def short_delay(min_sec: float = 1.0, max_sec: float = 3.0):
        """页面操作之间的短延迟（更像人类）"""
        await asyncio.sleep(random.uniform(min_sec, max_sec))


def apply_content_variant(content: str) -> str:
    """对内容做轻微变体，避免完全重复发布"""
    # 随机加 emoji 或微调标点
    suffixes = ["", " ✨", " 🚀", " 🔥", "!", ".", " 👀", " 💡"]
    if not content.endswith(tuple(suffixes[2:])):
        content = content.rstrip() + random.choice(suffixes)
    return content
