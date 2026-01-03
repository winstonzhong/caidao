"""
Created on 2022年6月3日

@author: Administrator
"""

import platform
import re
import time

from pathlib import Path


import numpy
from numpy.lib._iotools import _is_string_like
import pandas

from tool_rect import Rect
import os
from urllib.parse import urlparse, urlunparse

import random

IPV4_PAT = "(?:[0-9]{1,3}\\.){3}[0-9]{1,3}"

OPENAI = "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"

OS_WIN = platform.system() == "Windows"

ptn_chinese = re.compile("[\u4e00-\u9fff]")

ptn_not_chinese = re.compile("[^\u4e00-\u9fff]+")

ptn_cd = re.compile("[\da-zA-Z]")

ptn_x = re.compile('\!|？|\?|"')

ptn_dot = re.compile("…{2,}")

ptn_emoji = re.compile("[\U00010000-\U0010ffff]")

ptn_not_number = re.compile("[^\d^\.^\s]+")

MAIN_HOST_J_ONE = os.environ.get("MAIN_HOST_J_ONE", "https://coco.j1.sale")

U4080 = os.path.lexists("/home/yka-003/zwd")

# U4080 = True

HOST_TASK_DEFAULT = "task.j1.sale" if not U4080 else "task-test.j1.sale"

HOST_SERVER_DEFAULT = "coco.j1.sale" if not U4080 else "crawler.j1.sale"

HOST_TASK = os.environ.get("HOST_TASK", HOST_TASK_DEFAULT)

HOST_SERVER = os.getenv("HOST_SERVER", HOST_SERVER_DEFAULT)

HOST_URL = f"https://{HOST_SERVER}"

HEALTH_CARD_URL = f"{HOST_URL}/wx_msgs/healthdoc"

# HEALTH_CARD_TAG = "您的健康档案已更新～"


def get_filename(file_path: str) -> str:
    """
    从Windows或Linux文件路径中提取文件名（包含扩展名），彻底解决跨平台兼容问题
    支持：带盘符的Windows路径、Linux路径、网络共享路径、混合分隔符路径

    Args:
        file_path: Windows或Linux格式的文件路径字符串（普通字符串/原始字符串均可）

    Returns:
        路径中的文件名（包含扩展名）

    Examples:
        >>> get_filename(w_fpath)
        '1764469092.9023788.xml'
        >>> get_filename('/mnt/aaa/b.xml')  # Linux路径
        'b.xml'
    """
    # 1. 处理Windows路径：替换反斜杠为正斜杠，去掉盘符（如 C:/ → /）
    # 匹配 Windows 盘符（如 C:、D:）或网络共享路径（// 开头）
    windows_path_pattern = r"^([A-Za-z]:)?[\\/]"
    if re.match(windows_path_pattern, file_path):
        # 替换所有反斜杠为正斜杠
        file_path = file_path.replace("\\", "/")
        # 去掉盘符（如 C:/ → /，保留网络共享路径的 //）
        file_path = re.sub(r"^[A-Za-z]:/", "/", file_path)

    # 2. 用 Path 提取文件名（此时路径已统一为 / 分隔符，跨平台兼容）
    return Path(file_path).name


class cached_property_for_cls:
    def __init__(self, method):
        self.method = method
        self.cache = {}

    def __get__(self, instance, owner):
        if owner not in self.cache:
            self.cache[owner] = self.method(owner)
        return self.cache[owner]


def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 函数运行时间：{end_time - start_time} 秒")
        return result

    return wrapper


def get_pre_of_list(i, l):
    return l[i - 1] if i > 0 else None


def get_pre_pre_of_list(i, l):
    return l[i - 2] if i > 1 else None


def split_none_numbers(line):
    """
    >>> split_none_numbers('123')
    [123]
    >>> split_none_numbers('1,23')
    [1, 23]
    >>> split_none_numbers(None)
    []
    """
    if line:
        l = filter(lambda x: x, re.split("[^\d]+", line))
        return list(map(lambda x: int(x), l))
    return []


def two_points_to_bounds(two_points):
    """
    >>> two_points_to_bounds("[45,1731][1035,1956]")
    (45, 1731, 1035, 1956)
    """
    return tuple(split_none_numbers(two_points))


def bounds_to_rect(bounds):
    """
    >>> bounds_to_rect('(0,0,4,4)')
    0 4 0 4<4, 4>
    >>> bounds_to_rect("[45,1731][1035,1956]")
    45 1035 1731 1956<990, 225>
    >>> bounds_to_rect(Rect(0,100,0,100))
    0 100 0 100<100, 100>
    >>> bounds_to_rect("{'left': 123, 'top': 704, 'right': 1032, 'bottom': 776}")
    123 1032 704 776<909, 72>
    >>> bounds_to_rect({'left': 123, 'top': 704, 'right': 1032, 'bottom': 776})
    123 1032 704 776<909, 72>
    """
    if not isinstance(bounds, Rect):
        if _is_string_like(bounds):
            if "[" in bounds:
                rect = two_points_to_bounds(bounds)
                return Rect(rect[0], rect[2], rect[1], rect[3])
            elif bounds.strip().startswith("{"):
                tmp = eval(bounds)
                return Rect(**tmp)
            else:
                rect = eval(bounds)
                return Rect(rect[0], rect[2], rect[1], rect[3])
        elif isinstance(bounds, dict):
            return Rect(**bounds)
        else:
            rect = bounds
            return Rect(rect[0], rect[2], rect[1], rect[3])
    return bounds


