'''
Created on 2024年2月24日

@author: lenovo
'''

import re

import pandas

from tool_rect import Rect


ptn_session_name = re.compile('\(\d+\)$')

def clean_session_name(line):
    '''
    >>> clean_session_name('主流程测试(5)')
    '主流程测试'
    >>> clean_session_name('主流程测试(5)1')
    '主流程测试(5)1'
    '''
    return ptn_session_name.sub('',line)

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
    



if __name__ == '__main__':
    import doctest
    import numpy
    print(doctest.testmod(verbose=False, report=False))
