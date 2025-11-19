"""
Created on 2023年11月3日

@author: lenovo
"""

from datetime import timedelta
import datetime
import re
from time import strptime, mktime


from django.utils import timezone
import pandas
import pytz

from tool_env import is_string, to_float

# from tool_ffmpeg import to_seconds
# import numpy
from decimal import Decimal, InvalidOperation
import time


# from django.utils import timezone as datetime
# from datetime import timedelta
TIME_ZONE_SHANGHAI = pytz.timezone("Asia/Shanghai")

# TIME_ZONE_CN = pytz.timezone('UTC+8')


ptn_chinese_datetime1 = re.compile(
    "(\d{4}年\d{1,2}月\d{1,2}日)*\s*([^\d]{0,2})(\d{1,2}):(\d{1,2})"
)
ptn_chinese_datetime2 = re.compile("([^\s]+)*\s*([^\d]{0,2})(\d{1,2}):(\d{1,2})", re.U)

ptn_chinese_date1 = re.compile("(\d{4})年(\d{1,2})月(\d{1,2})日")
ptn_chinese_date2 = re.compile("(\d{4})*(\d{1,2})月(\d{1,2})日")

WEEKDAY_MAP = {
    "周一": 0,
    "周二": 1,
    "周三": 2,
    "周四": 3,
    "周五": 4,
    "周六": 5,
    "周日": 6,
}

units = {
    60: "分",
    60 * 60: "小时",
    60 * 60 * 24: "天",
    60 * 60 * 24 * 7: "周",
    60 * 60 * 24 * 30: "月",
    60 * 60 * 24 * 365: "年",
}


def seconds_to_friendly_unit(seconds):
    """
    >>> seconds_to_friendly_unit(1)
    '1秒'
    >>> seconds_to_friendly_unit(120)
    '2分'
    >>> seconds_to_friendly_unit(3620)
    '1小时'
    >>> seconds_to_friendly_unit(13620)
    '3小时'
    >>> seconds_to_friendly_unit(113620)
    '1天'
    """
    k_last = 1
    v_last = "秒"
    for k, v in units.items():
        if seconds < k:
            return "%d%s" % (seconds / k_last, v_last)
        k_last = k
        v_last = v


def get_firendly_display(dt_utc):
    return seconds_to_friendly_unit((timezone.now() - dt_utc).total_seconds())


def shanghai_time_now():
    return datetime.datetime.now(TIME_ZONE_SHANGHAI)  # .strftime("%H:%M:%S")


def shanghai_time_now_str():
    return shanghai_time_now().strftime("%H:%M:%S")


def 北京月日():
    return shanghai_time_now().strftime("%m-%d")


def time_now():
    return shanghai_time_now_str()


def shanghai_yesterday():
    return shanghai_time_now() - datetime.timedelta(days=1)


def shanghai_today():
    return dash_date(shanghai_time_now())


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


def from_dashdate(line):
    if isinstance(line, datetime.datetime) or isinstance(line, datetime.date):
        return line
    # return datetime.datetime.fromtimestamp(mktime(strptime(line, "%Y-%m-%d")))
    return datetime.datetime.strptime(line, "%Y-%m-%d")


def to_date(line):
    return from_dashdate(dash_date(line)).date()


def get_today(today=None):
    return from_dashdate(today) if today is not None else shanghai_time_now()


def get_weekday(name, today=None):
    """
    >>> get_weekday('周一', '2024-02-23')
    datetime.datetime(2024, 2, 19, 0, 0)
    >>> get_weekday('周二', '2024-02-23')
    datetime.datetime(2024, 2, 20, 0, 0)
    """
    v = WEEKDAY_MAP.get(name)
    assert v is not None
    today = get_today(today)
    while 1:
        today -= datetime.timedelta(days=1)
        if today.weekday() == v:
            return today


def from_datename(name, today=None):
    """
    >>> from_datename('昨天', '2022-01-01')
    datetime.datetime(2021, 12, 31, 0, 0)
    >>> from_datename('周一', '2024-01-01')
    datetime.datetime(2023, 12, 25, 0, 0)
    >>> from_datename('天天', '2024-01-01') # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ValueError:
    """
    if name == "昨天":
        return get_today(today) - datetime.timedelta(days=1)

    if WEEKDAY_MAP.get(name) is not None:
        return get_weekday(name, today)

    raise ValueError(name, today)