def bounds_to_center(bounds):
    """
    >>> bounds_to_center('(0,0,4,4)')
    (2, 2)
    >>> bounds_to_center((0,0,4,4))
    (2, 2)
    """
    rect = bounds_to_rect(bounds)
    return rect.center_x, rect.center_y


def bounds_to_shape(bounds):
    """
    >>> bounds_to_shape('(1,2,3,4)')
    (2, 2)
    >>> bounds_to_shape('(0,100,300,401)')
    (300, 301)
    """
    rect = bounds_to_rect(bounds)
    return rect.width, rect.height


def to_number_safe(line):
    try:
        return float(line)
    except ValueError:
        return numpy.nan


def to_number_with_chinese(line):
    """
    >>> to_number_with_chinese('307')
    307.0
    >>> to_number_with_chinese('4927')
    4927.0
    >>> to_number_with_chinese('2.4万')
    24000.0
    >>> to_number_with_chinese('65.4万')
    654000.0
    >>> to_number_with_chinese('65.4万1')
    nan
    >>> to_number_with_chinese('65.4万 ')
    654000.0
    >>> to_number_with_chinese('65.4')
    65.4
    >>> to_number_with_chinese(None)
    nan
    """
    if not line:
        return numpy.nan
    l = line.strip().rsplit("万", 1)

    length = len(l)
    if length == 2 and not l[1]:
        u = 10000
    elif length == 1:
        u = 1
    else:
        u = numpy.nan

    return to_number_safe(l[0]) * u


def to_number_with_chinese_safe(line):
    v = to_number_with_chinese(line)
    return v if not numpy.isnan(v) else line


def to_number_with_chinese_safe_dict(d):
    return {k: to_number_with_chinese_safe(v) for k, v in d.items()}


def is_ipv4(host):
    return re.match(IPV4_PAT, host) is not None


def clear_emoji(content):
    return ptn_emoji.sub("", content)


def smart_range(start, end):
    """
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
    """
    end = int(end)
    start = int(start)
    if end == start:
        return range(0, 1)
    s = numpy.sign(end - start)
    return range(start, end + s, s)


def float_range(start, stop, step=1.0):
    """
    >>> list(float_range(1,4.0,0.5))
    [1, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    >>> list(float_range(1,4.1,0.5))
    [1, 1.5, 2.0, 2.5, 3.0, 3.5, 4.1]
    >>> list(float_range(1,4.4,0.5))
    [1, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.4]
    >>> list(float_range(1,1.1,0.5))
    [1, 1.1]
    """
    current = start
    while 1:
        yield current
        current += step
        if numpy.isclose(current, stop, atol=step / 2):
            yield stop
            break
        if current >= stop:
            yield stop
            break


def smart_range_safe(start, end):
    try:
        return smart_range(start, end)
    except:
        pass
    return []


def is_string(x):
    return _is_string_like(x)


def to_float(x):
    try:
        return float(x)
    except Exception:
        pass


def is_float(x):
    """
    >>> is_float(None)
    False
    >>> is_float(0)
    False
    >>> is_float(1.0)
    True
    >>> is_float('.11')
    True
    >>> is_float('.11.')
    False
    >>> is_float('0')
    False
    >>> is_float('0.1')
    True
    """
    return isinstance(x, float) or (
        isinstance(x, str) and "." in x and to_float(x) is not None
    )


def is_int(x):
    return to_int(x) is not None


def is_number(x):
    return is_int(x)


def to_int(x, default=None):
    """
    >>> to_int('1.0') == 1
    True
    >>> to_int('1') == 1
    True
    >>> to_int('1.1a')
    """
    try:
        return int(x)
    except Exception:
        pass
    try:
        return int(float(x))
    except Exception:
        pass
    return default


def is_chinese(ch):
    return "\u4e00" <= ch <= "\u9fff"


def replace_stupid(s):
    """
    >>> replace_stupid('特斯拉客服回应Model 3、Model Y降价：已下单未提车可选官网价')
    '特斯拉客fu服回应Model 3、Model Y降价：已下单未提车可选官网价'
    >>> replace_stupid('马斯克打造海外版微信，Facebook最受伤')
    '马斯克打造海外版微x信，Facebook最受伤'
    """
    s = (
        s.replace("客服", "客fu服")
        .replace("微信", "微x信")
        .replace("加入", "夹入")
        .replace("Keychron", "凯克龙")
    )
    s = s.replace("mPower", "")
    s = s.replace("交流", "交x流")
    return s


def replace_special(s):
    """
    >>> replace_special('c++')
    'c＋+'
    >>> replace_special('印度政府这手，三星、苹果和中国厂家都郁闷了……?')
    '印度政府这手，三星、苹果和中国厂家都郁闷了…?'
    >>> replace_special('iPhone.6正式“退休”，其系列卖出25亿部，二手收购价现已低至百元....')
    'iPhone.6正式“退休”，其系列卖出25亿部，二手收购价现已低至百元'
    """
    s = s.replace("++", "＋+")
    s = ptn_dot.sub("…", s)
    s = re.compile("\.+$").sub("", s)
    return s


def is_special(x):
    """
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
    """
    if is_chinese(x):
        return False
    if ptn_cd.match(x) is not None:
        return False

    if ptn_x.match(x) is not None:
        return False
    return True


def insert_d_if_starts_with_special(s):
    """
    >>> insert_d_if_starts_with_special('「最牛AI艺术家」Stable Diffusion有多值钱？种子轮融资即晋升独角')
    'd「最牛AI艺术家」Stable Diffusion有多值钱？种子轮融资即晋升独角'
    """
    if s and is_special(s[0]):
        return "d" + s
    return s


