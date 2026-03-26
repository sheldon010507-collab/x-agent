"""
trends.py - 热点采集模块
支持: Reddit (PRAW), Google Trends (pytrends), X Trending (Nitter)
"""

import logging
import re
import httpx
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import unquote

logger = logging.getLogger(__name__)


# ============ Reddit 采集 ============

def fetch_reddit_trends(subreddits: List[str] = None, limit: int = 50) -> List[Dict]:
    """从 Reddit 采集热点"""
    if subreddits is None:
        subreddits = ["sex", "adulttoys", "relationships"]
    
    trends = []
    
    try:
        from praw import Reddit
        import os
        
        reddit = Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "x-agent/2.0"),
            read_only=True
        )
        
        for sub_name in subreddits:
            try:
                for post in reddit.subreddit(sub_name).hot(limit=limit):
                    if not post.removed_by_category:
                        trends.append({
                            "topic": post.title,
                            "source": "reddit",
                            "url": f"https://reddit.com{post.permalink}",
                            "raw_score": post.score + post.num_comments * 2,
                            "created_at": datetime.fromtimestamp(post.created_utc).isoformat()
                        })
            except Exception as e:
                logger.warning(f"[Reddit] r/{sub_name} 失败: {e}")
        
        logger.info(f"[Reddit] 采集到 {len(trends)} 条")
        
    except ImportError:
        logger.warning("[Reddit] PRAW 未安装")
    except Exception as e:
        logger.error(f"[Reddit] 失败: {e}")
    
    return trends


# ============ Google Trends 采集 ============

def fetch_google_trends(keywords: List[str] = None) -> List[Dict]:
    """从 Google Trends 采集"""
    if keywords is None:
        keywords = ["sex toy", "vibrator", "adult toy"]
    
    trends = []
    
    try:
        from pytrends.request import TrendReq
        
        pytrends = TrendReq(hl="en-US", tz=0)
        
        for kw in keywords[:5]:
            try:
                pytrends.build_payload([kw], timeframe="now 7-d")
                related = pytrends.related_queries()
                
                if related and kw in related:
                    rising = related[kw].get("rising")
                    if rising is not None and not rising.empty:
                        for _, row in rising.head(20).iterrows():
                            trends.append({
                                "topic": row["query"],
                                "source": "google",
                                "url": f"https://trends.google.com/trends/explore?q={row['query']}",
                                "raw_score": row.get("value", 100),
                                "created_at": datetime.now().isoformat()
                            })
            except Exception as e:
                logger.warning(f"[Google] '{kw}' 失败: {e}")
        
        logger.info(f"[Google] 采集到 {len(trends)} 条")
        
    except ImportError:
        logger.warning("[Google] pytrends 未安装")
    
    return trends


# ============ X Trending 采集 ============

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
]


def fetch_x_trends(locations: List[str] = None) -> List[Dict]:
    """从 X (Twitter) 采集趋势"""
    trends = []
    
    for nitter_url in NITTER_INSTANCES:
        try:
            response = httpx.get(f"{nitter_url}/trends", timeout=10.0, follow_redirects=True)
            
            if response.status_code == 200:
                trend_matches = re.findall(r'/search\?q=%23([^"&]+)', response.text)
                
                for trend_name in trend_matches[:20]:
                    topic = unquote(trend_name).replace("+", " ")
                    trends.append({
                        "topic": f"#{topic}",
                        "source": "x",
                        "url": f"https://x.com/search?q=%23{trend_name}",
                        "raw_score": 10000,
                        "created_at": datetime.now().isoformat()
                    })
                
                logger.info(f"[X] 获取 {len(trend_matches)} 条趋势")
                break
        
        except Exception as e:
            logger.warning(f"[X] {nitter_url} 失败: {e}")
    
    return trends


# ============ 统一入口 ============

def fetch_all_trends(niche: str = None, use_x: bool = True) -> List[Dict]:
    """执行所有热点源采集"""
    logger.info(f"[Trends] 开始采集")
    
    all_trends = []
    all_trends.extend(fetch_reddit_trends())
    all_trends.extend(fetch_google_trends())
    
    if use_x:
        all_trends.extend(fetch_x_trends())
    
    logger.info(f"[Trends] 采集完成，共 {len(all_trends)} 条")
    return all_trends
