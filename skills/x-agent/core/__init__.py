"""X-Agent Core - Browser-based trend research, content generation & social actions."""

from .config import Config
from .llm_router import LLMRouter, get_llm
from .generator import ContentGenerator
from .research import Researcher
from .scorer import TrendScorer
from .deduplicator import ContentDeduplicator
from .storage import Storage
from .browser import BrowserManager, SessionManager, SafetyGuard
