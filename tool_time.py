'''
Created on 2023年11月3日

@author: lenovo
'''
from datetime import timedelta
import datetime
import re
from time import strptime, mktime

from django.utils import timezone
import pandas
import pytz

from tool_env import is_string
from tool_ffmpeg import to_seconds
import numpy


# from django.utils import timezone as datetime
# from datetime import timedelta
TIME_ZONE_SHANGHAI = pytz.timezone('Asia/Shanghai')

# TIME_ZONE_CN = pytz.timezone('UTC+8')


ptn_chinese_datetime1 = re.compile('(\d{4}年\d{1,2}月\d{1,2}日)*\s*([^\d]{0,2})(\d{1,2}):(\d{1,2})')
ptn_chinese_datetime2 = re.compile('([^\s]+)*\s*([^\d]{0,2})(\d{1,2}):(\d{1,2})', re.U)

ptn_chinese_date1 = re.compile('(\d{4})年(\d{1,2})月(\d{1,2})日') 
ptn_chinese_date2 = re.compile('(\d{4})*(\d{1,2})月(\d{1,2})日')

WEEKDAY_MAP = {
    '周一': 0,
    '周二': 1,
    '周三': 2,
    '周四': 3,
    '周五': 4,
    '周六': 5,
    '周日': 6,
    }

units = {
      60:'分',  
      60*60:'小时',
      60*60*24:'天',
      60*60*24*7:'周',
      60*60*24*30:'月',
      60*60*24*365:'年',
    }

def seconds_to_friendly_unit(seconds):
    '''
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
    '''
    k_last = 1
    v_last = '秒'
    for k, v in units.items():
        if seconds < k:
            return '%d%s' % (seconds / k_last, v_last)
        k_last = k
        v_last = v

def get_firendly_display(dt_utc):
    return seconds_to_friendly_unit((timezone.now() - dt_utc).total_seconds())

def shanghai_time_now():
    return datetime.datetime.now(TIME_ZONE_SHANGHAI)#.strftime("%H:%M:%S")

def shanghai_yesterday():
    return shanghai_time_now() - datetime.timedelta(days=1)

def dash_date(tdate):
    '''
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
    '''
    if tdate:
        if isinstance(tdate, datetime.datetime) or isinstance(tdate, datetime.date):
            tdate = tdate.strftime("%Y-%m-%d")
        elif '-' not in tdate:
            tdate = datetime.datetime.fromtimestamp(mktime(strptime(tdate, "%Y%m%d"))).strftime("%Y-%m-%d")
    return tdate

def from_dashdate(line):
    if isinstance(line, datetime.datetime) or isinstance(line, datetime.date):
        return line
    return datetime.datetime.fromtimestamp(mktime(strptime(line, "%Y-%m-%d")))

def to_date(line):
    return from_dashdate(dash_date(line)).date()

def get_today(today=None):
    return from_dashdate(today) if today is not None else shanghai_time_now()

def get_weekday(name, today=None):
    '''
    >>> get_weekday('周一', '2024-02-23')
    datetime.datetime(2024, 2, 19, 0, 0)
    >>> get_weekday('周二', '2024-02-23')
    datetime.datetime(2024, 2, 20, 0, 0)
    '''
    v = WEEKDAY_MAP.get(name)
    assert  v is not None
    today = get_today(today) 
    while 1:
        today -= datetime.timedelta(days=1)
        if today.weekday() == v:
            return today

def from_datename(name, today=None):
    '''
    >>> from_datename('昨天', '2022-01-01')
    datetime.datetime(2021, 12, 31, 0, 0)
    >>> from_datename('周一', '2024-01-01')
    datetime.datetime(2023, 12, 25, 0, 0)
    >>> from_datename('天天', '2024-01-01') # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ValueError: 
    '''
    if name == '昨天':
        return get_today(today) - datetime.timedelta(days=1)
    
    if WEEKDAY_MAP.get(name) is not None:
        return get_weekday(name, today)
    
    raise ValueError(name, today)

def split_chinese_datetime(line):
    '''
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
    '''
    m = ptn_chinese_datetime1.match(line) or ptn_chinese_datetime2.match(line)
    return m.groups()

def chinese_to_date(line, today=None):
    '''
    >>> chinese_to_date('2023年12月21日')
    datetime.datetime(2023, 12, 21, 0, 0)
    >>> chinese_to_date('12月21日', today='2024-01-01')
    datetime.datetime(2024, 12, 21, 0, 0)
    >>> chinese_to_date('昨天', today='2024-01-01')
    datetime.datetime(2023, 12, 31, 0, 0)
    >>> chinese_to_date('周二', today='2024-02-23')
    datetime.datetime(2024, 2, 20, 0, 0)
    '''
    today = get_today(today)
    if not line:
        return today
        
    ptn_chinese_date1 = re.compile('(\d{4})年(\d{1,2})月(\d{1,2})日')
    ptn_chinese_date2 = re.compile('(\d{4})*(\d{1,2})月(\d{1,2})日')
    m = ptn_chinese_date1.match(line) or ptn_chinese_date2.match(line)
    
    if m is not None:
        year, month, day = m.groups()
        year = year if year else today.year
        return from_dashdate('%d-%02d-%02d' % (int(year), int(month), int(day)))
    return from_datename(line, today)
        

def convert_chinese_datetime(line, today=None):
    '''
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
    '''
    if pandas.isnull(line) or not is_string(line):
        return line
    cd, name, hour, minute =  split_chinese_datetime(line)
    d = chinese_to_date(cd, today)
    d = datetime.datetime(year=d.year, month=d.month, day=d.day)
    
    d = TIME_ZONE_SHANGHAI.localize(d)
    
    hour = int(hour)
    minute = int(minute)

    if name in ('晚上', '下午') and hour < 12:
        hour = (int(hour) + 12) % 24

    elif name == '凌晨' and hour == 12:
        hour = 0

    seconds = hour *3600 + minute * 60
    return d + timedelta(seconds=seconds)


def convert_time_utc(s):
    if s.dt.tz is not None:
        return s.dt.tz_convert('utc')
    return s.dt.tz_localize(tz='utc')


def is_between(v, start, end, include_equal=True):
    '''
    >>> is_between(1, 1, 2)
    True
    >>> is_between(1, 1, 2, False)
    False
    >>> is_between(1, 6, 2)
    False
    >>> is_between(1, 6, 2, False)
    False
    '''
    if include_equal:
        return v <= max(start, end) and v >= min(start, end)
    return v < max(start, end) and v > min(start, end)


if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
    