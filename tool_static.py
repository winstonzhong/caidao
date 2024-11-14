'''
Created on 2024年11月11日

@author: lenovo
'''
import os
import time

from tool_date import today


BASE_URL_56T = 'https://file.j1.sale/api/file'
BASE_DIR_56T = 'v:/file'


def 当前路径():
    fpath = os.path.join(BASE_DIR_56T, today())
    if not os.path.lexists(fpath):
        os.makedirs(fpath, exist_ok=True)
    return fpath

def 得到后缀(fpath=''):
    '''
    >>> 得到后缀('aaa')
    ''
    >>> 得到后缀('aaa.jpg')
    'jpg'
    >>> 得到后缀('ccc.aaa.jpg')
    'jpg'
    '''
    l = fpath.rsplit('.', maxsplit=1)
    return '' if len(l) < 2 else l[-1]

def 得到一个不重复的文件路径(fpath=''):
    time.sleep(0.01)
    return f'{os.path.join(当前路径(), str(time.time()))}.{得到后缀(fpath)}'
    
def 路径到链接(fpath):
    '''
    >>> 路径到链接(fpath1)
    'https://file.j1.sale/api/file/test/x.jpg'
    '''
    return fpath.lower().replace('\\', '/').replace(BASE_DIR_56T, BASE_URL_56T)

if __name__ == '__main__':
    import doctest
    fpath1 = r'v:\file\test\x.jpg'
    print(doctest.testmod(verbose=False, report=False))
