'''
Created on 2022年6月3日

@author: Administrator
'''
import platform
import re

import numpy
from urllib3.util.url import IPV4_RE, IPV4_PAT

from tool_rect import Rect


OPENAI = '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'

OS_WIN = platform.system() == 'Windows'

ptn_chinese = re.compile('[\u4e00-\u9fff]')

ptn_not_chinese = re.compile('[^\u4e00-\u9fff]+')

ptn_cd = re.compile('[\da-zA-Z]')

ptn_x = re.compile('\!|？|\?|"')

ptn_dot = re.compile('…{2,}')

ptn_emoji = re.compile(u'[\U00010000-\U0010ffff]')

def get_pre_of_list(i, l):
    return l[i - 1] if i > 0 else None

def get_pre_pre_of_list(i, l):
    return l[i - 2] if i > 1 else None


def bounds_to_rect(bounds):
    rect = eval(bounds)
    return Rect(rect[0],rect[2],rect[1],rect[3])

def bounds_to_center(bounds):
    '''
    >>> bounds_to_center('(0,0,4,4)')
    (2, 2)
    '''
    rect = eval(bounds)
    w, h = (rect[2]-rect[0],rect[3]-rect[1])
    return (int(rect[0]+w//2),int(rect[1]+h/2))
    

def bounds_to_shape(bounds):
    '''
    >>> bounds_to_shape('(1,2,3,4)')
    (2, 2)
    >>> bounds_to_shape('(0,100,300,401)')
    (300, 301)
    '''
    rect = eval(bounds)
    return (rect[2]-rect[0],rect[3]-rect[1])


def to_number_with_chinese(line):
    '''
    >>> to_number_with_chinese('307')
    307
    >>> to_number_with_chinese('4927')
    4927
    >>> to_number_with_chinese('2.4万')
    24000.0
    >>> to_number_with_chinese('65.4万')
    654000.0
    '''
    # ['2.4万', '9.1万', '65.4万', '307']
    # ['4927', '32', '10', '43']
    try:
        return int(line)
    except:
        return eval(line.replace('万', '*10000'))
    


def is_ipv4(host):
    return re.match(IPV4_PAT, host) is not None

def clear_emoji(content):
    return ptn_emoji.sub('', content)

def smart_range(start, end):
    '''
    >>> list(smart_range(0,10))
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    >>> list(smart_range(10,1))
    [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    >>> list(smart_range(*('1-3'.split('-'))))
    [1, 2, 3]
    >>> list(smart_range(0,0))
    [0]
    >>> list(smart_range(1,1))
    [0]
    '''
    end = int(end)
    start = int(start)
    if end == start:
        return range(0,1)
    s = numpy.sign(end - start)
    return range(start, end+s, s)

def smart_range_safe(start, end):
    try:
        return smart_range(start, end)
    except:
        pass
    return []

def is_number(x):
    try:
        int(x)
        return True
    except:
        pass
    return False

def is_chinese(ch):
    return '\u4e00' <= ch <= '\u9fff'

def replace_stupid(s):
    '''
    >>> replace_stupid('特斯拉客服回应Model 3、Model Y降价：已下单未提车可选官网价')
    '特斯拉客fu服回应Model 3、Model Y降价：已下单未提车可选官网价'
    >>> replace_stupid('马斯克打造海外版微信，Facebook最受伤')
    '马斯克打造海外版微x信，Facebook最受伤'
    '''
    s =  s.replace('客服', '客fu服').replace('微信','微x信').replace('加入', '夹入').replace('Keychron','凯克龙')
    s = s.replace('mPower','')
    return s
    

def replace_special(s):
    '''
    >>> replace_special('c++')
    'c＋+'
    >>> replace_special('印度政府这手，三星、苹果和中国厂家都郁闷了……?')
    '印度政府这手，三星、苹果和中国厂家都郁闷了…?'
    >>> replace_special('iPhone.6正式“退休”，其系列卖出25亿部，二手收购价现已低至百元....')
    'iPhone.6正式“退休”，其系列卖出25亿部，二手收购价现已低至百元'
    '''
    s = s.replace('++', '＋+')
    s = ptn_dot.sub('…', s) 
    s = re.compile('\.+$').sub('', s)
    return s

def is_special(x):
    '''
    >>> is_special('」')
    True
    >>> is_special('z')
    False
    >>> is_special(';')
    True
    >>> is_special('.')
    True
    >>> is_special('人')
    False
    >>> is_special('!')
    False
    >>> is_special('？')
    False
    >>> is_special('？')
    False
    >>> is_special('"')
    False
    >>> is_special('ä')
    True
    >>> is_special('「')
    True
    >>> is_special('？')
    False
    >>> is_special('：')
    True
    >>> is_special(chr(128076))
    True
    '''
    if is_chinese(x):
        return False
    if ptn_cd.match(x) is not None:
        return False
    
    if ptn_x.match(x) is not None:
        return False
    return True

def insert_d_if_starts_with_special(s):
    '''
    >>> insert_d_if_starts_with_special('「最牛AI艺术家」Stable Diffusion有多值钱？种子轮融资即晋升独角')
    'd「最牛AI艺术家」Stable Diffusion有多值钱？种子轮融资即晋升独角'
    '''
    if s and is_special(s[0]):
        return 'd' + s
    return s 
    
def append_qustion_mark_if_end_with_special(s):
    '''
    >>> append_qustion_mark_if_end_with_special('国际象棋比赛走「后」门？谁想出来的「智能肛珠」')
    '国际象棋比赛走「后」门？谁想出来的「智能肛珠」?'
    >>> append_qustion_mark_if_end_with_special('InfoQ 2022 年趋势报告：')
    'InfoQ 2022 年趋势报告：?'
    '''    
    if is_special(s[-1]):
        return s + "?"
    return s

def insert_double_qoute_if_start_with_special(s):
    '''
    >>> insert_double_qoute_if_start_with_special('「AI世界」还缺点啥？牛津大学教授：现实世界')
    '"「AI世界」还缺点啥？牛津大学教授：现实世界'
    '''
    if is_special(s[0]):
        return '"' + s
    return s

def replace_double_special_to_single(s):
    '''
    >>> replace_double_special_to_single('古人类DNA与重症新冠有关？2022诺奖得主Pääbo，竟是前诺奖得主私生子')
    '古人类DNA与重症新冠有关？2022诺奖得主Päbo，竟是前诺奖得主私生子'
    >>> replace_double_special_to_single('Meta被曝正悄悄裁员，或波及1.2万名员工')
    'Meta被曝正悄悄裁员，或波及1.2万名员工'
    >>> replace_double_special_to_single('磁带非但没被淘汰，容量还比硬盘大了？？？')
    '磁带非但没被淘汰，容量还比硬盘大了？'
    '''
    l = set(filter(lambda x:is_special(x), s))
    l.add('？')
    for x in l:
        s = re.compile('%s+'%re.escape(x)).sub(x, s)
    return s

def has_chinese(line):
    if line:
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

def density_chinese(line):
    '''
    >>> density_chinese('') == 0
    True
    >>> density_chinese(None) == 0
    True
    >>> density_chinese('1') == 0
    True
    >>> density_chinese('1人')
    0.5
    >>> density_chinese('人家')
    1.0
    '''
    if line and len(line) > 0:
        return len(remain_chinese(line)) / len(line)
    return 0

def clear_chinese(line):
    '''
    >>> clear_chinese('人家')  == ''
    True
    >>> len(clear_chinese(mulline_text)) == 8
    True
    '''
    return ptn_chinese.sub('', line)

def remain_chinese(line):
    '''
    >>> remain_chinese('人家12')  == '人家'
    True
    >>> remain_chinese(mulline_text) == '人家磁带非但没被淘汰容量还比硬盘大了'
    True
    '''
    return ptn_not_chinese.sub('', line)
    
def split_by_not_chinese(line):
    '''
    >>> split_by_not_chinese('人11222333大')
    ['人', '大']
    >>> split_by_not_chinese('人11222333大kk')
    ['人', '大']
    >>> split_by_not_chinese(None)
    []
    '''
    return list(filter(lambda x:x, ptn_not_chinese.split(line))) if line else []

def simple_encode(line, v=122):
    '''
    >>> simple_encode(simple_encode('h123')) == 'h123'
    True
    >>> simple_encode(simple_encode('http://www.baidu.com:8090/')) == 'http://www.baidu.com:8090/'
    True
    '''
    l = list(line)
    return ''.join(map(lambda x:chr(ord(x) ^ v), l))

if __name__ == '__main__':
    import doctest
    mulline_text = r'人家\r\n磁带非但没被淘汰，容量还比硬盘大了123'
    print(doctest.testmod(verbose=False, report=False))
