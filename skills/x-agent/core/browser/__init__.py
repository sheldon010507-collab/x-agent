"""Browser automation infrastructure (Playwright)."""

from .manager import BrowserManager
from .session import SessionManager, SUPPORTED_PLATFORMS
from .safety import SafetyGuard
