'''
Created on 2023年12月19日

@author: lenovo
'''
import numpy
import pandas
from tool_rect import Rect

def find_split_points(s, all_split=False, v_min=0, span_min=None):
    '''
    >>> find_split_points((0,1,1,1,1,1,0))
       0    1
    0  0  6.0
    >>> find_split_points((0,1,1,0,1,1,0))
       0    1
    0  0  3.0
    3  3  6.0
    '''
    s = pandas.Series(s)
    s = s[s <= v_min].index.to_series()
    df = pandas.concat([s, s.shift(-1)], axis=1)
    span = span_min or 1
    df = df[df[1] - df[0] > span]
    if not all_split:
        v = (df[1]-df[0]).std() if span_min is None else span_min
        if not numpy.isnan(v):
            df = df[df[1] - df[0] > v]
    return df

def split_cuizhi(mask, all_split=False, v_min=0, span_min=None):
    df = find_split_points(mask.sum(axis=0),all_split, v_min, span_min).rename(columns={0:'left', 1:'right'}).astype(int)
    return df.to_dict('records')

def split_shuiping(mask, all_split=False, v_min=0, span_min=None):
    df = find_split_points(mask.sum(axis=1),all_split, v_min, span_min).rename(columns={0:'top', 1:'bottom'}).astype(int)
    return df.to_dict('records')
    
def split_smart(mask, all_split=False, v_min=0, span_min=None):
    for x in split_shuiping(mask,all_split, v_min, span_min):
        for y in split_cuizhi(mask,all_split, v_min, span_min):
            tmp = y.copy()
            tmp.update(x)
            if Rect(**tmp).crop_img(mask).sum() > 0:
                yield tmp
                
if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
                