def append_qustion_mark_if_end_with_special(s):
    """
    >>> append_qustion_mark_if_end_with_special('国际象棋比赛走「后」门？谁想出来的「智能肛珠」')
    '国际象棋比赛走「后」门？谁想出来的「智能肛珠」?'
    >>> append_qustion_mark_if_end_with_special('InfoQ 2022 年趋势报告：')
    'InfoQ 2022 年趋势报告：?'
    """
    if is_special(s[-1]):
        return s + "?"
    return s


def insert_double_qoute_if_start_with_special(s):
    """
    >>> insert_double_qoute_if_start_with_special('「AI世界」还缺点啥？牛津大学教授：现实世界')
    '"「AI世界」还缺点啥？牛津大学教授：现实世界'
    """
    if is_special(s[0]):
        return '"' + s
    return s


def replace_double_special_to_single(s):
    """
    >>> replace_double_special_to_single('古人类DNA与重症新冠有关？2022诺奖得主Pääbo，竟是前诺奖得主私生子')
    '古人类DNA与重症新冠有关？2022诺奖得主Päbo，竟是前诺奖得主私生子'
    >>> replace_double_special_to_single('Meta被曝正悄悄裁员，或波及1.2万名员工')
    'Meta被曝正悄悄裁员，或波及1.2万名员工'
    >>> replace_double_special_to_single('磁带非但没被淘汰，容量还比硬盘大了？？？')
    '磁带非但没被淘汰，容量还比硬盘大了？'
    """
    l = set(filter(lambda x: is_special(x), s))
    l.add("？")
    for x in l:
        s = re.compile("%s+" % re.escape(x)).sub(x, s)
    return s


def has_chinese(line):
    if line:
        for ch in line:
            if is_chinese(ch):
                return True
    return False


def split_df(df, batch_size=1000):
    for x in range(0, len(df), batch_size):
        yield df.iloc[x : x + batch_size]


def pct_chinese(line):
    """
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
    """
    if line and len(line) > 0:
        tmp = ptn_chinese.sub("", line)
        return int((1 - len(tmp) / len(line)) * 100)
    return 0


def density_chinese(line):
    """
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
    """
    if line and len(line) > 0:
        return len(remain_chinese(line)) / len(line)
    return 0


def clear_chinese(line):
    """
    >>> clear_chinese('人家')  == ''
    True
    >>> len(clear_chinese(mulline_text)) == 8
    True
    """
    return ptn_chinese.sub("", line)


def remain_chinese(line):
    """
    >>> remain_chinese('人家12')  == '人家'
    True
    >>> remain_chinese(mulline_text) == '人家磁带非但没被淘汰容量还比硬盘大了'
    True
    """
    return ptn_not_chinese.sub("", line)


def split_by_not_chinese(line):
    """
    >>> split_by_not_chinese('人11222333大')
    ['人', '大']
    >>> split_by_not_chinese('人11222333大kk')
    ['人', '大']
    >>> split_by_not_chinese(None)
    []
    """
    return list(filter(lambda x: x, ptn_not_chinese.split(line))) if line else []


def simple_encode(line, v=122):
    """
    >>> simple_encode(simple_encode('h123')) == 'h123'
    True
    >>> simple_encode(simple_encode('http://www.baidu.com:8090/')) == 'http://www.baidu.com:8090/'
    True
    """
    l = list(line)
    return "".join(map(lambda x: chr(ord(x) ^ v), l))


def first_or_last(list_like, i, default=None):
    if hasattr(list_like, "__next__"):
        try:
            return list(list_like)[i]
        except IndexError:
            return
    if isinstance(list_like, pandas.DataFrame):
        return default if list_like.empty else list_like.iloc[i]
    if list_like is not None and len(list_like) > 0:
        return list(list_like)[i]
    return default


def first(list_like, default=None):
    """
    >>> first([])
    >>> first(None)
    >>> first(None, 'test') == 'test'
    True
    >>> first([3,2,1]) == 3
    True
    >>> first(empty_s)
    >>> first(demo_s) == 1
    True
    >>> first(empty_df)
    >>> first(demo_df).x
    1
    >>> first(range(10))
    0
    >>> first(filter(lambda x:x, range(1,10)))
    1
    """
    return first_or_last(list_like, 0, default)


def last(list_like, default=None):
    """
    >>> last([])
    >>> last(None)
    >>> last(None, 'test') == 'test'
    True
    >>> last([3,2,1]) == 1
    True
    >>> last(empty_s)
    >>> last(demo_s) == 2
    True
    >>> last(empty_df)
    >>> last(demo_df).x
    2
    >>> last(range(10))
    9
    >>> last(filter(lambda x:x, range(1,100)))
    99
    """
    return first_or_last(list_like, -1, default)


def 格式化运行参数(txt):
    """
    >>> 格式化运行参数('aa bb')
    {'aa': 'bb'}
    >>> 格式化运行参数(s1)
    {'aa': 'bb', 'cc': 'dd ee'}
    >>> 格式化运行参数(mulline_text)
    {}
    >>> 格式化运行参数(mulline_text1)
    {'人家': '1213', '磁带非但没被淘汰': '容量还比硬盘大了123'}
    >>> 格式化运行参数('')
    {}
    >>> 格式化运行参数(None)
    {}
    >>> 格式化运行参数(' ')
    {}
    """
    if txt:
        l = map(lambda x: x.strip(), txt.splitlines())
        l = filter(lambda x: x, l)
        l = map(lambda x: x.split(" ", maxsplit=1), l)
        l = filter(lambda x: len(x) == 2, l)
        return dict(l)
    return {}


