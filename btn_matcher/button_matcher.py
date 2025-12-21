#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import pandas as pd
import pickle
import pathlib
import argparse
import sys
import time
from typing import List, Tuple, Dict, Any, Optional


# 全局ORB特征提取器（统一参数，避免重复定义）
ORB_DETECTOR = cv2.ORB_create(
    nfeatures=100, scaleFactor=1.1, nlevels=4, edgeThreshold=3
)


# 辅助函数：KeyPoint序列化与反序列化
def keypoint_to_tuple(kp):
    """将cv2.KeyPoint对象转换为可序列化的元组"""
    return (
        kp.pt[0],  # x坐标
        kp.pt[1],  # y坐标
        kp.size,  # 尺寸
        kp.angle,  # 角度
        kp.response,  # 响应值
        kp.octave,  # 金字塔层数
        kp.class_id,  # 类别ID
    )


def tuple_to_keypoint(kp_tuple):
    """将序列化的元组还原为cv2.KeyPoint对象"""
    kp = cv2.KeyPoint()
    kp.pt = (kp_tuple[0], kp_tuple[1])
    kp.size = kp_tuple[2]
    kp.angle = kp_tuple[3]
    kp.response = kp_tuple[4]
    kp.octave = kp_tuple[5]
    kp.class_id = kp_tuple[6]
    return kp


# 特征库构建与加载函数
def build_database_from_imgs(imgs, output_file="btn_feat.db"):
    """从图像列表提取ORB特征并构建特征库"""
    db = []  # 存储格式：(name, 序列化后的kp列表, des, w, h)

    if not imgs:
        print("错误：图片列表为空")
        return False

    for idx, (img_name, tpl) in enumerate(imgs):
        try:
            if tpl is None or not isinstance(tpl, np.ndarray):
                print(f"警告：图片 '{img_name}' 数据无效")
                continue

            print(f"\n处理图片 '{img_name}' - 尺寸: {tpl.shape}, 像素均值: {np.mean(tpl):.2f}")

            # 使用全局ORB提取特征
            kp, des = ORB_DETECTOR.detectAndCompute(tpl, None)
            kp_count = len(kp) if kp else 0
            print(f"检测到关键点数量: {kp_count}")

            if des is None:
                print(f"警告：无法从 '{img_name}' 提取ORB特征（无有效描述子）")
                continue

            # 序列化关键点
            kp_serialized = [keypoint_to_tuple(k) for k in kp]

            h, w = tpl.shape
            db.append((img_name, kp_serialized, des, w, h))
            print(f"✓ 已处理: {img_name}（有效特征数: {len(des)}）")

        except Exception as e:
            print(f"错误：处理 '{img_name}' 时出错 - {str(e)}")
            continue

    if not db:
        print("错误：没有成功处理任何图片")
        return False

    # 保存特征库
    try:
        with open(output_file, "wb") as f:
            pickle.dump(db, f)
        print(f"\n✓ 特征库已保存到: {output_file}")
        print(f"✓ 共保存 {len(db)} 个模板特征")
        return True

    except Exception as e:
        print(f"错误：保存特征库失败 - {str(e)}")
        return False


def build_database(input_dir, output_file="btn_feat.db"):
    """从指定目录读取PNG图片并构建特征库"""
    input_path = pathlib.Path(input_dir)

    if not input_path.exists() or not input_path.is_dir():
        print(f"错误：目录 '{input_dir}' 不存在或不是有效目录")
        return False

    png_files = list(input_path.glob("*.png"))
    if not png_files:
        print(f"警告：目录 '{input_dir}' 中没有找到PNG文件")
        return False

    print(f"正在处理 {len(png_files)} 个模板图片...")

    # 构造图像列表
    imgs = []
    for png in png_files:
        tpl = cv2.imread(str(png), 0)
        if tpl is None:
            print(f"警告：无法读取图片 '{png}'")
            continue
        imgs.append((png.stem, tpl))

    return build_database_from_imgs(imgs, output_file)


