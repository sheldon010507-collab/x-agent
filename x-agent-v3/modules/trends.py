"""
trends.py - 趋势辅助采集模块

功能：
- Google Trends 采集
- X Trending 采集
- 行业自定义 RSS/关键词
- 支持多平台热点聚合
"""

import logging
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# ============ Google Trends 采集 ============

def fetch_google_trends(keywords: List[str] = None, geo: str = 'GB') -> List[Dict]:
    """
    从 Google Trends 采集热点
    
    Args:
        keywords: 关键词列表
        geo: 地理区域代码 (GB=英国，US=美国)
    
    Returns:
        List[Dict]: 趋势列表
    """
    if keywords is None:
        # 成人用品行业相关关键词
        keywords = [
            "sex toy", "vibrator", "adult toy", "couples toy",
            "wellness product", "intimate health", "pleasure product"
        ]
    
    trends = []
    
    try:
        from pytrends.request import TrendReq
        
        pytrends = TrendReq(hl="en-GB", tz=0, geo=geo)
        
        for kw in keywords[:5]:  # 限制关键词数量
            try:
                pytrends.build_payload([kw], timeframe="now 7-d", geo=geo)
                
                # 获取相关查询
                related = pytrends.related_queries()
                
                if related and kw in related:
                    rising = related[kw].get("rising")
                    
                    if rising is not None and not rising.empty:
                        for _, row in rising.head(20).iterrows():
                            trends.append({
                                "topic": str(row["query"]),
                                "source": "google",
                                "url": f"https://trends.google.com/trends/explore?q={row['query']}",
                                "raw_score": int(row.get("value", 100)),
                                "created_at": datetime.now().isoformat(),
                                "keyword": kw,
                                "geo": geo
                            })
                
            except Exception as e:
                logger.warning(f"[Google Trends] '{kw}' 失败：{e}")
        
        logger.info(f"[Google Trends] 采集到 {len(trends)} 条")
        
    except ImportError:
        logger.warning("[Google Trends] pytrends 未安装")
    except Exception as e:
        logger.error(f"[Google Trends] 失败：{e}")
    
    return trends


# ============ X Trending 采集 ============

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.lol",
]

def fetch_x_trends(locations: List[str] = None) -> List[Dict]:
    """
    从 X (Twitter) 采集趋势
    
    Args:
        locations: 地点列表（可选）
    
    Returns:
        List[Dict]: 趋势列表
    """
    trends = []
    
    for nitter_url in NITTER_INSTANCES:
        try:
            import httpx
            
            response = httpx.get(
                f"{nitter_url}/trends",
                timeout=10.0,
                follow_redirects=True
            )
            
            if response.status_code == 200:
                # 解析趋势
                trend_matches = re.findall(
                    r'/search\?q=%23([^"&]+)',
                    response.text
                )
                
                for trend_name in trend_matches[:20]:
                    from urllib.parse import unquote
                    topic = unquote(trend_name).replace("+", " ")
                    
                    trends.append({
                        "topic": f"#{topic}",
                        "source": "x",
                        "url": f"https://x.com/search?q=%23{trend_name}",
                        "raw_score": 10000,
                        "created_at": datetime.now().isoformat(),
                    })
                
                logger.info(f"[X Trends] 获取 {len(trend_matches)} 条趋势")
                break  # 成功获取后退出
                
        except ImportError:
            logger.warning("[X Trends] httpx 未安装")
            break
        except Exception as e:
            logger.warning(f"[X Trends] {nitter_url} 失败：{e}")
            continue
    
    return trends


# ============ Reddit 采集 ============

def fetch_reddit_trends(subreddits: List[str] = None, limit: int = 50) -> List[Dict]:
    """
    从 Reddit 采集热点
    
    Args:
        subreddits: Subreddit 列表
        limit: 每个版块限制数量
    
    Returns:
        List[Dict]: 趋势列表
    """
    if subreddits is None:
        # 成人用品相关版块
        subreddits = [
            "sex", "adulttoys", "relationships", "sextoys",
            "wellness", "health", "dating"
        ]
    
    trends = []
    
    try:
        import praw
        import os
        
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "x-agent/3.0"),
            read_only=True
        )
        
        for sub_name in subreddits:
            try:
                subreddit = reddit.subreddit(sub_name)
                
                for post in subreddit.hot(limit=limit):
                    if not post.removed_by_category:
                        trends.append({
                            "topic": post.title,
                            "source": "reddit",
                            "url": f"https://reddit.com{post.permalink}",
                            "raw_score": post.score + post.num_comments * 2,
                            "created_at": datetime.fromtimestamp(post.created_utc).isoformat(),
                            "subreddit": sub_name,
                            "author": str(post.author),
                        })
                        
            except Exception as e:
                logger.warning(f"[Reddit] r/{sub_name} 失败：{e}")
        
        logger.info(f"[Reddit] 采集到 {len(trends)} 条")
        
    except ImportError:
        logger.warning("[Reddit] PRAW 未安装")
    except Exception as e:
        logger.error(f"[Reddit] 失败：{e}")
    
    return trends


# ============ RSS 自定义采集 ============

