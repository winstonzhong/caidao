# encoding: utf-8
"""
抖音视频文案文本分类器 - 主入口

完整使用示例
"""

import sys
from pathlib import Path

# 添加父目录到路径，以便导入helper_synonym
sys.path.insert(0, str(Path(__file__).parent.parent))

from category_cache_manager import CategoryCacheManager
from .text_classifier import TextClassifier
from batch_processor import BatchProcessor
from evaluator import Evaluator
from simple_matcher import SimpleMatcher, 文本匹配, 获取相似度


def demo_simple_matcher():
    """演示简单匹配器（最简接口）"""
    print("\n" + "=" * 70)
    print("【演示1】简单匹配器（最简接口）")
    print("=" * 70)
    
    # JSON数据样例
    test_data = [
        {
            "作者": "@老陶电商",
            "文案": "#老陶电商 #拼多多运营 能发货的抓紧时间去报名活动和打开直通车！",
            "音乐": "@老陶电商创作的原声",
            "点赞": "344",
            "评论": "20",
            "类型": "视频"
        },
        {
            "作者": "@一只家养狗",
            "文案": "#拼多多 #福利 #电商日常 #省钱技巧",
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
    print(f"默认阈值: 0.3（经验值，可后续优化）\n")
    
    # 使用便捷函数
    print("【使用便捷函数】")
    for i, data in enumerate(test_data, 1):
        is_match = 文本匹配(类别描述, data)
        similarity = 获取相似度(类别描述, data)
        status = "✓ 匹配" if is_match else "✗ 不匹配"
        print(f"  {i}. [{status}] 相似度:{similarity:.4f} | {data['作者']}: {data['文案'][:30]}...")
    
    # 使用 SimpleMatcher 类
    print("\n【使用 SimpleMatcher 类】")
    matcher = SimpleMatcher()
    
    # 批量匹配
    matches = matcher.批量匹配(类别描述, test_data, 阈值=0.3)
    print(f"批量匹配结果: {len(matches)}/{len(test_data)} 条匹配")
    for item in matches:
        print(f"  - [{item['_相似度']:.4f}] {item['作者']}: {item['文案'][:30]}...")
    
    # 调整阈值演示
    print("\n【调整阈值演示】")
    print(f"原阈值: {matcher.default_threshold}")
    matcher.设置默认阈值(0.5)
    print(f"新阈值: {matcher.default_threshold}")
    
    matches_strict = matcher.批量匹配(类别描述, test_data)
    print(f"严格阈值(0.5)下匹配: {len(matches_strict)}/{len(test_data)} 条")


def demo_full_workflow():
    """演示完整工作流程"""
    print("\n" + "=" * 70)
    print("【演示2】完整工作流程（高级用法）")
    print("=" * 70)
    
    # 1. 初始化缓存管理器
    cache_manager = CategoryCacheManager(cache_dir="cache")
    
    # 2. 定义类别描述
    category_desc = "拼多多电商平台运营相关，包括店铺运营、发货、直通车、活动报名等"
    print(f"\n类别描述: {category_desc}")
    
    # 3. 获取或创建词库（自动处理缓存）
    print("\n【获取词库】")
    hash_id, word_bank, is_from_cache = cache_manager.get_or_create(
        description=category_desc,
        total_words=20
    )
    print(f"Hash ID: {hash_id}")
    print(f"来自缓存: {is_from_cache}")
    print(f"词库大小: {len(word_bank)} 个词")
    
    # 4. 初始化分类器
    classifier = TextClassifier(hashtag_weight=1.5)
    
    # 5. 单条测试
    print("\n【单条测试】")
    test_texts = [
        "#老陶电商 #拼多多运营 能发货的抓紧时间去报名活动和打开直通车！",
        "今天教大家如何做好淘宝店铺运营",
        "拼夕夕上面的东西真便宜，适合批发",
        "这是一个与电商无关的日常生活分享",
    ]
    
    for text in test_texts:
        result = classifier.classify(
            hash_id=hash_id,
            word_bank=word_bank,
            text=text,
            category_desc=category_desc,
            is_from_cache=is_from_cache
        )
        status = "✓ 匹配" if result.similarity >= 0.3 else "✗ 不匹配"
        print(f"\n  [{status}] 相似度:{result.similarity:.4f}")
        print(f"  文案: {text[:40]}...")
        if result.matched_words:
            print(f"  匹配词: {', '.join([w for w, _ in result.matched_words])}")
    
    # 6. 批量处理（使用真实的JSON文件）
    xmls_dir = "/home/yka-003/workspace/caidao/ut/xmls"
    
    if Path(xmls_dir).exists():
        print(f"\n【批量处理】")
        print(f"处理目录: {xmls_dir}")
        
        processor = BatchProcessor(classifier)
        results = processor.process_directory(
            hash_id=hash_id,
            word_bank=word_bank,
            category_desc=category_desc,
            xmls_dir=xmls_dir,
            threshold=0.3,
            is_from_cache=is_from_cache
        )
        
        # 7. 查看统计
        print("\n【统计信息】")
        stats = Evaluator.analyze_results(results)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 8. 查看Top5
        print(f"\n【最相似的5条文案】")
        for i, item in enumerate(results[:5], 1):
            文案 = item['文案'][:50] + "..." if len(item['文案']) > 50 else item['文案']
            print(f"{i}. [{item['相似度']:.4f}] {文案}")
            print(f"   作者: {item['作者']} | 匹配词: {', '.join(item['匹配词'][:3])}")
    else:
        print(f"\n目录不存在: {xmls_dir}")
        print("跳过批量处理")
    
    # 9. 查看缓存统计
    print(f"\n【缓存信息】")
    cached = cache_manager.list_cached()
    print(f"当前已缓存类别数: {len(cached)}")
    for item in cached:
        print(f"  - {item['hash_id']}: {item['词数']}词")


def demo_cache_reuse():
    """演示缓存复用"""
    print("\n" + "=" * 70)
    print("【演示3】缓存复用机制")
    print("=" * 70)
    
    cache_manager = CategoryCacheManager(cache_dir="cache")
    
    # 相同的描述会命中缓存
    desc = "拼多多电商平台运营相关，包括店铺运营、发货、直通车、活动报名等"
    
    print(f"\n类别描述: {desc[:40]}...")
    
    print(f"\n第一次调用:")
    hash1, bank1, cached1 = cache_manager.get_or_create(desc, total_words=20)
    print(f"  来自缓存: {cached1}")
    
    print(f"\n第二次调用（应该命中缓存）:")
    hash2, bank2, cached2 = cache_manager.get_or_create(desc, total_words=20)
    print(f"  来自缓存: {cached2}")
    
    print(f"\n结果验证:")
    print(f"  Hash ID相同: {hash1 == hash2}")
    print(f"  词库相同: {bank1 == bank2}")
    print(f"  缓存命中节省API调用: ✓")


if __name__ == "__main__":
    # 运行所有演示
    demo_simple_matcher()    # 演示1：最简接口
    demo_full_workflow()     # 演示2：完整流程
    demo_cache_reuse()       # 演示3：缓存复用
    
    print("\n" + "=" * 70)
    print("所有演示执行完成")
    print("=" * 70)