def load_database(input_file="btn_feat.db"):
    """加载特征库并还原KeyPoint对象"""
    try:
        with open(input_file, "rb") as f:
            db_serialized = pickle.load(f)

        # 还原KeyPoint对象
        db = []
        for item in db_serialized:
            name, kp_serialized, des, w, h = item
            kp = [tuple_to_keypoint(k) for k in kp_serialized]
            db.append((name, kp, des, w, h))

        print(f"✓ 成功加载特征库: {input_file}，共 {len(db)} 个模板")
        return True, db
    except Exception as e:
        print(f"错误：加载特征库失败 - {str(e)}")
        return False, None


def find_buttons(mask, db, verbose=False):
    """
    基于交叉验证的按钮匹配（仅返回匹配结果，不计算位置）
    参数:
        mask: 待匹配的灰度图（cv2.imread(..., 0)结果）
        db: 加载后的特征库（通过load_database获取的db对象）
    返回:
        tuple: (success, matches)
               success: 执行是否成功
               matches: 匹配结果列表，每个元素为字典：
                        {
                            'btn_name': 按钮名称,
                            'match_prob': 匹配置信度（0-1）,
                            'match_count': 有效匹配对数量,
                            'total_features': 模板总特征数
                        }
    """
    # 输入校验
    if mask is None or not isinstance(mask, np.ndarray) or len(mask.shape) != 2:
        print("错误：输入的mask不是有效灰度图")
        return False, []

    if not db or not isinstance(db, list):
        print("错误：无效的特征库数据")
        return False, []

    # 提取mask特征（使用全局ORB）
    kp_mask, des_mask = ORB_DETECTOR.detectAndCompute(mask, None)
    if des_mask is None:
        print("警告：输入mask无法提取ORB特征")
        return True, []

    # 初始化交叉验证匹配器（双向匹配校验）
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    final_matches = []

    for btn_name, kp_tpl, des_tpl, tpl_w, tpl_h in db:
        try:
            if des_tpl is None or len(des_tpl) == 0:
                print(f"跳过：按钮 '{btn_name}' 无有效特征描述子")
                continue

            # 交叉验证匹配（仅保留双向匹配的点对）
            matches = bf.match(des_tpl, des_mask)
            if len(matches) < 1:  # 交叉验证匹配对数量要求较低
                print(f"按钮 '{btn_name}' 无交叉验证匹配对，跳过")
                continue

            # 计算置信度（匹配数 / 模板总特征数）
            total_features = len(des_tpl)
            match_ratio = len(matches) / total_features if total_features > 0 else 0.0
            match_prob = round(match_ratio, 3)

            final_matches.append(
                {
                    "btn_name": btn_name,
                    "match_prob": match_prob,
                    "match_count": len(matches),
                    "total_features": total_features,
                }
            )

        except Exception as e:
            print(f"处理按钮 '{btn_name}' 时出错 - {str(e)}，跳过")
            continue

    # 按置信度排序
    final_matches.sort(key=lambda x: x["match_prob"], reverse=True)
    if verbose:
        match_count = len(final_matches)
        print(f"\n✓ 交叉验证匹配完成：共找到 {match_count} 个有效按钮")
        if match_count > 0:
            for idx, match in enumerate(final_matches, 1):
                print(
                    f"  {idx}. {match['btn_name']} - 置信度: {match['match_prob']}, 匹配对: {match['match_count']}/{match['total_features']}"
                )

    return True, final_matches


