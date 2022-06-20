'''
Created on 2022年6月3日

@author: Administrator
'''
import platform
import re


OS_WIN = platform.system() == 'Windows'

ptn_chinese = re.compile('[\u4e00-\u9fff]')


def is_chinese(ch):
    return '\u4e00' <= ch <= '\u9fff'


def has_chinese(line):
    for ch in line:
        if is_chinese(ch):
            return True
    return False


def split_df(df, batch_size=1000):
    for x in range(0, len(df), batch_size):
        yield df.iloc[x:x + batch_size]


def pct_chinese(line):
    '''
    >>> pct_chinese('') == 0
    True
    >>> pct_chinese(None) == 0
    True
    >>> pct_chinese('1') == 0
    True
    >>> pct_chinese('1人') == 50
    True
    >>> pct_chinese('人家') == 100
    True
    '''
    if line and len(line) > 0:
        tmp = ptn_chinese.sub('', line)
        return int((1 - len(tmp) / len(line)) * 100)
    return 0


if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
