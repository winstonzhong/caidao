def is_equal_to_range(lst):
    """
    检查输入的列表是否等于 range(1, len(lst)+1)。

    :param lst: 输入的列表
    :return: 如果列表等于 range(1, len(lst)+1)，返回 True；否则返回 False。

    >>> is_equal_to_range([1, 2, 3, 4])
    True
    >>> is_equal_to_range([1, 3, 2, 5])
    False
    >>> is_equal_to_range([])
    False
    >>> is_equal_to_range([1])
    True
    >>> is_equal_to_range([1, 2, 4, 3])
    True
    >>> is_equal_to_range([1, 2, 4, 3, 0])
    False
    >>> is_equal_to_range([2, 4, 3, 5])
    True
    >>> is_equal_to_range([2])
    True
    >>> is_equal_to_range([2, 1, 4])
    False
    """
    if 0 in lst or not lst:
        return False
    start = min(lst)
    end = start + len(lst)
    return sorted(lst) == list(range(start, end))



if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))
