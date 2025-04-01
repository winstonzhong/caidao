"""
Created on 2024年11月11日

@author: lenovo
"""

import os
import time

from tool_date import today
from helper_net import rget
import random
from tool_env import OS_WIN

BASE_URL_56T = "https://file.j1.sale/api/file"

BASE_DIR_56T = "v:/file" if OS_WIN else "/mnt/56T/file"


def 当前路径(base_dir=BASE_DIR_56T):
    fpath = os.path.join(base_dir, today())
    if not os.path.lexists(fpath):
        os.makedirs(fpath, exist_ok=True)
    return fpath


def 得到后缀(fpath=""):
    """
    >>> 得到后缀('aaa')
    ''
    >>> 得到后缀('aaa.jpg')
    'jpg'
    >>> 得到后缀('ccc.aaa.jpg')
    'jpg'
    >>> 得到后缀('.amr')
    'amr'
    """
    l = fpath.rsplit(".", maxsplit=1)
    return "" if len(l) < 2 else l[-1]


def 得到一个固定文件路径(相对路径, base_dir=BASE_DIR_56T):
    """
    >>> 得到一个固定文件路径('aaa/bbb') == f'{BASE_DIR_56T}/aaa/bbb'
    True
    >>> 得到一个固定文件路径('/aaa/bbb') == f'{BASE_DIR_56T}/aaa/bbb'
    True
    """
    相对路径 = 相对路径.replace("\\", "/")
    相对路径 = 相对路径[1:] if 相对路径.startswith("/") else 相对路径
    return os.path.join(base_dir, 相对路径).replace("\\", "/")


def 得到一个不重复的文件路径(fpath=""):
    time.sleep(0.01)
    后缀 = 得到后缀(fpath)
    后缀 = f".{后缀}" if 后缀 else ""
    # return f'{os.path.join(当前路径(), str(time.time()))}{后缀}'
    name = f"{time.time():.6f}{random.random():.4f}{后缀}"
    return os.path.join(当前路径(), name)


def 路径到链接(fpath, base_dir=BASE_DIR_56T):
    """
    >>> 路径到链接(f'{BASE_DIR_56T}/test/x.jpg')
    'https://file.j1.sale/api/file/test/x.jpg'
    """
    if OS_WIN:
        fpath = fpath.lower()
    return fpath.replace("\\", "/").replace(base_dir, BASE_URL_56T)


def 存储文件(content, suffix, 返回路径=False, base_dir=BASE_DIR_56T):
    fpath = 得到一个不重复的文件路径(f".{suffix}")
    with open(fpath, "wb") as fp:
        fp.write(content)
    return 路径到链接(fpath, base_dir=base_dir) if not 返回路径 else fpath


def 存储链接到文件(url, suffix, 返回路径=False, base_dir=BASE_DIR_56T):
    return 存储文件(rget(url).content, suffix, 返回路径, base_dir=base_dir)


def 链接到路径(url, base_dir=BASE_DIR_56T, safe=True):
    """
    >>> 链接到路径('https://file.j1.sale/api/file/2024-11-26/1732629182.2386892.amr') == f'{BASE_DIR_56T}/2024-11-26/1732629182.2386892.amr'
    True
    """
    if url.startswith(BASE_URL_56T):
        return url.replace(BASE_URL_56T, base_dir)
    elif safe:
        raise ValueError(f"{url}不是56T的链接")


def 链接到相对路径(url, base_dir=BASE_DIR_56T):
    """
    >>> 链接到相对路径('https://file.j1.sale/api/file/2024-11-26/1732629182.2386892.amr')
    'file/2024-11-26/1732629182.2386892.amr'
    """
    return 链接到路径(url, base_dir).replace(os.path.dirname(BASE_DIR_56T)+'/', "")



if __name__ == "__main__":
    import doctest
    fpath1 = r"v:\file\test\x.jpg"
    print(doctest.testmod(verbose=False, report=False))
