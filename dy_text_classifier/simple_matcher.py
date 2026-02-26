# encoding: utf-8
"""
简单文本匹配器

提供便捷的文本匹配接口，直接返回布尔结果
"""

from typing import Dict, Union
from .category_cache_manager import CategoryCacheManager
from .text_classifier import TextClassifier


class SimpleMatcher:
    """
    简单文本匹配器
    
    提供一键式的文本匹配功能：
    输入类别描述 + JSON数据 → 返回是否匹配
    
    自动处理：
    - 词库生成/缓存
    - 文本字段合并
    - 相似度计算
    - 阈值判断
    """
    
    # 默认相似度阈值（经验值，后续可通过学习优化）
    DEFAULT_THRESHOLD = 0.3
    
    def __init__(
        self, 
        cache_dir: str = "cache",
        hashtag_weight: float = 1.5,
        default_threshold: float = None
    ):
        """
        初始化简单匹配器
        
        Args:
            cache_dir: 缓存目录
            hashtag_weight: hashtag权重倍数
            default_threshold: 默认阈值（如不指定使用类默认值0.3）
        """
        self.cache_manager = CategoryCacheManager(cache_dir=cache_dir)
        self.classifier = TextClassifier(hashtag_weight=hashtag_weight)
        self.default_threshold = default_threshold or self.DEFAULT_THRESHOLD
        
        # 缓存类别词库，避免重复生成
        self._word_bank_cache = {}
    
    def _get_word_bank(self, category_desc: str, total_words: int = 20) -> tuple:
        """
        获取词库（带内存缓存）
        
        Args:
            category_desc: 类别描述
            total_words: 词库大小
        
        Returns:
            (hash_id, word_bank, is_from_cache)
        """
        # 检查内存缓存
        if category_desc in self._word_bank_cache:
            return self._word_bank_cache[category_desc]
        
        # 获取或创建词库
        hash_id, word_bank, is_from_cache = self.cache_manager.get_or_create(
            description=category_desc,
            total_words=total_words
        )
        
        # 存入内存缓存
        self._word_bank_cache[category_desc] = (hash_id, word_bank, is_from_cache)
        
        return hash_id, word_bank, is_from_cache
    
    def _合并文本字段(self, data: Dict) -> str:
        """
        合并JSON数据中的文本字段
        
        合并字段优先级：
        1. 文案（最核心）
        2. 作者
        3. 音乐
        
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
    
    def 文本匹配(
        self,
        类别描述: str,
        数据: Dict,
        阈值: float = None,
        总词数: int = 20
    ) -> bool:
        """
        判断数据是否匹配指定类别
        
        Args:
            类别描述: 类别描述文本，如"拼多多电商运营"
            数据: JSON数据字典（包含文案、作者等字段）
            阈值: 相似度阈值（默认0.3，可通过学习优化）
            总词数: 生成词库的大小
        
        Returns:
            bool: 是否匹配（相似度 >= 阈值）
        
        Examples:
            >>> matcher = SimpleMatcher()
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
        # 使用默认阈值
        if 阈值 is None:
            阈值 = self.default_threshold
        
        # 获取词库
        hash_id, word_bank, is_from_cache = self._get_word_bank(类别描述, 总词数)
        
        # 合并文本字段
        text = self._合并文本字段(数据)
        
        if not text:
            return False
        
        # 计算相似度
        result = self.classifier.classify(
            hash_id=hash_id,
            word_bank=word_bank,
            text=text,
            category_desc=类别描述,
            is_from_cache=is_from_cache
        )
        
        # 返回是否匹配
        return result.similarity >= 阈值
    
    def 获取相似度(
        self,
        类别描述: str,
        数据: Dict,
        总词数: int = 20
    ) -> float:
        """
        获取数据与类别的相似度（不判断阈值，返回具体分数）
        
        Args:
            类别描述: 类别描述文本
            数据: JSON数据字典
            总词数: 生成词库的大小
        
        Returns:
            float: 相似度分数 (0.0 - 1.0)
        """
        # 获取词库
        hash_id, word_bank, is_from_cache = self._get_word_bank(类别描述, 总词数)
        
        # 合并文本字段
        text = self._合并文本字段(数据)
        
        if not text:
            return 0.0
        
        # 计算相似度
        result = self.classifier.classify(
            hash_id=hash_id,
            word_bank=word_bank,
            text=text,
            category_desc=类别描述,
            is_from_cache=is_from_cache
        )
        
        return result.similarity
    
    def 批量匹配(
        self,
        类别描述: str,
        数据列表: list,
        阈值: float = None,
        总词数: int = 20
    ) -> list:
        """
        批量匹配多个数据
        
        Args:
            类别描述: 类别描述文本
            数据列表: JSON数据字典列表
            阈值: 相似度阈值
            总词数: 生成词库的大小
        
        Returns:
            list: 匹配的数据列表（每项包含原始数据和相似度）
        """
        if 阈值 is None:
            阈值 = self.default_threshold
        
        匹配结果 = []
        
        for 数据 in 数据列表:
            相似度 = self.获取相似度(类别描述, 数据, 总词数)
            if 相似度 >= 阈值:
                结果项 = 数据.copy()
                结果项['_相似度'] = 相似度
                匹配结果.append(结果项)
        
        # 按相似度降序排序
        匹配结果.sort(key=lambda x: x['_相似度'], reverse=True)
        
        return 匹配结果
    
    def 设置默认阈值(self, 阈值: float):
        """
        设置默认阈值
        
        可通过学习大量数据后，调用此方法设置最优阈值
        
        Args:
            阈值: 新的默认阈值
        """
        self.default_threshold = 阈值
        print(f"默认阈值已设置为: {阈值}")


