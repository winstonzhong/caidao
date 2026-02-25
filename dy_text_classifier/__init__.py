# encoding: utf-8
"""
抖音视频文案文本分类器

基于关键词匹配的轻量级文本分类解决方案
"""

from .category_cache_manager import CategoryCacheManager
from .text_classifier import TextClassifier, MatchResult
from .batch_processor import BatchProcessor
from .evaluator import Evaluator
from .simple_matcher import SimpleMatcher, 文本匹配, 获取相似度

__version__ = "1.0.0"
__all__ = [
    "CategoryCacheManager",
    "TextClassifier", 
    "MatchResult",
    "BatchProcessor",
    "Evaluator",
    "SimpleMatcher",
    "文本匹配",
    "获取相似度"
]
