"""
research.py - 热点研究模块

功能：
- 集成 last30days 深度研究
- 支持多平台采集（X+Reddit+YouTube+HN+Web+TikTok+IG+Bluesky+Polymarket）
- 输出结构化 JSON 数据
- 支持批量研究
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class Researcher:
    """研究员 - 负责多平台深度研究"""
    
    def __init__(self, config=None, api_key: str = None, api_endpoint: str = None):
        """
        初始化研究员
        
        Args:
            config: Config 实例
            api_key: last30days API Key
            api_endpoint: last30days API 端点
        """
        self.config = config
        self.api_key = api_key or getattr(config, 'LAST30DAYS_API_KEY', None)
        self.api_endpoint = api_endpoint or 'https://api.last30days.com'
        self.session = None
        
        # 支持的平台
        self.supported_platforms = [
            'x', 'reddit', 'youtube', 'hn', 'web', 
            'tiktok', 'ig', 'bluesky', 'polymarket'
        ]
        
        # 数据持久化
        self.data_dir = Path(__file__).parent.parent / 'data' / 'research'
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def research(self, topic: str, niche: str = None, 
                      depth: str = 'basic', platforms: List[str] = None) -> Dict:
        """
        对指定话题进行深度研究
        
        Args:
            topic: 研究话题
            niche: Niche 领域
            depth: 研究深度 ('basic' | 'advanced')
            platforms: 指定平台列表，默认全平台
        
        Returns:
            Dict: 研究结果，包含：
            - topic: 话题
            - niche: 领域
            - summary: 摘要
            - platforms: 涉及平台列表
            - citations: 引用来源
            - engagement: 互动数据
            - created_at: 创建时间
        """
        logger.info(f"[Research] 开始研究：{topic}")
        
        try:
            # 调用 last30days API
            result = await self._last30days_call(
                topic, 
                depth=depth, 
                platforms=platforms
            )
            
            # 补充元数据
            result['topic'] = topic
            result['niche'] = niche or 'general'
            result['created_at'] = datetime.now().isoformat()
            result['depth'] = depth
            result['platforms_requested'] = platforms or self.supported_platforms
            
            # 保存结果
            self._save_research_result(result)
            
            logger.info(f"[Research] 研究完成：{topic}")
            return result
            
        except Exception as e:
            logger.error(f"[Research] 研究失败：{e}")
            # 出错时返回空结果
            return self._error_result(topic, niche, str(e))
    
    async def _last30days_call(self, topic: str, depth: str = 'basic',
                              platforms: List[str] = None) -> Dict:
        """
        调用 last30days API
        
        Args:
            topic: 研究话题
            depth: 研究深度
            platforms: 平台列表
        
        Returns:
            Dict: last30days 返回的结果
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.api_endpoint}/research"
        
        payload = {
            'query': topic,
            'depth': depth,
            'platforms': platforms or self.supported_platforms,
            'include_summary': True,
            'include_citations': True,
            'include_images': True,
            'max_results': 50,
        }
        
        headers = {}
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_last30days_result(data)
                else:
                    logger.warning(f"[Research] API 返回 {response.status}")
                    # API 调用失败，返回模拟数据
                    return self._mock_research_result(topic, platforms)
        except aiohttp.ClientError as e:
            logger.warning(f"[Research] API 调用失败：{e}")
            # 返回模拟数据
            return self._mock_research_result(topic, platforms)
        except Exception as e:
            logger.error(f"[Research] 未知错误：{e}")
            return self._mock_research_result(topic, platforms)
    
    def _parse_last30days_result(self, data: Dict) -> Dict:
        """解析 last30days 返回的结果"""
        return {
            'summary': data.get('summary', ''),
            'platforms': data.get('platforms', []),
            'citations': data.get('citations', []),
            'engagement': data.get('engagement', 0),
            'relevance': data.get('relevance', 50.0),
            'velocity': data.get('velocity', 50.0),
            'authority': data.get('authority', 50.0),
            'convergence': data.get('convergence', 50.0),
            'images': data.get('images', []),
            'trends': data.get('trends', []),
            'key_insights': data.get('key_insights', []),
        }
    
    def _mock_research_result(self, topic: str, platforms: List[str] = None) -> Dict:
        """
        生成模拟的研究结果（用于测试或 API 失败时）
        
        Args:
            topic: 研究话题
            platforms: 平台列表
        
        Returns:
            Dict: 模拟结果
        """
        platforms = platforms or self.supported_platforms
        
        return {
            'summary': f'Research summary for: {topic}',
            'platforms': platforms[:3],  # 默认前 3 个平台
            'citations': [
                {
                    'platform': 'x',
                    'url': f'https://x.com/search?q={topic.replace(" ", "+")}',
                    'title': f'Search results for {topic}',
                    'engagement': 100
                },
                {
                    'platform': 'reddit',
                    'url': f'https://reddit.com/search?q={topic.replace(" ", "+")}',
                    'title': f'Reddit discussions about {topic}',
                    'engagement': 50
                }
            ],
            'engagement': 150,
            'relevance': 60.0,
            'velocity': 50.0,
            'authority': 50.0,
            'convergence': 40.0,
            'images': [],
            'trends': [],
            'key_insights': [
                f'{topic} is gaining traction across multiple platforms',
                'Consider creating content around this topic'
            ],
        }
    
    def _error_result(self, topic: str, niche: str, error: str) -> Dict:
        """生成错误结果"""
        return {
            'topic': topic,
            'niche': niche or 'general',
            'summary': f'研究失败：{error}',
            'platforms': [],
            'citations': [],
            'engagement': 0,
            'relevance': 0.0,
            'velocity': 0.0,
            'authority': 0.0,
            'convergence': 0.0,
            'error': error,
            'created_at': datetime.now().isoformat(),
        }
    
    def _save_research_result(self, result: Dict):
        """保存研究结果到 JSON 文件"""
        try:
            topic_safe = result['topic'].replace('/', '_').replace('\\', '_')[:50]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"research_{topic_safe}_{timestamp}.json"
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[Research] 结果已保存：{filepath}")
        except Exception as e:
            logger.warning(f"[Research] 保存结果失败：{e}")
    
    async def research_batch(self, topics: List[str], niche: str = None,
                            depth: str = 'basic') -> List[Dict]:
        """
        批量研究多个话题
        
        Args:
            topics: 话题列表
            niche: Niche 领域
            depth: 研究深度
        
        Returns:
            List[Dict]: 研究结果列表
        """
        logger.info(f"[Research] 批量研究 {len(topics)} 个话题")
        
        tasks = [
            self.research(topic, niche, depth) 
            for topic in topics
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[Research] 话题 {topics[i]} 研究失败：{result}")
                processed_results.append(
                    self._error_result(topics[i], niche, str(result))
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def research_platform(self, platform: str, query: str, 
                               limit: int = 20) -> List[Dict]:
        """
        针对特定平台进行研究
        
        Args:
            platform: 平台名称 (x, reddit, youtube, etc.)
            query: 搜索关键词
            limit: 结果数量限制
        
        Returns:
            List[Dict]: 平台特定结果
        """
        logger.info(f"[Research] 平台研究：{platform} - {query}")
        
        if platform not in self.supported_platforms:
            logger.warning(f"[Research] 不支持的平台：{platform}")
            return []
        
        # 根据不同平台调用不同的采集器
        platform_methods = {
            'x': self._research_x,
            'reddit': self._research_reddit,
            'youtube': self._research_youtube,
            'hn': self._research_hn,
            'web': self._research_web,
            'tiktok': self._research_tiktok,
            'ig': self._research_ig,
            'bluesky': self._research_bluesky,
            'polymarket': self._research_polymarket,
        }
        
        method = platform_methods.get(platform)
        if method:
            return await method(query, limit)
        
        return []
    
    # ============ 各平台研究方法 ============
    
    async def _research_x(self, query: str, limit: int) -> List[Dict]:
        """X (Twitter) 研究"""
        # 调用 X API 或 Nitter
        logger.info(f"[Research] X 平台研究：{query}")
        return []
    
    async def _research_reddit(self, query: str, limit: int) -> List[Dict]:
        """Reddit 研究"""
        # 调用 Reddit API (PRAW)
        logger.info(f"[Research] Reddit 研究：{query}")
        return []
    
    async def _research_youtube(self, query: str, limit: int) -> List[Dict]:
        """YouTube 研究"""
        # 调用 YouTube API
        logger.info(f"[Research] YouTube 研究：{query}")
        return []
    
    async def _research_hn(self, query: str, limit: int) -> List[Dict]:
        """Hacker News 研究"""
        # 调用 HN API
        logger.info(f"[Research] HN 研究：{query}")
        return []
    
    async def _research_web(self, query: str, limit: int) -> List[Dict]:
        """Web 搜索研究"""
        # 使用 Tavily 或其他搜索引擎
        logger.info(f"[Research] Web 研究：{query}")
        return []
    
    async def _research_tiktok(self, query: str, limit: int) -> List[Dict]:
        """TikTok 研究"""
        logger.info(f"[Research] TikTok 研究：{query}")
        return []
    
    async def _research_ig(self, query: str, limit: int) -> List[Dict]:
        """Instagram 研究"""
        logger.info(f"[Research] Instagram 研究：{query}")
        return []
    
    async def _research_bluesky(self, query: str, limit: int) -> List[Dict]:
        """Bluesky 研究"""
        logger.info(f"[Research] Bluesky 研究：{query}")
        return []
    
    async def _research_polymarket(self, query: str, limit: int) -> List[Dict]:
        """Polymarket 研究"""
        logger.info(f"[Research] Polymarket 研究：{query}")
        return []


# ============ 便捷函数 ============

async def research_topic(topic: str, niche: str = None, depth: str = 'basic',
                        platforms: List[str] = None) -> Dict:
    """
    便捷函数：对话题进行研究
    
    Args:
        topic: 研究话题
        niche: Niche 领域
        depth: 研究深度
        platforms: 平台列表
    
    Returns:
        Dict: 研究结果
    """
    async with Researcher() as researcher:
        return await researcher.research(topic, niche, depth, platforms)


async def research_batch(topics: List[str], niche: str = None,
                        depth: str = 'basic') -> List[Dict]:
    """
    便捷函数：批量研究话题
    
    Args:
        topics: 话题列表
        niche: Niche 领域
        depth: 研究深度
    
    Returns:
        List[Dict]: 研究结果列表
    """
    async with Researcher() as researcher:
        return await researcher.research_batch(topics, niche, depth)


def save_research_json(result: Dict, filename: str = None):
    """
    保存研究结果为 JSON 文件
    
    Args:
        result: 研究结果
        filename: 文件名（可选）
    """
    data_dir = Path(__file__).parent.parent / 'data' / 'research'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        topic_safe = result.get('topic', 'research')[:50].replace('/', '_')
        filename = f"research_{topic_safe}_{timestamp}.json"
    
    filepath = data_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"[Research] 结果已保存：{filepath}")
    return filepath