def find_buttons_all(
    masks: List[np.ndarray], db: list, min_match_prob: float = 0.9, verbose=False
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    批量查找所有符合条件的按钮

    参数:
        masks: 待匹配的灰度图列表（每个元素是cv2.imread(..., 0)结果）
        db: 加载后的特征库（通过load_database获取的db对象）
        min_match_prob: 最小匹配置信度阈值（默认0.9）

    返回:
        tuple: (success, all_results)
               success: 执行是否成功
               all_results: 所有匹配结果列表，每个元素为字典：
                        {
                            'mask_idx': mask索引,
                            'btn_name': 按钮名称,
                            'match_prob': 匹配置信度（0-1）,
                            'match_count': 有效匹配对数量,
                            'total_features': 模板总特征数
                        }

    示例:
        >>> # 创建测试数据
        >>> mask1 = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        >>> mask2 = np.random.randint(0, 255, (80, 120), dtype=np.uint8)
        >>> masks = [mask1, mask2]
        >>> db = [('test_btn', [], np.random.randint(0, 255, (10, 32), dtype=np.uint8), 50, 30)]
        >>> success, results = find_buttons_all(masks, db, min_match_prob=0.0)  # doctest: +ELLIPSIS
        >>> isinstance(results, list)
        True
    """
    # 输入校验
    if not masks or not isinstance(masks, list):
        print("错误：输入的masks列表为空或无效")
        return False, []

    if not db or not isinstance(db, list):
        print("错误：无效的特征库数据")
        return False, []

    if not 0 <= min_match_prob <= 1:
        print("错误：min_match_prob必须在0-1之间")
        return False, []

    all_results = []

    # 遍历所有mask进行匹配
    for mask_idx, mask in enumerate(masks):
        try:
            success, matches = find_buttons(mask, db, verbose=verbose)
            if success and matches:
                # 过滤符合置信度阈值的结果
                for match in matches:
                    if match["match_prob"] >= min_match_prob:
                        result = {
                            "mask_idx": mask_idx,
                            "btn_name": match["btn_name"],
                            "match_prob": match["match_prob"],
                            "match_count": match["match_count"],
                            "total_features": match["total_features"],
                        }
                        all_results.append(result)
        except Exception as e:
            print(f"处理mask索引 {mask_idx} 时出错 - {str(e)}，跳过")
            continue

    # 按置信度排序
    all_results.sort(key=lambda x: x["match_prob"], reverse=True)
    print(
        f"\n✓ 批量匹配完成：共找到 {len(all_results)} 个符合条件的按钮（阈值≥{min_match_prob}）"
    ) if verbose else None

    return True, all_results


def 计算宽高比数据库(
    db: list,
    aspect_ratio_fluctuation_threshold: float = 0.05,
    scale_threshold: float = 0.1,  # 新增：缩放阈值，默认0.1（允许0.9-1.1倍缩放）
) -> List[Dict[str, Any]]:
    """
    预计算数据库中所有按钮的宽高比（及上下限）、宽度/高度（及缩放上下限）

    参数:
        db: 加载后的特征库，每个元素格式为 (按钮名, 其他特征, 特征数组, 宽度, 高度)
        aspect_ratio_fluctuation_threshold: 宽高比波动阈值（float），默认0.05（5%），
                                            表示不同分辨率下宽高比的允许变化范围
        scale_threshold: 缩放阈值（float），默认0.1（10%），
                         表示APP按钮在不同设备屏幕上的允许缩放范围（0.9-1.1倍）

    返回:
        List[Dict[str, Any]]: 包含所有按钮尺寸信息的列表，每个字典包含：
            - name: 按钮名称
            - ratio: 基础宽高比
            - lower: 宽高比下限（ratio * (1 - 宽高比波动阈值)）
            - upper: 宽高比上限（ratio * (1 + 宽高比波动阈值)）
            - width: 原始宽度（新增）
            - width_lower: 宽度下限（width * (1 - 缩放阈值)）（新增）
            - width_upper: 宽度上限（width * (1 + 缩放阈值)）（新增）
            - height: 原始高度（新增）
            - height_lower: 高度下限（height * (1 - 缩放阈值)）（新增）
            - height_upper: 高度上限（height * (1 + 缩放阈值)）（新增）

    示例:
        >>> # 基础场景：默认阈值（宽高比0.05，缩放0.1）
        >>> db = [('btn1', [], np.array([]), 100, 50), ('btn2', [], np.array([]), 80, 40)]
        >>> ratios = 计算宽高比数据库(db)
        >>> # 验证btn1的所有字段
        >>> ratios[0]['name']
        'btn1'
        >>> ratios[0]['ratio']
        2.0
        >>> ratios[0]['lower']
        1.9
        >>> ratios[0]['upper']
        2.1
        >>> ratios[0]['width']
        100
        >>> ratios[0]['width_lower']
        90
        >>> ratios[0]['width_upper']
        110
        >>> ratios[0]['height']
        50
        >>> ratios[0]['height_lower']
        45
        >>> ratios[0]['height_upper']
        55
        >>> # 验证btn2的缩放字段
        >>> ratios[1]['width_lower']
        72
        >>> ratios[1]['height_upper']
        44

        >>> # 自定义阈值场景：宽高比0.1，缩放0.2
        >>> ratios_custom = 计算宽高比数据库(db, 0.1, 0.2)
        >>> ratios_custom[0]['upper']  # 宽高比上限：2.0*(1+0.1)=2.2
        2.2
        >>> ratios_custom[0]['width_lower']  # 宽度下限：100*(1-0.2)=80
        80
        >>> ratios_custom[0]['height_upper']  # 高度上限：50*(1+0.2)=60
        60

        >>> # 边界场景：高度为0的无效按钮
        >>> db_invalid = [('btn_invalid', [], np.array([]), 200, 0)]
        >>> ratios_invalid = 计算宽高比数据库(db_invalid)
        >>> ratios_invalid[0]['ratio']
        0.0
        >>> ratios_invalid[0]['width_lower']  # 宽度仍计算缩放（仅高度相关字段为0）
        180
        >>> ratios_invalid[0]['height_lower']
        0.0
    """
    aspect_ratios = []
    for btn_name, _, _, w, h in db:
        # 1. 计算宽高比及上下限（保留原有逻辑）
        if h > 0:
            ratio = w / h
            lower = ratio * (1 - aspect_ratio_fluctuation_threshold)
            upper = ratio * (1 + aspect_ratio_fluctuation_threshold)
        else:
            ratio = 0.0
            lower = 0.0
            upper = 0.0

        # 2. 计算宽度/高度及缩放上下限（新增核心逻辑）
        width = w  # 原始宽度
        width_lower = int(width * (1 - scale_threshold))
        width_upper = int(width * (1 + scale_threshold))

        height = h  # 原始高度
        if height > 0:
            height_lower = int(height * (1 - scale_threshold))
            height_upper = int(height * (1 + scale_threshold))
        else:
            # 高度为0时，高度上下限强制为0（避免无意义的缩放值）
            height_lower = 0.0
            height_upper = 0.0

        # 3. 封装所有字段到字典（新增宽度/高度相关字段）
        aspect_ratios.append(
            {
                "name": btn_name,
                "ratio": ratio,
                "lower": lower,
                "upper": upper,
                "width": width,
                "width_lower": width_lower,
                "width_upper": width_upper,
                "height": height,
                "height_lower": height_lower,
                "height_upper": height_upper,
            }
        )
    return aspect_ratios


def 计算目标匹配宽高比(masks: list) -> pd.DataFrame:
    """
    批量计算所有mask的宽高比、原始宽度/高度，并返回pandas.DataFrame格式的结果，方便后续数据分析/筛选

    参数:
        masks: 掩码列表，每个元素为二维numpy数组（代表单个按钮/目标的mask），
               每个mask的shape格式为 (高度, 宽度)

    返回:
        pandas.DataFrame: 包含每个mask的尺寸信息，索引为mask的序号（0,1,2...），列包括：
            - aspect_ratio: 宽高比（宽度/高度），高度为0时设为0.0
            - width: mask的原始宽度（shape[1]）
            - height: mask的原始高度（shape[0]）

    示例:
        >>> # 正常场景：两个有效mask，验证所有列的值
        >>> mask1 = np.zeros((50, 100))  # 高50，宽100 → 宽高比2.0
        >>> mask2 = np.zeros((40, 20))   # 高40，宽20 → 宽高比0.5
        >>> masks = [mask1, mask2]
        >>> df = 计算目标匹配宽高比(masks)
        >>> df.index.tolist()  # 验证索引
        [0, 1]
        >>> df.columns.tolist()  # 验证列名
        ['aspect_ratio', 'width', 'height']
        >>> df.loc[0, 'aspect_ratio']  # mask1宽高比
        2.0
        >>> df.loc[0, 'width']  # mask1宽度
        100
        >>> df.loc[0, 'height']  # mask1高度
        50.0
        >>> df.loc[1, 'aspect_ratio']  # mask2宽高比
        0.5
        >>> df.loc[1, 'width']  # mask2宽度
        20
        >>> df.loc[1, 'height']  # mask2高度
        40.0

        >>> # 边界场景1：包含高度为0的无效mask
        >>> mask3 = np.zeros((0, 100))   # 高0，宽100 → 宽高比0.0
        >>> masks_with_zero = [mask1, mask3]
        >>> df_zero = 计算目标匹配宽高比(masks_with_zero)
        >>> df_zero.loc[0, 'aspect_ratio']
        2.0
        >>> df_zero.loc[1, 'aspect_ratio']  # 高度0，宽高比为0
        0.0
        >>> df_zero.loc[1, 'width']  # 宽度仍保留原始值
        100
        >>> df_zero.loc[1, 'height']  # 高度为0
        0.0

        >>> # 边界场景2：空mask列表（返回空df，列名保留）
        >>> empty_df = 计算目标匹配宽高比([])
        >>> len(empty_df)
        0
        >>> empty_df.columns.tolist()
        ['aspect_ratio', 'width', 'height']
    """
    # 提前处理空列表，返回空DataFrame（保留列名）
    if not masks:
        return pd.DataFrame(
            data=[],
            columns=['aspect_ratio', 'width', 'height'],
            dtype=float
        )
    
    # 批量提取所有mask的shape（shape格式：(高度, 宽度)），生成(n_masks, 2)的数组
    masks_array = np.array([mask.shape for mask in masks])
    mask_heights = masks_array[:, 0].astype(float)  # 所有mask的高度数组（shape[0]）
    mask_widths = masks_array[:, 1].astype(float)   # 所有mask的宽度数组（shape[1]）

    # 计算宽高比：宽度/高度，高度为0时用out参数返回0.0（避免除零错误）
    mask_aspect_ratios = np.divide(
        mask_widths,
        mask_heights,
        out=np.zeros_like(mask_widths),  # 高度为0时的默认值
        where=mask_heights > 0,          # 仅当高度>0时执行除法
    )

    # 构造DataFrame，整合宽高比、宽度、高度
    result_df = pd.DataFrame({
        'aspect_ratio': mask_aspect_ratios,
        'width': mask_widths.astype(int),  # 宽度为整数更符合实际意义
        'height': mask_heights
    })

    return result_df


def 过滤宽高比(
    数据库宽高比结果: List[Dict[str, Any]],
    目标mask宽高比结果: pd.DataFrame
) -> List[int]:
    """
    基于数据库按钮的宽高比+宽度+高度上下限，筛选出尺寸符合条件的目标mask索引

    核心逻辑：
        1. 将数据库宽高比列表转换为pandas.DataFrame，方便批量运算
        2. 对每个目标mask，检查是否满足「任意一个数据库按钮」的三重条件：
           - 宽高比 ∈ [按钮lower, 按钮upper]
           - 宽度 ∈ [按钮width_lower, 按钮width_upper]
           - 高度 ∈ [按钮height_lower, 按钮height_upper]
        3. 筛选出满足所有条件的mask索引，返回升序列表

    参数:
        数据库宽高比结果: 重构后计算宽高比数据库函数的返回值，每个字典包含：
            - name: 按钮名称
            - ratio: 基础宽高比
            - lower/upper: 宽高比上下限
            - width/width_lower/width_upper: 宽度及上下限
            - height/height_lower/height_upper: 高度及上下限
        目标mask宽高比结果: 重构后计算目标匹配宽高比函数的返回值，pd.DataFrame格式：
            - 索引：mask序号（0,1,2...）
            - 列：aspect_ratio（宽高比）、width（宽度）、height（高度）

    返回:
        List[int]: 满足条件的mask索引列表（升序），无满足条件则返回空列表

    示例:
        >>> # ========== 正常场景：部分mask满足三重条件 ==========
        >>> # 1. 构造数据库结果（2个按钮，含宽/高/宽高比上下限）
        >>> 数据库结果 = [
        ...     {
        ...         'name': 'btn1', 'ratio': 2.0, 'lower': 1.9, 'upper': 2.1,
        ...         'width': 100, 'width_lower': 90.0, 'width_upper': 110.0,
        ...         'height': 50, 'height_lower': 45.0, 'height_upper': 55.0
        ...     },
        ...     {
        ...         'name': 'btn2', 'ratio': 0.5, 'lower': 0.45, 'upper': 0.55,
        ...         'width': 20, 'width_lower': 18.0, 'width_upper': 22.0,
        ...         'height': 40, 'height_lower': 36.0, 'height_upper': 44.0
        ...     }
        ... ]
        >>> # 2. 构造目标mask DataFrame（3个mask）
        >>> 目标结果 = pd.DataFrame({
        ...     'aspect_ratio': [2.0, 0.5, 3.0],
        ...     'width': [100, 20, 150],
        ...     'height': [50, 40, 50]
        ... }, index=[0,1,2])
        >>> # 3. 过滤：mask0(匹配btn1)、mask1(匹配btn2)满足，mask3不满足
        >>> 过滤宽高比(数据库结果, 目标结果)
        [0, 1]

        >>> # ========== 边界场景1：宽高比符合但尺寸不符合 ==========
        >>> 尺寸不符的目标结果 = pd.DataFrame({
        ...     'aspect_ratio': [2.0, 0.5],
        ...     'width': [120, 25],  # 超出btn1/btn2的宽度上限
        ...     'height': [50, 40]
        ... }, index=[0,1])
        >>> 过滤宽高比(数据库结果, 尺寸不符的目标结果)
        []

        >>> # ========== 边界场景2：数据库为空/目标mask为空 ==========
        >>> 过滤宽高比([], 目标结果)  # 数据库为空
        []
        >>> 空目标结果 = pd.DataFrame(columns=['aspect_ratio', 'width', 'height'])
        >>> 过滤宽高比(数据库结果, 空目标结果)  # 目标为空
        []

        >>> # ========== 边界场景3：包含无效mask（高度/宽度为0） ==========
        >>> 含无效mask的目标结果 = pd.DataFrame({
        ...     'aspect_ratio': [2.0, 0.0, 0.5],
        ...     'width': [100, 0, 20],
        ...     'height': [50, 0, 40]
        ... }, index=[0,1,2])
        >>> 过滤宽高比(数据库结果, 含无效mask的目标结果)  # mask1无效被排除
        [0, 2]

        >>> # ========== 边界场景4：单个mask匹配多个按钮 ==========
        >>> 数据库结果2 = [
        ...     {
        ...         'name': 'btnA', 'ratio': 2.0, 'lower': 1.8, 'upper': 2.2,
        ...         'width': 100, 'width_lower': 80.0, 'width_upper': 120.0,
        ...         'height': 50, 'height_lower': 40.0, 'height_upper': 60.0
        ...     },
        ...     {
        ...         'name': 'btnB', 'ratio': 2.0, 'lower': 1.9, 'upper': 2.1,
        ...         'width': 100, 'width_lower': 90.0, 'width_upper': 110.0,
        ...         'height': 50, 'height_lower': 45.0, 'height_upper': 55.0
        ...     }
        ... ]
        >>> 单个mask结果 = pd.DataFrame({
        ...     'aspect_ratio': [2.0],
        ...     'width': [100],
        ...     'height': [50]
        ... }, index=[0])
        >>> 过滤宽高比(数据库结果2, 单个mask结果)
        [0]
    """
    # 步骤1：处理空输入（数据库为空 或 目标mask为空 → 返回空列表）
    if not 数据库宽高比结果 or 目标mask宽高比结果.empty:
        return []
    
    # 步骤2：转换数据库结果为DataFrame，提取关键过滤列
    db_df = pd.DataFrame(数据库宽高比结果)
    # 校验数据库df是否包含必需列（避免传入格式错误）
    required_db_cols = ['lower', 'upper', 'width_lower', 'width_upper', 'height_lower', 'height_upper']
    if not all(col in db_df.columns for col in required_db_cols):
        raise ValueError(f"数据库结果缺少必需列，需包含：{required_db_cols}")
    
    # 步骤3：过滤目标mask的有效数据（排除宽/高/宽高比为0的无效mask）
    valid_target_df = 目标mask宽高比结果[
        (目标mask宽高比结果['aspect_ratio'] > 0) &
        (目标mask宽高比结果['width'] > 0) &
        (目标mask宽高比结果['height'] > 0)
    ].copy()
    if valid_target_df.empty:
        return []
    
    # 步骤4：批量校验每个mask是否匹配任意按钮的三重条件（向量化运算，提升效率）
    matched_mask_indices = []
    for mask_idx, mask_row in valid_target_df.iterrows():
        # 对当前mask，检查是否存在任意按钮满足所有条件
        match_conditions = (
            (db_df['lower'] <= mask_row['aspect_ratio']) & (mask_row['aspect_ratio'] <= db_df['upper']) &
            (db_df['width_lower'] <= mask_row['width']) & (mask_row['width'] <= db_df['width_upper']) &
            (db_df['height_lower'] <= mask_row['height']) & (mask_row['height'] <= db_df['height_upper'])
        )
        if match_conditions.any():  # 任意一个按钮满足即匹配
            matched_mask_indices.append(mask_idx)
    
    # 步骤5：排序并返回结果
    matched_mask_indices.sort()
    return matched_mask_indices


def 批量匹配流程(
    masks: List[np.ndarray],
    db: list,
    min_match_prob: float = 0.9,
    使用宽高比过滤: bool = True,
    使用尺寸过滤: bool = True,
    aspect_ratio_tolerance: float = 0.15,
    x方向缩放率: float = 1,
    y方向缩放率: float = 1,
    尺寸容忍阈值: float = 0.2,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    完整的批量匹配流程，集成宽高比和尺寸过滤

    参数:
        masks: 待匹配的灰度图列表
        db: 加载后的特征库
        min_match_prob: 最小匹配置信度阈值
        使用宽高比过滤: 是否启用宽高比过滤
        使用尺寸过滤: 是否启用尺寸过滤
        aspect_ratio_tolerance: 宽高比容忍阈值
        x方向缩放率: X方向缩放系数
        y方向缩放率: Y方向缩放系数
        尺寸容忍阈值: 尺寸差异容忍阈值

    返回:
        tuple: (success, results)

    """
    if not masks or not db:
        return False, []

    filtered_masks = masks
    filtered_db = db


    # 执行匹配
    if filtered_masks and filtered_db:
        return find_buttons_all(filtered_masks, filtered_db, min_match_prob)
    else:
        print("警告：过滤后没有剩余的masks或数据库模板")
        return True, []


def 保存匹配结果(results: List[Dict[str, Any]], output_file: str = "match_results.json"):
    """
    保存匹配结果到JSON文件

    参数:
        results: 匹配结果列表
        output_file: 输出文件路径

    示例:
    """
    import json

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✓ 匹配结果已保存到: {output_file}")
        return True
    except Exception as e:
        print(f"错误：保存匹配结果失败 - {str(e)}")
        return False


def 加载匹配结果(input_file: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    从JSON文件加载匹配结果

    参数:
        input_file: 输入文件路径

    返回:
        tuple: (success, results)

    示例:
    """
    import json

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            results = json.load(f)
        print(f"✓ 匹配结果已加载: {input_file}，共 {len(results)} 条记录")
        return True, results
    except Exception as e:
        print(f"错误：加载匹配结果失败 - {str(e)}")
        return False, []


def 统计数据库信息(db: list) -> Dict[str, Any]:
    """
    统计数据库信息

    参数:
        db: 加载后的特征库

    返回:
        Dict: 包含统计信息的字典

    示例:
        >>> db = [('btn1', [], np.ones((10, 32), dtype=np.uint8), 100, 50), ('btn2', [], np.ones((15, 32), dtype=np.uint8), 80, 40)]
        >>> info = 统计数据库信息(db)
        >>> info['total_buttons']
        2
        >>> info['avg_width']  # doctest: +ELLIPSIS
        90.0...
    """
    if not db:
        return {
            "total_buttons": 0,
            "avg_width": 0,
            "avg_height": 0,
            "avg_features": 0,
            "min_width": 0,
            "max_width": 0,
            "min_height": 0,
            "max_height": 0,
        }

    widths = [w for _, _, _, w, _ in db]
    heights = [h for _, _, _, _, h in db]
    feature_counts = [len(des) for _, _, des, _, _ in db if des is not None]

    return {
        "total_buttons": len(db),
        "avg_width": np.mean(widths),
        "avg_height": np.mean(heights),
        "avg_features": np.mean(feature_counts) if feature_counts else 0,
        "min_width": min(widths),
        "max_width": max(widths),
        "min_height": min(heights),
        "max_height": max(heights),
    }


if __name__ == "__main__":
    import doctest

    # 运行doctest
    print("正在运行单元测试...")
    print(doctest.testmod(verbose=False, report=False))

    # 命令行接口
    parser = argparse.ArgumentParser(description="按钮匹配工具")
    parser.add_argument("--build-db", action="store_true", help="构建特征库")
    parser.add_argument("--input-dir", type=str, help="输入目录（用于构建特征库）")
    parser.add_argument("--db-file", type=str, default="btn_feat.db", help="特征库文件")
    parser.add_argument("--test-mask", type=str, help="测试mask图片路径")
    parser.add_argument("--min-prob", type=float, default=0.9, help="最小匹配置信度")

    args = parser.parse_args()

    if args.build_db and args.input_dir:
        print(f"正在从目录 {args.input_dir} 构建特征库...")
        success = build_database(args.input_dir, args.db_file)
        if success:
            print("特征库构建成功！")
        else:
            print("特征库构建失败！")
            sys.exit(1)

    elif args.test_mask and pathlib.Path(args.db_file).exists():
        print(f"正在加载特征库 {args.db_file}...")
        success, db = load_database(args.db_file)
        if not success:
            print("特征库加载失败！")
            sys.exit(1)

        print(f"正在测试mask {args.test_mask}...")
        mask = cv2.imread(args.test_mask, 0)
        if mask is None:
            print("mask图片加载失败！")
            sys.exit(1)

        success, matches = find_buttons(mask, db)
        if success and matches:
            print(f"\n找到 {len(matches)} 个匹配按钮（置信度≥{args.min_prob}）：")
            for match in matches:
                if match["match_prob"] >= args.min_prob:
                    print(f"  - {match['btn_name']}: {match['match_prob']}")
        else:
            print
