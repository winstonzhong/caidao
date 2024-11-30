'''
Created on 2024年11月11日

@author: lenovo
'''
import os
import time

from tool_date import today
from helper_net import rget


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

def 得到一个固定文件路径(相对路径):
    '''
    >>> 得到一个固定文件路径('aaa/bbb')
    'v:/file/aaa/bbb'
    >>> 得到一个固定文件路径('/aaa/bbb')
    'v:/file/aaa/bbb'
    '''
    相对路径 = 相对路径.replace('\\','/')
    相对路径 = 相对路径[1:] if 相对路径.startswith('/') else 相对路径
    return os.path.join(BASE_DIR_56T,相对路径).replace('\\','/')

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

def 存储文件(content, suffix, 返回路径=False):
    fpath = 得到一个不重复的文件路径(f'.{suffix}')
    with open(fpath, 'wb') as fp:
        fp.write(content)
    return 路径到链接(fpath) if not 返回路径 else fpath

def 存储链接到文件(url, suffix, 返回路径=False):
    return 存储文件(rget(url).content, suffix, 返回路径)

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
