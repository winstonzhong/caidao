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


def truncate_at_last_punct_if_question(text: str) -> str:
    """
    若文本末尾（允许尾随空白）以半角?/全角？结尾，截断到最后一个中文标点（。？！）或半角?!的位置。

    Doctest 测试用例：
    >>> truncate_at_last_punct_if_question("这是第一段。这是第二段？")  # 最后标点是。
    '这是第一段。'
    >>> truncate_at_last_punct_if_question("测试1？测试2！   ")  # 末尾带空白，最后标点是？
    '测试1？测试2！'
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
    '混合标点。a?b！'
    """
    # 匹配末尾的半角?/全角？，允许尾随空白
    question_end_pattern = r"[?？]\s*$"
    if not re.search(question_end_pattern, text):
        return text.strip()

    # 定义需要查找的标点（全角。？！ + 半角?!）
    text = text.strip()[:-1]
    target_puncts = "。？！?!"
    # 遍历所有标点，找到最后出现的位置
    last_punct_idx = -1
    for punct in target_puncts:
        current_idx = text.rfind(punct)
        if current_idx > last_punct_idx:
            last_punct_idx = current_idx

    # 找到标点则截断，否则返回原文
    return text[: last_punct_idx + 1] if last_punct_idx != -1 else text


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
    """
    # 步骤1：去除首尾空白字符
    cleaned_txt = txt.strip()

    # 步骤2：检查是否包含引号包裹的「无」（中英文单/双引号）
    invalid_quote_patterns = {"“无”", '"无"', "‘无’", "'无'"}
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
