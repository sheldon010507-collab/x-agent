"""
research.py - 数据采集模块

调用 last30days-skill 进行多平台深度研究
支持：X + Reddit + YouTube + HN + Web + TikTok + IG
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime


class Researcher:
    """研究员 - 负责多平台数据采集"""
    
    def __init__(self, config=None):
        """
        初始化研究员
        
        Args:
            config: Config 实例
        """
        self.config = config
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def research(self, topic: str, niche: str = None, depth: str = 'basic') -> Dict:
        """
        对指定话题进行深度研究
        
        Args:
            topic: 研究话题
            niche: Niche 领域
            depth: 研究深度 ('basic' | 'advanced')
        
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
        try:
            # 调用 last30days API
            result = await self._last30days_call(topic, depth)
            
            # 补充元数据
            result['topic'] = topic
            result['niche'] = niche or 'general'
            result['created_at'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            # 出错时返回空结果
            return {
                'topic': topic,
                'niche': niche or 'general',
                'summary': f'研究失败：{str(e)}',
                'platforms': [],
                'citations': [],
                'engagement': 0,
                'created_at': datetime.now().isoformat()
            }
    
    async def _last30days_call(self, topic: str, depth: str = 'basic') -> Dict:
        """
        调用 last30days API
        
        Args:
            topic: 研究话题
            depth: 研究深度
        
        Returns:
            Dict: last30days 返回的结果
        """
        # 这里调用 last30days API
        # 实际实现需要 last30days 的 API Key 和端点
        url = "https://api.last30days.com/research"
        
        payload = {
            'query': topic,
            'depth': depth,
            'platforms': ['x', 'reddit', 'youtube', 'hn', 'web', 'tiktok', 'ig'],
            'include_summary': True,
            'include_citations': True
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_last30days_result(data)
                else:
                    # API 调用失败，返回模拟数据
                    return self._mock_research_result(topic)
        except Exception as e:
            # 返回模拟数据
            return self._mock_research_result(topic)
    
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
            'convergence': data.get('convergence', 50.0)
        }
    
    def _mock_research_result(self, topic: str) -> Dict:
        """
        生成模拟的研究结果（用于测试或 API 失败时）
        
        Args:
            topic: 研究话题
        
        Returns:
            Dict: 模拟结果
        """
        return {
            'summary': f'Research summary for: {topic}',
            'platforms': ['x', 'reddit'],
            'citations': [
                {'platform': 'x', 'url': 'https://x.com/search?q=' + topic.replace(' ', '+')},
                {'platform': 'reddit', 'url': 'https://reddit.com/search?q=' + topic.replace(' ', '+')}
            ],
            'engagement': 50,
            'relevance': 60.0,
            'velocity': 50.0,
            'authority': 50.0,
            'convergence': 40.0
        }
    
    async def research_batch(self, topics: List[str], niche: str = None) -> List[Dict]:
        """
        批量研究多个话题
        
        Args:
            topics: 话题列表
            niche: Niche 领域
        
        Returns:
            List[Dict]: 研究结果列表
        """
        tasks = [self.research(topic, niche) for topic in topics]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 出错时使用模拟数据
                processed_results.append(self._mock_research_result(topics[i]))
            else:
                processed_results.append(result)
        
        return processed_results


async def research_topic(topic: str, niche: str = None, depth: str = 'basic') -> Dict:
    """
    便捷函数：对话题进行研究
    
    Args:
        topic: 研究话题
        niche: Niche 领域
        depth: 研究深度
    
    Returns:
        Dict: 研究结果
    """
    async with Researcher() as researcher:
        return await researcher.research(topic, niche, depth)


async def research_batch(topics: List[str], niche: str = None) -> List[Dict]:
    """
    便捷函数：批量研究话题
    
    Args:
        topics: 话题列表
        niche: Niche 领域
    
    Returns:
        List[Dict]: 研究结果列表
    """
    async with Researcher() as researcher:
        return await researcher.research_batch(topics, niche)
