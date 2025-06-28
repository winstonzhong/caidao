"""
Created on 2020年12月2日

@author: winston
"""

import datetime
from time import strptime, mktime
import time

import numpy
import pytz
import re


TIME_ZONE_SHANGHAI = pytz.timezone("Asia/Shanghai")


def timing_it(func):
    def wrapper(*arg, **kw):
        old = time.time()
        res = func(*arg, **kw)
        print(func.__name__, "%.2f" % (time.time() - old))
        return res

    return wrapper


def time_shanghai():
    return datetime.datetime.now(TIME_ZONE_SHANGHAI)


def time_now():
    return time_shanghai().strftime("%H:%M:%S")


def 今天():
    return datetime.datetime.now(TIME_ZONE_SHANGHAI).date()


def today():
    return dash_date(今天())


def yesterday():
    return dash_date(今天() - datetime.timedelta(days=1))


def 一年前的某天():
    return dash_date(今天() - datetime.timedelta(days=365))


def n年前(n, tdate=None):
    if tdate is not None:
        tdate = to_date(tdate)
    else:
        tdate = 今天()
    return tdate - datetime.timedelta(days=n * 365)


def first_day_of_month():
    return today()[:-2] + "01"


def to_code(symbol):
    return int(symbol[:6])


def to_symbol_tt(code):
    code = full_ticker(code)
    return (
        "sh%s" % code
        if code[:1] in ["5", "6", "9"] or code[:2] in ["11", "13"]
        else "sz%s" % code
    )


def to_symbol_sina(code):
    """
    >>> to_symbol_sina(1)
    'sz000001'
    >>> to_symbol_sina(830779)
    'bj830779'
    >>> to_symbol_sina(689009)
    'sh689009'
    >>> to_symbol_sina('689009')
    'sh689009'
    """
    code = full_ticker(code)
    if code[:1] in ["5", "6", "9"]:
        return "sh" + code

    if code[:2] in ["11", "13"]:
        return "sh" + code

    if code[:1] in ["0", "3"]:
        return "sz" + code

    if code[:1] in ["4", "8"]:
        return "bj" + code

    raise ValueError


def to_symbol(code):
    code = full_ticker(code)
    return (
        "%s.SH" % code
        if code[:1] in ["5", "6", "9"] or code[:2] in ["11", "13"]
        else "%s.SZ" % code
    )


def ticker_to_code(code):
    """
    >>> ticker_to_code(1)
    'sz000001'
    """
    from tushare.stock.cons import _code_to_symbol

    return _code_to_symbol(full_ticker(code))


def full_ticker(code):
    """
    >>> full_ticker(22)
    '000022'
    >>> full_ticker("112233")
    '112233'
    """
    return "%06d" % int(code)


def neat_ticker(code):
    """
    >>> neat_ticker("0022")
    '22'
    >>> neat_ticker("00220")
    '220'
    >>> neat_ticker("220")
    '220'
    >>> neat_ticker("221")
    '221'
    >>> neat_ticker(21)
    '21'
    """
    return str(int(code))


def dash_date(tdate):
    """
    >>> dash_date('20160308')
    '2016-03-08'
    >>> dash_date('20161231')
    '2016-12-31'
    >>> dash_date(datetime.datetime(year=2016,month=12,day=31))
    '2016-12-31'
    >>> dash_date(datetime.date(year=2016,month=12,day=31))
    '2016-12-31'
    >>> dash_date('2016-12-31')
    '2016-12-31'
    >>> dash_date(None)
    """
    if tdate:
        if isinstance(tdate, datetime.datetime) or isinstance(tdate, datetime.date):
            tdate = tdate.strftime("%Y-%m-%d")
        elif "-" not in tdate:
            tdate = datetime.datetime.fromtimestamp(
                mktime(strptime(tdate, "%Y%m%d"))
            ).strftime("%Y-%m-%d")
    return tdate


