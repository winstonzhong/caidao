import cv2
import numpy as np
import pandas as pd

import pathlib
from tool_split import split_shuiping, img2edges

from functools import reduce
from typing import List


def get_path(save_path):
    base_dir = pathlib.Path(__file__).parent
    return base_dir / "ut" / save_path


def 匹配上下图片单个区域(img_up, img_down, region: dict, match_threshold=0.99):
    tpl = img_up[region["top"] : region["bottom"],]
    result = cv2.matchTemplate(img_down, tpl, cv2.TM_CCOEFF_NORMED)
    # height = img_up.shape[0]

    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= match_threshold:
        return {
            "up": region.get("top"),
            "down": max_loc[1],
            # "left": max_loc[0],
            # "max_val": max_val,
            # "region": region,
            "total": img_down.shape[0] - max_loc[1] + region["top"],
        }


def 匹配上下图片(
    img_up,
    img_down,
    match_threshold=0.99,
    v_min=0,
    span_min=None,
    low=70,
    high=200,
    all_split=True,
):
    mask = img2edges(img_up, low, high)

    regions = split_shuiping(mask, all_split, v_min, span_min)
    results = []
    for region in regions:
        x = 匹配上下图片单个区域(img_up, img_down, region, match_threshold)
        if x is not None:
            results.append(x)

    return pd.DataFrame(results)


def 得到正确的拼接结果(df: pd.DataFrame) -> tuple | None:
    """
    根据指定规则从DataFrame中筛选并返回对应的up和down值

    算法步骤:
    1. 过滤掉up == down相等的记录
    2. 按total分组，计算每个组的记录数
    3. 找到记录数最大的所有total组，选择其中total值最大的组
    4. 取该组的第一条记录，返回其up和down值
    5. 若过滤后无数据，返回None

    参数:
        df: 包含up、down、total列的pandas DataFrame

    返回:
        元组(up, down)，过滤后无数据则返回None

    Doctest示例:
    >>> # 示例1: 基础场景（用户提供的样例）
    >>> df1 = pd.DataFrame({
    ...     'up': [138, 1606, 2100, 2228],
    ...     'down': [138, 374, 868, 2228],
    ...     'total': [2340, 3572, 3572, 2340]
    ... })
    >>> 得到正确的拼接结果(df1)
    (1606, 374)

    >>> # 示例2: 过滤后无数据（所有记录up==down）
    >>> df2 = pd.DataFrame({
    ...     'up': [100, 200, 300],
    ...     'down': [100, 200, 300],
    ...     'total': [500, 600, 700]
    ... })
    >>> 得到正确的拼接结果(df2) == (None, None)
    True

    >>> # 示例3: 过滤后只有1条记录
    >>> df3 = pd.DataFrame({
    ...     'up': [10, 20],
    ...     'down': [10, 30],
    ...     'total': [100, 200]
    ... })
    >>> 得到正确的拼接结果(df3)
    (20, 30)

    >>> # 示例4: 多个total组数量相同且为最大值
    >>> df4 = pd.DataFrame({
    ...     'up': [1,2,3,4,5,6],
    ...     'down': [0,0,0,0,0,0],
    ...     'total': [10,10,20,20,30,30]
    ... })
    >>> 得到正确的拼接结果(df4)  # 三个组数量都是2，取total最大的30组第一条
    (5, 0)

    >>> # 示例5: 单组多条记录
    >>> df5 = pd.DataFrame({
    ...     'up': [100, 200, 300],
    ...     'down': [99, 199, 299],
    ...     'total': [500, 500, 500]
    ... })
    >>> 得到正确的拼接结果(df5)
    (100, 99)
    """
    # 步骤1: 过滤up == down的记录
    df_filtered = df[df["up"] != df["down"]].copy()

    # 处理过滤后无数据的情况
    if df_filtered.empty:
        return None, None

    # 步骤2: 按total分组，计算每个组的记录数
    group_counts = df_filtered.groupby("total").size()

    # 步骤3: 找到最大的分组记录数
    max_count = group_counts.max()

    # 步骤4: 筛选出所有记录数等于max_count的total（候选total）
    candidate_totals = group_counts[group_counts == max_count].index

    # 步骤5: 选择候选total中最大的那个
    target_total = candidate_totals.max()

    # 步骤6: 筛选出target_total对应的组，取第一条记录
    target_row = df_filtered[df_filtered["total"] == target_total].iloc[0]

    # 步骤7: 返回up和down组成的元组
    return (target_row["up"], target_row["down"])


def 拼接上下图片(
    img_up,
    img_down,
    match_threshold=0.99,
    v_min=0,
    span_min=None,
    low=70,
    high=200,
    all_split=True,
):
    df = 匹配上下图片(
        img_up, img_down, match_threshold, v_min, span_min, low, high, all_split
    )
    # print(df)
    up, down = 得到正确的拼接结果(df)
    if up is None or down is None:
        raise Exception("没有找到匹配的图片")
    return np.concatenate((img_up[:up,], img_down[down:,]), axis=0)


def 无缝拼接所有图片(
    img_list: List[np.ndarray],
    match_threshold=0.99,
    v_min=0,
    span_min=None,
    low=70,
    high=200,
    all_split=True,
) -> np.ndarray:
    """
    使用reduce方法依次拼接从下到上排列的图片序列，生成完整无缝拼接图

    参数:
        img_list: cv2格式的图片序列（numpy.ndarray），index 0 = 最底部图片，index 1 = 上一屏，index 2 = 上两屏...
        match_threshold: 匹配阈值，透传给拼接上下图片函数
        v_min: 垂直最小匹配范围，透传
        span_min: 最小跨度，透传
        low/high: 边缘检测阈值，透传
        all_split: 是否全部分割，透传

    返回:
        完整拼接后的cv2格式图片（numpy.ndarray）

    异常:
        - 空图片列表：抛出ValueError
        - 拼接过程中匹配失败：抛出Exception（继承自拼接上下图片的异常）

    示例逻辑:
        img_list = [img0(最底), img1(中), img2(最上)]
        拼接流程：img1(up) + img0(down) → temp → img2(up) + temp(down) → 最终结果
    """
    # 边界检查1：空列表
    if not img_list:
        raise ValueError("图片列表不能为空")

    # 边界检查2：只有1张图片，直接返回拷贝（避免原数组引用问题）
    if len(img_list) == 1:
        return img_list[0].copy()

    # 核心逻辑：使用reduce累积拼接
    # reduce的工作原理：
    # - 初始值：img_list[0]（最底部图片）
    # - 累积函数：将「下一张上方图片(curr)」作为img_up，「已拼接的结果(acc)」作为img_down，调用拼接上下图片
    def 累积拼接函数(已拼接图片: np.ndarray, 待拼接上方图片: np.ndarray) -> np.ndarray:
        try:
            # 调用拼接上下图片：参数顺序是(img_up, img_down)
            return 拼接上下图片(
                待拼接上方图片,
                已拼接图片,
                match_threshold=match_threshold,
                v_min=v_min,
                span_min=span_min,
                low=low,
                high=high,
                all_split=all_split,
            )
        except Exception as e:
            # 增强异常信息，定位拼接失败的环节
            raise Exception(
                f"拼接图片时失败（待拼接上方图片与已拼接图片匹配失败）：{str(e)}"
            ) from e

    # 执行reduce：从img_list[0]开始，依次拼接img_list[1:]的所有上方图片
    最终拼接图 = reduce(累积拼接函数, img_list[1:], img_list[0])

    return 最终拼接图


# 执行单元测试
if __name__ == "__main__":
    import doctest

    print(doctest.testmod())
