'''
Created on 2024年11月16日

@author: lenovo
'''
import re
ptn_goods_url = re.compile('https://mobile\.yangkeduo\.com/goods\d*.html\?ps=[\w\d]{10}$')


def 是否正确的PDD商品链接(url):
    '''
    >>> 是否正确的PDD商品链接('https://mobile.yangkeduo.com/goods.html?ps=RkjYHrFhUh')
    True
    >>> 是否正确的PDD商品链接('https://mobile.yangkeduo.com/goods.html?ps=RkjYHrFhUh1')
    False
    >>> 是否正确的PDD商品链接('https://mobile.yangkeduo.com/goods.html?ps=9s8na894Yk')
    True
    '''
    return ptn_goods_url.match(url) is not None 



if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
