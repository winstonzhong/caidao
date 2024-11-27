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
    >>> 得到后缀('.amr')
    'amr'
    '''
    l = fpath.rsplit('.', maxsplit=1)
    return '' if len(l) < 2 else l[-1]

def 得到一个不重复的文件路径(fpath=''):
    time.sleep(0.01)
    后缀 = 得到后缀(fpath)
    后缀 = f'.{后缀}' if 后缀 else ''
    return f'{os.path.join(当前路径(), str(time.time()))}{后缀}'
    
def 路径到链接(fpath):
    '''
    >>> 路径到链接(fpath1)
    'https://file.j1.sale/api/file/test/x.jpg'
    '''
    return fpath.lower().replace('\\', '/').replace(BASE_DIR_56T, BASE_URL_56T)

def 存储文件(content, suffix):
    fpath = 得到一个不重复的文件路径(f'.{suffix}')
    with open(fpath, 'wb') as fp:
        fp.write(content)
    return 路径到链接(fpath)

def 链接到路径(url):
    '''
    >>> 链接到路径('https://file.j1.sale/api/file/2024-11-26/1732629182.2386892.amr')
    'v:/file/2024-11-26/1732629182.2386892.amr'
    '''
    assert url.startswith(BASE_URL_56T)
    return url.replace(BASE_URL_56T,BASE_DIR_56T)

if __name__ == '__main__':
    import doctest
    fpath1 = r'v:\file\test\x.jpg'
    print(doctest.testmod(verbose=False, report=False))
