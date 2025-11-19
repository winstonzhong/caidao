import pandas as pd
import numpy as np

import datetime
import pytz


def 提取指定日期中午12点到前一天中午12点的所有记录(
    df: pd.DataFrame, dt: datetime.date
) -> pd.DataFrame:
    """
    提取指定日期中午12点到前一天中午12点之间的所有记录。

    步骤：
    1. 将create_time转换为北京时间（Asia/Shanghai）的datetime类型。
    2. 计算时间范围：前一天12:00:00（含）到指定日期12:00:00（不含）。
    3. 筛选出在此范围内的记录。

    参数：
        df: 包含create_time列的DataFrame，create_time可为字符串或datetime。
        dt: 指定的日期，用于确定时间范围。

    返回：
        筛选后的pandas.DataFrame。

    >>> import pandas as pd
    >>> import datetime
    >>> # 测试字符串类型的create_time
    >>> data_str = {
    ...     'create_time': [
    ...         '2025-10-21 12:00:00+08:00',
    ...         '2025-10-21 18:30:00+08:00',
    ...         '2025-10-22 11:59:59+08:00',
    ...         '2025-10-22 12:00:00+08:00',
    ...         '2025-10-20 12:00:00+08:00'
    ...     ],
    ...     'value': [10, 20, 30, 40, 50]
    ... }
    >>> df_str = pd.DataFrame(data_str)
    >>> test_dt = datetime.date(2025, 10, 22)
    >>> result_str = 提取指定日期中午12点到前一天中午12点的所有记录(df_str, test_dt)
    >>> result_str['value'].tolist()
    [10, 20, 30]
    >>> # 测试datetime类型（带UTC时区）的create_time
    >>> tz_utc = pytz.UTC
    >>> tz_cn = pytz.timezone('Asia/Shanghai')
    >>> # UTC时间2025-10-21 04:00 等于 北京时间12:00
    >>> dt1 = datetime.datetime(2025, 10, 21, 4, 0, 0, tzinfo=tz_utc)
    >>> # UTC时间2025-10-22 03:59:59 等于 北京时间11:59:59
    >>> dt2 = datetime.datetime(2025, 10, 22, 3, 59, 59, tzinfo=tz_utc)
    >>> # UTC时间2025-10-22 04:00 等于 北京时间12:00
    >>> dt3 = datetime.datetime(2025, 10, 22, 4, 0, 0, tzinfo=tz_utc)
    >>> data_dt = {
    ...     'create_time': [dt1, dt2, dt3],
    ...     'value': [100, 200, 300]
    ... }
    >>> df_dt = pd.DataFrame(data_dt)
    >>> result_dt = 提取指定日期中午12点到前一天中午12点的所有记录(df_dt, test_dt)
    >>> result_dt['value'].tolist()
    [100, 200]
    >>> # 测试datetime类型（不带时区）的create_time，假设为北京时间
    >>> dt4 = datetime.datetime(2025, 10, 21, 12, 0, 0)  # 不带时区
    >>> dt5 = datetime.datetime(2025, 10, 22, 11, 59, 59)
    >>> dt6 = datetime.datetime(2025, 10, 22, 12, 0, 0)
    >>> data_naive = {
    ...     'create_time': [dt4, dt5, dt6],
    ...     'value': [400, 500, 600]
    ... }
    >>> df_naive = pd.DataFrame(data_naive)
    >>> result_naive = 提取指定日期中午12点到前一天中午12点的所有记录(df_naive, test_dt)
    >>> result_naive['value'].tolist()
    [400, 500]
    """
    # 复制原DataFrame避免修改原始数据
    df_copy = df.copy()

    # 转换create_time为datetime类型
    df_copy["create_time"] = pd.to_datetime(df_copy["create_time"], format="ISO8601")

    # 处理时区，转换为北京时间（Asia/Shanghai）
    tz_cn = pytz.timezone("Asia/Shanghai")
    if df_copy["create_time"].dt.tz is None:
        # 无时区信息，视为北京时间并添加时区
        df_copy["create_time"] = df_copy["create_time"].dt.tz_localize(tz_cn)
    else:
        # 有其他时区，转换为北京时间
        df_copy["create_time"] = df_copy["create_time"].dt.tz_convert(tz_cn)

    # 计算时间范围的起始和结束
    前一天 = dt - datetime.timedelta(days=1)
    # 前一天中午12点（含）
    start = datetime.datetime.combine(前一天, datetime.time(12, 0, 0))
    start = tz_cn.localize(start)  # 使用localize方法添加时区，更规范
    # 指定日期中午12点（不含）
    end = datetime.datetime.combine(dt, datetime.time(12, 0, 0))
    end = tz_cn.localize(end)

    # 筛选符合条件的记录
    筛选条件 = (df_copy["create_time"] >= start) & (df_copy["create_time"] < end)
    return df_copy[筛选条件]