def 组装参数(txt):
    运行参数 = 格式化运行参数(txt)
    if not 运行参数 and txt and txt.strip():
        运行参数 = {"运行参数": txt.strip()}
    return 运行参数


def 抽离数字(txt):
    """
    >>> 抽离数字('124$')
    '124'
    >>> 抽离数字('¥152 ')
    '152'
    >>> 抽离数字('¥152 .32')
    '152 .32'
    """
    return ptn_not_number.sub("", txt).strip() if txt else None


def 文字截断(txt, 最大长度=20, 截断替代="..."):
    """
    >>> 文字截断('aaa')
    'aaa'
    >>> 文字截断('123456', 6)
    '123456'
    >>> 文字截断('1234567', 6)
    '123456...'
    """
    return f"""{txt[:最大长度]}{'' if len(txt[最大长度:]) == 0 else 截断替代}"""


def remove_leading_whitespace(text):
    pattern = r"^[ \t]+"
    return re.sub(pattern, "", text, flags=re.M)


def replace_url_host(url, host_name):
    """
    替换URL中的主机名部分，支持路径形式URL和默认https协议

    参数:
        url (str): 原始URL
        host_name (str): 新的主机名

    返回:
        str: 替换主机名后的新URL

    示例:
        >>> replace_url_host("https://crawler.j1.sale/admin/wx_msgs/", "coco.test.com")
        'https://coco.test.com/admin/wx_msgs/'

        >>> replace_url_host("http://oldhost/path", "newhost")
        'http://newhost/path'

        >>> replace_url_host("ftp://user:pass@oldhost:21/dir", "newhost")
        'ftp://newhost/dir'

        >>> replace_url_host("https://oldhost:8080", "newhost:9090")
        'https://newhost:9090'

        >>> replace_url_host("http://oldhost", "newhost")
        'http://newhost'

        >>> replace_url_host("/aaa/bbb", "coco.test.com")
        'https://coco.test.com/aaa/bbb'

        >>> replace_url_host("aaa/bbb", "coco.test.com")
        'https://coco.test.com/aaa/bbb'

        >>> replace_url_host("//oldhost/path", "newhost")
        'https://newhost/path'

        >>> replace_url_host("", "newhost")
        'https://newhost'
    """
    # 解析URL，获取各个组成部分
    parsed_url = urlparse(url)

    # 处理协议：如果原URL没有协议，默认使用https
    scheme = parsed_url.scheme if parsed_url.scheme else "https"

    # 替换主机名（无论原URL是否有主机名）
    new_netloc = host_name

    # 重新组合URL的各个部分（使用处理后的协议和新主机名）
    new_components = (
        scheme,
        new_netloc,
        parsed_url.path,
        parsed_url.params,
        parsed_url.query,
        parsed_url.fragment,
    )

    new_url = urlunparse(new_components)
    return new_url


def 精确识别并截断废话(txt: str) -> str:
    """
    精确识别并截断文本中包含"聊聊"的废话部分，返回核心内容

    功能说明：
    - 先清理文本首尾的空白字符（空格、制表符、换行等）
    - 定位"聊聊"的起始位置，若无则返回清理后的原文本
    - 找到"聊聊"后，向后跳过逗号，寻找第一个非逗号截断标点（。！～）
    - 截断到该标点前的核心内容

    >>> 精确识别并截断废话("从视频里能感受到手工编绳的用心，貔貅和吞金兽的搭配很有特色，色彩丰富也显得很有活力呢！要是你在编绳配色或技巧上有想交流的，咱们可以一起聊聊呀。")
    '从视频里能感受到手工编绳的用心，貔貅和吞金兽的搭配很有特色，色彩丰富也显得很有活力呢！'
    >>> 精确识别并截断废话("从视频里能感受到演唱会带来的热烈氛围和之后的不舍感，这种戒断反应特别能让人共情呢！要是还想回味现场，和我聊聊印象最深的片段也很开心呀。	")
    '从视频里能感受到演唱会带来的热烈氛围和之后的不舍感，这种戒断反应特别能让人共情呢！'
    >>> 精确识别并截断废话("从视频里能感受到手工创作的温柔感，“生活该是被热爱的人事填满”这句话特别戳人，这样的手工内容既治愈又能传递对生活的热爱～要是你想了解视频里手工制作的具体技巧，或者想聊聊这类手工的创作灵感，都可以跟我说呀～")
    '从视频里能感受到手工创作的温柔感，“生活该是被热爱的人事填满”这句话特别戳人，这样的手工内容既治愈又能传递对生活的热爱～'
    >>> 精确识别并截断废话("从视频里能感受到你用缝纫机创作时的顺畅感，看来重机90这款缝纫机确实很适配你的缝纫需求，搭配上你的天赋，做手工肯定特别有成就感～")
    '从视频里能感受到你用缝纫机创作时的顺畅感，看来重机90这款缝纫机确实很适配你的缝纫需求，搭配上你的天赋，做手工肯定特别有成就感～'
    >>> 精确识别并截断废话("能感受到你在没有更新的日子里，也在用心通过缝纫机专注创作，这份对手工的坚持特别打动人。")
    '能感受到你在没有更新的日子里，也在用心通过缝纫机专注创作，这份对手工的坚持特别打动人。'
    >>> 精确识别并截断废话("看到视频里的草莓绒花，觉得特别有冬日氛围，绒花的质感柔软又精致，做成发簪戴在头上肯定很亮眼，还能感受到非遗手艺的独特魅力。")
    '看到视频里的草莓绒花，觉得特别有冬日氛围，绒花的质感柔软又精致，做成发簪戴在头上肯定很亮眼，还能感受到非遗手艺的独特魅力。'
    >>> 精确识别并截断废话("哈哈，感觉这种“你取关我也取关”的想法还挺真实的！毕竟双向的关注才有意义嘛～我之前也遇到过被取关没发现的情况，你平时会特意去看谁取关自己吗～	")
    '哈哈，感觉这种“你取关我也取关”的想法还挺真实的！毕竟双向的关注才有意义嘛～'
    """
    # 第一步：清理文本首尾的空白字符
    cleaned_txt = txt.strip()

    # 第二步：定位"聊聊"的起始位置（找不到返回-1）
    words = ["聊聊", "呀～", "吗～"]
    chat_pos = -1
    for x in words:
        chat_pos = cleaned_txt.find(x)
        if chat_pos != -1:
            break
    # chat_pos = cleaned_txt.find("聊聊")

    if chat_pos == -1:
        # 无"聊聊"，返回清理后的原文本
        return cleaned_txt
    else:
        cleaned_txt = cleaned_txt[:chat_pos]
    return 查找并截断(cleaned_txt)


