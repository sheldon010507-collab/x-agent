""" research.py - 热点研究模块 v3.0 Final

调用 last30days-skill CLI 进行多平台深度研究
支持：X + Reddit + YouTube + HN + Web + TikTok + IG + Bluesky + Polymarket

功能：
- 直接调用 last30days CLI（subprocess）
- 本地缓存到 data/research/
- 支持批量研究
- 兼容异步接口
"""

import subprocess
import json
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 数据缓存目录
DATA_DIR = Path(__file__).parent.parent / 'data' / 'research'
DATA_DIR.mkdir(parents=True, exist_ok=True)


def research_topic(
    niche: str,
    days: int = 7,
    sources: str = "x,reddit,youtube,web,tiktok,hackernews"
) -> Dict:
    """
    调用 last30days-skill 进行多平台深度研究（同步版本）

    Args:
        niche: 研究领域/话题
        days: 回溯天数 (1-30)
        sources: 数据源列表，逗号分隔

    Returns:
        Dict: 研究结果，包含：
            - relevance_score: 相关性分数 (0-100)
            - velocity_24h: 24h 互动增速
            - authority_score: 权威性分数
            - platform_count: 平台数量
            - summary: 摘要
            - citations: 引用列表
            - trends: 趋势列表
    """
    logger.info(f"[Research] 开始研究：{niche}")

    # 构建 last30days 命令
    cmd = [
        "last30days",
        niche,
        f"--days={days}",
        f"--sources={sources}",
        "--agent",
        "--output=json"
    ]

    try:
        # 执行 CLI 命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            logger.error(f"[Research] CLI 错误：{result.stderr}")
            return _error_result(niche, result.stderr.strip())

        # 解析 JSON 输出
        data = json.loads(result.stdout)

        # 本地缓存
        _save_research_cache(data, niche)

        logger.info(f"[Research] 研究完成：{niche}")
        return data

    except subprocess.TimeoutExpired:
        logger.error(f"[Research] CLI 超时")
        return _error_result(niche, "CLI timeout")

    except json.JSONDecodeError as e:
        logger.error(f"[Research] JSON 解析失败：{e}")
        return _error_result(niche, str(e))

    except FileNotFoundError:
        logger.warning("[Research] last30days CLI 未安装，返回模拟数据")
        return _mock_result(niche)

    except Exception as e:
        logger.error(f"[Research] 未知错误：{e}")
        return _error_result(niche, str(e))


async def research_topic_async(
    niche: str,
    days: int = 7,
    sources: str = "x,reddit,youtube,web,tiktok,hackernews"
) -> Dict:
    """
    异步版本的研究函数

    使用 asyncio.to_thread 包装同步调用
    """
    return await asyncio.to_thread(research_topic, niche, days, sources)


def research_batch(
    topics: List[str],
    days: int = 7,
    sources: str = "x,reddit,youtube,web,tiktok,hackernews"
) -> List[Dict]:
    """
    批量研究多个话题

    Args:
        topics: 话题列表
        days: 回溯天数
        sources: 数据源

    Returns:
        List[Dict]: 研究结果列表
    """
    logger.info(f"[Research] 批量研究 {len(topics)} 个话题")
    results = []

    for topic in topics:
        result = research_topic(topic, days, sources)
        results.append(result)

    return results


async def research_batch_async(
    topics: List[str],
    days: int = 7,
    sources: str = "x,reddit,youtube,web,tiktok,hackernews"
) -> List[Dict]:
    """
    异步批量研究

    并发执行多个研究任务
    """
    tasks = [
        research_topic_async(topic, days, sources)
        for topic in topics
    ]
    return await asyncio.gather(*tasks)


def _save_research_cache(data: Dict, niche: str):
    """保存研究结果到本地缓存"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        niche_safe = niche.replace("/", "_").replace("\\", "_")[:30]
        filename = f"research_{niche_safe}_{timestamp}.json"
        filepath = DATA_DIR / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"[Research] 缓存已保存：{filepath}")
    except Exception as e:
        logger.warning(f"[Research] 缓存保存失败：{e}")


def _error_result(niche: str, error: str) -> Dict:
    """生成错误结果"""
    return {
        "niche": niche,
        "error": error,
        "relevance_score": 0,
        "velocity_24h": 0,
        "authority_score": 0,
        "platform_count": 0,
        "summary": f"研究失败：{error}",
        "citations": [],
        "trends": [],
        "created_at": datetime.now().isoformat()
    }


def _mock_result(niche: str) -> Dict:
    """
    生成模拟结果（当 CLI 不可用时）

    用于测试和开发环境
    """
    import random

    return {
        "niche": niche,
        "relevance_score": random.uniform(50, 80),
        "velocity_24h": random.uniform(30, 70),
        "authority_score": random.uniform(40, 60),
        "platform_count": random.randint(2, 5),
        "summary": f"模拟研究结果：{niche} 在多个平台表现活跃",
        "citations": [
            {"platform": "x", "url": f"https://x.com/search?q={niche}"},
            {"platform": "reddit", "url": f"https://reddit.com/search?q={niche}"}
        ],
        "trends": [
            {"topic": f"{niche} 最新动态", "score": 75}
        ],
        "created_at": datetime.now().isoformat(),
        "mock": True
    }


# ============ 兼容旧接口 ============

class Researcher:
    """
    研究员类（兼容旧代码）

    内部使用 last30days CLI
    """

    def __init__(self, config=None):
        self.config = config
        self.supported_platforms = [
            'x', 'reddit', 'youtube', 'hn', 'web',
            'tiktok', 'ig', 'bluesky', 'polymarket'
        ]

    async def research(self, topic: str, niche: str = None, depth: str = 'basic') -> Dict:
        """异步研究接口"""
        result = research_topic(topic or niche, days=7 if depth == 'basic' else 30)
        result['niche'] = niche or topic
        return result

    async def research_batch(self, topics: List[str], niche: str = None) -> List[Dict]:
        """异步批量研究"""
        return await research_batch_async(topics)


# ============ 便捷函数导出 ============

__all__ = [
    'research_topic',
    'research_topic_async',
    'research_batch',
    'research_batch_async',
    'Researcher'
]