def 提取步数数据(data: dict) -> pd.DataFrame:
    """
    提取步数数据并转换为pandas DataFrame。

    如果history_list为空或None，则从data_list中提取微信步数的值，创建一条包含该值和NaN时间的记录；
    否则直接将history_list转换为DataFrame。

    示例:
    >>> data1 = {'data_list': [{'name': '微信步数', 'value': 335, 'unit': '步'}, {'name': '强度', 'value': '中速', 'unit': ''}], 'summary': '2025-11-18走了335步', 'history_list': [{'create_time': '2025-11-18 11:30:40', 'value': 335}]}
    >>> df1 = 提取步数数据(data1)
    >>> print(df1.to_dict('records'))
    [{'create_time': '2025-11-18 11:30:40', 'value': 335}]
    >>> data2 = {'data_list': [{'name': '微信步数', 'value': 500, 'unit': '步'}], 'summary': '示例数据', 'history_list': []}
    >>> df2 = 提取步数数据(data2)
    >>> records2 = df2.to_dict('records')
    >>> len(records2) == 1 and np.isnan(records2[0]['create_time']) and records2[0]['value'] == 500
    True
    >>> data3 = {'data_list': [{'name': '微信步数', 'value': 1000, 'unit': '步'}], 'summary': '示例数据', 'history_list': None}
    >>> df3 = 提取步数数据(data3)
    >>> records3 = df3.to_dict('records')
    >>> len(records3) == 1 and np.isnan(records3[0]['create_time']) and records3[0]['value'] == 1000
    True
    """
    history_list = data.get("history_list")

    # 检查history_list是否为空或None
    if history_list is None or len(history_list) == 0:
        # 从data_list中提取微信步数
        for item in data.get("data_list", []):
            if item.get("name") == "微信步数":
                step_value = item["value"]
                return pd.DataFrame([{"create_time": np.nan, "value": step_value}])
        # 若未找到微信步数，返回空DataFrame（按题目假设此情况可能不发生）
        return pd.DataFrame(columns=["create_time", "value"])
    else:
        # 直接转换history_list为DataFrame
        return pd.DataFrame(history_list)


def 按日期分组并选择值最大的行记录返回(
    df: pd.DataFrame, today: datetime.date = None, ndays: int = 30
) -> pd.DataFrame:
    """
    按日期分组并选择每个日期中value最大的行记录，返回新的DataFrame。

    步骤：
    1. 转换create_time列为datetime类型（如果是字符串）。
    2. 确定基准日期today，默认为当前日期。
    3. 筛选出create_time在[today - ndays, today]范围内的记录。
    4. 按create_time的日期部分分组，每个组选择value最大的行。

    参数：
        df: 输入的DataFrame，包含create_time和value列。
        today: 基准日期，默认为当前日期。
        ndays: 向前推的天数，默认30天。

    返回：
        每个日期中value最大的行组成的DataFrame。

    示例：
        >>> import pandas as pd
        >>> import datetime
        >>> data = [
        ...     ("2025-10-20 16:39:39.712410+08:00", 20364),
        ...     ("2025-10-20 17:39:39.712410+08:00", 25000),
        ...     ("2025-10-21 12:00:22.602884+08:00", 20243),
        ...     ("2025-10-22 12:19:32.491605+08:00", 6826),
        ...     ("2025-10-19 18:31:42.025412+08:00", 21427),
        ...     ("2025-11-18 07:30:25+08:00", 3494),
        ...     ("2025-11-18 09:30:37+08:00", 3517),
        ...     ("2025-11-18 10:30:25+08:00", 6005),
        ...     ("2025-11-18 11:30:40+08:00", 6006),
        ...     ("2025-11-18 12:30:31+08:00", 6595),
        ... ]
        >>> df = pd.DataFrame(data, columns=["create_time", "value"])
        >>> today = datetime.date(2025, 11, 19)
        >>> result = 按日期分组并选择值最大的行记录返回(df, today, 30)
        >>> len(result)
        4
        >>> result.value.tolist()
        [25000, 20243, 6826, 6595]
        >>> df_empty = pd.DataFrame(columns=["create_time", "value"])
        >>> result_empty = 按日期分组并选择值最大的行记录返回(df_empty)
        >>> result_empty.empty
        True
        >>> data_single = [("2025-11-19 10:00:00+08:00", 100)]
        >>> df_single = pd.DataFrame(data_single, columns=["create_time", "value"])
        >>> result_single = 按日期分组并选择值最大的行记录返回(df_single, today, 1)
        >>> result_single["value"].iloc[0]
        100
    """
    if df.empty:
        return df
    # 复制输入DataFrame以避免修改原始数据
    df_copy = df.copy()

    # 转换create_time列为datetime类型（如果是字符串类型）
    if pd.api.types.is_string_dtype(df_copy["create_time"]):
        df_copy["create_time"] = pd.to_datetime(
            df_copy["create_time"], format="ISO8601"
        )

    # 确定基准日期today，默认为当前日期
    if today is None:
        today = datetime.date.today()

    # 计算筛选的起始日期
    start_date = today - datetime.timedelta(days=ndays)

    # 提取create_time的日期部分作为新列，用于筛选和分组
    df_copy["create_time"] = df_copy["create_time"].dt.date

    # 筛选出日期在起始日期及之后的记录
    df_filtered = df_copy[df_copy["create_time"] >= start_date]

    # 如果筛选后没有数据，返回空DataFrame（移除临时date列）
    if df_filtered.empty:
        return df_filtered

    grouped = df_filtered.groupby("create_time")

    max_indices = grouped["value"].idxmax()

    # 根据索引获取结果，并按create_time排序
    result = df_filtered.loc[max_indices].sort_values(by="create_time")

    return result


if __name__ == "__main__":
    # 示例数据
    import doctest

    print(doctest.testmod())