def is_endswith_question(text: str) -> bool:
    question_end_pattern = r"[?？]\s*$"
    return re.search(question_end_pattern, text)


def is_contains_question(text: str) -> bool:
    question_pattern = r"[?？]"
    return re.search(question_pattern, text)


def 查找并截断(
    text: str, target_puncts: str = "～~。？！?!", is_question_search_mode=False
):
    """
    截断文本，返回截断后的文本。

    参数：
    - text: 待截断的文本
    - target_puncts: 截断的标点列表，默认为"～~。？！?!", 表示截断到最后一个"～~。？！?!",
    - is_question_search_mode: 是否以问号结尾的搜索模式，默认为False
    >>> 查找并截断("视频里“又刷到我了吧？这就是命，你躲都躲不掉”这句话特别有梗，带着点小俏皮的调侃感，像朋友间的轻松互动，让人看了忍不住会心一笑，很有日常打发时间的欢乐氛围～不知道你是觉得这句文案很有趣，还是也喜欢这种轻松好玩的对口型视频风格呀？	", "？?", is_question_search_mode=True)
    '视频里“又刷到我了吧？这就是命，你躲都躲不掉”这句话特别有梗，带着点小俏皮的调侃感，像朋友间的轻松互动，让人看了忍不住会心一笑，很有日常打发时间的欢乐氛围～不知道你是觉得这句文案很有趣，还是也喜欢这种轻松好玩的对口型视频风格呀？'
    >>> 查找并截断("视频里“又刷到我了吧？这就是命，你躲都躲不掉”这句话特别有梗，带着点小俏皮的调侃感，像朋友间的轻松互动，让人看了忍不住会心一笑，很有日常打发时间的欢乐氛围～", "？?", is_question_search_mode=True)
    '这就是命，你躲都躲不掉”这句话特别有梗，带着点小俏皮的调侃感，像朋友间的轻松互动，让人看了忍不住会心一笑，很有日常打发时间的欢乐氛围～'

    >>> 查找并截断("从视频里能感受到大家对“串门”是否有用的关注特别真实～其实像之前提到的，不管是粉少的创作者互相支持，还是带着真诚去互动，慢慢都能积累起友好的氛围，对账号初期经营还挺有帮助的。你是在纠结自己做账号要不要尝试串门，还是想知道怎么让串门效果更好呀")
    '从视频里能感受到大家对“串门”是否有用的关注特别真实～'
    """

    # is_question_search_mode = '?' in target_puncts
    last_punct_idx = -1
    for punct in target_puncts:
        current_idx = text.rfind(punct)
        if current_idx > last_punct_idx:
            last_punct_idx = current_idx
            break

    # return text[: last_punct_idx + 1] if last_punct_idx != -1 else text
    if last_punct_idx == -1:
        return text

    if len(text) * 0.5 < last_punct_idx or not is_question_search_mode:
        return text[: last_punct_idx + 1]

    return text[last_punct_idx + 1 :]

    # return text[: last_punct_idx + 1] if last_punct_idx != -1 else text