def split_chinese_datetime(line):
    """
    >>> split_chinese_datetime('2023年12月21日 晚上23:32')
    ('2023年12月21日', '晚上', '23', '32')
    >>> split_chinese_datetime('晚上23:32')
    (None, '晚上', '23', '32')
    >>> split_chinese_datetime('下午2:56')
    (None, '下午', '2', '56')
    >>> split_chinese_datetime('昨天 晚上11:43')
    ('昨天', '晚上', '11', '43')
    >>> split_chinese_datetime('上午11:39')
    (None, '上午', '11', '39')
    >>> split_chinese_datetime('周二 09:39')
    ('周二', '', '09', '39')
    >>> split_chinese_datetime('2月15日 上午10:12')
    ('2月15日', '上午', '10', '12')
    >>> split_chinese_datetime('2月15日 晚上10:12')
    ('2月15日', '晚上', '10', '12')
    >>> split_chinese_datetime('1月21日 中午12:38')
    ('1月21日', '中午', '12', '38')
    >>> split_chinese_datetime('2:56')
    (None, '', '2', '56')
    >>> split_chinese_datetime('公交卡余额不足')
    """
    m = ptn_chinese_datetime1.match(line) or ptn_chinese_datetime2.match(line)
    return m.groups() if m is not None else None


def chinese_to_date(line, today=None):
    """
    >>> chinese_to_date('2023年12月21日')
    datetime.datetime(2023, 12, 21, 0, 0)
    >>> chinese_to_date('12月21日', today='2024-01-01')
    datetime.datetime(2024, 12, 21, 0, 0)
    >>> chinese_to_date('昨天', today='2024-01-01')
    datetime.datetime(2023, 12, 31, 0, 0)
    >>> chinese_to_date('周二', today='2024-02-23')
    datetime.datetime(2024, 2, 20, 0, 0)
    """
    today = get_today(today)
    if not line:
        return today

    ptn_chinese_date1 = re.compile("(\d{4})年(\d{1,2})月(\d{1,2})日")
    ptn_chinese_date2 = re.compile("(\d{4})*(\d{1,2})月(\d{1,2})日")
    m = ptn_chinese_date1.match(line) or ptn_chinese_date2.match(line)

    if m is not None:
        year, month, day = m.groups()
        year = year if year else today.year
        return from_dashdate("%d-%02d-%02d" % (int(year), int(month), int(day)))
    return from_datename(line, today)


def convert_chinese_datetime(line, today=None):
    """
    >>> import numpy
    >>> convert_chinese_datetime('2023年12月21日 晚上23:32', today='2024-02-23')
    datetime.datetime(2023, 12, 21, 23, 32, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('晚上23:32', today='2024-02-23')
    datetime.datetime(2024, 2, 23, 23, 32, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('下午2:56', today='2024-02-23')
    datetime.datetime(2024, 2, 23, 14, 56, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('昨天 晚上11:43', today='2024-02-23')
    datetime.datetime(2024, 2, 22, 23, 43, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('上午11:39', today='2024-02-23')
    datetime.datetime(2024, 2, 23, 11, 39, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('周二 09:39', today='2024-02-23')
    datetime.datetime(2024, 2, 20, 9, 39, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('2月15日 上午10:12', today='1975-02-23')
    datetime.datetime(1975, 2, 15, 10, 12, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('2月15日 晚上10:12', today='2024-02-23')
    datetime.datetime(2024, 2, 15, 22, 12, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('1月21日 中午12:38', today='2024-02-23')
    datetime.datetime(2024, 1, 21, 12, 38, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('2:56', today='2024-02-23')
    datetime.datetime(2024, 2, 23, 2, 56, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('周四 10:47', today='2024-02-24')
    datetime.datetime(2024, 2, 22, 10, 47, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('凌晨12:34', today='2024-05-01')
    datetime.datetime(2024, 5, 1, 0, 34, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('凌晨1:50', today='2024-05-01')
    datetime.datetime(2024, 5, 1, 1, 50, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime(numpy.nan)
    nan
    >>> convert_chinese_datetime(None)
    >>> convert_chinese_datetime('周四 10:45 ', today='2025-10-10')
    datetime.datetime(2025, 10, 9, 10, 45, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> convert_chinese_datetime('受苦不吃亏')
    """
    if pandas.isnull(line) or not is_string(line):
        return line
    r = split_chinese_datetime(line)
    if r is None:
        return None
    cd, name, hour, minute = r
    d = chinese_to_date(cd, today)
    d = datetime.datetime(year=d.year, month=d.month, day=d.day)

    d = TIME_ZONE_SHANGHAI.localize(d)

    hour = int(hour)
    minute = int(minute)

    if name in ("晚上", "下午") and hour < 12:
        hour = (int(hour) + 12) % 24

    elif name == "凌晨" and hour == 12:
        hour = 0

    seconds = hour * 3600 + minute * 60
    return d + timedelta(seconds=seconds)


