'''
Created on 2024年2月24日

@author: lenovo
'''

import re

import pandas

from tool_rect import Rect
from tool_env import bounds_to_rect


ptn_session_name = re.compile('\(\d+\)$')

def clean_session_name(line):
    '''
    >>> clean_session_name('主流程测试(5)')
    '主流程测试'
    >>> clean_session_name('主流程测试(5)1')
    '主流程测试(5)1'
    >>> clean_session_name(None)
    '''
    return ptn_session_name.sub('',line) if line else None

def clean_head_description(line):
    '''
    >>> clean_head_description('SunnyAftRain头像')
    'SunnyAftRain'
    '''
    return line[:-2]


def two_points_bounds_to_rect(line):
    '''
    >>> two_points_bounds_to_rect('[201,1569][366,1628]')
    201 366 1569 1628<165, 59>
    >>> two_points_bounds_to_rect(None)
    >>> two_points_bounds_to_rect(numpy.nan)
    '''
    if not pandas.isnull(line):
        left,top,right, bottom = filter(lambda x:x, re.split('[^\d]+', line))
        return Rect(left, right, top, bottom)
    

def is_close_to_top(rect, bounds):
    '''
    >>> is_close_to_top(rect_container_chat, "[0,226][1080,308]")
    True
    >>> is_close_to_top(rect_container_chat, "[0,308][1080,745]")
    False
    >>> is_close_to_top(rect_container_chat, "[0,1975][1080,2055]")
    False
    >>> is_close_to_top(rect_container_chat, "[0,1835][1080,1975]")
    False
    >>> is_close_to_top(rect_container_chat, "[0,1899][1080,2039]")
    False
    >>> is_close_to_top(rect_container_chat, "[0,226][1080,557]")
    True
    '''
    return abs(rect.top - bounds_to_rect(bounds).top) <= 1

def is_close_to_bottom(rect, bounds):
    '''
    >>> is_close_to_bottom(rect_container_chat, "[0,226][1080,308]")
    False
    >>> is_close_to_bottom(rect_container_chat, "[0,308][1080,745]")
    False
    >>> is_close_to_bottom(rect_container_chat, "[0,1975][1080,2055]")
    True
    >>> is_close_to_bottom(rect_container_chat, "[0,1835][1080,1975]")
    False
    >>> is_close_to_bottom(rect_container_chat, "[0,1899][1080,2039]")
    False
    >>> is_close_to_bottom(rect_container_chat, "[0,226][1080,557]")
    False
    '''
    return abs(rect.bottom - bounds_to_rect(bounds).bottom) <= 1


def is_not_equal_ignore_null(d1, d2, name):
    '''
    >>> is_not_equal_ignore_null(d_up, d_down, 'type')
    False
    >>> is_not_equal_ignore_null(d_up, d_down, 'text')
    False
    >>> is_not_equal_ignore_null(d_up, d_down, 'role')
    False
    >>> is_not_equal_ignore_null(d_up, d_false, 'type')
    True
    >>> is_not_equal_ignore_null(d_up, d_false, 'from_icon_des')
    False
    >>> is_not_equal_ignore_null({'type':1,}, {'type':2,}, 'type')
    True
    >>> is_not_equal_ignore_null({'type':1,}, {'type':numpy.nan,}, 'type')
    False
    >>> is_not_equal_ignore_null({'type':1,}, {'type':-1,}, 'type')
    False
    '''
    if pandas.isnull(d1.get(name)) or pandas.isnull(d2.get(name)) or d1.get(name) == d2.get(name):
        return False
    if name == 'type' and -1 in (d1.get(name), d2.get(name)):
        return False
    return True 

def is_up_down_same(d1, d2):
    '''
    >>> is_up_down_same(d_up, d_down)
    True
    >>> is_up_down_same(d_down,d_up)
    True
    >>> is_up_down_same(d_down,d_false)
    False
    >>> is_up_down_same(d_up,d_false)
    False
    '''
    if is_not_equal_ignore_null(d1, d2, name='type'):
        return False

    if is_not_equal_ignore_null(d1, d2, name='text'):
        return False

    if is_not_equal_ignore_null(d1, d2, name='role'):
        return False
    
    if (d1.get('upside') and d2.get('underside')) or (d2.get('upside') and d1.get('underside')):
        return True 
    
    return False 

def remove_null(d):
    return {k:v for k, v in d.items() if not pandas.isnull(v)}
    
def merge_up_down(d1, d2):
    '''
    >>> merge_up_down(d_up, d_down).get('send_time')
    123
    >>> merge_up_down(d_down, d_up).get('send_time')
    123
    '''
    assert is_up_down_same(d1, d2)
    d = remove_null(d1)
    d.update(remove_null(d2))
    return d    

def merge_up_down_df(df_up, df_down):
    l_up = df_up.to_dict('records') 
    l_down = df_down.to_dict('records')
    d_up = l_up[-1]
    d_down = l_down[0]
    if is_up_down_same(d_up, d_down):
        d = merge_up_down(d_up, d_down)
        l = l_up[:-1] + [d] + l_down[1:]
    else:
        l = l_up + l_down
    return pandas.DataFrame(l)

if __name__ == '__main__':
    import doctest
    import numpy
    rect_container_chat = Rect(0,1080,226,2055)

    d_up = {'type': 1,
     'big_bounds': '[0,226][1080,308]',
     'upside': True,
     'underside': False,
     'from_icon_des': '钟文栋头像',
     'from_icon_bounds': '[16,226][156,308]',
     'role': 1,
     'text': '第3回测试。',
     'send_time': pandas.NaT,
     'bounds': '[156,226][490,292]'}

    d_down = {'type': 1,
     'big_bounds': '[0,1975][1080,2055]',
     'upside': False,
     'underside': True,
     'role': 1,
     'text': '第3回测试。',
     'bounds': '[156,1991][490,2055]',
     'from_icon_des': '钟文栋头像',
     'send_time': 123,
     'from_icon_bounds': '[16,1975][156,2055]',
     }
    
    d_false = {'type': 3,
     'big_bounds': '[0,226][1080,557]',
     'upside': True,
     'underside': False,
     'role': 0,
     'text': 'InfoQ',
     'bounds': '[167,226][623,541]',
     'from_icon_des': numpy.nan,
     'from_icon_bounds': numpy.nan,
     'send_time': pandas.NaT,
     }
    
    print(doctest.testmod(verbose=False, report=False))
