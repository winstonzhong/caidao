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
    >>> import numpy as np
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


# def 得到需要处理的图片df(df_本页, df_历史):
#     tmp = df_本页[(df_本页.类型 == "图片") & (~df_本页.已处理)]
#     # tmp = df_本页[(df_本页.类型 == "图片") & (~df_本页.已处理) & ((df_本页.容器key != df_历史.容器key) | (df_本页.唯一值 == df_历史.唯一值))]
#     # 容器key
#     print(tmp)
#     print(tmp.iloc[0])
#     print(df_历史)


def 得到需要处理的图片df(df_本页, df_历史):
    """
    筛选本页未处理的图片记录，并剔除历史数据中已存在（容器key+唯一值组合匹配）的记录。

    参数:
        df_本页 (pd.DataFrame): 包含本页数据的DataFrame，需包含字段：类型、已处理、容器key、唯一值
        df_历史 (pd.DataFrame): 包含历史数据的DataFrame，需包含字段：容器key、唯一值

    返回:
        pd.DataFrame: 筛选后的待处理图片记录

    示例:
    >>> # 测试场景1：常规场景（部分记录在历史中）
    >>> df_本页1 = pd.DataFrame({
    ...     '类型': ['图片', '文字', '图片', '图片'],
    ...     '已处理': [False, False, False, True],
    ...     '容器key': ['key1', 'key2', 'key3', 'key1'],
    ...     '唯一值': ['val1', 'val2', 'val3', 'val1']
    ... }, index=[0, 1, 2, 3])  # 显式指定索引，保证输出一致
    >>> df_历史1 = pd.DataFrame({
    ...     '容器key': ['key1', 'key4'],
    ...     '唯一值': ['val1', 'val4']
    ... }, index=[0, 1])
    >>> result1 = 得到需要处理的图片df(df_本页1, df_历史1)
    >>> result1.index.tolist()
    [2]

    >>> # 测试场景2：历史数据为空，返回所有未处理图片
    >>> df_本页2 = pd.DataFrame({
    ...     '类型': ['图片', '图片'],
    ...     '已处理': [False, False],
    ...     '容器key': ['key5', 'key6'],
    ...     '唯一值': ['val5', 'val6']
    ... }, index=[0, 1])
    >>> df_历史2 = pd.DataFrame(columns=['容器key', '唯一值'])  # 空历史数据
    >>> result2 = 得到需要处理的图片df(df_本页2, df_历史2)
    >>> result2.index.tolist()
    [0, 1]

    >>> # 测试场景3：本页无未处理图片，返回空DataFrame
    >>> df_本页3 = pd.DataFrame({
    ...     '类型': ['图片', '文字'],
    ...     '已处理': [True, False],
    ...     '容器key': ['key7', 'key8'],
    ...     '唯一值': ['val7', 'val8']
    ... }, index=[0, 1])
    >>> df_历史3 = pd.DataFrame({
    ...     '容器key': ['key7'],
    ...     '唯一值': ['val7']
    ... }, index=[0])
    >>> result3 = 得到需要处理的图片df(df_本页3, df_历史3)
    >>> print(result3.empty)
    True

    >>> # 测试场景4：所有未处理图片都在历史中，返回空DataFrame
    >>> df_本页4 = pd.DataFrame({
    ...     '类型': ['图片', '图片'],
    ...     '已处理': [False, False],
    ...     '容器key': ['key9', 'key10'],
    ...     '唯一值': ['val9', 'val10']
    ... }, index=[0, 1])
    >>> df_历史4 = pd.DataFrame({
    ...     '容器key': ['key9', 'key10'],
    ...     '唯一值': ['val9', 'val10']
    ... }, index=[0, 1])
    >>> result4 = 得到需要处理的图片df(df_本页4, df_历史4)
    >>> print(result4.empty)
    True
    >>> result4 = 得到需要处理的图片df(df1, df2)
    >>> result4.iloc[0].上下文
    '钟北川:[分享了一张图片<405x226>]'
    """
    # 1. 筛选本页中类型为图片且未处理的记录
    tmp = df_本页[(df_本页.类型 == "图片") & (~df_本页.已处理)]

    # 2. 处理边界情况：如果历史数据为空，直接返回筛选后的结果
    if df_历史.empty:
        return tmp

    # 3. 提取历史数据中"容器key"和"唯一值"的组合（元组形式），转为集合提升查询效率
    历史_容器唯一值组合 = set(zip(df_历史["容器key"], df_历史["唯一值"]))

    # 4. 过滤tmp：保留"容器key+唯一值"不在历史组合中的记录
    需要处理的df = tmp[
        ~tmp.apply(
            lambda row: (row["容器key"], row["唯一值"]) in 历史_容器唯一值组合, axis=1
        )
    ]

    return 需要处理的df


