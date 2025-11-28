import pandas as pd


def 合并上下df(df上: pd.DataFrame, df下: pd.DataFrame) -> pd.DataFrame:
    """
    合并两个DataFrame，处理重叠部分并去重。

    通过将['原始时间', '唯一值', '图片key']三列合并为"新唯一值"字符串来计算重叠区域。
    重叠部分定义为：df上的最后n行与df下的前n行在新唯一值上完全匹配。
    如果找到有效重叠，则合并时去重；否则直接拼接。

    参数:
        df上: 较早的数据，pandas.DataFrame
        df下: 较晚的数据，pandas.DataFrame

    返回:
        合并后的DataFrame，重叠部分只保留一次

    示例:
    >>> # 基本重叠情况 - 完美匹配
    >>> df1 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:56:00', '2025-11-10 23:00:00'],
    ...     '唯一值': ['a', 'b'],
    ...     '图片key': ['img1', 'img2'],
    ...     '其他列': [100, 200]
    ... })
    >>> df2 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 23:00:00', '2025-11-10 23:05:00'],
    ...     '唯一值': ['b', 'c'],
    ...     '图片key': ['img2', 'img3'],
    ...     '其他列': [200, 300]
    ... })
    >>> result = 合并上下df(df1, df2)
    >>> len(result)
    3
    >>> list(result['唯一值'])
    ['a', 'b', 'c']
    >>> list(result['其他列'])
    [100, 200, 300]
    >>> '新唯一值' in result.columns
    False

    >>> # 无重叠情况
    >>> df3 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00'],
    ...     '唯一值': ['x'],
    ...     '图片key': ['imgx'],
    ...     '数值列': [1.5]
    ... })
    >>> df4 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 23:00:00'],
    ...     '唯一值': ['y'],
    ...     '图片key': ['imgy'],
    ...     '数值列': [2.5]
    ... })
    >>> result = 合并上下df(df3, df4)
    >>> len(result)
    2
    >>> list(result['唯一值'])
    ['x', 'y']
    >>> '新唯一值' in result.columns
    False

    >>> # 重叠部分不匹配 - 图片key不同
    >>> df5 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00', '2025-11-10 23:00:00'],
    ...     '唯一值': ['a', 'b'],
    ...     '图片key': ['img1', 'img2'],
    ...     '标记': [True, False]
    ... })
    >>> df6 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 23:00:00', '2025-11-10 23:05:00'],
    ...     '唯一值': ['b', 'c'],
    ...     '图片key': ['img_different', 'img3'],
    ...     '标记': [False, True]
    ... })
    >>> result = 合并上下df(df5, df6)
    >>> len(result)
    4
    >>> list(result['图片key'])
    ['img1', 'img2', 'img_different', 'img3']
    >>> list(result['标记'])
    [True, False, False, True]

    >>> # 包含nan值的情况
    >>> df7 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00', np.nan],
    ...     '唯一值': ['a', 'b'],
    ...     '图片key': ['img1', np.nan],
    ...     '额外信息': ['ok', 'missing']
    ... })
    >>> df8 = pd.DataFrame({
    ...     '原始时间': [np.nan, '2025-11-10 23:00:00'],
    ...     '唯一值': ['b', 'c'],
    ...     '图片key': [np.nan, 'img3'],
    ...     '额外信息': ['missing', 'new']
    ... })
    >>> result = 合并上下df(df7, df8)
    >>> len(result)
    3
    >>> list(result['唯一值'])
    ['a', 'b', 'c']
    >>> list(result['额外信息'])
    ['ok', 'missing', 'new']

    >>> # 空DataFrame情况
    >>> df9 = pd.DataFrame(columns=['原始时间', '唯一值', '图片key', '数据'])
    >>> df10 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 23:00:00'],
    ...     '唯一值': ['a'],
    ...     '图片key': ['img1'],
    ...     '数据': [42]
    ... })
    >>> result = 合并上下df(df9, df10)
    >>> len(result)
    1
    >>> list(result['唯一值'])
    ['a']

    >>> # 完全重叠情况
    >>> df11 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00', '2025-11-10 23:00:00'],
    ...     '唯一值': ['a', 'b'],
    ...     '图片key': ['img1', 'img2'],
    ...     '值': [10, 20]
    ... })
    >>> df12 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00', '2025-11-10 23:00:00'],
    ...     '唯一值': ['a', 'b'],
    ...     '图片key': ['img1', 'img2'],
    ...     '值': [10, 20]
    ... })
    >>> result = 合并上下df(df11, df12)
    >>> len(result)
    2
    >>> list(result['唯一值'])
    ['a', 'b']
    >>> list(result['值'])
    [10, 20]

    >>> # 包含额外列的情况
    >>> df13 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00', '2025-11-10 23:00:00'],
    ...     '唯一值': ['a', 'b'],
    ...     '图片key': ['img1', 'img2'],
    ...     '列1': [1, 2],
    ...     '列2': ['x', 'y']
    ... })
    >>> df14 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 23:00:00', '2025-11-11 00:00:00'],
    ...     '唯一值': ['b', 'c'],
    ...     '图片key': ['img2', 'img3'],
    ...     '列1': [2, 3],
    ...     '列2': ['y', 'z']
    ... })
    >>> result = 合并上下df(df13, df14)
    >>> len(result)
    3
    >>> list(result['唯一值'])
    ['a', 'b', 'c']
    >>> list(result['列1'])
    [1, 2, 3]
    >>> list(result['列2'])
    ['x', 'y', 'z']

    >>> # 重叠区域大小为1的情况
    >>> df15 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00', '2025-11-10 23:00:00'],
    ...     '唯一值': ['a', 'b'],
    ...     '图片key': ['img1', 'img2'],
    ...     '标签': ['old1', 'old2']
    ... })
    >>> df16 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 23:00:00', '2025-11-11 00:00:00'],
    ...     '唯一值': ['b', 'c'],
    ...     '图片key': ['img2', 'img3'],
    ...     '标签': ['old2', 'new']
    ... })
    >>> result = 合并上下df(df15, df16)
    >>> len(result)
    3
    >>> list(result['标签'])
    ['old1', 'old2', 'new']

    >>> # DataFrame中已存在'新唯一值'列的情况
    >>> df17 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00'],
    ...     '唯一值': ['a'],
    ...     '图片key': ['img1'],
    ...     '新唯一值': ['existing_key']
    ... })
    >>> df18 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00', '2025-11-10 23:00:00'],
    ...     '唯一值': ['a', 'b'],
    ...     '图片key': ['img1', 'img2'],
    ...     '新唯一值': ['should_be_overwritten', 'new_key']
    ... })
    >>> result = 合并上下df(df17, df18)
    >>> len(result)
    2
    >>> '新唯一值' in result.columns
    False
    >>> list(result['唯一值'])
    ['a', 'b']

    >>> # 测试新唯一值的格式: nan值应转换为'nan'
    >>> df19 = pd.DataFrame({
    ...     '原始时间': [np.nan],
    ...     '唯一值': ['test'],
    ...     '图片key': [np.nan],
    ...     '数据': [1]
    ... })
    >>> df20 = pd.DataFrame({
    ...     '原始时间': [np.nan, '2025-11-10 23:00:00'],
    ...     '唯一值': ['test', 'other'],
    ...     '图片key': [np.nan, 'img'],
    ...     '数据': [1, 2]
    ... })
    >>> result = 合并上下df(df19, df20)
    >>> len(result)
    2
    >>> list(result['唯一值'])
    ['test', 'other']
    >>> list(result['数据'])
    [1, 2]

    >>> # 重叠部分三列相同但其他列不同的情况
    >>> df21 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 23:00:00'],
    ...     '唯一值': ['b'],
    ...     '图片key': ['img2'],
    ...     '附加数据': [100]
    ... })
    >>> df22 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 23:00:00', '2025-11-10 23:05:00'],
    ...     '唯一值': ['b', 'c'],
    ...     '图片key': ['img2', 'img3'],
    ...     '附加数据': [200, 300]
    ... })
    >>> result = 合并上下df(df21, df22)
    >>> len(result)
    2
    >>> list(result['附加数据'])  # 应保留df上的值(100)
    [100, 300]


    >>> # 情况1: df上有3行, df下有3行, 有1行数据相同但不重叠（相同行不在边界）
    >>> df23 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00', '2025-11-10 23:00:00', '2025-11-11 00:00:00'],
    ...     '唯一值': ['a', 'b', 'c'],
    ...     '图片key': ['img1', 'img2', 'img3'],
    ...     '标记': [1, 2, 3]
    ... })
    >>> df24 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 23:00:00', '2025-11-11 01:00:00', '2025-11-11 02:00:00'],
    ...     '唯一值': ['b', 'd', 'e'],
    ...     '图片key': ['img2', 'img4', 'img5'],
    ...     '标记': [2, 4, 5]
    ... })
    >>> result = 合并上下df(df23, df24)
    >>> len(result)
    6
    >>> list(result['标记'])
    [1, 2, 3, 2, 4, 5]

    >>> # 情况2: df上有3行, df下有3行, 有2行数据相同但不重叠
    >>> df25 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00', '2025-11-10 23:00:00', '2025-11-11 00:00:00'],
    ...     '唯一值': ['a', 'b', 'c'],
    ...     '图片key': ['img1', 'img2', 'img3'],
    ...     '序号': [10, 20, 30]
    ... })
    >>> df26 = pd.DataFrame({
    ...     '原始时间': ['2025-11-10 22:00:00', '2025-11-10 23:00:00', '2025-11-11 02:00:00'],
    ...     '唯一值': ['a', 'b', 'd'],
    ...     '图片key': ['img1', 'img2', 'img4'],
    ...     '序号': [10, 20, 40]
    ... })
    >>> result = 合并上下df(df25, df26)
    >>> len(result)
    6
    >>> list(result['序号'])
    [10, 20, 30, 10, 20, 40]
    """
    # 复制输入DataFrame以避免修改原始数据
    df上 = df上.copy()
    df下 = df下.copy()

    # 检查必需列是否存在
    required_cols = ["原始时间", "唯一值", "图片key"]
    for col in required_cols:
        if col not in df上.columns or col not in df下.columns:
            raise ValueError(f"输入DataFrame必须包含列: {required_cols}")

    # 如果任一DataFrame为空，直接返回另一个
    if df上.empty:
        return df下.reset_index(drop=True)
    if df下.empty:
        return df上.reset_index(drop=True)

    # 创建辅助列：新唯一值，将三列合并为一个字符串
    # 将nan转换为字符串'nan'，使用'-'作为连接符
    def create_unique_key(df):
        # 复制这三列以避免修改原数据
        temp_df = df[required_cols].copy()
        # 将nan值转换为'nan'字符串
        temp_df = temp_df.fillna("nan")
        # 合并为三列
        return (
            temp_df["原始时间"].astype(str)
            + "-"
            + temp_df["唯一值"].astype(str)
            + "-"
            + temp_df["图片key"].astype(str)
        )

    # 添加辅助列（如果已存在则先删除）
    for df in [df上, df下]:
        if "新唯一值" in df.columns:
            df.drop(columns=["新唯一值"], inplace=True)

    df上["新唯一值"] = create_unique_key(df上)
    df下["新唯一值"] = create_unique_key(df下)

    # 确定最大可能的重叠行数
    max_overlap = min(len(df上), len(df下))
    overlap_size = 0

    # 从大到小尝试找到有效的重叠区域
    # 优先匹配最大的重叠部分
    for n in range(max_overlap, 0, -1):
        # 获取df上的最后n行和df下的前n行的新唯一值
        upper_tail_keys = df上["新唯一值"].tail(n).reset_index(drop=True)
        lower_head_keys = df下["新唯一值"].head(n).reset_index(drop=True)

        # 检查这两部分是否完全相同
        if upper_tail_keys.equals(lower_head_keys):
            overlap_size = n
            break

    # 删除辅助列
    df上 = df上.drop(columns=["新唯一值"])
    df下 = df下.drop(columns=["新唯一值"])

    # 根据找到的重叠大小合并DataFrame
    if overlap_size > 0:
        # 去重合并：df上的全部 + df下的非重叠部分
        result = pd.concat([df上, df下.iloc[overlap_size:]], ignore_index=True)
    else:
        # 无有效重叠，直接拼接
        result = pd.concat([df上, df下], ignore_index=True)

    return result


if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
