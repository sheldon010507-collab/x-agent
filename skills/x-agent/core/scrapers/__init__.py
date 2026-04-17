"""Browser-based scrapers for all platforms."""

from .base import BaseScraper
from .x import XScraper
from .tiktok import TikTokScraper
from .youtube import YouTubeScraper
from .reddit import RedditScraper
from .hackernews import HackerNewsScraper
from .google_trends import GoogleTrendsScraper


SCRAPER_REGISTRY = {
    "x": XScraper,
    "twitter": XScraper,
    "tiktok": TikTokScraper,
    "youtube": YouTubeScraper,
    "yt": YouTubeScraper,
    "reddit": RedditScraper,
    "hackernews": HackerNewsScraper,
    "hn": HackerNewsScraper,
    "google_trends": GoogleTrendsScraper,
    "web": GoogleTrendsScraper,
}


def get_scraper(platform: str, browser_manager):
    """工厂方法：根据平台名返回 scraper 实例"""
    scraper_cls = SCRAPER_REGISTRY.get(platform.lower())
    if not scraper_cls:
        raise ValueError(f"Unknown platform: {platform}")
    return scraper_cls(browser_manager)