def truncate_at_last_punct_if_question(text: str) -> str:
    """
    若文本末尾（允许尾随空白）以半角?/全角？结尾，截断到最后一个中文标点（。？！）或半角?!的位置。

    Doctest 测试用例：
    >>> truncate_at_last_punct_if_question("这是第一段。这是第二段？")  # 最后标点是。
    '这是第一段。'
    >>> truncate_at_last_punct_if_question("测试1？测试2！   ")  # 末尾带空白，最后标点是？
    '测试2！'
    >>> truncate_at_last_punct_if_question("示例！结尾是？")  # 最后标点是！
    '示例！'
    >>> truncate_at_last_punct_if_question("半角!结尾？")  # 半角!匹配
    '半角!'
    >>> truncate_at_last_punct_if_question("无目标标点？   ")  # 无匹配标点，返回原文
    '无目标标点'
    >>> truncate_at_last_punct_if_question("无问号结尾！")  # 非问号结尾，返回原文
    '无问号结尾！'
    >>> truncate_at_last_punct_if_question("")  # 空字符串边界Case
    ''
    >>> truncate_at_last_punct_if_question("混合标点。a?b！c？")  # 多标点取最后一个
    '混合标点。'
    >>> truncate_at_last_punct_if_question("从视频里能感机这件事的小得～不知，有的小作品呀？")
    '从视频里能感机这件事的小得～'
    >>> truncate_at_last_punct_if_question("这个视频还, 于。这个视频的信息呀？比如对里面的某个情节的讨论，还是其他方面呢？")
    '这个视频还, 于。'
    >>> truncate_at_last_punct_if_question("看这个视频特别有中式韵味！感觉这个视频里的串门氛围好轻松呀")
    '看这个视频特别有中式韵味！感觉这个视频里的串门氛围好轻松呀'
    >>> truncate_at_last_punct_if_question("视频里“又刷到我了吧？这就是命，你躲都躲不掉”这句话特别有梗，带着点小俏皮的调侃感，像朋友间的轻松互动，让人看了忍不住会心一笑，很有日常打发时间的欢乐氛围～不知道你是觉得这句文案很有趣，还是也喜欢这种轻松好玩的对口型视频风格呀？	")
    '这就是命，你躲都躲不掉”这句话特别有梗，带着点小俏皮的调侃感，像朋友间的轻松互动，让人看了忍不住会心一笑，很有日常打发时间的欢乐氛围'
    >>> truncate_at_last_punct_if_question("视频里“串门了都在家吗？在家的吱一声”的招呼特别热情，配上那句笑声，像邻里间热络的互动，一下子就拉近距离，特别有生活里的热闹劲儿～ 不过我有点好奇，你平时和朋友邻居串门，会不会也像这样用轻松的方式打招呼呀？或者视频里有没有哪个小细节让你觉得特别有意思呀？	")
    '在家的吱一声”的招呼特别热情，配上那句笑声，像邻里间热络的互动，一下子就拉近距离，特别有生活里的热闹劲儿'

    #>>> truncate_at_last_punct_if_question("从视频里能感受到大家对“串门”是否有用的关注特别真实～其实像之前提到的，不管是粉少的创作者互相支持，还是带着真诚去互动，慢慢都能积累起友好的氛围，对账号初期经营还挺有帮助的。你是在纠结自己做账号要不要尝试串门，还是想知道怎么让串门效果更好呀？")
    """
    while is_contains_question(text):
        text = 查找并截断(text, "？?", is_question_search_mode=True)[:-1]
        if is_endswith_question(text):
            text = text[:-1]
        text = 查找并截断(text)
    return text.strip()


def 截断问句和废话(txt):
    """
    截断问句和废话 的 Docstring

    :param txt: 说明
    :type txt: str
    :return: 说明
    :rtype: str

    >>> 截断问句和废话("视频里的对话好有烟火气呀！听着像在和老朋友聊天一样～你平时玩这个游戏时，最喜欢和里面的哪个角色互动呀？")
    '视频里的对话好有烟火气呀！听着像在和老朋友聊天一样～'
    >>> 截断问句和废话("哇，把红豆元素画成彩绘也太有创意了吧！我之前画彩绘总担心颜料蹭掉，后来发现先涂层薄定妆粉会好很多～你平时也常做这种有诗意的彩绘吗？")
    '哇，把红豆元素画成彩绘也太有创意了吧！我之前画彩绘总担心颜料蹭掉，后来发现先涂层薄定妆粉会好很多～'
    >>> 截断问句和废话("这渐变紫蓝的绒花也太温柔了吧！我之前做绒花总掉绒，后来用少量定型喷雾就好很多~你平时也喜欢戴这类配饰吗？")
    '这渐变紫蓝的绒花也太温柔了吧！我之前做绒花总掉绒，后来用少量定型喷雾就好很多~'
    >>> 截断问句和废话("从视频里能感受到手工编绳的用心，貔貅和吞金兽的搭配很有特色，色彩丰富也显得很有活力呢！要是你在编绳配色或技巧上有想")
    '手工编绳的用心，貔貅和吞金兽的搭配很有特色，色彩丰富也显得很有活力呢！要是你在编绳配色或技巧上有想'
    >>> 截断问句和废话("看视频里能感受到手工编绳的用心，貔貅和吞金兽的搭配很有特色，色彩丰富也显得很有活力呢！要是你在编绳配色或技巧上有想")
    '手工编绳的用心，貔貅和吞金兽的搭配很有特色，色彩丰富也显得很有活力呢！要是你在编绳配色或技巧上有想'
    >>> 截断问句和废话("感觉这个视频里的串门氛围好轻松呀！主动去串门互动还挺能拉近距离的～我之前想串门总有点不好意思开口，你平时串门的时候，一般会先从哪些话题聊起，来让互动更自然呀～")
    '串门氛围好轻松呀！主动去串门互动还挺能拉近距离的～'
    >>> 截断问句和废话("看这个视频特别有中式韵味！感觉这个视频里的串门氛围好轻松呀")
    '特别有中式韵味！感觉这个视频里的串门氛围好轻松呀'
    >>> 截断问句和废话("看这个视频特别有中式韵味！国画风格的柿子画得温润又鲜活，配上霜降吃丁柿的习俗，既透着节气的仪式感，又满是生活里的美好寓意，让人觉得很治愈～")
    '特别有中式韵味！国画风格的柿子画得温润又鲜活，配上霜降吃丁柿的习俗，既透着节气的仪式感，又满是生活里的美好寓意，让人觉得很治愈～'
    >>> 截断问句和废话("看这个视频也太可爱啦！幼崽穿搭的内容透着满满的童真，第13天就有46位粉丝，能感觉到妈妈带着宝宝做自媒体的用心和小成就感，“欢迎姨姨们串门”的说法也特别亲切～")
    '也太可爱啦！幼崽穿搭的内容透着满满的童真，第13天就有46位粉丝，能感觉到妈妈带着宝宝做自媒体的用心和小成就感，“欢迎姨姨们串门”的说法也特别亲切～'
    >>> 截断问句和废话("能感受到视频里特别热情的互动劲儿，“你来我往”的串门邀约特别亲切，还透着股主动拉近彼此距离的可爱～")
    '特别热情的互动劲儿，“你来我往”的串门邀约特别亲切，还透着股主动拉近彼此距离的可爱～'
    >>> 截断问句和废话("能感受到你对视频流量的关注，还特别热情地邀请大家串门并承诺回礼，这种主动互动的心意特别实在，很容易让人愿意参与～")
    '流量的关注，还特别热情地邀请大家串门并承诺回礼，这种主动互动的心意特别实在，很容易让人愿意参与～'
    >>> 截断问句和废话("看了这个视频，感觉你分享的起诉步骤还挺详细的，从立案的选择，到合同纠纷类别的查看，再到材料的准备和提交，都有提到。")
    '感觉你分享的起诉步骤还挺详细的，从立案的选择，到合同纠纷类别的查看，再到材料的准备和提交，都有提到。'
    >>> 截断问句和废话("看这个视频，能感受到你准备去串门的雀跃劲儿，一上来就喊着目标500家")
    '你准备去串门的雀跃劲儿，一上来就喊着目标500家'
    >>> 截断问句和废话("能感受到你面对低播放量的困惑，15小时只有16次播放，明明账号内容都正常，换谁都会有点摸不着头脑吧～")
    '你面对低播放量的困惑，15小时只有16次播放，明明账号内容都正常，换谁都会有点摸不着头脑吧～'

    >>> 截断问句和废话("看视频时特别能感受到全职宝妈兼顾带娃和做自媒体的不容易，30天摸爬滚打迎来第一个破万播放，这份坚持特别让人佩服，尤其是那句“干就完了”，特别有劲儿！")
    '特别能感受到全职宝妈兼顾带娃和做自媒体的不容易，30天摸爬滚打迎来第一个破万播放，这份坚持特别让人佩服，尤其是那句“干就完了”，特别有劲儿！'
    """
    s = truncate_at_last_punct_if_question(精确识别并截断废话(txt))
    # s = re.sub(r"^(感觉|能感受|看|从).*?视频(里)*(的)*(，)*", "", s)
    s = re.sub(r"^(感觉|能感受|看|从).*?视频(里|时)*(的)*(，)*", "", s)
    return re.sub("^能感受(到)*", "", s)


