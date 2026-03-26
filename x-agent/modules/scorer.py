"""
scorer.py - 热点复合评分模块 (v3)
实现 4 维评分：Relevance(40%) + Velocity(30%) + Authority(15%) + Convergence(15%)
输出 0-100 分数
≥80 分立即推送，60-79 汇总，<60 丢弃
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TrendScorer:
    """
    热点评分器
    
    评分维度：
    - Relevance (40%): 文本相关性/语义相似度
    - Velocity (30%): 24h 互动增速
    - Authority (15%): 作者权威性/来源可信度
    - Convergence (15%): 跨平台汇聚性
    """
    
    def __init__(self, db=None):
        """
        初始化评分器
        
        Args:
            db: Database 实例（用于查询历史数据）
        """
        self.db = db
        
        # 各维度权重
        self.WEIGHTS = {
            'relevance': 0.40,    # 40%
            'velocity': 0.30,     # 30%
            'authority': 0.15,    # 15%
            'convergence': 0.15   # 15%
        }
    
    def calculate_score(self, trend_data: Dict) -> float:
        """
        计算热点的综合评分
        
        Args:
            trend_data: 热点数据，包含以下字段：
                - topic: 话题
                - summary: 摘要
                - source: 来源
                - engagement_24h: 24h 互动数
                - author_score: 作者分数 (0-100)
                - platforms: 平台列表
                - upvotes: 点赞数
                - created_at: 创建时间
                - relevance: 相关性分数 (可选)
                - velocity: 增速分数 (可选)
                - authority: 权威性分数 (可选)
                - convergence: 汇聚性分数 (可选)
        
        Returns:
            float: 综合评分 (0-100)
        """
        # 计算各维度得分
        relevance_score = self._relevance_score(trend_data)
        velocity_score = self._velocity_score(trend_data)
        authority_score = self._authority_score(trend_data)
        convergence_score = self._convergence_score(trend_data)
        
        # 记录各维度分数（用于调试和分析）
        trend_data['dimension_scores'] = {
            'relevance': relevance_score,
            'velocity': velocity_score,
            'authority': authority_score,
            'convergence': convergence_score
        }
        
        # 加权平均
        total_score = (
            relevance_score * self.WEIGHTS['relevance'] +
            velocity_score * self.WEIGHTS['velocity'] +
            authority_score * self.WEIGHTS['authority'] +
            convergence_score * self.WEIGHTS['convergence']
        )
        
        # 确保在 0-100 范围内
        final_score = max(0.0, min(100.0, total_score))
        
        # 保存各维度原始分数
        trend_data['relevance'] = relevance_score
        trend_data['velocity'] = velocity_score
        trend_data['authority'] = authority_score
        trend_data['convergence'] = convergence_score
        trend_data['score'] = final_score
        
        return final_score
    
    def _relevance_score(self, data: Dict) -> float:
        """
        计算相关性得分（40% 权重）
        
        基于：
        - 文本相似度（如果有预计算）
        - 话题热度
        - 与 Niche 的相关性
        
        Args:
            data: 热点数据
        
        Returns:
            float: 相关性分数 (0-100)
        """
        # 如果已有分数，直接使用
        if 'relevance' in data and data['relevance'] is not None:
            return min(100.0, max(0.0, data['relevance']))
        
        score = 50.0  # 基础分
        
        # 从 summary 或 citations 推断
        if 'summary' in data and data['summary']:
            # 有摘要说明相关性较高
            score += 20.0
        
        # 从话题关键词推断
        if 'topic' in data:
            topic = data['topic'].lower()
            # 高价值关键词
            high_value_keywords = ['breaking', 'exclusive', 'leaked', 'confirmed', 'official']
            for keyword in high_value_keywords:
                if keyword in topic:
                    score += 5.0
                    break
        
        # 从来源推断
        if 'source' in data:
            source = data['source'].lower()
            # 高质量来源
            premium_sources = ['twitter', 'reddit', 'youtube', 'tiktok']
            if any(s in source for s in premium_sources):
                score += 10.0
        
        return min(100.0, max(0.0, score))
    
    def _velocity_score(self, data: Dict) -> float:
        """
        计算增速得分（30% 权重）
        
        基于：
        - 24h 互动增速
        - 时间新鲜度
        - 传播速度
        
        Args:
            data: 热点数据
        
        Returns:
            float: 增速分数 (0-100)
        """
        # 如果已有分数，直接使用
        if 'velocity' in data and data['velocity'] is not None:
            return min(100.0, max(0.0, data['velocity']))
        
        score = 50.0  # 基础分
        
        # 从互动数据计算
        if 'engagement_24h' in data:
            engagement = data['engagement_24h']
            # 增速 = (当前 - 之前) / 之前 * 100
            if engagement > 100:
                score += min(50.0, (engagement - 100) * 0.5)
            else:
                score = 50.0 * (engagement / 100.0)
        
        # 从时间戳推断新鲜度
        if 'created_at' in data:
            try:
                created = data['created_at']
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                elif isinstance(created, datetime):
                    pass
                else:
                    created = None
                
                if created:
                    hours_ago = (datetime.now() - created).total_seconds() / 3600
                    # 24 小时内：分数递减
                    if hours_ago < 24:
                        time_score = max(0.0, 100.0 - (hours_ago / 24) * 50)
                        score = (score + time_score) / 2
            except Exception as e:
                logger.debug(f"解析时间失败：{e}")
        
        return min(100.0, max(0.0, score))
    
    def _authority_score(self, data: Dict) -> float:
        """
        计算权威性得分（15% 权重）
        
        基于：
        - 作者粉丝数/赞同数
        - 来源可信度
        - 跨平台验证
        
        Args:
            data: 热点数据
        
        Returns:
            float: 权威性分数 (0-100)
        """
        # 如果已有分数，直接使用
        if 'authority' in data and data['authority'] is not None:
            return min(100.0, max(0.0, data['authority']))
        
        score = 50.0  # 基础分
        
        # 作者权威性
        if 'author_score' in data:
            score += min(30.0, data['author_score'] / 10.0)
        
        # 跨平台出现
        platforms = data.get('platforms', [])
        if len(platforms) >= 3:
            score += 20.0  # 3 个平台以上 +20 分
        elif len(platforms) >= 2:
            score += 10.0  # 2 个平台 +10 分
        
        # 高赞/高互动
        if 'upvotes' in data:
            upvotes = data['upvotes']
            if upvotes > 1000:
                score += 15.0
            elif upvotes > 100:
                score += 10.0
            elif upvotes > 10:
                score += 5.0
        
        # 来源权威性
        if 'source' in data:
            source = data['source'].lower()
            authoritative_sources = ['verified', 'official', 'blue check']
            if any(s in source for s in authoritative_sources):
                score += 10.0
        
        return min(100.0, max(0.0, score))
    
    def _convergence_score(self, data: Dict) -> float:
        """
        计算汇聚性得分（15% 权重）
        
        基于：
        - X+Reddit+YouTube 同时出现
        - 多平台交叉验证
        
        Args:
            data: 热点数据
        
        Returns:
            float: 汇聚性分数 (0-100)
        """
        # 如果已有分数，直接使用
        if 'convergence' in data and data['convergence'] is not None:
            return min(100.0, max(0.0, data['convergence']))
        
        platforms = data.get('platforms', [])
        platform_count = len(set(platforms))  # 去重
        
        # 3 个平台以上：100 分
        # 2 个平台：70 分
        # 1 个平台：40 分
        if platform_count >= 3:
            return 100.0
        elif platform_count == 2:
            return 70.0
        elif platform_count == 1:
            return 40.0
        else:
            return 50.0  # 未知情况给基础分
    
    def get_score_level(self, score: float) -> str:
        """
        根据分数返回等级
        
        Args:
            score: 分数 (0-100)
        
        Returns:
            str: 等级描述
        """
        if score >= 80:
            return 'HIGH'      # 立即推送
        elif score >= 60:
            return 'MEDIUM'    # 汇总展示
        else:
            return 'LOW'       # 丢弃
    
    def should_push_immediately(self, score: float) -> bool:
        """是否应该立即推送（≥80 分）"""
        return score >= 80
    
    def should_store(self, score: float) -> bool:
        """是否应该存储（≥60 分）"""
        return score >= 60
    
    def should_discard(self, score: float) -> bool:
        """是否应该丢弃（<60 分）"""
        return score < 60
    
    def get_action_recommendation(self, score: float) -> Dict:
        """
        获取分数对应的操作建议
        
        Args:
            score: 分数
        
        Returns:
            Dict: 操作建议
        """
        if score >= 80:
            return {
                'action': 'push_immediately',
                'priority': 'high',
                'description': '高分热点，立即推送'
            }
        elif score >= 60:
            return {
                'action': 'store_for_summary',
                'priority': 'medium',
                'description': '中等分数，存入每日汇总'
            }
        else:
            return {
                'action': 'discard',
                'priority': 'low',
                'description': '分数较低，建议丢弃'
            }


# ============ 便捷函数 ============

def calculate_trend_score(trend_data: Dict, db=None) -> float:
    """
    便捷函数：计算热点评分
    
    Args:
        trend_data: 热点数据
        db: Database 实例
    
    Returns:
        float: 综合评分
    """
    scorer = TrendScorer(db)
    return scorer.calculate_score(trend_data)


def batch_calculate_scores(trend_list: List[Dict], db=None) -> List[Dict]:
    """
    批量计算热点评分
    
    Args:
        trend_list: 热点数据列表
        db: Database 实例
    
    Returns:
        List[Dict]: 添加了 score 和 score_level 的热点列表
    """
    scorer = TrendScorer(db)
    results = []
    
    for trend in trend_list:
        score = scorer.calculate_score(trend)
        
        # 创建副本避免修改原始数据
        trend_copy = trend.copy()
        trend_copy['score'] = score
        trend_copy['score_level'] = scorer.get_score_level(score)
        trend_copy['should_push'] = scorer.should_push_immediately(score)
        trend_copy['should_store'] = scorer.should_store(score)
        trend_copy['should_discard'] = scorer.should_discard(score)
        trend_copy['action_recommendation'] = scorer.get_action_recommendation(score)
        
        results.append(trend_copy)
    
    # 按分数降序排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results


def filter_by_threshold(trend_list: List[Dict], min_score: float = 60) -> List[Dict]:
    """
    过滤低于阈值的热点
    
    Args:
        trend_list: 热点数据列表
        min_score: 最低分数
    
    Returns:
        List[Dict]: 过滤后的热点列表
    """
    return [t for t in trend_list if t.get('score', 0) >= min_score]


def categorize_by_score(trend_list: List[Dict]) -> Dict[str, List[Dict]]:
    """
    按分数分类热点
    
    Args:
        trend_list: 热点数据列表
    
    Returns:
        Dict: 分类结果 {high: [...], medium: [...], low: [...]}
    """
    scorer = TrendScorer()
    
    categories = {
        'high': [],    # ≥80 分
        'medium': [],  # 60-79 分
        'low': []      # <60 分
    }
    
    for trend in trend_list:
        score = trend.get('score', 0)
        level = scorer.get_score_level(score)
        
        if level == 'HIGH':
            categories['high'].append(trend)
        elif level == 'MEDIUM':
            categories['medium'].append(trend)
        else:
            categories['low'].append(trend)
    
    return categories


# ============ 测试代码 ============
if __name__ == '__main__':
    # 测试评分器
    test_trend = {
        'topic': 'Breaking: AI breakthrough announced',
        'summary': 'Major AI company announces new model',
        'source': 'Twitter Verified',
        'engagement_24h': 150,
        'author_score': 85,
        'platforms': ['twitter', 'reddit', 'youtube'],
        'upvotes': 500,
        'created_at': datetime.now()
    }
    
    scorer = TrendScorer()
    score = scorer.calculate_score(test_trend)
    
    print(f"热点评分：{score:.2f}")
    print(f"等级：{scorer.get_score_level(score)}")
    print(f"立即推送：{scorer.should_push_immediately(score)}")
    print(f"存储：{scorer.should_store(score)}")
    print(f"丢弃：{scorer.should_discard(score)}")
    print(f"操作建议：{scorer.get_action_recommendation(score)}")