# 便捷函数接口
def 文本匹配(
    类别描述: str,
    数据: Dict,
    阈值: float = 0.3,
    缓存目录: str = "cache"
) -> bool:
    """
    便捷的文本匹配函数（单例模式）
    
    Args:
        类别描述: 类别描述文本
        数据: JSON数据字典
        阈值: 相似度阈值（默认0.3）
        缓存目录: 缓存目录路径
    
    Returns:
        bool: 是否匹配
    
    Examples:
        >>> data = {"文案": "#拼多多运营 发货！", "作者": "@老陶"}
        >>> 文本匹配("拼多多电商运营", data)
        True
    """
    # 使用单例避免重复初始化
    if not hasattr(文本匹配, '_matcher'):
        文本匹配._matcher = SimpleMatcher(cache_dir=缓存目录)
    
    return 文本匹配._matcher.文本匹配(类别描述, 数据, 阈值)


def 获取相似度(
    类别描述: str,
    数据: Dict,
    缓存目录: str = "cache"
) -> float:
    """
    获取相似度分数
    
    Args:
        类别描述: 类别描述文本
        数据: JSON数据字典
        缓存目录: 缓存目录路径
    
    Returns:
        float: 相似度分数 (0.0 - 1.0)
    """
    if not hasattr(获取相似度, '_matcher'):
        获取相似度._matcher = SimpleMatcher(cache_dir=缓存目录)
    
    return 获取相似度._matcher.获取相似度(类别描述, 数据)


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("简单文本匹配器测试")
    print("=" * 60)
    
    matcher = SimpleMatcher()
    
    # 测试数据
    test_data = [
        {
            "作者": "@老陶电商",
            "文案": "#老陶电商 #拼多多运营 能发货的抓紧时间去报名活动和打开直通车！",
            "音乐": "@老陶电商创作的原声",
            "点赞": "344",
            "评论": "20",
            "收藏": "142",
            "分享": "124",
            "类型": "视频"
        },
        {
            "作者": "@一只家养狗",
            "文案": "#拼多多 #福利 #分享生活小技巧 #电商日常 #省钱技巧",
            "音乐": "@创作的原声",
            "点赞": "123",
            "类型": "视频"
        },
        {
            "作者": "@美食博主",
            "文案": "今天教大家做一道家常菜，简单好吃！",
            "音乐": "轻音乐",
            "点赞": "500",
            "类型": "视频"
        },
    ]
    
    类别描述 = "拼多多电商运营"
    
    print(f"\n类别描述: {类别描述}")
    print(f"默认阈值: {matcher.default_threshold}")
    
    print("\n【测试单个匹配】")
    for i, data in enumerate(test_data, 1):
        is_match = matcher.文本匹配(类别描述, data)
        similarity = matcher.获取相似度(类别描述, data)
        print(f"\n  测试 {i}:")
        print(f"    作者: {data['作者']}")
        print(f"    文案: {data['文案'][:40]}...")
        print(f"    相似度: {similarity:.4f}")
        print(f"    是否匹配: {is_match}")
    
    print("\n【测试批量匹配】")
    matches = matcher.批量匹配(类别描述, test_data)
    print(f"匹配数量: {len(matches)}/{len(test_data)}")
    for item in matches:
        print(f"  [{item['_相似度']:.4f}] {item['作者']}: {item['文案'][:30]}...")
    
    print("\n【测试便捷函数】")
    # 使用便捷函数
    result = 文本匹配(类别描述, test_data[0])
    print(f"便捷函数结果: {result}")
    
    similarity = 获取相似度(类别描述, test_data[0])
    print(f"便捷函数相似度: {similarity:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成")