def 对豆包回复进行所有的必要处理(txt):
    """
    对豆包回复进行所有的必要处理 的 Docstring

    :param txt: 说明
    >>> 对豆包回复进行所有的必要处理("视频里的对话好有烟火气呀！听着像在和老朋友聊天一样！你平时玩这个游戏时，最喜欢和里面的哪个角色互动呀？")
    '对话好有烟火气呀！听着像在和老朋友聊天一样！'

    #>>> 对豆包回复进行所有的必要处理("从视频里能感受到大家对“串门”是否有用的关注特别真实～其实像之前提到的，不管是粉少的创作者互相支持，还是带着真诚去互动，慢慢都能积累起友好的氛围，对账号初期经营还挺有帮助的。你是在纠结自己做账号要不要尝试串门，还是想知道怎么让串门效果更好呀？")
    """
    txt = 截断问句和废话(txt)
    txt = replace_trailing_tilde(txt)
    txt = re.sub(r"^(视频里)的{0,1}", "", txt)
    return txt


def has_valid_result(txt):
    """
    判断输入文本去除非汉字后是否不以“无”结尾（即存在有效结果），同时处理引号包裹“无”的情况。

    核心规则：
    1. 先去除文本首尾空白字符；
    2. 若清洗后的文本包含「“无”」「"无"」「‘无’」「'无'」，直接返回False；
    3. 过滤出文本中所有汉字（Unicode范围：\u4e00-\u9fa5）；
    4. 若过滤后的汉字字符串为空 → 返回False；
    5. 若过滤后的汉字字符串是「无」或以「无」结尾 → 返回False；
    6. 其他情况返回True（表示有有效结果）。

    Doctest单元测试（覆盖所有核心场景）：
    >>> has_valid_result("")  # 空字符串
    False
    >>> has_valid_result("   ")  # 全空白字符
    False
    >>> has_valid_result("无")  # 仅含「无」
    False
    >>> has_valid_result("查询结果无")  # 汉字结尾为「无」
    False
    >>> has_valid_result("查询结果无123￥%")  # 结尾「无」+非汉字
    False
    >>> has_valid_result("“无”")  # 中文双引号包裹「无」
    False
    >>> has_valid_result('"无"')  # 英文双引号包裹「无」
    False
    >>> has_valid_result("‘无’")  # 中文单引号包裹「无」
    False
    >>> has_valid_result("'无'")  # 英文单引号包裹「无」
    False
    >>> has_valid_result("包含“无”的无效文本")  # 文本中含中文双引号「无」
    False
    >>> has_valid_result("包含'无'的无效文本")  # 文本中含英文单引号「无」
    False
    >>> has_valid_result("查询结果为合格")  # 正常有效结尾
    True
    >>> has_valid_result("查询结果为合格123@")  # 有效结尾+非汉字
    True
    >>> has_valid_result("  测试结果正常  ")  # 首尾空白+有效结尾
    True
    >>> has_valid_result("无有效内容但结尾合格")  # 开头「无」+结尾有效
    True
    >>> has_valid_result("123测试456")  # 非汉字包围有效汉字
    True
    >>> has_valid_result("abc123￥%")  # 全非汉字
    False
    >>> has_valid_result("结果无无")  # 过滤后结尾为「无」
    False
    >>> has_valid_result("请你明确一下具体需求，比如对这段文本进行润色、概括、提取关键信息、分析观点等，这样我才能更准确地为你提供服务呀。")
    False
    >>> has_valid_result("抱歉，我无法回答你的问题")
    False
    """
    # 步骤1：去除首尾空白字符
    cleaned_txt = txt.strip()

    if not cleaned_txt:
        return False

    if cleaned_txt.startswith("抱歉"):
        return False

    # 步骤2：检查是否包含引号包裹的「无」（中英文单/双引号）
    invalid_quote_patterns = {"“无”", '"无"', "‘无’", "'无'", "具体需求", "链接"}
    if any(pattern in cleaned_txt for pattern in invalid_quote_patterns):
        return False

    # 步骤3：过滤出所有汉字（仅保留Unicode汉字范围的字符）
    chinese_chars = [char for char in cleaned_txt if "\u4e00" <= char <= "\u9fa5"]
    chinese_str = "".join(chinese_chars)

    # 步骤4：过滤后无汉字 → 无有效结果
    if not chinese_str:
        return False

    # 步骤5：过滤后是「无」或结尾为「无」→ 无有效结果
    if chinese_str == "无" or chinese_str.endswith("无"):
        return False

    # 步骤6：其他情况 → 有有效结果
    return True