def tight_date(tdate):
    """
    >>> tight_date('20160308')
    '20160308'
    >>> tight_date('2016-12-31')
    '20161231'
    >>> tight_date(datetime.datetime(year=2016,month=12,day=31))
    '20161231'
    >>> tight_date(datetime.date(year=2016,month=12,day=31))
    '20161231'
    >>> tight_date('2016-12-31')
    '20161231'
    >>> tight_date(None)
    """
    if tdate:
        if isinstance(tdate, datetime.datetime) or isinstance(tdate, datetime.date):
            tdate = tdate.strftime("%Y%m%d")
        elif "-" in tdate:
            tdate = datetime.datetime.fromtimestamp(
                mktime(strptime(tdate, "%Y-%m-%d"))
            ).strftime("%Y%m%d")
    return tdate


def to_date(date):
    """
    >>> to_date(datetime.datetime(year=2016, month=3, day=9))
    datetime.date(2016, 3, 9)
    >>> to_date('20160308')
    datetime.date(2016, 3, 8)
    >>> to_date('2016-12-31')
    datetime.date(2016, 12, 31)
    >>> to_date('a')
    >>> to_date(None)
    >>> to_date(0)
    >>> to_date(u'2016-04-22 10:46:00')
    datetime.date(2016, 4, 22)
    >>> to_date('1967-10-17')
    datetime.date(1967, 10, 17)
    """
    if isinstance(date, datetime.datetime):
        return date.date()
    if isinstance(date, datetime.date):
        return date
    try:
        return datetime.datetime.fromtimestamp(
            mktime(strptime(dash_date(date)[:10], "%Y-%m-%d"))
        ).date()
    except OverflowError as e:
        raise e
    except Exception:
        pass


def is_half_year_old(tdate):
    d = datetime.datetime.now(TIME_ZONE_SHANGHAI).date() - to_date(tdate)
    return d.days >= 180


def get_date_ndays_ago(ndays):
    return datetime.datetime.now(TIME_ZONE_SHANGHAI).date() - datetime.timedelta(
        days=ndays
    )


def get_date_half_year_old():
    return get_date_ndays_ago(180)
    # return datetime.datetime.now(TIME_ZONE_SHANGHAI).date() - datetime.timedelta(days=180)


def isnan(v):
    """
    >>> isnan(1)
    False
    >>> isnan(None)
    False
    >>> isnan('111')
    False
    >>> isnan(numpy.nan)
    True
    """
    try:
        return numpy.isnan(v)
    except Exception:
        return False


def none2nan(v):
    """c
    >>> none2nan(None)
    nan
    >>> none2nan(1) == 1
    True
    >>> none2nan(0) == 0
    True
    """
    return v if v is not None else numpy.nan


def nan2none(v):
    return None if isnan(v) else v


def timing_print(func):
    def wrapper(*arg, **kw):
        old = time.time()
        rtn = func(*arg, **kw)
        print("%s:%.2f" % (func.__name__, time.time() - old))
        return rtn

    return wrapper


def calculate_birthdate(age: int, input_date: datetime.date) -> datetime.date:
    """
    根据年龄和输入日期计算出生日期。

    Args:
        age: 当前年龄
        input_date: 计算时的日期

    Returns:
        计算出的出生日期

    >>> calculate_birthdate(30, datetime.date(2025, 6, 28))
    datetime.date(1995, 6, 28)
    >>> calculate_birthdate(25, datetime.date(2025, 6, 28))
    datetime.date(2000, 6, 28)
    >>> calculate_birthdate(25, datetime.date(2000, 2, 29))
    datetime.date(1975, 2, 28)
    >>> calculate_birthdate(None, datetime.date(2000, 2, 28))
    >>> calculate_birthdate(11, None)
    """
    if not age or not input_date:
        return
    age = int(age)
    input_date = convert_to_date(input_date)
    # 直接用输入日期减去年龄对应的年数
    birth_year = input_date.year - age
    birth_month = input_date.month
    birth_day = input_date.day

    # 处理2月29日的情况
    if birth_month == 2 and birth_day >= 29:
        # 如果出生那年不是闰年，使用2月28日
        if not (
            birth_year % 4 == 0 and (birth_year % 100 != 0 or birth_year % 400 == 0)
        ):
            birth_day = 28
    return datetime.date(birth_year, birth_month, birth_day)


