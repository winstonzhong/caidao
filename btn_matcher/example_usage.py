#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Button Matcher 使用示例
展示如何使用增强版的按钮匹配工具
"""

import cv2
import numpy as np
from button_matcher import *


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例1: 基本使用")
    print("=" * 60)
    
    # 1. 构建测试数据库
    print("\n1. 构建测试数据库...")
    templates = []
    for i, size in enumerate([(100, 50), (80, 40), (120, 60)]):
        # 创建模板
        template = np.zeros((size[1], size[0]), dtype=np.uint8)
        cv2.rectangle(template, (20, 10), (size[0]-20, size[1]-10), 255, -1)
        cv2.circle(template, (size[0]//2, size[1]//2), 10, 128, -1)
        templates.append((f'button_{i}', template))
    
    # 构建数据库
    success = build_database_from_imgs(templates, 'example.db')
    print(f"✓ 数据库构建: {'成功' if success else '失败'}")
    
    # 2. 加载数据库
    print("\n2. 加载数据库...")
    success, db = load_database('example.db')
    if not success:
        print("数据库加载失败")
        return
    print(f"✓ 加载 {len(db)} 个模板")
    
    # 3. 创建测试mask
    print("\n3. 创建测试mask...")
    test_mask = templates[0][1].copy()
    test_mask = cv2.GaussianBlur(test_mask, (3, 3), 0.5)  # 添加模糊
    print(f"✓ 测试mask尺寸: {test_mask.shape}")
    
    # 4. 执行匹配
    print("\n4. 执行匹配...")
    success, matches = find_buttons(test_mask, db)
    if success and matches:
        print(f"✓ 找到 {len(matches)} 个匹配:")
        for i, match in enumerate(matches[:3], 1):
            print(f"  {i}. {match['btn_name']}: {match['match_prob']:.3f}")
    else:
        print("✗ 未找到匹配")


def example_batch_processing():
    """批量处理示例"""
    print("\n" + "=" * 60)
    print("示例2: 批量处理")
    print("=" * 60)
    
    # 加载数据库
    success, db = load_database('example.db')
    if not success:
        return
    
    # 创建多个测试masks
    print("\n1. 创建多个测试masks...")
    masks = []
    for i in range(5):
        # 创建不同变体的模板
        mask = np.zeros((50, 100), dtype=np.uint8)
        cv2.rectangle(mask, (20+i*2, 10+i), (80-i*2, 40-i), 255, -1)
        if i % 2 == 0:
            mask = cv2.GaussianBlur(mask, (3, 3), 0.5)
        masks.append(mask)
    
    print(f"✓ 创建 {len(masks)} 个测试masks")
    
    # 方法1: 使用find_buttons_all
    print("\n2. 使用find_buttons_all...")
    success, results = find_buttons_all(masks, db, min_match_prob=0.2)
    if success:
        print(f"✓ 找到 {len(results)} 个匹配结果:")
        for result in results:
            print(f"  Mask {result['mask_idx']}: {result['btn_name']} "
                  f"(置信度: {result['match_prob']:.3f})")
    
    # 方法2: 使用批量匹配流程（推荐）
    print("\n3. 使用批量匹配流程（带过滤）...")
    success, results = 批量匹配流程(
        masks, db,
        min_match_prob=0.2,
        使用宽高比过滤=True,
        使用尺寸过滤=True,
        aspect_ratio_tolerance=0.15,
        尺寸容忍阈值=0.25
    )
    if success:
        print(f"✓ 过滤后找到 {len(results)} 个匹配结果:")
        for i, result in enumerate(results[:5], 1):
            print(f"  {i}. Mask {result['mask_idx']}: {result['btn_name']} "
                  f"(置信度: {result['match_prob']:.3f})")


def example_device_adaptation():
    """设备适配示例"""
    print("\n" + "=" * 60)
    print("示例3: 设备适配")
    print("=" * 60)
    
    # 加载数据库
    success, db = load_database('example.db')
    if not success:
        return
    
    # 创建测试masks
    masks = []
    for i in range(3):
        # 模拟不同尺寸的masks
        h, w = 45 + i*5, 90 + i*10
        mask = np.random.randint(0, 255, (h, w), dtype=np.uint8)
        masks.append(mask)
    
    print(f"✓ 创建 {len(masks)} 个不同尺寸的masks")
    
    # 手机设备（小屏）
    print("\n1. 手机设备适配...")
    success, results_phone = 批量匹配流程(
        masks, db,
        min_match_prob=0.1,
        x方向缩放率=0.7,    # 宽度缩小30%
        y方向缩放率=0.75,   # 高度缩小25%
        尺寸容忍阈值=0.3    # 更大的容忍度
    )
    print(f"✓ 手机设备: 找到 {len(results_phone)} 个匹配")
    
    # 平板设备（大屏）
    print("\n2. 平板设备适配...")
    success, results_tablet = 批量匹配流程(
        masks, db,
        min_match_prob=0.1,
        x方向缩放率=1.2,    # 宽度放大20%
        y方向缩放率=1.15,   # 高度放大15%
        尺寸容忍阈值=0.25
    )
    print(f"✓ 平板设备: 找到 {len(results_tablet)} 个匹配")
    
    # 比较结果
    print("\n3. 结果比较...")
    print(f"  手机设备匹配数: {len(results_phone)}")
    print(f"  平板设备匹配数: {len(results_tablet)}")


def example_filtering_strategies():
    """过滤策略示例"""
    print("\n" + "=" * 60)
    print("示例4: 过滤策略")
    print("=" * 60)
    
    # 加载数据库
    success, db = load_database('example.db')
    if not success:
        return
    
    # 创建多样化的测试masks
    print("\n1. 创建多样化测试masks...")
    masks = []
    # 相似模板
    for i in range(3):
        mask = np.zeros((50, 100), dtype=np.uint8)
        cv2.rectangle(mask, (20, 10), (80, 40), 255, -1)
        masks.append(mask)
    # 不同尺寸
    for i in range(2):
        mask = np.zeros((60, 120), dtype=np.uint8)
        cv2.rectangle(mask, (25, 15), (95, 45), 255, -1)
        masks.append(mask)
    # 随机图案（不匹配）
    for i in range(2):
        mask = np.random.randint(0, 255, (45, 90), dtype=np.uint8)
        masks.append(mask)
    
    print(f"✓ 创建 {len(masks)} 个测试masks")
    
    # 统计数据库信息
    print("\n2. 数据库统计...")
    info = 统计数据库信息(db)
    print(f"  总模板数: {info['total_buttons']}")
    print(f"  平均尺寸: {info['avg_width']:.1f}x{info['avg_height']:.1f}")
    print(f"  平均特征数: {info['avg_features']:.1f}")
    
    # 测试不同过滤策略
    print("\n3. 测试不同过滤策略...")
    
    # 无过滤
    print("\n  3.1 无过滤...")
    success, results_no_filter = 批量匹配流程(
        masks, db,
        min_match_prob=0.1,
        使用宽高比过滤=False,
        使用尺寸过滤=False
    )
    print(f"      结果数: {len(results_no_filter)}")
    
    # 仅宽高比过滤
    print("\n  3.2 仅宽高比过滤...")
    success, results_ar = 批量匹配流程(
        masks, db,
        min_match_prob=0.1,
        使用宽高比过滤=True,
        使用尺寸过滤=False,
        aspect_ratio_tolerance=0.2
    )
    print(f"      结果数: {len(results_ar)}")
    
    # 宽高比+尺寸过滤
    print("\n  3.3 宽高比+尺寸过滤...")
    success, results_both = 批量匹配流程(
        masks, db,
        min_match_prob=0.1,
        使用宽高比过滤=True,
        使用尺寸过滤=True,
        aspect_ratio_tolerance=0.2,
        尺寸容忍阈值=0.3
    )
    print(f"      结果数: {len(results_both)}")
    
    print(f"\n  过滤效果:")
    print(f"    无过滤: {len(results_no_filter)} 个结果")
    print(f"    宽高比过滤: {len(results_ar)} 个结果")
    print(f"    双重过滤: {len(results_both)} 个结果")


def example_data_persistence():
    """数据持久化示例"""
    print("\n" + "=" * 60)
    print("示例5: 数据持久化")
    print("=" * 60)
    
    # 加载数据库
    success, db = load_database('example.db')
    if not success:
        return
    
    # 创建测试数据
    print("\n1. 执行匹配...")
    masks = [np.zeros((50, 100), dtype=np.uint8) for _ in range(3)]
    success, results = find_buttons_all(masks, db, min_match_prob=0.0)
    
    print(f"✓ 获得 {len(results)} 个匹配结果")
    
    # 保存结果
    print("\n2. 保存匹配结果...")
    output_file = 'match_results.json'
    success = 保存匹配结果(results, output_file)
    print(f"✓ 保存: {'成功' if success else '失败'}")
    
    # 加载结果
    print("\n3. 加载匹配结果...")
    success, loaded_results = 加载匹配结果(output_file)
    if success:
        print(f"✓ 加载成功，共 {len(loaded_results)} 条记录")
        print("\n  前3条记录:")
        for i, result in enumerate(loaded_results[:3], 1):
            print(f"    {i}. Mask {result['mask_idx']}: {result['btn_name']}")
    
    # 对比原始数据和加载数据
    print("\n4. 数据验证...")
    if len(results) == len(loaded_results):
        print("✓ 数据完整性验证通过")
    else:
        print("✗ 数据完整性验证失败")


def example_performance_test():
    """性能测试示例"""
    print("\n" + "=" * 60)
    print("示例6: 性能测试")
    print("=" * 60)
    
    # 加载数据库
    success, db = load_database('example.db')
    if not success:
        return
    
    # 创建大规模测试数据
    print("\n1. 创建大规模测试数据...")
    import time
    
    large_masks = []
    for i in range(50):
        h = np.random.randint(40, 100)
        w = np.random.randint(80, 150)
        mask = np.random.randint(0, 255, (h, w), dtype=np.uint8)
        large_masks.append(mask)
    
    print(f"✓ 创建 {len(large_masks)} 个masks")
    
    # 测试过滤性能
    print("\n2. 测试过滤性能...")
    
    start = time.time()
    filtered_masks, filtered_db, _ = 过滤宽高比(
        large_masks, db, aspect_ratio_tolerance=0.2
    )
    ar_time = time.time() - start
    
    start = time.time()
    filtered_masks2, filtered_db2, _ = 过滤尺寸(
        large_masks, db, x方向缩放率=1.0, y方向缩放率=1.0, 容忍阈值=0.3
    )
    size_time = time.time() - start
    
    print(f"  宽高比过滤: {ar_time*1000:.2f}ms ({len(large_masks)} → {len(filtered_masks)} masks)")
    print(f"  尺寸过滤: {size_time*1000:.2f}ms ({len(large_masks)} → {len(filtered_masks2)} masks)")
    
    # 测试匹配性能
    print("\n3. 测试匹配性能...")
    test_subset = large_masks[:10]  # 只测试10个以节省时间
    
    start = time.time()
    success, results = find_buttons_all(test_subset, db, min_match_prob=0.0)
    match_time = time.time() - start
    
    print(f"  批量匹配: {match_time*1000:.2f}ms ({len(test_subset)}个masks)")
    print(f"  平均每mask: {match_time/len(test_subset)*1000:.2f}ms")
    print(f"  匹配结果数: {len(results)}")
    
    # 完整流程性能
    print("\n4. 测试完整流程性能...")
    start = time.time()
    success, results = 批量匹配流程(
        test_subset, db,
        min_match_prob=0.2,
        使用宽高比过滤=True,
        使用尺寸过滤=True
    )
    full_time = time.time() - start
    
    print(f"  完整流程: {full_time*1000:.2f}ms ({len(test_subset)}个masks)")
    print(f"  平均每mask: {full_time/len(test_subset)*1000:.2f}ms")
    print(f"  最终结果数: {len(results)}")


def main():
    """运行所有示例"""
    print("Button Matcher 使用示例")
    print("=" * 60)
    
    examples = [
        ("基本使用", example_basic_usage),
        ("批量处理", example_batch_processing),
        ("设备适配", example_device_adaptation),
        ("过滤策略", example_filtering_strategies),
        ("数据持久化", example_data_persistence),
        ("性能测试", example_performance_test),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            print(f"\n\n{'='*60}")
            print(f"示例 {i}: {name}")
            print(f"{'='*60}")
            func()
        except Exception as e:
            print(f"✗ 示例 {i} 执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