def fetch_rss_trends(rss_urls: List[str] = None) -> List[Dict]:
    """
    从自定义 RSS 源采集
    
    Args:
        rss_urls: RSS 源 URL 列表
    
    Returns:
        List[Dict]: 趋势列表
    """
    if rss_urls is None:
        # 默认 RSS 源（行业相关）
        rss_urls = [
            "https://www.adultempire.com/blog/feed/",
            "https://xbiz.com/news/rss",
            "https://www.avn.com/rss",
        ]
    
    trends = []
    
    try:
        import feedparser
        
        for url in rss_urls:
            try:
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:10]:
                    trends.append({
                        "topic": entry.title,
                        "source": "rss",
                        "url": entry.link,
                        "raw_score": 100,
                        "created_at": datetime.now().isoformat(),
                        "rss_source": url,
                        "summary": entry.get('summary', '')[:200],
                    })
                    
            except Exception as e:
                logger.warning(f"[RSS] {url} 失败：{e}")
        
        logger.info(f"[RSS] 采集到 {len(trends)} 条")
        
    except ImportError:
        logger.warning("[RSS] feedparser 未安装")
    except Exception as e:
        logger.error(f"[RSS] 失败：{e}")
    
    return trends


# ============ 关键词监控采集 ============

def fetch_keyword_trends(keywords: List[str] = None) -> List[Dict]:
    """
    从关键词监控采集（使用 Tavily 搜索）
    
    Args:
        keywords: 关键词列表
    
    Returns:
        List[Dict]: 趋势列表
    """
    if keywords is None:
        keywords = [
            "adult toy trends 2026",
            "sex tech innovation",
            "wellness product launch",
            "intimate health news"
        ]
    
    trends = []
    
    try:
        import requests
        
        for keyword in keywords:
            try:
                # 使用 Tavily 搜索
                from .research import Researcher
                import asyncio
                
                async def search():
                    async with Researcher() as researcher:
                        result = await researcher.research(keyword, depth='basic')
                        return result
                
                result = asyncio.run(search())
                
                if result.get('citations'):
                    for citation in result['citations'][:5]:
                        trends.append({
                            "topic": citation.get('title', keyword),
                            "source": "web_search",
                            "url": citation.get('url', ''),
                            "raw_score": citation.get('engagement', 100),
                            "created_at": datetime.now().isoformat(),
                            "keyword": keyword,
                        })
                
            except Exception as e:
                logger.warning(f"[Keyword] '{keyword}' 失败：{e}")
        
        logger.info(f"[Keyword] 采集到 {len(trends)} 条")
        
    except Exception as e:
        logger.error(f"[Keyword] 失败：{e}")
    
    return trends


# ============ 统一入口 ============

def fetch_all_trends(niche: str = None, use_x: bool = True,
                    use_reddit: bool = True, use_google: bool = True,
                    use_rss: bool = False, use_keywords: bool = False) -> List[Dict]:
    """
    执行所有热点源采集
    
    Args:
        niche: Niche 领域（用于过滤）
        use_x: 是否使用 X 采集
        use_reddit: 是否使用 Reddit 采集
        use_google: 是否使用 Google Trends
        use_rss: 是否使用 RSS 采集
        use_keywords: 是否使用关键词采集
    
    Returns:
        List[Dict]: 所有趋势列表
    """
    logger.info(f"[Trends] 开始采集 (niche={niche})")
    
    all_trends = []
    
    # Google Trends
    if use_google:
        try:
            trends = fetch_google_trends()
            all_trends.extend(trends)
            logger.info(f"[Trends] Google: {len(trends)} 条")
        except Exception as e:
            logger.error(f"[Trends] Google 失败：{e}")
    
    # X Trends
    if use_x:
        try:
            trends = fetch_x_trends()
            all_trends.extend(trends)
            logger.info(f"[Trends] X: {len(trends)} 条")
        except Exception as e:
            logger.error(f"[Trends] X 失败：{e}")
    
    # Reddit
    if use_reddit:
        try:
            trends = fetch_reddit_trends()
            all_trends.extend(trends)
            logger.info(f"[Trends] Reddit: {len(trends)} 条")
        except Exception as e:
            logger.error(f"[Trends] Reddit 失败：{e}")
    
    # RSS
    if use_rss:
        try:
            trends = fetch_rss_trends()
            all_trends.extend(trends)
            logger.info(f"[Trends] RSS: {len(trends)} 条")
        except Exception as e:
            logger.error(f"[Trends] RSS 失败：{e}")
    
    # Keywords
    if use_keywords:
        try:
            trends = fetch_keyword_trends()
            all_trends.extend(trends)
            logger.info(f"[Trends] Keywords: {len(trends)} 条")
        except Exception as e:
            logger.error(f"[Trends] Keywords 失败：{e}")
    
    logger.info(f"[Trends] 采集完成，共 {len(all_trends)} 条")
    
    return all_trends


# ============ 数据保存 ============

def save_trends_to_json(trends: List[Dict], filename: str = None):
    """
    保存趋势到 JSON 文件
    
    Args:
        trends: 趋势列表
        filename: 文件名（可选）
    """
    data_dir = Path(__file__).parent.parent / 'data' / 'trends'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"trends_{timestamp}.json"
    
    filepath = data_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(trends, f, indent=2, ensure_ascii=False)
    
    logger.info(f"[Trends] 结果已保存：{filepath}")
    return filepath


# ============ 主函数（测试用） ============

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("开始采集热点...")
    trends = fetch_all_trends()
    print(f"采集到 {len(trends)} 条趋势")
    
    if trends:
        save_trends_to_json(trends)
        print(f"前 3 条趋势:")
        for i, trend in enumerate(trends[:3]):
            print(f"{i+1}. {trend['topic']} ({trend['source']})")