def convert_time_utc(s):
    if s.dt.tz is not None:
        return s.dt.tz_convert("utc")
    return s.dt.tz_localize(tz="utc")


def is_between(v, start, end, include_equal=True):
    """
    >>> is_between(1, 1, 2)
    True
    >>> is_between(1, 1, 2, False)
    False
    >>> is_between(1, 6, 2)
    False
    >>> is_between(1, 6, 2, False)
    False
    """
    if include_equal:
        return v <= max(start, end) and v >= min(start, end)
    return v < max(start, end) and v > min(start, end)


def friendly_time_expression(dt):
    """
    将输入的datetime值根据当天时间转换为用户友好的时间表达。

    Args:
        dt (datetime.datetime): 输入的datetime值。

    Returns:
        str: 用户友好的时间表达。

    Examples:
        >>> friendly_time_expression(datetime.datetime.now())
        '刚刚'
        >>> friendly_time_expression(datetime.datetime.now() - datetime.timedelta(minutes=5))
        '5分钟前'
        >>> friendly_time_expression(datetime.datetime.now() - datetime.timedelta(hours=1))
        '1小时前'
        >>> friendly_time_expression(datetime.datetime.now() - datetime.timedelta(days=1))
        '1天前'
        >>> friendly_time_expression(datetime.datetime.now() - datetime.timedelta(days=7))
        '1周前'
        >>> friendly_time_expression(datetime.datetime.now() - datetime.timedelta(days=30))
        '1个月前'
        >>> friendly_time_expression(datetime.datetime.now() - datetime.timedelta(days=365))
        '1年前'
    """
    now = datetime.datetime.now()
    delta = now - dt

    if delta.total_seconds() < 60:
        return "刚刚"
    elif delta.total_seconds() < 3600:
        return f"{int(delta.total_seconds() // 60)}分钟前"
    elif delta.total_seconds() < 86400:
        return f"{int(delta.total_seconds() // 3600)}小时前"
    elif delta.days < 7:
        return f"{delta.days}天前"
    elif delta.days < 30:
        return f"{delta.days // 7}周前"
    elif delta.days < 365:
        return f"{delta.days // 30}个月前"
    else:
        return f"{delta.days // 365}年前"


def 获取前一天0点的时间戳(日期):
    """
    获取前一天0点的时间戳。

    Args:
        日期 (str): 日期。

    Returns:
        int: 前一天0点的时间戳。

    Examples:
        >>> 获取前一天0点的时间戳("2023-11-03")
        1698854400
    """
    return int(
        (datetime.datetime.strptime(日期, "%Y-%m-%d") - datetime.timedelta(days=1))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )


def 获取当前日期的0点时间戳(日期=None):
    """
    获取当前日期的0点时间戳。

    Args:
        日期 (str): 日期。

    Returns:
        int: 当前日期的0点时间戳。

    Examples:
        >>> 获取当前日期的0点时间戳("2023-11-03")
        1698940800
    """
    日期 = 日期 or datetime.datetime.now().strftime("%Y-%m-%d")
    return int(
        datetime.datetime.strptime(日期, "%Y-%m-%d")
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )


