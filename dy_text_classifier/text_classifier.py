# encoding: utf-8
"""
文本分类器核心模块

基于关键词匹配的轻量级文本分类器
"""

import re
from dataclasses import dataclass
from typing import List, Tuple, Dict


@dataclass
class MatchResult:
    """匹配结果"""
    hash_id: str
    category_desc: str
    similarity: float
    matched_words: List[Tuple[str, str]]  # (词, 位置)
    is_from_cache: bool
    
    def to_dict(self) -> dict:
        return {
            'hash_id': self.hash_id[:16] + "..." if len(self.hash_id) > 16 else self.hash_id,
            '类别描述': self.category_desc,
            '相似度': round(self.similarity, 4),
            '匹配词': [w for w, _ in self.matched_words],
            '匹配位置': dict(self.matched_words),
            '来自缓存': self.is_from_cache
        }


class TextClassifier:
    """
    轻量级关键词分类器
    
    特点：
    - 纯关键词匹配，无模型依赖
    - 支持hashtag加权
    - 匹配结果可解释
    """
    
    def __init__(self, hashtag_weight: float = 1.5, max_score: float = 1.0):
        """
        初始化分类器
        
        Args:
            hashtag_weight: hashtag内匹配的权重倍数
            max_score: 用于归一化的最大分数
        """
        self.hashtag_weight = hashtag_weight
        self.max_score = max_score
    
    def classify(
        self, 
        hash_id: str,
        word_bank: Dict[str, float], 
        text: str, 
        category_desc: str = "",
        is_from_cache: bool = False
    ) -> MatchResult:
        """
        对文本进行分类匹配
        
        Args:
            hash_id: 类别Hash ID
            word_bank: 词库 {词: 权重}
            text: 待分类文本
            category_desc: 类别描述（用于结果展示）
            is_from_cache: 是否来自缓存
        
        Returns:
            MatchResult: 匹配结果
        """
        if not text:
            return MatchResult(
                hash_id=hash_id,
                category_desc=category_desc,
                similarity=0.0,
                matched_words=[],
                is_from_cache=is_from_cache
            )
        
        # 提取hashtag
        hashtags = re.findall(r'#([^#\s]+)', text)
        normal_text = re.sub(r'#[^#\s]+', '', text)
        
        matched_words = []
        score = 0.0
        matched_word_set = set()  # 防止重复计分
        
        # 在hashtag中匹配（加权）
        for tag in hashtags:
            for word, weight in word_bank.items():
                if word in tag and word not in matched_word_set:
                    score += weight * self.hashtag_weight
                    matched_words.append((word, f"#{tag}"))
                    matched_word_set.add(word)
                    break
        
        # 在普通文本中匹配
        for word, weight in word_bank.items():
            if word in normal_text and word not in matched_word_set:
                score += weight
                matched_words.append((word, "正文"))
                matched_word_set.add(word)
        
        # 归一化
        if self.max_score and self.max_score > 0:
            final_score = min(score / self.max_score, 1.0)
        else:
            final_score = min(score, 1.0)
        
        return MatchResult(
            hash_id=hash_id,
            category_desc=category_desc,
            similarity=final_score,
            matched_words=matched_words,
            is_from_cache=is_from_cache
        )
    
    def batch_classify(
        self,
        hash_id: str,
        word_bank: Dict[str, float],
        texts: List[Dict],
        category_desc: str = "",
        is_from_cache: bool = False
    ) -> List[MatchResult]:
        """
        批量分类
        
        Args:
            hash_id: 类别Hash ID
            word_bank: 词库
            texts: 文本列表，每项为包含'文案'key的字典
            category_desc: 类别描述
            is_from_cache: 是否来自缓存
        
        Returns:
            MatchResult列表
        """
        results = []
        for item in texts:
            text = item.get('文案', '') if isinstance(item, dict) else str(item)
            result = self.classify(
                hash_id=hash_id,
                word_bank=word_bank,
                text=text,
                category_desc=category_desc,
                is_from_cache=is_from_cache
            )
            results.append(result)
        return results


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("文本分类器测试")
    print("=" * 60)
    
    classifier = TextClassifier(hashtag_weight=1.5)
    
    # 测试词库
    word_bank = {
        "拼多多": 1.0,
        "运营": 1.0,
        "PDD": 0.6,
        "拼夕夕": 0.6,
        "店铺": 0.6
    }
    
    # 测试文本
    test_texts = [
        "#拼多多运营 能发货的抓紧时间去报名活动！",
        "今天教大家如何做好淘宝店铺运营",
        "拼夕夕上面的东西真便宜",
        "这是一个无关的文案"
    ]
    
    print("\n测试分类:")
    for text in test_texts:
        result = classifier.classify(
            hash_id="test_hash_123",
            word_bank=word_bank,
            text=text,
            category_desc="拼多多电商",
            is_from_cache=False
        )
        print(f"\n文案: {text[:30]}...")
        print(f"相似度: {result.similarity:.4f}")
        print(f"匹配词: {result.matched_words}")
    
    print("\n" + "=" * 60)
    print("测试完成")
