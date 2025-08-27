import pandas as pd


def check_series_contains(series: pd.Series, lst: list) -> bool:
    """
    检查pandas.Series是否满足以下两种情况之一:
    1. 完整且连续包含整个列表
    2. 包含列表的一部分list[i:]，该部分在Series中连续且list[i]是Series的首元素

    参数:
        series: pandas.Series对象
        lst: 要检查的列表

    返回:
        满足任一情况返回True，否则返回False

    测试用例:
    >>> check_series_contains(pd.Series([1,2,3,4,5]), [2,3,4])  # 情况1: 完整包含子列表
    True
    >>> check_series_contains(pd.Series([3,4,5,6]), [1,2,3,4])  # 情况2: 包含列表的一部分[3,4...]且3是首元素
    True
    >>> check_series_contains(pd.Series([2,3,4]), [1,2,3,4,5])  # 情况2: 包含列表的一部分[2,3,4]且2是首元素, 但不完整
    False
    >>> check_series_contains(pd.Series([1,2,3]), [2,1,3])  # 不连续包含
    False
    >>> check_series_contains(pd.Series([1,2,3]), [3,4])  # 列表元素在Series但位置不对
    False
    >>> check_series_contains(pd.Series([1,2,3]), [2])  # 情况1: 单元素包含
    True
    >>> check_series_contains(pd.Series([5]), [1,2,5])  # 情况2: 单元素匹配
    True
    >>> check_series_contains(pd.Series([1,2]), [2,3,4])  # 首元素不匹配且不包含整个列表
    False
    >>> check_series_contains(pd.Series([]), [1,2])  # 空Series
    False
    >>> check_series_contains(pd.Series([1,2]), [])  # 空列表
    False
    >>> check_series_contains(pd.Series([1,2,3,4]), [2,4])  # 非连续元素
    False
    >>> check_series_contains(pd.Series([3,4]), [1,2,3,4,5])  # 情况2: 包含列表的一部分且长度匹配, 不完整
    False
    >>> check_series_contains(pd.Series([3,4]), [1,2,3,4,5,6])  # 情况2: 包含列表的一部分但长度不足
    False
    >>> check_series_contains(pd.Series([3,4,5]), [1,2,3,4,5])  # 情况2: 包含列表的一部分且长度匹配, 完整
    True
    >>> check_series_contains(pd.Series([3,4,]), [1,2,3,4,])  # 情况2: 包含列表的一部分且长度匹配, 完整
    True
    """
    # 将Series转换为列表以便处理
    series_list = series.tolist()
    len_series = len(series_list)
    len_lst = len(lst)

    # 处理空列表或空Series的情况
    if len_lst == 0 or len_series == 0:
        return False

    # 情况1: 检查Series是否完整且连续包含整个列表
    for i in range(len_series - len_lst + 1):
        if series_list[i : i + len_lst] == lst:
            return True

    # 情况2: 检查Series是否包含列表的一部分list[i:]，且list[i]是Series的首行
    first_element = series_list[0]
    for i in range(len_lst):
        if lst[i] == first_element:
            # 计算子列表长度
            sublist_length = len_lst - i
            # 确保子列表长度不超过Series长度
            if sublist_length <= len_series:
                # 检查Series是否从开头匹配子列表
                if series_list[:sublist_length] == lst[i:]:
                    return True

    # 两种情况都不满足
    return False


if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
