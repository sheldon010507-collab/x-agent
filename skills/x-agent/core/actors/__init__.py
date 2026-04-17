"""Browser-based actors (post, comment, like, retweet) per platform."""

from .base import BaseActor
from .x import XActor
from .tiktok import TikTokActor
from .youtube import YouTubeActor


ACTOR_REGISTRY = {
    "x": XActor,
    "twitter": XActor,
    "tiktok": TikTokActor,
    "youtube": YouTubeActor,
    "yt": YouTubeActor,
}


def get_actor(platform: str, browser_manager, safety_guard):
    cls = ACTOR_REGISTRY.get(platform.lower())
    if not cls:
        raise ValueError(f"No actor for platform: {platform}")
    return cls(browser_manager, safety_guard)
