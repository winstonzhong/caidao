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
import random
from django.utils import timezone

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


def 现在():
    return time_shanghai()


def 今天():
    return datetime.datetime.now(TIME_ZONE_SHANGHAI).date()


def 昨天():
    return 今天() - datetime.timedelta(days=1)


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
        birthdate_str = "-"

    # 生成并返回标准化标识
    return f"{standardized_name}|{standardized_gender}|{birthdate_str}"


def 北京时间字符串转UTC(time_str):
    """
    将北京时间（Asia/Shanghai）字符串转换为UTC时区的datetime对象

    参数:
        time_str (str): 北京时间字符串，格式为 "%Y-%m-%d %H:%M:%S"（例如 "2025-01-01 08:29:00"）

    返回:
        datetime: 带UTC时区信息的datetime对象（aware datetime）
    """
    if time_str and isinstance(time_str, str):
        # 1. 解析字符串为 naive datetime（不带时区）
        naive_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

        # 2. 指定原始时区为北京时间（Asia/Shanghai）
        beijing_tz = pytz.timezone("Asia/Shanghai")
        beijing_time = beijing_tz.localize(naive_time)  # 转换为北京时间的aware datetime

        # 3. 转换为UTC时区
        utc_time = beijing_time.astimezone(pytz.UTC)

        return utc_time
    return time_str


def 日期转中文周几(tdate: datetime.date):
    """
    将日期转换为中文表示的周几

    :param tdate: 待转换的日期
    :return: 中文表示的周几

    >>> 日期转中文周几(datetime.date(2023, 1, 1))
    '星期天'
    """
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期天"]
    return weekdays[tdate.weekday()]


def 日期转中文几日(tdate: datetime.date):
    """
    将日期转换为中文表示的几日

    :param tdate: 待转换的日期
    :return: 中文表示的几日

    >>> 日期转中文几日(datetime.date(2023, 1, 1))
    '1日'
    """
    return f"{tdate.day}日"


def 日期列表转不重复的中文几月列表(
    dates: list[datetime.date], include_year=False
) -> list[str]:
    """
    将日期列表转换为不重复的中文几月列表

    :param dates: 待转换的日期列表
    :return: 不重复的中文几月列表

    >>> 日期列表转不重复的中文几月列表([datetime.date(2023, 1, 1), datetime.date(2023, 2, 1), datetime.date(2023, 3, 1)])
    ['1月', '2月', '3月']
    >>> 日期列表转不重复的中文几月列表([datetime.date(2023, 1, 1), datetime.date(2023, 2, 1), datetime.date(2023, 3, 1), datetime.date(2024, 1, 1)])
    ['1月', '2月', '3月', '1月']
    >>> 日期列表转不重复的中文几月列表([datetime.date(2023, 1, 1), datetime.date(2023, 2, 1), datetime.date(2023, 3, 1), datetime.date(2024, 1, 1)], True)
    ['2023年-1月', '2023年-2月', '2023年-3月', '2024年-1月']
    """
    months = []
    for date in dates:
        key = f"{date.year}年-{date.month}月"
        if key not in months:
            months.append(key)
    return [item.split("-")[-1] for item in months] if not include_year else months


def 获取日期范围(
    总天数: int, 截止日期: datetime.datetime = None
) -> list[datetime.date]:
    """
    生成从开始日期到截止日期（包含两端）的所有日期列表

    参数:
        总天数 (int): 非负整数，用于计算开始日期（开始日期 = 截止日期 - 总天数）
        截止日期 (datetime.datetime, 可选): 范围的结束日期，默认为None（此时使用当前日期时间）

    返回:
        list[datetime.date]: 包含开始日期到截止日期的所有日期（仅日期部分，不含时间）

    异常:
        TypeError: 若截止日期不是datetime.datetime类型（当提供时）
        ValueError: 若总天数为负数或非整数
    """
    # 处理截止日期默认值（为None时使用当前时间）
    if 截止日期 is None:
        截止日期 = 今天()
    elif not isinstance(截止日期, datetime.datetime):
        截止日期 = to_date(截止日期)

    # 输入参数验证
    if not isinstance(截止日期, datetime.date):
        raise TypeError("截止日期必须是 datetime.datetime 类型")

    if not isinstance(总天数, int) or 总天数 < 0:
        raise ValueError("总天数必须是非负整数")

    # 计算开始日期（取日期部分，忽略时间）
    开始日期 = 截止日期 - datetime.timedelta(days=总天数 - 1)
    # 提取截止日期的日期部分（忽略时间）
    结束日期 = 截止日期

    # 生成范围内所有日期
    日期列表 = []
    当前日期 = 开始日期
    while 当前日期 <= 结束日期:
        日期列表.append(当前日期)
        当前日期 += datetime.timedelta(days=1)

    return 日期列表


