"""
deduplicator.py - 基于Jaccard相似度的内容去重模块

实现多平台内容去重：
- Jaccard相似度算法（不区分词序）
- 支持推文、评论、帖子去重
- 可配置的相似度阈值
- LRU缓存优化性能
"""

import logging
import re
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class ContentDeduplicator:
    """基于Jaccard相似度的内容去重器"""

    def __init__(self, threshold: float = 0.75, cache_size: int = 10000):
        """
        初始化去重器

        Args:
            threshold: Jaccard相似度阈值 (0.0-1.0), 默认0.75
                     相似度 >= threshold 视为重复
            cache_size: LRU缓存大小，避免重复处理
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be between 0 and 1, got {threshold}")

        self.threshold = threshold
        self.cache_size = cache_size
        self.cache = OrderedDict()  # LRU cache: {hash: (text, tokens)}
        self.logger = logging.getLogger(__name__)

    def normalize_text(self, text: str) -> str:
        """
        规范化文本：清理URL、特殊字符、多余空格

        Args:
            text: 原始文本

        Returns:
            规范化后的文本（小写，去除URL，去除多余空格）
        """
        if not text:
            return ""

        # 转小写
        text = text.lower()

        # 去除URL
        text = re.sub(r"http\S+|www\S+", "", text)

        # 去除@mention
        text = re.sub(r"@\w+", "", text)

        # 去除hashtag符号（保留文字）
        text = re.sub(r"#", "", text)

        # 去除表情符号（保留ASCII）
        text = re.sub(r"[^\w\s]", " ", text)

        # 规范化空格
        text = " ".join(text.split())

        return text

    def tokenize(self, text: str, k: int = 3) -> Set[str]:
        """
        将文本转换为k-shingles集合（n-gram分词）

        Args:
            text: 规范化后的文本
            k: shingle大小，默认3-gram

        Returns:
            shingles集合
        """
        if not text or len(text) < k:
            return set()

        # 按字符生成k-gram
        shingles = set()
        for i in range(len(text) - k + 1):
            shingles.add(text[i : i + k])

        return shingles

    def jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """
        计算两个集合的Jaccard相似度

        Jaccard相似度 = |intersection| / |union|

        Args:
            set1: 第一个集合
            set2: 第二个集合

        Returns:
            Jaccard相似度 (0.0-1.0)
        """
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 第一个文本
            text2: 第二个文本

        Returns:
            相似度 (0.0-1.0)
        """
        # 规范化
        normalized1 = self.normalize_text(text1)
        normalized2 = self.normalize_text(text2)

        # 生成shingles
        tokens1 = self.tokenize(normalized1)
        tokens2 = self.tokenize(normalized2)

        # 计算Jaccard相似度
        return self.jaccard_similarity(tokens1, tokens2)

    def is_duplicate(self, content1: str, content2: str) -> bool:
        """
        检查两个内容是否为重复

        Args:
            content1: 第一个内容
            content2: 第二个内容

        Returns:
            True if 相似度 >= threshold
        """
        similarity = self.text_similarity(content1, content2)
        return similarity >= self.threshold

    def _manage_cache(self, text_hash: str):
        """管理LRU缓存"""
        if text_hash in self.cache:
            self.cache.move_to_end(text_hash)
        elif len(self.cache) >= self.cache_size:
            self.cache.popitem(last=False)

    def deduplicate_batch(
        self, items: List[Dict], content_key: str = "text", score_key: str = "score"
    ) -> List[Dict]:
        """
        从项目列表中移除重复项

        策略：保留相同项目中分数最高的那个

        Args:
            items: 项目列表，每个项目是Dict
            content_key: 指定文本字段的键名（默认"text"）
            score_key: 指定分数字段的键名，用于选择最佳项
                      如果不存在则按出现顺序保留

        Returns:
            去重后的项目列表（保持相似度排序）
        """
        if not items:
            return []

        unique_items = []
        processed_indices = set()

        for i, item in enumerate(items):
            if i in processed_indices:
                continue

            # 当前项是唯一的，添加到结果
            unique_items.append(item)
            processed_indices.add(i)

            # 查找与当前项重复的后续项
            current_text = str(item.get(content_key, ""))
            duplicates = [item]
            duplicate_indices = [i]

            for j in range(i + 1, len(items)):
                if j in processed_indices:
                    continue

                other_text = str(items[j].get(content_key, ""))

                if self.is_duplicate(current_text, other_text):
                    processed_indices.add(j)
                    duplicate_indices.append(j)
                    duplicates.append(items[j])

            # 如果找到重复项，选择分数最高的
            if len(duplicates) > 1 and score_key:
                best = max(duplicates, key=lambda x: x.get(score_key, 0))
                # 更新results中的项为最佳项
                unique_items[-1] = best

        self.logger.info(
            f"Deduplication: {len(items)} items → {len(unique_items)} items "
            f"(removed {len(items) - len(unique_items)})"
        )

        return unique_items

    def find_similar_groups(self, items: List[Dict], content_key: str = "text") -> List[List[Dict]]:
        """
        将相似项目分组（用于聚类分析）

        Args:
            items: 项目列表
            content_key: 文本字段键名

        Returns:
            分组列表，每组包含相似项目
        """
        if not items:
            return []

        groups = []
        processed = set()

        for i, item in enumerate(items):
            if i in processed:
                continue

            # 创建新组
            group = [item]
            processed.add(i)
            current_text = str(item.get(content_key, ""))

            # 找相似项加入组
            for j in range(i + 1, len(items)):
                if j in processed:
                    continue

                other_text = str(items[j].get(content_key, ""))
                if self.is_duplicate(current_text, other_text):
                    group.append(items[j])
                    processed.add(j)

            groups.append(group)

        self.logger.info(f"Grouping: {len(items)} items → {len(groups)} groups")
        return groups

    def get_stats(self) -> Dict:
        """获取去重器统计信息"""
        return {
            "threshold": self.threshold,
            "cache_size": self.cache_size,
            "cached_items": len(self.cache),
        }


def calculate_shingle_similarity(
    text1: str, text2: str, k: int = 3, threshold: float = 0.75
) -> Tuple[float, bool]:
    """
    快速计算两个文本的相似度

    便利函数，无需创建对象

    Args:
        text1: 第一个文本
        text2: 第二个文本
        k: shingle大小（默认3-gram）
        threshold: 相似度阈值（用于判断是否重复）

    Returns:
        (相似度, 是否重复)
    """
    dedup = ContentDeduplicator(threshold=threshold)
    similarity = dedup.text_similarity(text1, text2)
    is_dup = similarity >= threshold
    return similarity, is_dup
