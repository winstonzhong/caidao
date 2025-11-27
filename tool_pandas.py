"""
Created on 2024年5月29日

@author: lenovo
"""

import pandas

from tool_env import is_string
from tool_numpy import bin2array

import pandas as pd


def load_test_arr():
    with open("f:/tmp/test.arr", "rb") as fp:
        return bin2array(fp.read())


def merge(df, left_on=1, right_on=0):
    df = pandas.merge(
        df,
        df,
        how="inner",
        left_on=left_on,
        right_on=right_on,
    )

    columns = {f"{i}_x": i for i in range(left_on)}
    columns[f"{left_on}_y"] = left_on + 1

    return df.rename(columns=columns)[list(range(left_on + 2))]

    # return df.rename(columns={'0_x':0,
    #                           '1_x':1,
    #                           '2_x':2,
    #                           '3_y':4})[[0,1,2,3,4]]


def is_empty(a):
    return 0 in a.shape


def get_connected_simple(a):
    i = 0
    rtn = []
    tmp = a[0].tolist()
    while not is_empty(a):
        i = a[:, 0] == tmp[-1]
        s = a[i]
        if is_empty(s):
            if len(tmp) > 2:
                rtn.append(tmp)
            a = a[1:]
            if is_empty(a):
                break
            tmp = a[0].tolist()
        else:
            assert s.shape[0] == 1, s
            tmp.append(s[0].tolist()[-1])
            a = a[~i]

    if len(tmp) > 2 and tmp not in rtn:
        rtn.append(tmp)

    return rtn


def get_connected_by_pandas(a):
    df = pandas.DataFrame(a)

    i = 1
    rtn = []

    while 1:
        df = merge(df, i, i - 1)
        if df.empty:
            break
        rtn.append(df)
        i += 1
    return rtn


def test_pandas():
    r = load_test_arr()
    df = pandas.DataFrame(r)
    df1 = merge(df, 1, 0)
    return df, df1
    print(df1)

    df2 = merge(df1, 2, 1)
    print(df2)

    df1[(df1[0] != df2[0]) | (df1[1] != df2[1]) | (df1[2] != df2[2])]
    return df1, df2

    print(df2)

    df2 = df2.rename(columns={"0_x": 0, "1_x": 1, "2_y": 3})[[0, 1, 2, 3]]
    print(df2)
    df3 = merge(df2, 3, 2)

    print(df3)

    df3 = df3.rename(columns={"0_x": 0, "1_x": 1, "2_x": 2, "3_y": 4})[[0, 1, 2, 3, 4]]

    print(df3)


op_dict = {
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "isnull": ".isnull()==",
}


def format_query(name, value):
    """
    >>> format_query('x', 1)
    'df[df["x"]==1]'
    >>> format_query('x__gte', 1)
    'df[df["x"]>=1]'
    >>> format_query('x__isnull', True)
    'df[df["x"].isnull()==True]'
    >>> format_query('x__isnull', False)
    'df[df["x"].isnull()==False]'
    >>> format_query('x', '1')
    'df[df["x"]=="1"]'
    """
    l = name.split("__")
    assert len(l) <= 2 and len(l) > 0
    op = "==" if len(l) == 1 else op_dict.get(l[1])
    name = l[0]
    if is_string(value):
        value = f'"{value}"'

    return f"""df[df["{name}"]{op}{value}]"""


def query_df(df, **k):
    """
    >>> df = pandas.DataFrame([{'x':1, 'y':2, 'type':None},{'x':3, 'y':4, 'type':0}])
    >>> query_df(df, x=1)
       x  y  type
    0  1  2   NaN
    >>> query_df(df, type__isnull=False)
       x  y  type
    1  3  4   0.0
    >>> query_df(df, type__isnull=True)
       x  y  type
    0  1  2   NaN
    """
    for name, value in k.items():
        exp = format_query(name, value)
        df = eval(exp)
    return df