def 截断已存储的历史部分(df: pd.DataFrame, 最后历史时间: str = None) -> pd.DataFrame:
    """
    截断已存储的历史部分 的 Docstring

    :param df: 说明
    :type df: pd.DataFrame
    :param 最后历史时间: 说明
    :type 最后历史时间: str
    :return: 说明
    :rtype: DataFrame

    >>> data = {
    ...     '原始时间': ['2025-01-01 10:00:00', '2025-01-01 11:00:00', '2025-01-01 12:00:00', '2025-01-01 13:00:00'],
    ...     '数值': [1, 2, 3, 4]
    ... }
    >>> df = pd.DataFrame(data)
    >>> # 测试1: 传入中间时间，截断后返回后续行
    >>> 截断后的_df = 截断已存储的历史部分(df, '2025-01-01 11:00:00')
    >>> len(截断后的_df)
    2
    """
    if 最后历史时间 is None:
        return df

    符合条件的行 = df["原始时间"] <= 最后历史时间

    # 确定截断位置
    if 符合条件的行.any():
        # 取最后一个符合条件的行索引，截断位置为该索引+1
        最后符合条件索引 = df[符合条件的行].index[-1]
        截断位置 = 最后符合条件索引 + 1
    else:
        # 无符合条件的行，截断位置为0（返回全部数据）
        截断位置 = 0

    # 执行截断，并将时间列转回字符串格式（保持原数据格式）
    结果_df = df.iloc[截断位置:].copy()

    return 结果_df


def 设置已处理(df: pd.DataFrame, 最后历史时间: str = None) -> pd.DataFrame:
    """
    根据最后历史时间更新DataFrame的'已处理'列值。

    当最后历史时间不为None时，筛选出'已处理'为False的行，判断其'原始时间'是否≤传入的时间字符串，
    满足条件则将该行'已处理'设为True；不满足/最后历史时间为None时保持原有值。
    函数返回处理后的DataFrame副本，避免修改原数据。

    参数:
        df: 必须包含'已处理'(bool类型)和'原始时间'(字符串/时间类型)列的DataFrame
        最后历史时间: 格式为"YYYY-MM-DD HH:MM:SS"的时间字符串，默认为None

    返回:
        处理后的DataFrame副本

    示例:
    >>> import pandas as pd
    >>> # 构造基础测试数据
    >>> data = {
    ...     '原始时间': ['2025-12-16 22:00:00', '2025-12-16 22:02:00', '2025-12-16 22:05:00', None],
    ...     '已处理': [False, False, False, False]
    ... }
    >>> df = pd.DataFrame(data)
    >>> # 测试1: 正常场景（部分行满足条件）
    >>> df_result1 = 设置已处理(df, "2025-12-16 22:02:00")
    >>> df_result1['已处理'].tolist()
    [True, True, False, False]
    >>> # 测试2: 最后历史时间为None（不处理）
    >>> df_result2 = 设置已处理(df, None)
    >>> df_result2['已处理'].tolist()
    [False, False, False, False]
    >>> # 测试3: 原始时间等于最后历史时间
    >>> df3 = pd.DataFrame({'原始时间': ['2025-12-16 22:02:00'], '已处理': [False]})
    >>> df_result3 = 设置已处理(df3, "2025-12-16 22:02:00")
    >>> df_result3['已处理'].iloc[0]
    True
    >>> # 测试4: 原始时间大于最后历史时间
    >>> df4 = pd.DataFrame({'原始时间': ['2025-12-16 22:03:00'], '已处理': [False]})
    >>> df_result4 = 设置已处理(df4, "2025-12-16 22:02:00")
    >>> df_result4['已处理'].iloc[0]
    False
    >>> # 测试5: 部分行已处理为True（不修改）
    >>> df5 = pd.DataFrame({
    ...     '原始时间': ['2025-12-16 22:00:00', '2025-12-16 22:01:00'],
    ...     '已处理': [True, False]
    ... })
    >>> df_result5 = 设置已处理(df5, "2025-12-16 22:02:00")
    >>> df_result5['已处理'].tolist()
    [True, True]
    """
    # 1. 创建DataFrame副本，避免修改原数据（最佳实践）
    df_copy = df.copy()
    if 最后历史时间 is not None:
        更新掩码 = (~df_copy["已处理"]) & (df_copy["原始时间"] <= 最后历史时间)
        df_copy.loc[更新掩码, "已处理"] = True
    return df_copy


if __name__ == "__main__":
    import doctest

    # /home/yka-003/workspace/caidao/ut/df1_1765955223.729453.json
    # /home/yka-003/workspace/caidao/ut/df2_1765955223.7296903.json

    # /home/yka-003/workspace/caidao/ut/df1_1765963449.458808.json
    # /home/yka-003/workspace/caidao/ut/df2_1765963449.4590175.json

    df1 = pd.read_json("/home/yka-003/workspace/caidao/ut/df1_1765955223.729453.json")
    df2 = pd.read_json("/home/yka-003/workspace/caidao/ut/df2_1765955223.7296903.json")

    # /home/yka-003/workspace/caidao/ut/df1_1765965165.2201815.json
    # /home/yka-003/workspace/caidao/ut/df2_1765965165.2204852.json

    # df11 = pd.read_json("/home/yka-003/workspace/caidao/ut/df1_1765965165.2201815.json")
    # df22 = pd.read_json("/home/yka-003/workspace/caidao/ut/df2_1765965165.2204852.json")
    # # print(df11.iloc[-1])
    # # print(df22.iloc[-1])
    # print(df11)
    # print(df22)
    # print(df11.iloc[0].容器key)
    # print(df22.iloc[0].容器key)
    # print(df11 == df22)
    # print(df11.xy)
    # print(df22.xy)

    得到需要处理的图片df(df1, df2)
    print(doctest.testmod(verbose=False, report=False))
