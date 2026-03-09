# encoding: utf-8
"""
简单匹配器 V2 - 任意词命中即匹配

核心逻辑：
1. 从目标描述提取/扩展关键词 → 词库（含同义词）
2. 对待匹配文本分词、去停用词
3. 检查是否有词库中的词出现在文本中
4. 命中任意一词 → 匹配成功

特点：
- 无需阈值调参
- 基于集合交集判断，简单可靠
- 支持同义词扩展，提高召回率
"""

import os
import re
from typing import Dict, List, Set, Optional

# 尝试导入jieba，如未安装则使用简单分词
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("[SimpleMatcherV2] 警告: jieba未安装，使用简单分词模式")
    print("[SimpleMatcherV2] 建议: pip install jieba 以获得更好分词效果")

from .synonym_cache_manager import SynonymCacheManager


# 默认停用词（简化版，实际应从文件加载）
DEFAULT_STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
    "啊", "呢", "吧", "吗", "哦", "哈", "嗯", "哎", "喂",
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
}


class SimpleMatcherV2:
    """
    简单匹配器 V2
    
    提供一键式的文本匹配功能：
    输入目标描述 + JSON数据 → 返回是否匹配（布尔值）
    
    匹配规则：词库中任意一词命中即匹配成功
    """
    
    def __init__(
        self, 
        cache_dir: str = "synonym_cache",
        stopwords: Optional[Set[str]] = None
    ):
        """
        初始化简单匹配器
        
        Args:
            cache_dir: 同义词缓存目录
            stopwords: 停用词集合（如不提供则使用默认停用词）
        """
        self.cache_manager = SynonymCacheManager(cache_dir=cache_dir)
        self.stopwords = stopwords or DEFAULT_STOPWORDS
        
        # 内存缓存：目标描述 → 词库集合
        self._word_set_cache = {}
    
    def _提取关键词(self, description: str) -> List[str]:
        """
        从目标描述中提取关键词
        
        策略：
        1. 按标点符号分割
        2. 过滤停用词和短词
        3. 去重
        
        Args:
            description: 目标描述文本
        
        Returns:
            关键词列表
        """
        # 按常见标点分割
        words = re.split(r'[、，,；;。！!？?：:\s\n\r\-\[\]]+', description)
        
        # 过滤和清理
        keywords = []
        for word in words:
            word = word.strip()
            # 过滤条件：长度>=2，不是纯数字，不是停用词
            if (len(word) >= 2 and 
                not word.isdigit() and 
                word not in self.stopwords):
                keywords.append(word)
        
        # 去重保持顺序
        seen = set()
        unique_keywords = []
        for word in keywords:
            if word not in seen:
                seen.add(word)
                unique_keywords.append(word)
        
        return unique_keywords
    
    def _get_word_set(self, description: str) -> Set[str]:
        """
        获取目标描述的词库集合（含同义词）
        
        逻辑：
        1. 检查内存缓存
        2. 获取或创建同义词库
        3. 合并所有关键词及其同义词为集合
        
        Args:
            description: 目标描述
        
        Returns:
            词库集合 {词1, 词2, 同义词1, ...}
        """
        # 检查内存缓存
        if description in self._word_set_cache:
            return self._word_set_cache[description]
        
        # 提取关键词
        keywords = self._提取关键词(description)
        
        # 获取同义词库
        hash_id, synonyms, is_from_cache = self.cache_manager.get_or_create(
            description=description,
            keywords=keywords
        )
        
        # 构建词库集合：关键词 + 同义词
        word_set = set()
        for keyword, syn_list in synonyms.items():
            word_set.add(keyword)  # 添加关键词本身
            word_set.update(syn_list)  # 添加同义词
        
        # 存入内存缓存
        self._word_set_cache[description] = word_set
        
        return word_set
    
    def _分词(self, text: str) -> List[str]:
        """
        对文本进行分词
        
        Args:
            text: 待分词文本
        
        Returns:
            分词结果列表
        """
        if JIEBA_AVAILABLE:
            return list(jieba.cut(text))
        else:
            # 备用分词：按字符和简单规则
            return self._简单分词(text)
    
    def _简单分词(self, text: str) -> List[str]:
        """
        简单分词（jieba不可用时使用）
        
        策略：
        1. 按非中文字符分割
        2. 提取连续的中文字符
        3. 提取连续的英文字符
        """
        words = []
        
        # 提取连续中文字符（2-8个字作为词）
        for match in re.finditer(r'[\u4e00-\u9fff]{2,8}', text):
            words.append(match.group())
        
        # 提取连续英文字符
        for match in re.finditer(r'[a-zA-Z]+', text):
            word = match.group().lower()
            if len(word) >= 2:
                words.append(word)
        
        # 提取数字
        for match in re.finditer(r'\d+', text):
            words.append(match.group())
        
        return words
    
    def _提取文本(self, data: Dict) -> str:
        """
        从JSON数据中提取待匹配文本
        
        合并字段优先级：
        1. 文案（最核心）
        2. 作者
        3. 音乐
        4. 其他字符串字段
        
        Args:
            data: JSON数据字典
        
        Returns:
            合并后的文本字符串
        """
        文本片段 = []
        
        # 文案（权重最高）
        if '文案' in data and data['文案']:
            文本片段.append(str(data['文案']))
        
        # 作者
        if '作者' in data and data['作者']:
            文本片段.append(str(data['作者']))
        
        # 音乐
        if '音乐' in data and data['音乐']:
            文本片段.append(str(data['音乐']))
        
        # 如果没有上述字段，尝试合并所有字符串类型的值
        if not 文本片段:
            for key, value in data.items():
                if isinstance(value, str) and value:
                    文本片段.append(value)
        
        return ' '.join(文本片段)
    
    def _对文本分词去停用词(self, text: str) -> Set[str]:
        """
        对文本分词并去除停用词
        
        Args:
            text: 待处理文本
        
        Returns:
            分词后的集合（去停用词后），同时包含原始文本用于子串匹配
        """
        # 分词
        words = self._分词(text)
        
        # 去停用词，过滤短词
        result = set()
        for word in words:
            word = word.strip()
            if (len(word) >= 2 and 
                word not in self.stopwords and
                not word.isspace()):
                result.add(word)
        
        # 同时保留原始文本，用于子串匹配（解决jieba分词不准确的问题）
        result.add(text)
        
        return result
    
    def 文本匹配(
        self,
        目标描述: str,
        数据: Dict
    ) -> bool:
        """
        判断数据是否匹配指定目标描述
        
        匹配规则：词库中任意一词在文本中出现（子串匹配）即匹配成功
        
        Args:
            目标描述: 目标描述文本
            数据: JSON数据字典（包含文案、作者等字段）
        
        Returns:
            bool: 是否匹配（任意词命中即True）
        
        Examples:
            >>> matcher = SimpleMatcherV2()
            >>> data = {
            ...     "作者": "@老陶电商",
            ...     "文案": "#拼多多运营 能发货的抓紧时间去报名活动！",
            ...     "音乐": "@老陶电商创作的原声"
            ... }
            >>> matcher.文本匹配("拼多多电商运营", data)
            True
            
            >>> data2 = {
            ...     "作者": "@美食博主",
            ...     "文案": "今天教大家做一道家常菜",
            ... }
            >>> matcher.文本匹配("拼多多电商运营", data2)
            False
        """
        # 获取词库集合
        word_set = self._get_word_set(目标描述)
        
        if not word_set:
            print(f"[SimpleMatcherV2] 警告: 词库为空")
            return False
        
        # 提取待匹配文本
        text = self._提取文本(数据)
        
        if not text:
            return False
        
        # 检查词库中任意一词是否在文本中出现（子串匹配）
        matched_words = []
        for word in word_set:
            if word in text:
                matched_words.append(word)
        
        is_match = len(matched_words) > 0
        
        if is_match:
            print(f"[SimpleMatcherV2] 匹配成功，命中词汇: {matched_words[:5]}")
        else:
            print(f"[SimpleMatcherV2] 匹配失败，无命中词汇")
        
        return is_match
    
    def 获取匹配详情(
        self,
        目标描述: str,
        数据: Dict
    ) -> Dict:
        """
        获取匹配的详细信息（调试用）
        
        Args:
            目标描述: 目标描述文本
            数据: JSON数据字典
        
        Returns:
            匹配详情字典
        """
        # 获取词库集合
        word_set = self._get_word_set(目标描述)
        
        # 提取待匹配文本
        text = self._提取文本(数据)
        
        # 查找命中词汇
        matched_words = []
        for word in word_set:
            if word in text:
                matched_words.append(word)
        
        return {
            "是否匹配": len(matched_words) > 0,
            "词库大小": len(word_set),
            "命中词汇数": len(matched_words),
            "命中词汇": matched_words,
            "词库样本": list(word_set)[:10],
            "待匹配文本": text[:100] + "..." if len(text) > 100 else text
        }
    
    def 清除缓存(self, 目标描述: str = None):
        """
        清除缓存
        
        Args:
            目标描述: 如指定则清理该描述的缓存，否则清理全部
        """
        if 目标描述:
            # 清除内存缓存
            if 目标描述 in self._word_set_cache:
                del self._word_set_cache[目标描述]
            
            # 清除文件缓存
            hash_id = self.cache_manager.compute_hash(目标描述)
            self.cache_manager.clear_cache(hash_id)
        else:
            # 清除全部
            self._word_set_cache.clear()
            self.cache_manager.clear_cache()


# 全局单例（便于直接使用）
_matcher_v2_instance = None

def 文本匹配(目标描述: str, 数据: Dict) -> bool:
    """
    便捷函数：直接使用SimpleMatcherV2进行文本匹配
    
    Args:
        目标描述: 目标描述文本
        数据: JSON数据字典
    
    Returns:
        bool: 是否匹配
    """
    global _matcher_v2_instance
    if _matcher_v2_instance is None:
        _matcher_v2_instance = SimpleMatcherV2()
    
    return _matcher_v2_instance.文本匹配(目标描述, 数据)


def 获取匹配详情(目标描述: str, 数据: Dict) -> Dict:
    """
    便捷函数：获取匹配详情
    """
    global _matcher_v2_instance
    if _matcher_v2_instance is None:
        _matcher_v2_instance = SimpleMatcherV2()
    
    return _matcher_v2_instance.获取匹配详情(目标描述, 数据)