def 解析一般格式日期时间(time_str):
    """
    >>> 解析一般格式日期时间('Sat, 29 Mar 2025 11:16:00 GMT')
    datetime.datetime(2025, 3, 29, 11, 16, tzinfo=zoneinfo.ZoneInfo(key='GMT'))
    """
    from zoneinfo import ZoneInfo

    try:
        # 定义时间格式
        time_format = "%a, %d %b %Y %H:%M:%S %Z"
        # 解析时间字符串
        naive_dt = datetime.datetime.strptime(time_str, time_format)
        aware_dt = naive_dt.replace(tzinfo=ZoneInfo("GMT"))
        return aware_dt
    except ValueError as e:
        print(f"解析时间字符串失败：{e}")


def convert_time_description_to_seconds(description):
    """
    将定时任务描述转换为以秒为单位的时间。

    参数:
        description (str): 定时任务描述，格式为 "every n unit"，例如 "every 2 seconds"。

    返回:
        int: 对应的秒数。

    示例:
        >>> convert_time_description_to_seconds("2")
        2
        >>> convert_time_description_to_seconds("2 seconds")
        2
        >>> convert_time_description_to_seconds("every 2 seconds")
        2
        >>> convert_time_description_to_seconds("every 1 minute")
        60
        >>> convert_time_description_to_seconds("every 2 minute")
        120
        >>> convert_time_description_to_seconds("every 1 hour")
        3600
        >>> convert_time_description_to_seconds("every 1 day")
        86400
        >>> convert_time_description_to_seconds("every 1 week")
        604800
        >>> convert_time_description_to_seconds("every 3 months")
        7776000
        >>> convert_time_description_to_seconds("every 1 year")
        31536000
        >>> convert_time_description_to_seconds("every abc seconds")
        Traceback (most recent call last):
          ...
        ValueError: 描述中的数字部分必须是有效的整数。
        >>> convert_time_description_to_seconds("abc 2 seconds")
        Traceback (most recent call last):
          ...
        ValueError: 输入的描述格式不正确，应遵循 'every n unit' 的格式。
        >>> convert_time_description_to_seconds("every 1 abc")
        Traceback (most recent call last):
          ...
        ValueError: 不支持的时间单位: abc
        >>> convert_time_description_to_seconds("seconds")
        Traceback (most recent call last):
          ...
        ValueError: 描述中的数字部分必须是有效的整数。
    """
    parts = re.split("\s+", description.strip())

    if len(parts) != 3:
        try:
            return int(parts[0])
        except ValueError:
            raise ValueError("描述中的数字部分必须是有效的整数。")

    if len(parts) != 3 or parts[0] != "every":
        raise ValueError("输入的描述格式不正确，应遵循 'every n unit' 的格式。")
    try:
        number = int(parts[1])
    except ValueError:
        raise ValueError("描述中的数字部分必须是有效的整数。")
    unit = parts[2].lower()
    if unit.endswith("s"):
        unit = unit[:-1]
    conversion = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400,
        "week": 604800,
        "month": 2592000,  # 按照 30 天估算
        "year": 31536000,
    }
    if unit not in conversion:
        raise ValueError(f"不支持的时间单位: {unit}")
    return number * conversion[unit]


def 岁数转生日(年龄):
    return datetime.date.today() - datetime.timedelta(days=365 * 年龄)


def 生日转岁数(生日, today=None):
    """
    >>> 生日转岁数(datetime.date(2000, 1, 1), today='2025-06-06')
    25
    >>> 生日转岁数(datetime.date(2200, 1, 1), today='2025-06-05')
    0
    >>> 生日转岁数('1975-06-25', today='2025-06-05')
    50
    >>> 生日转岁数('1975-06-25') > 0
    True
    """
    today = datetime.date.today() if today is None else to_date(today)
    age = today.year - to_date(生日).year
    return age if age >= 0 else 0


