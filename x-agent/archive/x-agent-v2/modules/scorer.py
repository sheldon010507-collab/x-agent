"""
scorer.py - 热点复合评分模块

复合评分公式（满分 100）：
- Relevance (40%): last30days 自带文本相似度
- Velocity (30%): 24h 互动增速
- Authority (15%): 高赞作者/跨平台出现
- Convergence (15%): X+Reddit+YouTube 同时出现
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


class TrendScorer:
    """热点评分器"""
    
    def __init__(self, db=None):
        """
        初始化评分器
        
        Args:
            db: Database 实例（用于查询历史数据）
        """
        self.db = db
    
    def calculate_score(self, trend_data: Dict) -> float:
        """
        计算热点的综合评分
        
        Args:
            trend_data: 热点数据，包含以下字段：
                - relevance: 相关性分数 (0-100)
                - velocity: 增速数据 (0-100)
                - authority: 权威性数据 (0-100)
                - convergence: 跨平台数据 (0-100)
        
        Returns:
            float: 综合评分 (0-100)
        """
        # 各维度权重
        WEIGHTS = {
            'relevance': 0.40,    # 40%
            'velocity': 0.30,     # 30%
            'authority': 0.15,    # 15%
            'convergence': 0.15   # 15%
        }
        
        # 计算各维度得分
        relevance_score = self._relevance_score(trend_data)
        velocity_score = self._velocity_score(trend_data)
        authority_score = self._authority_score(trend_data)
        convergence_score = self._convergence_score(trend_data)
        
        # 加权平均
        total_score = (
            relevance_score * WEIGHTS['relevance'] +
            velocity_score * WEIGHTS['velocity'] +
            authority_score * WEIGHTS['authority'] +
            convergence_score * WEIGHTS['convergence']
        )
        
        # 确保在 0-100 范围内
        return max(0.0, min(100.0, total_score))
    
    def _relevance_score(self, data: Dict) -> float:
        """
        计算相关性得分（40% 权重）
        
        基于 last30days 的文本相似度
        """
        # 如果已有分数，直接使用
        if 'relevance' in data:
            return min(100.0, max(0.0, data['relevance']))
        
        # 从 summary 或 citations 推断
        if 'summary' in data and data['summary']:
            # 有摘要说明相关性较高
            return 70.0
        
        # 默认分数
        return 50.0
    
    def _velocity_score(self, data: Dict) -> float:
        """
        计算增速得分（30% 权重）
        
        基于 24h 互动增速
        """
        # 如果已有分数，直接使用
        if 'velocity' in data:
            return min(100.0, max(0.0, data['velocity']))
        
        # 从互动数据计算
        if 'engagement_24h' in data:
            engagement = data['engagement_24h']
            # 增速 = (当前 - 之前) / 之前 * 100
            if engagement > 100:
                return min(100.0, 50.0 + (engagement - 100) * 0.5)
            else:
                return 50.0 * (engagement / 100.0)
        
        # 从时间戳推断新鲜度
        if 'created_at' in data:
            try:
                created = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                hours_ago = (datetime.now() - created).total_seconds() / 3600
                # 24 小时内：分数递减
                if hours_ago < 24:
                    return max(0.0, 100.0 - (hours_ago / 24) * 50)
            except:
                pass
        
        # 默认分数
        return 50.0
    
    def _authority_score(self, data: Dict) -> float:
        """
        计算权威性得分（15% 权重）
        
        基于：
        - 作者粉丝数/赞同数
        - 跨平台出现次数
        """
        # 如果已有分数，直接使用
        if 'authority' in data:
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
        
        return min(100.0, score)
    
    def _convergence_score(self, data: Dict) -> float:
        """
        计算汇聚性得分（15% 权重）
        
        X+Reddit+YouTube 同时出现
        """
        # 如果已有分数，直接使用
        if 'convergence' in data:
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
            return 'HIGH'  # 立即推送
        elif score >= 60:
            return 'MEDIUM'  # 汇总展示
        else:
            return 'LOW'  # 丢弃
    
    def should_push_immediately(self, score: float) -> bool:
        """是否应该立即推送"""
        return score >= 80
    
    def should_store(self, score: float) -> bool:
        """是否应该存储"""
        return score >= 60


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
        trend_copy = trend.copy()
        trend_copy['score'] = score
        trend_copy['score_level'] = scorer.get_score_level(score)
        trend_copy['should_push'] = scorer.should_push_immediately(score)
        trend_copy['should_store'] = scorer.should_store(score)
        results.append(trend_copy)
    
    # 按分数降序排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results
