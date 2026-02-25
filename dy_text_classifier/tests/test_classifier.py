# encoding: utf-8
"""
单元测试
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from category_cache_manager import CategoryCacheManager
from text_classifier import TextClassifier
from batch_processor import BatchProcessor
from evaluator import Evaluator


def test_hash_consistency():
    """测试Hash计算一致性"""
    print("\n测试: Hash计算一致性")
    desc = "拼多多电商运营"
    hash1 = CategoryCacheManager.compute_hash(desc)
    hash2 = CategoryCacheManager.compute_hash(desc)
    assert hash1 == hash2, f"Hash不一致: {hash1} != {hash2}"
    assert len(hash1) == 32, f"Hash长度错误: {len(hash1)}"
    print(f"  ✓ Hash一致: {hash1}")


def test_cache_roundtrip():
    """测试缓存读写"""
    print("\n测试: 缓存读写")
    import shutil
    test_dir = "test_cache_temp"
    
    try:
        manager = CategoryCacheManager(cache_dir=test_dir)
        hash_id = "test_hash_12345678"
        word_bank = {"拼多多": 1.0, "PDD": 0.6}
        
        # 保存
        manager.save(hash_id, "测试描述", word_bank)
        
        # 读取
        loaded = manager.load(hash_id)
        assert loaded == word_bank, f"加载数据不一致: {loaded} != {word_bank}"
        print(f"  ✓ 缓存读写正常")
        
    finally:
        # 清理
        if Path(test_dir).exists():
            shutil.rmtree(test_dir)


def test_cache_hit():
    """测试缓存命中检查"""
    print("\n测试: 缓存命中检查")
    import shutil
    test_dir = "test_cache_hit"
    
    try:
        manager = CategoryCacheManager(cache_dir=test_dir)
        hash_id = "test_hash_hit_123"
        
        # 初始不存在
        assert not manager.exists(hash_id), "缓存不应存在"
        
        # 保存后存在
        manager.save(hash_id, "测试", {"测试": 1.0})
        assert manager.exists(hash_id), "缓存应存在"
        
        print(f"  ✓ 缓存命中检查正常")
        
    finally:
        if Path(test_dir).exists():
            shutil.rmtree(test_dir)


def test_basic_match():
    """测试基础匹配"""
    print("\n测试: 基础匹配")
    classifier = TextClassifier()
    word_bank = {"拼多多": 1.0, "运营": 1.0}
    
    result = classifier.classify(
        hash_id="test",
        word_bank=word_bank,
        text="拼多多运营技巧",
        category_desc="测试"
    )
    
    assert result.similarity > 0.5, f"相似度应大于0.5: {result.similarity}"
    assert "拼多多" in [w for w, _ in result.matched_words], "应匹配'拼多多'"
    print(f"  ✓ 基础匹配正常，相似度: {result.similarity}")


def test_hashtag_weight():
    """测试hashtag加权"""
    print("\n测试: hashtag加权")
    # 使用扩展词（权重0.6）来测试，避免被1.0上限截断
    classifier = TextClassifier(hashtag_weight=2.0, max_score=10.0)  # 提高max_score避免截断
    word_bank = {"拼多多": 0.6}  # 使用扩展词权重
    
    # 同样的词，在hashtag中应该得分更高
    result1 = classifier.classify(
        hash_id="test",
        word_bank=word_bank,
        text="#拼多多 技巧"
    )
    result2 = classifier.classify(
        hash_id="test",
        word_bank=word_bank,
        text="拼多多技巧"
    )
    
    assert result1.similarity > result2.similarity, \
        f"hashtag中应得分更高: {result1.similarity} vs {result2.similarity}"
    print(f"  ✓ hashtag加权正常: {result1.similarity:.4f} vs {result2.similarity:.4f}")


def test_empty_text():
    """测试空文本处理"""
    print("\n测试: 空文本处理")
    classifier = TextClassifier()
    word_bank = {"拼多多": 1.0}
    
    result = classifier.classify(
        hash_id="test",
        word_bank=word_bank,
        text=""
    )
    
    assert result.similarity == 0.0, f"空文本相似度应为0: {result.similarity}"
    print(f"  ✓ 空文本处理正常")


def test_analyze_results():
    """测试结果分析"""
    print("\n测试: 结果分析")
    test_results = [
        {'相似度': 0.85},
        {'相似度': 0.72},
        {'相似度': 0.45},
        {'相似度': 0.30},
    ]
    
    stats = Evaluator.analyze_results(test_results)
    
    assert stats["样本数"] == 4, f"样本数错误: {stats['样本数']}"
    assert stats["最高相似度"] == 0.85, f"最高相似度错误: {stats['最高相似度']}"
    assert stats["最低相似度"] == 0.30, f"最低相似度错误: {stats['最低相似度']}"
    print(f"  ✓ 结果分析正常")


def test_batch_processor():
    """测试批量处理器"""
    print("\n测试: 批量处理器")
    classifier = TextClassifier()
    processor = BatchProcessor(classifier)
    
    word_bank = {"拼多多": 1.0, "运营": 0.6}
    
    test_items = [
        {'文案': '拼多多运营技巧', '作者': '@test1'},
        {'文案': '淘宝店铺管理', '作者': '@test2'},
        {'文案': '不相关的文案', '作者': '@test3'},
    ]
    
    results = processor.process_list(
        hash_id="test",
        word_bank=word_bank,
        category_desc="测试",
        items=test_items,
        threshold=0.3
    )
    
    # 应该过滤掉不相关的文案
    assert len(results) < len(test_items), "应有过滤"
    assert all(r['相似度'] >= 0.3 for r in results), "应满足阈值"
    print(f"  ✓ 批量处理正常，命中 {len(results)}/{len(test_items)} 条")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行单元测试")
    print("=" * 60)
    
    tests = [
        test_hash_consistency,
        test_cache_roundtrip,
        test_cache_hit,
        test_basic_match,
        test_hashtag_weight,
        test_empty_text,
        test_analyze_results,
        test_batch_processor,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ 异常: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}, 失败 {failed}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