def time_str_to_seconds(time_str: str) -> int:
    """
    将时间字符串（格式HH:MM:SS）转换为当天0点开始的总秒数。

    参数:
        time_str: 时间字符串，必须符合HH:MM:SS格式（如"12:00:30"）

    返回:
        int: 从当天0点到该时间的总秒数

    异常:
        ValueError: 若输入格式错误或数值超出合理范围（如小时>23），则抛出此异常

    示例:
        >>> time_str_to_seconds("00:00:00")  # 0点0分0秒
        0
        >>> time_str_to_seconds("01:00:00")  # 1小时=3600秒
        3600
        >>> time_str_to_seconds("12:00:30")  # 12*3600 + 0*60 +30
        43230
        >>> time_str_to_seconds("23:59:59")  # 当天最后一秒
        86399
        >>> time_str_to_seconds("00:01:01")  # 1分1秒=61秒
        61
        >>> time_str_to_seconds("12:34:56")  # 12*3600 +34*60 +56
        45296
        >>> time_str_to_seconds("12:00")  # 格式错误（缺少秒）
        Traceback (most recent call last):
        ...
        ValueError: 时间格式错误，请使用HH:MM:SS格式
        >>> time_str_to_seconds("25:00:00")  # 小时超出范围（25>23）
        Traceback (most recent call last):
        ...
        ValueError: 时间数值超出范围，小时0-23，分钟和秒0-59
        >>> time_str_to_seconds("12:60:00")  # 分钟超出范围（60>59）
        Traceback (most recent call last):
        ...
        ValueError: 时间数值超出范围，小时0-23，分钟和秒0-59
    """
    # 分割时间字符串为小时、分钟、秒
    parts = time_str.split(":")

    # 验证格式是否为3个部分
    if len(parts) != 3:
        raise ValueError("时间格式错误，请使用HH:MM:SS格式")

    try:
        # 转换为整数
        hours, minutes, seconds = map(int, parts)
    except ValueError:
        raise ValueError("时间格式错误，时、分、秒必须为整数")

    # 验证数值范围
    if not (0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60):
        raise ValueError("时间数值超出范围，小时0-23，分钟和秒0-59")

    # 计算总秒数
    return hours * 3600 + minutes * 60 + seconds


def time_str_to_percentage(time_str: str, decimal_places: int = 2) -> float:
    """
    将时间字符串（格式HH:MM:SS）转换为当天已流逝时间的百分比（0.0%~100.0%）。

    计算逻辑：
        时间百分比 = (当前时间秒数 ÷ 一天总秒数) × 100
        其中，一天总秒数 = 24×3600 = 86400

    参数:
        time_str: 时间字符串，必须符合HH:MM:SS格式（如"12:00:30"）
        decimal_places: 百分比结果保留的小数位数，默认2位

    返回:
        float: 当天时间百分比（如12:00:00返回50.0）

    异常:
        ValueError: 若输入时间字符串格式错误或数值超出范围（继承自time_str_to_seconds）
    >>> time_str_to_percentage("00:00:00")  # 0点0分0秒
    0.0
    >>> time_str_to_percentage("12:00:00")
    0.5
    >>> time_str_to_percentage("23:59:59")
    1.0
    """
    # 1. 复用函数获取当前时间的秒数
    current_seconds = time_str_to_seconds(time_str)
    # 2. 一天的总秒数（固定值：24小时×3600秒/小时）
    total_seconds_per_day = 24 * 3600  # 86400
    # 3. 计算百分比并保留指定小数位数
    percentage = current_seconds / total_seconds_per_day
    return round(percentage, decimal_places)


def 中文时长描述转秒数(描述):
    """
    将中文时长描述转换为对应的秒数。

    >>> 中文时长描述转秒数('3小时')
    10800
    >>> 中文时长描述转秒数('45分钟')
    2700
    >>> 中文时长描述转秒数('50秒')
    50
    >>> 中文时长描述转秒数('2小时10分钟')
    7800
    >>> 中文时长描述转秒数('1小时30秒')
    3630
    >>> 中文时长描述转秒数('5分钟20秒')
    320
    >>> 中文时长描述转秒数('1小时2分钟3秒')
    3723
    >>> 中文时长描述转秒数('10小时20分钟30秒')
    37230
    >>> 中文时长描述转秒数('0小时5分钟')
    300
    >>> 中文时长描述转秒数('3小时0分钟10秒')
    10810
    >>> 中文时长描述转秒数('10分钟1小时')
    4200
    >>> 中文时长描述转秒数('5秒2小时3分钟')
    7385
    >>> 中文时长描述转秒数('0秒')
    0
    >>> 中文时长描述转秒数('')
    0
    >>> 中文时长描述转秒数('123')
    0
    >>> 中文时长描述转秒数(None)
    0
    """
    if not 描述:
        return 0
    小时 = 0
    分钟 = 0
    秒 = 0

    # 提取小时数值
    匹配小时 = re.search(r"(\d+)小时", 描述)
    if 匹配小时:
        小时 = int(匹配小时.group(1))

    # 提取分钟数值
    匹配分钟 = re.search(r"(\d+)分钟", 描述)
    if 匹配分钟:
        分钟 = int(匹配分钟.group(1))

    # 提取秒数值
    匹配秒 = re.search(r"(\d+)秒", 描述)
    if 匹配秒:
        秒 = int(匹配秒.group(1))

    # 计算总秒数
    return 小时 * 3600 + 分钟 * 60 + 秒


