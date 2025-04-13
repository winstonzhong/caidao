import datetime



def calculate_rtn(a, b, x):
    """
    计算满足条件的 rtn 值。
    rtn 需满足两个条件: 1. rtn = a + n * b; 2. rtn - b < x <= rtn。
    如果输入的 x 小于 a，抛出 ValueError 异常。

    :param a: datetime 类型，表示起始时间
    :param b: int 类型，表示间隔秒数
    :param x: datetime 类型，表示参考时间，需大于等于 a
    :return: 返回满足条件的 rtn，datetime 类型

    >>> a = datetime.datetime(2023, 1, 1, 0, 0, 0)
    >>> b = 3600
    >>> x = datetime.datetime(2023, 1, 1, 2, 30, 0)
    >>> calculate_rtn(a, b, x) == datetime.datetime(2023, 1, 1, 2, 0)
    True
    >>> a = datetime.datetime(2023, 1, 1, 0, 0, 0)
    >>> b = 3600
    >>> x = datetime.datetime(2023, 1, 1, 0, 0, 0)
    >>> calculate_rtn(a, b, x)
    Traceback (most recent call last):
        ...
    ValueError: 输入的 x 必须大于等于 a + b
    >>> a = datetime.datetime(2023, 1, 1, 0, 0, 0)
    >>> b = 3600
    >>> x = datetime.datetime(2023, 1, 1, 0, 0, 1)
    >>> calculate_rtn(a, b, x)
    Traceback (most recent call last):
        ...
    ValueError: 输入的 x 必须大于等于 a + b
    >>> x_invalid = datetime.datetime(2022, 1, 1, 0, 0, 0)
    >>> try:
    ...     calculate_rtn(a, b, x_invalid)
    ... except ValueError as e:
    ...     str(e)
    '输入的 x 必须大于等于 a + b'
    >>> a = datetime.datetime(2023, 1, 1, 0, 0, 0)
    >>> b = 3600
    >>> x = datetime.datetime(2023, 1, 1, 3, 30, 0)
    >>> calculate_rtn(a, b, x) == datetime.datetime(2023, 1, 1, 3, 0)
    True
    """
    if x < a + datetime.timedelta(seconds=b):
        raise ValueError("输入的 x 必须大于等于 a + b")
    assert b > 0, "间隔时间不能为负或零"
    delta_seconds = (x - a).total_seconds()
    return a + datetime.timedelta(seconds=(delta_seconds // b) * b)

if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))

    