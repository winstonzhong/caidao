import pandas as pd


def process_df(df: pd.DataFrame, keys: list) -> pd.DataFrame:
    """
    根据给定逻辑处理DataFrame的"已处理"列。

    处理逻辑：
    1. 如果"唯一值"在keys中且"时间"不为nan，则"已处理"为True
    2. 如果"唯一值"在keys中且"时间"为nan，且上一行或下一行"已处理"为True，则"已处理"为True
    3. 其他情况，"已处理"为False

    参数:
        df: 包含"已处理"、"时间"、"唯一值"列的DataFrame
        keys: 可能与df["唯一值"]匹配的字符串列表

    返回:
        处理后的DataFrame

    >>> # 测试情况1：唯一值在keys中，时间不为nan
    >>> df1 = pd.DataFrame({
    ...     "已处理": [False, False],
    ...     "时间": ["2023-01-01", "2023-01-02"],
    ...     "唯一值": ["A", "B"]
    ... })
    >>> keys1 = ["A", "C"]
    >>> result1 = process_df(df1, keys1)
    >>> result1["已处理"].tolist()
    [True, False]

    >>> # 测试情况2：唯一值在keys中，时间为nan
    >>> df2 = pd.DataFrame({
    ...     "已处理": [False, False, False],
    ...     "时间": ["2023-01-01", np.nan, "2023-01-03"],
    ...     "唯一值": ["A", "C", "B"]
    ... })
    >>> keys2 = ["A"]
    >>> result2 = process_df(df2, keys2)
    >>> result2["已处理"].tolist()
    [True, True, False]

    >>> # 测试情况3：唯一值在keys中，时间为nan，上一行已处理=True
    >>> df3 = pd.DataFrame({
    ...     "已处理": [False, False, False],
    ...     "时间": ["2023-01-01", np.nan, "2023-01-03"],
    ...     "唯一值": ["A", "A", "A"]
    ... })
    >>> keys3 = ["A"]
    >>> result3 = process_df(df3, keys3)
    >>> result3["已处理"].tolist()
    [True, True, True]

    >>> # 测试情况4：唯一值在keys中，时间为nan，下一行已处理=True
    >>> df4 = pd.DataFrame({
    ...     "已处理": [False, False, False],
    ...     "时间": [np.nan, "2023-01-02", np.nan],
    ...     "唯一值": ["A", "A", "A"]
    ... })
    >>> keys4 = ["A"]
    >>> result4 = process_df(df4, keys4)
    >>> result4["已处理"].tolist()
    [True, True, True]

    >>> # 测试情况5：唯一值不在keys中
    >>> df5 = pd.DataFrame({
    ...     "已处理": [False, False],
    ...     "时间": ["2023-01-01", np.nan],
    ...     "唯一值": ["B", "B"]
    ... })
    >>> keys5 = ["A"]
    >>> result5 = process_df(df5, keys5)
    >>> result5["已处理"].tolist()
    [False, False]

    >>> # 测试边界情况：第一行（没有上一行）
    >>> df6 = pd.DataFrame({
    ...     "已处理": [False, False, False],
    ...     "时间": [np.nan, "2023-01-02", "2023-01-03"],
    ...     "唯一值": ["A", "A", "B"]
    ... })
    >>> keys6 = ["A"]
    >>> result6 = process_df(df6, keys6)
    >>> result6["已处理"].tolist()
    [True, True, False]

    >>> # 测试边界情况：最后一行（没有下一行）
    >>> df7 = pd.DataFrame({
    ...     "已处理": [False, False, False],
    ...     "时间": ["2023-01-01", "2023-01-02", np.nan],
    ...     "唯一值": ["A", "A", "A"]
    ... })
    >>> keys7 = ["A"]
    >>> result7 = process_df(df7, keys7)
    >>> result7["已处理"].tolist()
    [True, True, True]

    >>> # 测试连续多行的情况
    >>> df8 = pd.DataFrame({
    ...     "已处理": [False]*5,
    ...     "时间": ["2023-01-01", np.nan, np.nan, np.nan, "2023-01-05"],
    ...     "唯一值": ["A", "A", "B", "A", "A"]
    ... })
    >>> keys8 = ["A"]
    >>> result8 = process_df(df8, keys8)
    >>> result8["已处理"].tolist()
    [True, True, False, True, True]

    >>> # 测试混合情况
    >>> df9 = pd.DataFrame({
    ...     "已处理": [False]*6,
    ...     "时间": [np.nan, "2023-01-02", np.nan, np.nan, "2023-01-05", np.nan],
    ...     "唯一值": ["A", "A", "B", "A", "C", "C"]
    ... })
    >>> keys9 = ["A", "C"]
    >>> result9 = process_df(df9, keys9)
    >>> result9["已处理"].tolist()
    [True, True, False, True, True, True]

    >>> # 测试空DataFrame
    >>> df10 = pd.DataFrame(columns=["已处理", "时间", "唯一值"])
    >>> keys10 = ["A"]
    >>> result10 = process_df(df10, keys10)
    >>> result10.empty
    True

    >>> # 测试只有一行的情况
    >>> df11 = pd.DataFrame({
    ...     "已处理": [False],
    ...     "时间": [np.nan],
    ...     "唯一值": ["A"]
    ... })
    >>> keys11 = ["A"]
    >>> result11 = process_df(df11, keys11)
    >>> result11["已处理"].tolist()
    [False]

    >>> # 测试多轮传递的情况（中间隔多行）
    >>> df12 = pd.DataFrame({
    ...     "已处理": [False]*7,
    ...     "时间": ["2023-01-01", np.nan, np.nan, np.nan, np.nan, np.nan, "2023-01-07"],
    ...     "唯一值": ["A", "A", "A", "A", "A", "A", "A"]
    ... })
    >>> keys12 = ["A"]
    >>> result12 = process_df(df12, keys12)
    >>> result12["已处理"].tolist()
    [True, True, True, True, True, True, True]
    """
    # 创建一个副本，避免修改原始DataFrame
    result_df = df.copy()

    # 预先计算唯一值在keys中的掩码，提高效率
    in_keys_mask = result_df["唯一值"].isin(keys)

    # 首先处理情况1：唯一值在keys中，且时间不为nan
    mask1 = in_keys_mask & ~result_df["时间"].isna()
    result_df.loc[mask1, "已处理"] = True

    # 处理情况2：唯一值在keys中，时间为nan，且上下行有True
    # 使用循环处理依赖关系，直到没有更多变化
    changed = True
    while changed:
        changed = False
        for i in range(len(result_df)):
            # 如果已经是True，跳过
            if result_df["已处理"].iloc[i]:
                continue

            # 检查是否"唯一值"在keys中且"时间"为nan
            if in_keys_mask.iloc[i] and pd.isna(result_df["时间"].iloc[i]):
                # 检查上一行或下一行是否为True
                has_true_neighbor = False
                if i > 0 and result_df["已处理"].iloc[i - 1]:
                    has_true_neighbor = True
                if i < len(result_df) - 1 and result_df["已处理"].iloc[i + 1]:
                    has_true_neighbor = True

                if has_true_neighbor:
                    result_df.loc[result_df.index[i], "已处理"] = True
                    changed = True

    # 对于不满足情况1和情况2的，设置为False
    result_df.loc[~result_df["已处理"], "已处理"] = False

    return result_df


if __name__ == "__main__":
    import doctest
    import numpy as np
    print(doctest.testmod(verbose=False, report=False))