def 中文时长描述转小时数(描述, 保留小数点位数=None):
    """
    将中文时长描述转换为对应的小时数（使用decimal保证精度），并支持指定保留小数点位数。

    参数:
        描述: 中文时长描述字符串（如'5小时19分钟'、'30秒'等）
        保留小数点位数: 非负整数或None，指定返回结果保留的小数位数，
                        默认为None（返回高精度原始值）

    返回:
        转换后的小时数（decimal.Decimal类型）

    >>> 中文时长描述转小时数('3小时')
    Decimal('3')
    >>> 中文时长描述转小时数('60分钟')
    Decimal('1')
    >>> 中文时长描述转小时数('3600秒')
    Decimal('1')
    >>> 中文时长描述转小时数('1小时30分钟')  # 1.5小时
    Decimal('1.5')
    >>> 中文时长描述转小时数('2小时15分钟30秒')  # 2 + 15/60 + 30/3600 = 2.258333...
    Decimal('2.258333333333333333333333333')
    >>> 中文时长描述转小时数('0秒')
    Decimal('0')
    >>> 中文时长描述转小时数('')
    Decimal('0')
    >>> 中文时长描述转小时数('123')  # 无有效单位
    Decimal('123')
    >>> 中文时长描述转小时数('30分钟', 保留小数点位数=0)  # 0.5四舍五入为1
    Decimal('0')
    >>> 中文时长描述转小时数('45分钟', 保留小数点位数=1)  # 0.75保留1位→0.8
    Decimal('0.8')
    >>> 中文时长描述转小时数('1小时20分钟', 保留小数点位数=2)  # 1.333...保留2位→1.33
    Decimal('1.33')
    >>> 中文时长描述转小时数('5秒', 保留小数点位数=5)  # 5/3600≈0.0013888...保留5位→0.00139
    Decimal('0.00139')
    >>> 中文时长描述转小时数('10分钟', 保留小数点位数=-1)  # 无效参数（负数）
    Traceback (most recent call last):
    ...
    ValueError: 保留小数点位数必须是非负整数或None
    >>> 中文时长描述转小时数('1小时', 保留小数点位数=2.5)  # 无效参数（非整数）
    Traceback (most recent call last):
    ...
    ValueError: 保留小数点位数必须是非负整数或None
    """

    小时数 = to_float(描述)
    if 小时数 is None:
        # 1. 调用原函数获取总秒数
        总秒数 = 中文时长描述转秒数(描述)

        # 2. 转换为小时数（使用Decimal保证高精度）
        小时数 = Decimal(总秒数) / Decimal(3600)  # 除法用Decimal避免精度损失
    else:
        # 直接使用传入的数字作为小时数
        小时数 = Decimal(小时数)

    # 3. 处理保留小数点位数
    if 保留小数点位数 is None:
        return 小时数
    else:
        # 校验参数合法性
        if not isinstance(保留小数点位数, int) or 保留小数点位数 < 0:
            raise ValueError("保留小数点位数必须是非负整数或None")

        # 构造精度格式（如保留2位→'0.00'）
        精度格式 = Decimal("0." + "0" * 保留小数点位数)

        # 使用quantize进行精确四舍五入（比round更可靠的十进制处理）
        try:
            return 小时数.quantize(精度格式)
        except InvalidOperation as e:
            raise ValueError(f"无法保留{保留小数点位数}位小数：{e}")





if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
