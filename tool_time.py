'''
Created on 2023年11月3日

@author: lenovo
'''
from django.utils import timezone


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


if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
    