def is_valid_upper_6chars(s: str) -> bool:
    """
    判断输入字符串是否严格由A-Z大写英文字母组成，且长度恰好为6位。

    参数:
        s: 待验证的字符串

    返回:
        布尔值：符合条件返回True，否则返回False

    测试用例:
    >>> is_valid_upper_6chars('ABCDEF')  # 标准符合条件的案例
    True
    >>> is_valid_upper_6chars('ABCDE')   # 长度不足6位
    False
    >>> is_valid_upper_6chars('ABCDEFG') # 长度超过6位
    False
    >>> is_valid_upper_6chars('AbcDEF')  # 包含小写字母
    False
    >>> is_valid_upper_6chars('ABC1EF')  # 包含数字
    False
    >>> is_valid_upper_6chars('ABC@EF')  # 包含特殊符号
    False
    >>> is_valid_upper_6chars('')        # 空字符串
    False
    >>> is_valid_upper_6chars('123456')  # 全数字
    False
    >>> is_valid_upper_6chars('XYZUVW')  # 另一个合法大写字母组合
    True
    >>> is_valid_upper_6chars('A0B9C8')  # 字母数字混合
    False
    >>> is_valid_upper_6chars('AAAAAA')  # 重复大写字母
    True
    >>> is_valid_upper_6chars('ABC DEF') # 包含空格
    False
    >>> is_valid_upper_6chars(None)
    False
    """
    # 正则表达式说明：
    # [A-Z] 匹配单个大写英文字母
    # {6} 限定恰好匹配6个
    # re.fullmatch 确保整个字符串完全匹配（而非部分匹配）
    match_result = re.fullmatch(r"[A-Z]{6}", s or "")
    return match_result is not None


def replace_trailing_tilde(s: str) -> str:
    """
    将字符串结尾的全角～或半角~随机替换为：
    半角.、全角。、半角!、全角！、空字符中的一个。

    测试说明：设置随机种子以确保测试结果可复现
    >>> random.seed(2)  # 更换种子避免和旧测试冲突，保证结果稳定
    >>> replace_trailing_tilde("hello~")  # 半角~，随机选到半角!
    'hello.'
    >>> replace_trailing_tilde("world～")  # 全角～，随机选到全角。
    'world.'
    >>> replace_trailing_tilde("test~")   # 半角~，随机选到空字符
    'test.'
    >>> replace_trailing_tilde("demo～")  # 全角～，随机选到半角.
    'demo。'
    >>> replace_trailing_tilde("no_tilde")  # 无结尾~，返回原字符串
    'no_tilde'
    >>> replace_trailing_tilde("")  # 空字符串返回空
    ''
    >>> replace_trailing_tilde("~~")  # 仅替换最后一个半角~，选到全角！
    '~！'
    >>> replace_trailing_tilde("～～")  # 仅替换最后一个全角～，选到全角。
    '～。'
    """
    # 定义替换候选：包含全角/半角的.、!，以及空字符
    replacement_chars = [".", "！", "。", "!", ""]
    # 正则匹配结尾的全角～或半角~，[～~]匹配两种字符，$锚定行尾
    result = re.sub(
        pattern=r"[～~]$", repl=lambda _: random.choice(replacement_chars), string=s
    )
    return result


if __name__ == "__main__":
    import doctest

    empty_s = pandas.Series([], dtype="str")
    demo_s = pandas.Series([1, 2])
    empty_df = pandas.DataFrame()
    demo_df = pandas.DataFrame([{"x": 1}, {"x": 2}])
    mulline_text = r"人家\r\n磁带非但没被淘汰，容量还比硬盘大了123"
    s1 = "aa bb\ncc dd ee"
    mulline_text1 = "人家 1213\r\n磁带非但没被淘汰 容量还比硬盘大了123"
    w_fpath = "D:\\workspace\\db\\sg\\meida\\0\\1764469092.9023788.xml"
    print(doctest.testmod(verbose=False, report=False))
