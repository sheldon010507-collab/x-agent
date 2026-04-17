"""
base.py - 动作执行器抽象基类
"""

import logging
from abc import ABC
from datetime import datetime
from typing import Dict

from ..browser.safety import SafetyGuard, apply_content_variant

logger = logging.getLogger(__name__)


class BaseActor(ABC):
    PLATFORM: str = "base"
    REQUIRES_LOGIN: bool = True

    def __init__(self, browser_manager, safety_guard: SafetyGuard):
        self.browser = browser_manager
        self.safety = safety_guard

    def _check_login(self):
        if self.REQUIRES_LOGIN and not self.browser.session_mgr.has_session(self.PLATFORM):
            raise RuntimeError(
                f"{self.PLATFORM} requires login. Run: x-agent login --platform {self.PLATFORM}"
            )

    def _check_quota(self, action: str):
        if not self.safety.can_perform(self.PLATFORM, action):
            limit = self.safety.limits.get(self.PLATFORM, {}).get(action, "?")
            used = self.safety.get_used(self.PLATFORM, action)
            raise RuntimeError(
                f"Daily {action} limit reached for {self.PLATFORM} ({used}/{limit}). "
                f"Try again tomorrow or adjust limits."
            )

    def _success(self, action: str, **kwargs) -> Dict:
        self.safety.record_action(self.PLATFORM, action)
        return {
            "platform": self.PLATFORM,
            "action": action,
            "success": True,
            "performed_at": datetime.now().isoformat(),
            **kwargs,
        }

    def _failure(self, action: str, error: str, **kwargs) -> Dict:
        return {
            "platform": self.PLATFORM,
            "action": action,
            "success": False,
            "error": error,
            "performed_at": datetime.now().isoformat(),
            **kwargs,
        }

    @staticmethod
    def _vary(content: str) -> str:
        return apply_content_variant(content)