def 获取日周月年期范围(类型: str, 截止日期: datetime.datetime = None):
    总天数 = {
        "日": 1,
        "周": 7,
        "月": 30,
        "年": 365,
    }.get(类型)
    assert 总天数 is not None, f"未知的类型：{类型}"
    return 获取日期范围(总天数, 截止日期)


def 日期转随机北京时间(current_date, start_hour=0, end_hour=23):
    """
    给定一个日期，随机生成该日期对应的北京时间。

    参数:
    current_date: 需要转换的时间，可以是 datetime.date 或者 datetime.datetime 类型的对象。

    返回:
    一个 datetime.datetime 类型的对象，表示转换后的北京时间。

    """
    current_date = to_date(current_date)
    hour = random.randint(start_hour, end_hour)
    minute = random.randint(0, 59)
    target = datetime.datetime.combine(current_date, datetime.time(hour, minute))

    return timezone.make_aware(
        target,
        timezone=timezone.get_current_timezone(),  # 使用 Django 配置的时区（如 Asia/Shanghai）
    )


def 是否在时间段内(
    起始时间: str = "00:00:00", 结束时间: str = "24:00:00", 当前时间: str = None
) -> bool:
    """
    判断当前时间是否在起始时间和结束时间之间（包含边界）。

    参数:
        起始时间: 格式为"%H:%M:%S"的字符串，默认为'00:00:00'
        结束时间: 格式为"%H:%M:%S"的字符串，默认为'24:00:00'
        当前时间: 格式为"%H:%M:%S"的字符串，若为None则使用当前上海时间，默认为None

    返回:
        bool: 当前时间在时间段内返回True，否则返回False

    示例:
        >>> 是否在时间段内('08:00:00', '18:00:00', '12:00:00')
        True
        >>> 是否在时间段内('08:00:00', '18:00:00', '07:59:59')
        False
        >>> 是否在时间段内('08:00:00', '18:00:00', '08:00:00')
        True
        >>> 是否在时间段内('08:00:00', '18:00:00', '18:00:00')
        True
        >>> 是否在时间段内('23:00:00', '01:00:00', '23:30:00')
        True
        >>> 是否在时间段内('23:00:00', '01:00:00', '00:30:00')
        True
        >>> 是否在时间段内('23:00:00', '01:00:00', '02:00:00')
        False
        >>> 是否在时间段内('24:00:00', '00:00:00', '00:00:00')
        True
        >>> 是否在时间段内('00:00:00', '24:00:00', '12:34:56')
        True
        >>> 是否在时间段内('12:34:56', '12:34:56', '12:34:56')
        True
        >>> 是否在时间段内('12:34:55', '12:34:55', '12:34:56')
        False
        >>> 是否在时间段内('23:00:00', '08:00:00', '23:30:56')
        True
        >>> 是否在时间段内('23:00:00', '08:00:00', '00:00:00')
        True
        >>> 是否在时间段内('23:00:00', '08:00:00', '07:30:56')
        True
        >>> 是否在时间段内('23:00:00', '08:00:00', '21:30:56')
        False
        >>> 是否在时间段内('23:00:00', '08:00:00', '08:01:00')
        False
        >>> 是否在时间段内('23:00:00', '08:00:00', '13:01:00')
        False
    """
    # 确定当前时间
    if 当前时间 is None:
        当前时间 = time_now()

    # 辅助函数：将时间字符串转换为秒数
    def to_seconds(time_str: str) -> int:
        hours, minutes, seconds = map(int, time_str.split(":"))
        return hours * 3600 + minutes * 60 + seconds

    # 转换所有时间为秒数
    start_sec = to_seconds(起始时间)
    end_sec = to_seconds(结束时间)
    current_sec = to_seconds(当前时间)

    # 判断当前时间是否在时间段内
    if start_sec <= end_sec:
        return start_sec <= current_sec <= end_sec
    else:
        return current_sec >= start_sec or current_sec <= end_sec


def generate_health_audio_filename(
    time_format="weekday", content_templates="{0}健康资讯每日听.mp3"
):
    """
    生成健康资讯音频的文件名，适配中老年用户和微信文件场景

    参数:
        time_format: 时间格式，可选"weekday"(默认，如"周一")或"month_day"(如"11.10")

    返回:
        字符串，生成的文件名（含.mp3后缀）
    """
    # 1. 定义时间标识（周几/月.日）
    today = datetime.datetime.today()

    # 周几格式（如"周一"到"周日"）
    weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_map[today.weekday()]  # today.weekday()返回0-6，对应周一到周日

    # 月.日格式（如"11.10"）
    month_day = today.strftime("%m.%d")  # %m是两位数月份，%d是两位数日期

    # 根据格式选择时间前缀
    time_prefix = weekday if time_format == "weekday" else month_day

    # 4. 组合文件名
    return content_templates.format(time_prefix)


if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))


