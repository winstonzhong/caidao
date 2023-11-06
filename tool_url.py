'''
Created on 2023年10月17日

@author: lenovo
'''
import os
import re
import threading
from urllib.parse import urlparse

from helper_net import get_with_random_agent


ptn_ftype = re.compile('http.+/format/(\w+)')

class ImageDownloadThread(threading.Thread):
    def __init__(self, url, fpath):
        threading.Thread.__init__(self)
        self.url = url
        self.fpath = fpath
 
    def run(self):
        with open(self.fpath, 'wb') as fp:
            print('downloading:', self.url)
            fp.write(get_with_random_agent(self.url).content)

    @classmethod
    def download(cls, url, fpath, wait=False):
        t = cls(url, fpath)
        t.start()
        if wait:
            t.join()


def get_uuid_img_small_red_book(url):
    '''
    >>> get_uuid_img_small_red_book('http://ci.xiaohongshu.com/110/0/01e4b0260b46d6fe001000000001895014a4d5_0.jpg?imageView2/2/w/1080/format/jpg')
    '/110/0/01e4b0260b46d6fe001000000001895014a4d5_0.jpg'
    >>> get_uuid_img_small_red_book('http://ci.xiaohongshu.com/spectrum/1000g0k02b3ia1osh20005n4gogf4hna990kn1rg?imageView2/2/w/1080/format/jpg')
    '/spectrum/1000g0k02b3ia1osh20005n4gogf4hna990kn1rg'
    '''
    return urlparse(url).path

def get_img_file_id_small_red_book(url):
    '''
    >>> get_img_file_id_small_red_book('http://ci.xiaohongshu.com/110/0/01e4b0260b46d6fe001000000001895014a4d5_0.jpg?imageView2/2/w/1080/format/jpg')
    '01e4b0260b46d6fe001000000001895014a4d5_0.jpg'
    >>> get_img_file_id_small_red_book('http://ci.xiaohongshu.com/spectrum/1000g0k02b3ia1osh20005n4gogf4hna990kn1rg?imageView2/2/w/1080/format/jpg')
    '1000g0k02b3ia1osh20005n4gogf4hna990kn1rg'
    '''
    return os.path.basename(urlparse(url).path)


def get_ftype_img_small_red_book(url):
    '''
    >>> get_ftype_img_small_red_book('http://ci.xiaohongshu.com/110/0/01e4b0260b46d6fe001000000001895014a4d5_0.jpg?imageView2/2/w/1080/format/jpg')
    'jpg'
    >>> get_ftype_img_small_red_book('http://ci.xiaohongshu.com/spectrum/1000g0k02b3ia1osh20005n4gogf4hna990kn1rg?imageView2/2/w/1080/format/png')
    'png'
    '''
    return ptn_ftype.match(url).groups()[0]

def get_fpath_img_small_red_book(url, base='z:/tpl'):
    '''
    >>> get_fpath_img_small_red_book('http://ci.xiaohongshu.com/110/0/01e4b0260b46d6fe001000000001895014a4d5_0.jpg?imageView2/2/w/1080/format/jpg')
    'z:/tpl/110/0/01e4b0260b46d6fe001000000001895014a4d5_0.jpg'
    >>> get_fpath_img_small_red_book('http://ci.xiaohongshu.com/spectrum/1000g0k02b3ia1osh20005n4gogf4hna990kn1rg?imageView2/2/w/1080/format/png')
    'z:/tpl/spectrum/1000g0k02b3ia1osh20005n4gogf4hna990kn1rg.png'
    '''
    fpath = get_uuid_img_small_red_book(url)
    ftype = get_ftype_img_small_red_book(url)
    if not fpath.endswith('.%s' % ftype):
        fpath += '.%s' % ftype
    return os.path.join(base, fpath[1:]).replace('\\', '/')
    
def download_small_red_book(url, base=r'Z:\shenghuo\tpl', wait=False):
    fpath = get_fpath_img_small_red_book(url, base)
    if not os.path.lexists(fpath):
        if not os.path.lexists(os.path.dirname(fpath)):
            os.makedirs(os.path.dirname(fpath), exist_ok=True)
        ImageDownloadThread.download(url, fpath, wait)
    return fpath

    
if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
    