def 自动补齐后续缺失时间并自动加1秒(df: pd.DataFrame) -> pd.DataFrame:
    """
    处理DataFrame的"时间"列，完成格式转换、缺失填充和组内秒数递增

    处理逻辑：
    1. 将"时间"列从字符串格式转换为datetime64格式（无法转换的设为NaT）
    2. 对"时间"列执行前向填充(ffill)，用前一个有效时间填充后续缺失值
    3. 按填充后的"时间"分组，组内按行位置依次递增0秒、1秒、2秒...

    参数:
        df: 必须包含"时间"列的DataFrame，"时间"列可包含字符串格式时间和NaN

    返回:
        处理后的DataFrame，"时间"列已完成格式转换和秒数递增，其他列保持不变

    示例:
        >>> import pandas as pd
        >>> # 测试基础场景（用户示例数据）
        >>> data1 = {
        ...     '时间': ['2025-11-25 22:00:00', None, '2025-11-26 16:01:00', None],
        ...     '已处理': [False, False, True, False]
        ... }
        >>> df1 = pd.DataFrame(data1)
        >>> result1 = 自动补齐后续缺失时间并自动加1秒(df1)
        >>> # 验证时间列结果
        >>> result1.时间
        0    2025-11-25 22:00:00
        1    2025-11-25 22:00:01
        2    2025-11-26 16:01:00
        3    2025-11-26 16:01:01
        Name: 时间, dtype: object
        >>> # 测试多个连续缺失值场景
        >>> data2 = {
        ...     '时间': ['2025-01-01 00:00:00', None, None, '2025-01-02 12:34:56', None, None, None],
        ...     '数值': [10, 20, 30, 40, 50, 60, 70]
        ... }
        >>> df2 = pd.DataFrame(data2)
        >>> result2 = 自动补齐后续缺失时间并自动加1秒(df2)
        >>> result2.时间
        0    2025-01-01 00:00:00
        1    2025-01-01 00:00:01
        2    2025-01-01 00:00:02
        3    2025-01-02 12:34:56
        4    2025-01-02 12:34:57
        5    2025-01-02 12:34:58
        6    2025-01-02 12:34:59
        Name: 时间, dtype: object
        >>> # 测试无缺失值场景
        >>> data3 = {
        ...     '时间': ['2025-03-03 08:00:00', '2025-03-03 09:00:00'],
        ...     '状态': ['运行', '停止']
        ... }
        >>> df3 = pd.DataFrame(data3)
        >>> result3 = 自动补齐后续缺失时间并自动加1秒(df3)
        >>> result3.时间
        0    2025-03-03 08:00:00
        1    2025-03-03 09:00:00
        Name: 时间, dtype: object

        >>> # 测试第一行时间即为None的场景（重点测试）
        >>> data4 = {
        ...     '时间': [None, None, '2025-05-05 10:10:10', None, None, '2025-05-06 09:09:09', None],
        ...     '标记': [1, 2, 3, 4, 5, 6, 7]
        ... }
        >>> df4 = pd.DataFrame(data4)
        >>> result4 = 自动补齐后续缺失时间并自动加1秒(df4)
        >>> result4.时间
        0                    NaN
        1                    NaN
        2    2025-05-05 10:10:10
        3    2025-05-05 10:10:11
        4    2025-05-05 10:10:12
        5    2025-05-06 09:09:09
        6    2025-05-06 09:09:10
        Name: 时间, dtype: object
        >>> # 测试第一行None且后续无有效时间的极端场景
        >>> data5 = {
        ...     '时间': [None, None, None],
        ...     '数值': [100, 200, 300]
        ... }
        >>> df5 = pd.DataFrame(data5)
        >>> result5 = 自动补齐后续缺失时间并自动加1秒(df5)
        >>> result5.时间
        0    NaN
        1    NaN
        2    NaN
        Name: 时间, dtype: object
    """
    # 复制原数据，避免修改输入DataFrame
    df_copy = df.copy()
    
    # 1. 字符串转datetime（无法转换的设为NaT）
    df_copy['时间'] = pd.to_datetime(df_copy['时间'], errors='coerce')
    
    # 2. 前向填充缺失时间
    df_copy['时间'] = df_copy['时间'].ffill()
    
    # 3. 组内按位置递增秒数（cumcount()返回组内索引：0,1,2...）
    df_copy['时间'] += pd.to_timedelta(df_copy.groupby('时间').cumcount(), unit='s')
    
    df_copy['时间'] = df_copy['时间'].dt.strftime('%Y-%m-%d %H:%M:%S')

    
    return df_copy

if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
