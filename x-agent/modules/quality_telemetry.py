"""Minimal telemetry stub for compatibility with dashboard tests."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class RunMetrics:
    run_id: str
    account_id: str
    platform: str
    action: str
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    items_found: int = 0
    items_new: int = 0
    items_duplicate: int = 0
    success: bool = True
    error_type: Optional[str] = None
    error_detail: str = ""
    duration_seconds: float = 0.0

    @property
    def success_rate_contribution(self) -> float:
        return 1.0 if self.success else 0.0

    def to_dict(self) -> Dict:
        return {
            "run_id": self.run_id,
            "account_id": self.account_id,
            "platform": self.platform,
            "action": self.action,
            "success": self.success,
            "error_type": self.error_type,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class AccountHealth:
    account_id: str
    platform: str
    username: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    rate_limit_count: int = 0
    login_fail_count: int = 0
    timeout_count: int = 0
    health_score: float = 100.0

    def record_success(self) -> None:
        self.total_runs += 1
        self.successful_runs += 1
        self.health_score = 100.0

    def record_failure(self, error_type: str = "unknown") -> None:
        self.total_runs += 1
        self.failed_runs += 1
        if error_type == "rate_limit":
            self.rate_limit_count += 1
        elif error_type == "login_failed":
            self.login_fail_count += 1
        elif error_type == "timeout":
            self.timeout_count += 1
        self.health_score = max(0.0, 100.0 - self.failed_runs * 10.0)

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 1.0
        return self.successful_runs / self.total_runs

    def to_dict(self) -> Dict:
        return {
            "account_id": self.account_id,
            "platform": self.platform,
            "username": self.username,
            "success_rate": round(self.success_rate, 3),
            "health_score": self.health_score,
        }


class TelemetryStore:
    def __init__(self):
        self._runs: Dict[str, RunMetrics] = {}
        self._health: Dict[str, AccountHealth] = {}

    def record_run(self, metrics: RunMetrics) -> None:
        self._runs[metrics.run_id] = metrics

    def get_health(self, account_id: str) -> Optional[AccountHealth]:
        return self._health.get(account_id)

    def get_all_health(self) -> List[AccountHealth]:
        return list(self._health.values())

    def get_run(self, run_id: str) -> Optional[RunMetrics]:
        return self._runs.get(run_id)

    def get_recent_runs(self, limit: int = 100) -> List[RunMetrics]:
        return list(self._runs.values())[-limit:]

    def global_stats(self) -> Dict:
        return {
            "total_runs": len(self._runs),
            "accounts": len(self._health),
            "health": [health.to_dict() for health in self._health.values()],
        }


telemetry = TelemetryStore()
