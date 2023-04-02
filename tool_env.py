'''
Created on 2022年6月3日

@author: Administrator
'''
import platform
import re

OPENAI = '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'

OS_WIN = platform.system() == 'Windows'

ptn_chinese = re.compile('[\u4e00-\u9fff]')

ptn_not_chinese = re.compile('[^\u4e00-\u9fff]')

ptn_cd = re.compile('[\da-zA-Z]')

ptn_x = re.compile('\!|？|\?|"')

ptn_dot = re.compile('…{2,}')

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
    >>> remain_chinese('人家')  == '人家'
    True
    >>> remain_chinese(mulline_text) == '人家磁带非但没被淘汰容量还比硬盘大了'
    True
    '''
    return ptn_not_chinese.sub('', line)
    


if __name__ == '__main__':
    import doctest
    mulline_text = r'人家\r\n磁带非但没被淘汰，容量还比硬盘大了123'
    print(doctest.testmod(verbose=False, report=False))
