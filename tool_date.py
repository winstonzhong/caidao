'''
Created on 2020年12月2日

@author: winston
'''
import datetime
from time import strptime, mktime
import time

import numpy
import pytz



TIME_ZONE_SHANGHAI = pytz.timezone('Asia/Shanghai')


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

def n年前(n):
    return dash_date(今天() - datetime.timedelta(days=n*365))

def first_day_of_month():
    return today()[:-2] + '01'
    
def to_code(symbol):
    return int(symbol[:6])

def to_symbol_tt(code):
    code = full_ticker(code)
    return 'sh%s'%code if code[:1] in ['5', '6', '9'] or code[:2] in ['11', '13'] else 'sz%s'% code

def to_symbol_sina(code):
    '''
    >>> to_symbol_sina(1)
    'sz000001'
    >>> to_symbol_sina(830779)
    'bj830779'
    >>> to_symbol_sina(689009)
    'sh689009'
    >>> to_symbol_sina('689009')
    'sh689009'
    '''
    code = full_ticker(code)
    if code[:1] in ['5', '6', '9']:
        return 'sh' + code
     
    if code[:2] in ['11', '13']:
        return 'sh' + code
    
    if code[:1] in ['0', '3']:
        return 'sz' + code
    
    if code[:1] in ['4', '8']:
        return 'bj' + code
    
    raise ValueError

def to_symbol(code):
    code = full_ticker(code)
    return '%s.SH'%code if code[:1] in ['5', '6', '9'] or code[:2] in ['11', '13'] else '%s.SZ'%code

def ticker_to_code(code):
    '''
    >>> ticker_to_code(1)
    'sz000001'
    '''
    from tushare.stock.cons import _code_to_symbol
    return _code_to_symbol(full_ticker(code))

def full_ticker(code):
    '''
    >>> full_ticker(22)
    '000022'
    >>> full_ticker("112233")
    '112233'
    '''
    return "%06d" % int(code)


def neat_ticker(code):
    '''
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
    '''
    return str(int(code))


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

def tight_date(tdate):
    '''
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
    '''
    if tdate:
        if isinstance(tdate, datetime.datetime) or isinstance(tdate, datetime.date):
            tdate = tdate.strftime("%Y%m%d")
        elif '-' in tdate:
            tdate = datetime.datetime.fromtimestamp(mktime(strptime(tdate, "%Y-%m-%d"))).strftime("%Y%m%d")
    return tdate

def to_date(date):
    '''
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
    '''
    if isinstance(date, datetime.datetime):
        return date.date()
    if isinstance(date, datetime.date):
        return date
    try:
        return datetime.datetime.fromtimestamp(mktime(strptime(dash_date(date)[:10], "%Y-%m-%d"))).date()
    except:
        pass

def is_half_year_old(tdate):
    d = datetime.datetime.now(TIME_ZONE_SHANGHAI).date() - to_date(tdate)
    return d.days >= 180

def get_date_half_year_old():
    return datetime.datetime.now(TIME_ZONE_SHANGHAI).date() - datetime.timedelta(days=180)


def isnan(v):
    '''
    >>> isnan(1)
    False
    >>> isnan(None)
    False
    >>> isnan('111')
    False
    >>> isnan(numpy.nan)
    True
    '''
    try:
        return numpy.isnan(v)
    except:
        return False    

def none2nan(v):
    '''c
    >>> none2nan(None)
    nan
    >>> none2nan(1) == 1
    True
    >>> none2nan(0) == 0
    True
    '''    
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

if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
