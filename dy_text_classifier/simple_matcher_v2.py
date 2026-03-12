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
    # 中文停用词
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
    "啊", "呢", "吧", "吗", "哦", "哈", "嗯", "哎", "喂",
    # 英文停用词（介词、冠词、be动词等）
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "up", "about", "into", "through", "during", "before", "after",
    "above", "below", "between", "among", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "can", "will", "just", "should",
    "now", "and", "but", "if", "or", "because", "as", "until",
    "while", "this", "that", "these", "those", "am", "it", "its",
}

# 最短词长限制
MIN_WORD_LENGTH = 2  # 中文词最短2字
MIN_ENGLISH_WORD_LENGTH = 3  # 英文词最短3字母（过滤 'in', 'on', 'at' 等停用词，但保留 'Max', 'Maya', '3ds' 等专业词汇）


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
        3. 过滤短英文单词（防止匹配 'in', 'on' 等）
        4. 去重
        
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
            if not word:
                continue
            # 过滤条件：
            # 1. 不是纯数字
            # 2. 不是停用词
            # 3. 中文词：长度 >= MIN_WORD_LENGTH（2）
            # 4. 纯英文词：长度 >= MIN_ENGLISH_WORD_LENGTH（3），过滤停用词如 'in', 'on'
            #    但保留专业词汇如 'Max', 'Maya', '3ds', 'C4D'
            is_chinese = any('\u4e00' <= c <= '\u9fff' for c in word)
            is_pure_ascii_english = word.isalpha() and all(c.isascii() for c in word)
            
            # 纯ASCII英文词长度检查（仅过滤3字母以下的停用词）
            if is_pure_ascii_english and len(word) < MIN_ENGLISH_WORD_LENGTH:
                continue
            
            if (not word.isdigit() and 
                word not in self.stopwords and
                (is_chinese or len(word) >= MIN_ENGLISH_WORD_LENGTH)):
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
        获取目标描述的词库集合（含同义词及子串）
        
        逻辑：
        1. 检查内存缓存
        2. 获取或创建同义词库
        3. 合并所有关键词及其同义词为集合
        4. 提取关键词的子串（处理像"售后白嫖"中包含"白嫖"的情况）
        
        Args:
            description: 目标描述
        
        Returns:
            词库集合 {词1, 词2, 同义词1, 子串1, ...}
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
        
        # 构建词库集合：关键词 + 同义词 + 关键词子串
        word_set = set()
        for keyword, syn_list in synonyms.items():
            # 检查关键词本身是否有效
            if self._是有效子串(keyword):
                word_set.add(keyword)  # 添加关键词本身
                # 对英文词同时添加全小写形式（支持大小写不敏感匹配）
                if keyword.isalpha() and all(c.isascii() for c in keyword):
                    word_set.add(keyword.lower())
            
            # 添加同义词（过滤短词）
            for syn in syn_list:
                if self._是有效子串(syn):
                    word_set.add(syn)
                    # 对英文词同时添加全小写形式
                    if syn.isalpha() and all(c.isascii() for c in syn):
                        word_set.add(syn.lower())
            
            # 添加关键词的子串（仅中文词提取子串）
            # 例如"售后白嫖" → 添加"售后"、"白嫖"等
            # 注意：纯英文单词不进行子串提取，避免"Maya"提取出"Ma"、"Max"提取出"Ma"
            # 注意：数字字母混合词不进行子串提取，避免"3ds"提取出"3d"
            # 注意：不跨语言边界提取，避免"Fusion视频"提取出"视频"
            
            # 判断关键词类型
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in keyword)
            is_pure_ascii_english = all(c.isascii() and c.isalpha() for c in keyword) and not has_chinese
            has_mixed_alnum = any(c.isdigit() for c in keyword) and any(c.isalpha() for c in keyword)
            
            # 只有包含中文的关键词才提取子串
            if has_chinese:
                for i in range(len(keyword)):
                    for j in range(i + MIN_WORD_LENGTH, min(i + MIN_WORD_LENGTH + 3, len(keyword) + 1)):
                        substring = keyword[i:j]
                        # 确保子串不跨语言边界
                        if not self._是语言一致子串(keyword, i, j):
                            continue
                        # 检查子串有效性
                        if not self._是有效子串(substring):
                            continue
                        # 子串也必须包含中文（避免从"3D打印"中提取出"D打"）
                        if not any('\u4e00' <= c <= '\u9fff' for c in substring):
                            continue
                        word_set.add(substring)
        
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
            # 区分中英文
            is_chinese = any('\u4e00' <= c <= '\u9fff' for c in word)
            is_english_short = word.isalpha() and word.islower() and len(word) < MIN_ENGLISH_WORD_LENGTH
            
            if (word not in self.stopwords and
                not word.isspace() and
                not is_english_short and
                (is_chinese or len(word) >= MIN_ENGLISH_WORD_LENGTH)):
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
        # 同时检查文本中的词是否在词库中（双向匹配）
        # 支持大小写不敏感匹配（对纯ASCII英文词）
        matched_words = []
        
        # 预计算文本的小写形式（用于大小写不敏感匹配）
        text_lower = text.lower()
        
        # 方式1: 词库中的词在文本中（支持大小写不敏感）
        for word in word_set:
            # 原始形式匹配
            if word in text:
                matched_words.append(word)
            else:
                # 对纯ASCII英文词，尝试大小写不敏感匹配
                if word.isalpha() and all(c.isascii() for c in word):
                    if word.lower() in text_lower:
                        matched_words.append(word)
        
        # 方式2: 文本中的词（2字以上）在词库中（处理jieba分词不准确的情况）
        # 提取文本中所有2字以上的子串进行检查
        text_words = self._提取文本中的所有可能词(text)
        for word in text_words:
            if word in word_set:
                if word not in matched_words:
                    matched_words.append(word)
            else:
                # 对纯ASCII英文词，尝试大小写不敏感匹配
                if word.isalpha() and all(c.isascii() for c in word):
                    if word.lower() in word_set:
                        if word not in matched_words:
                            matched_words.append(word)
        
        is_match = len(matched_words) > 0
        
        if is_match:
            print(f"[SimpleMatcherV2] 匹配成功，命中词汇: {matched_words[:5]}")
        else:
            print(f"[SimpleMatcherV2] 匹配失败，无命中词汇")
            print(f"[SimpleMatcherV2] 调试信息 - 词库大小: {len(word_set)}, 文本长度: {len(text)}")
            print(f"[SimpleMatcherV2] 调试信息 - 词库样本: {list(word_set)[:10]}")
        
        return is_match
    
    def _提取文本中的所有可能词(self, text: str, min_len: int = None, max_len: int = 8) -> Set[str]:
        """
        提取文本中所有可能长度的子串
        
        用于处理jieba分词不准确的情况，例如：
        - "恶意白嫖"被jieba分成["恶意", "白", "嫖"]
        - 但通过子串提取可以找到"白嫖"
        
        Args:
            text: 输入文本
            min_len: 最小词长（默认使用 MIN_WORD_LENGTH）
            max_len: 最大词长
        
        Returns:
            所有可能的子串集合
        """
        if min_len is None:
            min_len = MIN_WORD_LENGTH
            
        words = set()
        for i in range(len(text)):
            for j in range(i + min_len, min(i + max_len + 1, len(text) + 1)):
                substring = text[i:j]
                # 过滤包含停用词和标点的
                if self._是有效子串(substring):
                    words.add(substring)
        return words
    
    def _是有效子串(self, s: str) -> bool:
        """检查子串是否有效（不包含停用词、标点、短英文单词）"""
        # 过滤标点
        if any(c in s for c in '，。！？；：""''（）【】[]{},.!?;:\'"()'):
            return False
        # 过滤纯数字
        if s.isdigit():
            return False
        # 过滤停用词
        if s in self.stopwords:
            return False
        
        # 区分中英文
        is_chinese = any('\u4e00' <= c <= '\u9fff' for c in s)
        is_english = s.isalpha() and all(c.isascii() for c in s)
        is_all_lowercase = is_english and s.islower()
        
        # 过滤纯英文小写短单词（如 'in', 'on', 'at'）
        # 但保留混合大小写的专业词汇（如 'OpenClaw', 'ClawdBot'）
        if is_all_lowercase and len(s) < MIN_ENGLISH_WORD_LENGTH:
            return False
        
        # 非中文非英文的内容（如纯数字、特殊符号）且长度不足
        if not is_chinese and len(s) < MIN_WORD_LENGTH:
            return False
            
        return True
    
    def _是语言一致子串(self, keyword: str, start: int, end: int) -> bool:
        """
        检查子串是否不跨越语言边界
        
        例如：
        - "Fusion视频"提取"视频"：Fusion(英文) + 视频(中文) → 跨越边界，不添加
        - "售后白嫖"提取"白嫖"：都是中文 → 一致，添加
        
        Args:
            keyword: 原始关键词
            start: 子串起始位置
            end: 子串结束位置
        
        Returns:
            是否语言一致
        """
        substring = keyword[start:end]
        
        # 检查子串中是否混合了中英文
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in substring)
        has_english = any(c.isalpha() and c.isascii() for c in substring)
        
        # 如果子串本身混合了中英文，不允许
        if has_chinese and has_english:
            return False
        
        # 检查子串是否与原始关键词的语言边界对齐
        # 即子串应该完全位于同一个语言块内
        if start > 0:
            # 检查起始位置是否跨越边界
            prev_char = keyword[start - 1]
            first_char = keyword[start]
            prev_is_cn = '\u4e00' <= prev_char <= '\u9fff'
            first_is_cn = '\u4e00' <= first_char <= '\u9fff'
            if prev_is_cn != first_is_cn:
                return False
        
        if end < len(keyword):
            # 检查结束位置是否跨越边界
            last_char = keyword[end - 1]
            next_char = keyword[end]
            last_is_cn = '\u4e00' <= last_char <= '\u9fff'
            next_is_cn = '\u4e00' <= next_char <= '\u9fff'
            if last_is_cn != next_is_cn:
                return False
        
        return True
    
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
