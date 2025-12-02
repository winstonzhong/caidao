import pandas as pd

def 寻找上下df中相同的文本记录并设置(df上, df下):
    """
    在df下中查找满足条件的记录，并将其时间、唯一值设置为df上中匹配的第一行

    匹配条件：
    1. df下.类型 == "文本"
    2. df下.探头 == "True" (CSV中存储为字符串)
    3. df下.上下文 在 df上.上下文 中存在相等匹配且不为空
    4. df下.时间 为NaN 或者 df下.时间 == df上.时间且不为空

    参数:
        df上 (pd.DataFrame): 上游数据
        df下 (pd.DataFrame): 下游数据，会被修改

    返回:
        pd.DataFrame: 修改后的df下

    示例:
    >>> # 准备测试数据
    >>> import numpy as np
    >>> data上 = pd.DataFrame({
    ...     '上下文': ['文本A', '文本B', '文本A'],
    ...     '时间': ['2025-01-01 10:00:00', '2025-01-01 11:00:00', '2025-01-01 12:00:00'],
    ...     '类型': ['文本', '文本', '文本'],
    ...     '探头': [False, False, False],
    ...     '唯一值': ['uniq1', 'uniq2', 'uniq3']
    ... })
    >>>
    >>> data下 = pd.DataFrame({
    ...     '上下文': ['文本A', '文本C', '文本A', '文本A', '文本A'],
    ...     '时间': [np.nan, '2025-01-01 11:00:00', '2025-01-01 10:00:00', '2025-01-01 12:00:00', '2025-01-01 12:00:01'],
    ...     '探头': [True, True, True, True, True],
    ...     '类型': ['文本', '文本', '文本', '文本', '文本'],
    ...     '唯一值': ['old1', 'old2', 'old3', 'old4', 'old5']
    ... })
    >>>
    >>> result = 寻找上下df中相同的文本记录并设置(data上, data下)
    >>>
    >>> # 第0行：上下文匹配文本A，时间为NaN，应更新为df上第一行文本A的数据
    >>> result.loc[0, '时间']
    '2025-01-01 10:00:00'
    >>> result.loc[0, '唯一值']
    'uniq1'
    >>>
    >>> # 第1行：上下文文本C在df上中不存在，不应更新
    >>> result.loc[1, '时间']
    '2025-01-01 11:00:00'
    >>> result.loc[1, '唯一值']
    'old2'
    >>>
    >>> # 第2行：上下文文本A匹配，时间10:00:00也匹配，应更新
    >>> result.loc[2, '时间']
    '2025-01-01 10:00:00'
    >>> result.loc[2, '唯一值']
    'uniq1'
    >>>
    >>> # 第3行：上下文文本A匹配，时间12:00:00匹配df上第三行，应更新
    >>> result.loc[3, '时间']
    '2025-01-01 12:00:00'
    >>> result.loc[3, '唯一值']
    'uniq3'
    >>> # 第3行：上下文文本A匹配，时间12:00:01 无匹配，不应更新
    >>> result.loc[4, '时间']
    '2025-01-01 12:00:01'
    >>> result.loc[4, '唯一值']
    'old5'
    >>> result = 寻找上下df中相同的文本记录并设置(df_up, df_down.copy())
    >>> result.iloc[0].时间 == df_up.iloc[1].时间
    True
    >>> df_down.iloc[0].时间
    nan
    >>> result.iloc[0].唯一值 == df_up.iloc[1].唯一值
    True
    >>> df_down.iloc[0].唯一值 != result.iloc[0].唯一值
    True
    """
    # 创建df上中上下文的映射，只保留类型为文本的行
    df上_文本 = df上[df上["类型"] == "文本"][["上下文", "时间", "唯一值"]].dropna(
        subset=["上下文"]
    )

    # 建立上下文到(时间, 唯一值)列表的映射
    上文映射 = (
        df上_文本.groupby("上下文")
        .apply(lambda x: x[["时间", "唯一值"]].to_dict("records"))
        .to_dict()
    )

    # 获取df下中需要处理的行索引
    mask = (df下["类型"] == "文本") & (df下["探头"])
    待处理索引 = df下[mask].index

    # 遍历处理
    for idx in 待处理索引:
        row = df下.loc[idx]
        上下文值 = row["上下文"]

        if pd.isna(上下文值) or 上下文值 == "":
            continue

        if 上下文值 not in 上文映射:
            continue

        # 查找匹配的时间
        for 上数据 in 上文映射[上下文值]:
            # 时间条件：df下时间为NaN 或 时间相等
            if pd.isna(row["时间"]) or row["时间"] == 上数据["时间"]:
                # 更新df下
                df下.at[idx, "时间"] = 上数据["时间"]
                df下.at[idx, "唯一值"] = 上数据["唯一值"]
                break

    return df下


if __name__ == "__main__":
    import doctest
    from pathlib import Path
    UT_BASE_DIR = Path(__file__).resolve().parent / 'ut'
    df_down = pd.read_csv(UT_BASE_DIR / "down_1.csv")
    df_up = pd.read_csv(UT_BASE_DIR / "up_1.csv")
    # print(df_up[["上下文", "时间", "类型"]])
    # print(df_down[["上下文", "时间", "类型"]])

    print(doctest.testmod(verbose=False, report=False))

