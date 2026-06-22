"""
last30days_reddit — keyless Reddit 抓取适配层

模仿 mvanhorn/last30days-skill 的 reddit 模块族，把三层 keyless 管线嫁接
到 x-agent 工程上：

Tier 0  legacy  ``.json`` 搜索（datacenter IP 多被 403，但成本低值得一试）
Tier 1  RSS Atom 订阅 — 无需 key，负载能力稳定，作为主路径
Tier 2  shreddit ``/svc/shreddit/`` partials — 拿真实 upvote / 评论数

不依赖 Playwright 时全 HTTP 层即可工作；上层业务可选择叠加 Playwright 抓
DM / 登录态页面。
"""

from .pipeline import RedditPipeline
from .reddit_keyless import RedditKeylessFetcher
from .reddit_listing import RedditListingFetcher
from .reddit_rss import RedditRSSFetcher
from .reddit_shreddit import RedditShredditEnricher

__all__ = [
    "RedditKeylessFetcher",
    "RedditRSSFetcher",
    "RedditListingFetcher",
    "RedditShredditEnricher",
    "RedditPipeline",
]
