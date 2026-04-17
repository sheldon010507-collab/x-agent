"""
deduplicator.py - Jaccard 相似度内容去重模块
"""

import logging
import re
from collections import OrderedDict
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class ContentDeduplicator:
    def __init__(self, threshold: float = 0.75, cache_size: int = 10000):
        self.threshold = threshold
        self.cache_size = cache_size
        self.cache = OrderedDict()

    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"http\S+|www\S+", "", text)
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"#", "", text)
        text = re.sub(r"[^\w\s]", " ", text)
        return " ".join(text.split())

    def tokenize(self, text: str, k: int = 3) -> Set[str]:
        if not text or len(text) < k:
            return set()
        return {text[i : i + k] for i in range(len(text) - k + 1)}

    def jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union else 0.0

    def text_similarity(self, text1: str, text2: str) -> float:
        tokens1 = self.tokenize(self.normalize_text(text1))
        tokens2 = self.tokenize(self.normalize_text(text2))
        return self.jaccard_similarity(tokens1, tokens2)

    def is_duplicate(self, content1: str, content2: str) -> bool:
        return self.text_similarity(content1, content2) >= self.threshold

    def deduplicate_batch(
        self, items: List[Dict], content_key: str = "text", score_key: str = "score"
    ) -> List[Dict]:
        if not items:
            return []

        unique_items = []
        processed = set()

        for i, item in enumerate(items):
            if i in processed:
                continue
            unique_items.append(item)
            processed.add(i)

            current_text = str(item.get(content_key, ""))
            duplicates = [item]

            for j in range(i + 1, len(items)):
                if j in processed:
                    continue
                if self.is_duplicate(current_text, str(items[j].get(content_key, ""))):
                    processed.add(j)
                    duplicates.append(items[j])

            if len(duplicates) > 1 and score_key:
                unique_items[-1] = max(duplicates, key=lambda x: x.get(score_key, 0))

        return unique_items
