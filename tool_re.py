'''
Created on 2024年11月13日

@author: lenovo
'''
import re

from helper_hash import get_hash_jsonable
from tool_env import bounds_to_rect


class 错误的款式表达(Exception):
    pass

class 需要点击选择(Exception):
    pass
 
class 需要向下滑动(Exception):
    pass

class 选择款式型号失败(Exception):
    pass


def 装配表达式(r):
    '''
    >>> 装配表达式('aaa***ccc')
    'aaa.*ccc'
    '''
    l = filter(lambda x:x, r.split('*'))
    l = map(lambda x:re.escape(x), l)
    l = '.*'.join(l)
    return l

def 匹配表达式(r, txt, 已经转换=False):
    '''
    >>> 匹配表达式('*确定', '确定')
    True
    >>> 匹配表达式('粉', '男女通用马卡粉')
    True
    >>> 匹配表达式('粉', '男女通用马卡蓝')
    False
    >>> 匹配表达式('.*确定', '确定', True)
    True
    >>> 匹配表达式('无*黑', '[无盖 黑色]确定', False)
    True
    '''
    r = 装配表达式(r) if not 已经转换 else r
    # print('================', r, txt)
    return re.search(r, txt) is not None

def 底边过滤(v, infos):
    if v:
        rtn = []
        for d in infos:
            if d.get('bounds') and bounds_to_rect(d.get('bounds')).bottom <= v:
                rtn.append(d)
        return rtn
    return infos

class 多组表达式迷糊匹配器(object):
    def __init__(self, line=None, **k):
        '''
        >>> 多组表达式迷糊匹配器('aa bb   c').l
        ['aa', 'bb', 'c']
        >>> 多组表达式迷糊匹配器('aa aa') # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        错误的款式表达:        
        '''
        self.结果 = {}
        self.上一次匹配 = None

        if line is not None:
            l = re.split('\s+', line or '')
            l = [装配表达式(x) for x in l]
            self.l = l
            if len(l) <= 0 or len(l) != len(set(l)):
                raise 错误的款式表达(self)
        else:
            for name, value in k.items():
                setattr(self, name, value)
        # self.当前匹配 = None
        
    def to_dict(self):
        return {
            'l':self.l,
            '结果': self.结果,
            '上一次匹配':self.上一次匹配,
            }

    @classmethod
    def from_dict(cls, d):
        '''
        >>> c = 多组表达式迷糊匹配器.from_dict({'l':['粉', '小号']})
        >>> c.匹配一轮([{'text':'成熟粉'}, {'text':'成熟蓝'}, {'text':'小号 sl'}, {'text':'大号 xl'} ])
        ('粉', {'text': '成熟粉'})
        '''
        return cls(**d) if d else None
    
    @property
    def 款式(self):
        return ','.join(map(lambda x:x.get('text'), self.结果.values()))
    
    @property
    def 未匹配表达式(self):
        for x in self.l:
            if x not in self.结果:
                return x 
    
    def 是否已经完成(self):
        return self.未匹配表达式 is None
    
    def 匹配一轮(self, l):
        '''
        >>> c = 多组表达式迷糊匹配器('粉 小号')
        >>> c.匹配一轮([{'text':'成熟粉'}, {'text':'成熟蓝'}, {'text':'小号 sl'}, {'text':'大号 xl'} ])
        ('粉', {'text': '成熟粉'})
        '''
        r = self.未匹配表达式
        if r:
            for x in l:
                if 匹配表达式(r, x.get('text'), True):
                    return r, x
    
    def 匹配(self, l, 底部浮动菜单上边=None):
        '''
        >>> c = 多组表达式迷糊匹配器('粉 小号')
        >>> c.匹配([{'text':'成熟粉', 'selected':'true'}, {'text':'成熟蓝'}, {'text':'小号 sl', 'selected':'true'}, {'text':'大号 xl'} ])
        >>> c.是否已经完成()
        True
        >>> c = 多组表达式迷糊匹配器('粉 小号 滑')
        >>> c.匹配([{'text':'成熟粉', 'selected':'true'}, {'text':'成熟蓝'}, {'text':'小号 sl', 'selected':'true'}, {'text':'大号 xl'} ]) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        需要向下滑动
        >>> c.匹配([{'text':'成熟粉', 'selected':'true'}, {'text':'成熟蓝'}, {'text':'小号 sl', 'selected':'true'}, {'text':'大号 xl'} ]) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        选择款式型号失败
        >>> c.匹配([{'text':'丝滑Q弹', 'selected':'false'}, {'text':'成熟蓝'}, {'text':'小号 sl', 'selected':'true'}, {'text':'大号 xl'} ]) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        需要点击选择
        '''
        assert not self.是否已经完成()
        
        l = list(底边过滤(底部浮动菜单上边, l))
        
        while not self.是否已经完成():
            result = self.匹配一轮(l)
            if result is None:
                break
            if result[1].get('selected') != "true":
                raise 需要点击选择(result[1])
            self.结果[result[0]] = result[1]
        
        # h = get_hash_jsonable(l)
        
        是否到底 = self.上一次匹配 == l
        self.上一次匹配 = l
        # if not self.是否已经完成():
        #     raise 需要向下滑动
        
        if not self.是否已经完成():
            if not 是否到底:
                raise 需要向下滑动
            else:
                raise 选择款式型号失败(self)
        
        
        
    def 是否到底(self):
        return self.上一次匹配 == self.当前匹配
    
    
if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