def convert_to_date(date_input) -> datetime.date:
    """
    将常见日期格式的字符串或date对象转换为date对象。

    Args:
        date_input: 日期输入，可以是字符串或date对象

    Returns:
        转换后的date对象

    >>> convert_to_date(datetime.date(2022, 11, 21))
    datetime.date(2022, 11, 21)
    >>> convert_to_date("2022.11.21")
    datetime.date(2022, 11, 21)
    >>> convert_to_date("2022/11/21")
    datetime.date(2022, 11, 21)
    >>> convert_to_date("2022-11-21")
    datetime.date(2022, 11, 21)
    >>> convert_to_date("2022 11 21")
    datetime.date(2022, 11, 21)
    >>> convert_to_date("22.11.21")
    datetime.date(2022, 11, 21)
    >>> convert_to_date("2021-5-4")
    datetime.date(2021, 5, 4)
    >>> convert_to_date("2021-05-4")
    datetime.date(2021, 5, 4)
    >>> convert_to_date("2021-5-04")
    datetime.date(2021, 5, 4)
    >>> convert_to_date("75.6.24")
    datetime.date(1975, 6, 24)
    """
    if isinstance(date_input, datetime.date):
        return date_input

    if not isinstance(date_input, str):
        raise TypeError("输入类型必须是字符串或date对象")

    # 匹配常见日期格式，允许月/日为1位数字
    match = re.match(
        r"^(?:(\d{4})|(\d{2}))[^\d](\d{1,2})[^\d](\d{1,2})$", date_input.strip()
    )

    if not match:
        raise ValueError(f"无法解析日期格式: {date_input}")

    year_str, short_year, month_str, day_str = match.groups()

    # 处理年份
    if year_str:
        year = int(year_str)
    else:
        # 短年份处理 (如 22 -> 2022)
        short_year = int(short_year)
        year = 2000 + short_year if short_year < 50 else 1900 + short_year

    month = int(month_str)
    day = int(day_str)

    try:
        return datetime.date(year, month, day)
    except ValueError:
        raise ValueError(f"无效的日期: {date_input}")


def generate_person_id(name: str, birthdate, gender: str) -> str:
    """
    生成标准化的人员唯一标识字符串。

    Args:
        name: 姓名
        birthdate: 出生日期，可以是date对象或符合convert_to_date支持格式的字符串
        gender: 性别描述字符串

    Returns:
        标准化的人员标识字符串，格式为"姓名|性别|YYYY-MM-DD"

    >>> generate_person_id("张三", datetime.date(1953, 1, 21), "男")
    '张三|男|1953-01-21'
    >>> generate_person_id("李四", "1990/05/15", "女")
    '李四|女|1990-05-15'
    >>> generate_person_id("王五", "2001.3.8", "男性")
    '王五|男|2001-03-08'
    >>> generate_person_id("赵六", "2022-11-21", "女生")
    '赵六|女|2022-11-21'
    >>> generate_person_id("钱七", "22/11/21", "未知")
    '钱七|-|2022-11-21'
    >>> generate_person_id("钱七", "22/11/21", None)
    '钱七|-|2022-11-21'
    >>> generate_person_id("钱七", None, None)
    '钱七|-|-'
    """

    # 标准化姓名：去除前后空格
    standardized_name = name.strip()

    # 标准化性别：根据字符串内容判断
    gender_text = gender.strip() if gender else "-"
    if "男" in gender_text:
        standardized_gender = "男"
    elif "女" in gender_text:
        standardized_gender = "女"
    else:
        standardized_gender = "-"

    # 标准化出生日期
    if birthdate:
        standardized_birthdate = convert_to_date(birthdate)
        birthdate_str = standardized_birthdate.strftime("%Y-%m-%d")
    else:
        birthdate_str = '-'

    # 生成并返回标准化标识
    return f"{standardized_name}|{standardized_gender}|{birthdate_str}"


if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
