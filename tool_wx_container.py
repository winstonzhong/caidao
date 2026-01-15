from functools import cached_property
from tool_env import bounds_to_rect, first, is_int
from tool_wx import (
    clean_session_name,
    is_session_name,
    is_renamed_name,
    cutoff_renamed_suffix,
)
import numpy
from helper_hash import get_hash_jsonable, get_hash, MyEncoder, get_hash_bytes, get_hash_df
from tool_time import convert_chinese_datetime
import re
import pandas
from lxml import etree
import cv2
from collections import ChainMap

namespaces = {"re": "http://exslt.org/regular-expressions"}

ptn_root = """//*[@class="androidx.recyclerview.widget.RecyclerView"][@package="com.tencent.mm"]"""

ptn_container = '//*[@class="androidx.recyclerview.widget.RecyclerView"]/*[re:match(@class,".+RelativeLayout|LinearLayout")]'

ptn_elements = './/*[@content-desc!=""] | .//*[@text!=""] | .//*[@class="android.widget.ImageView"]'

ptn_wx_root = (
    """/*/android.widget.FrameLayout[@resource-id=""][@package="com.tencent.mm"]"""
)

ptn_recycler = """//*[@class="androidx.recyclerview.widget.RecyclerView"]"""


#############################################

x_nav = '//android.widget.FrameLayout/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.TextView[@text="微信"][@content-desc=""]/../../../..'
x_session = "./android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout[1]/android.widget.LinearLayout/android.view.View"
x_head = '//android.widget.FrameLayout/android.view.ViewGroup/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.RelativeLayout[@text=""][@content-desc="搜索"]/../../..'
x_subtitle = "./android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.widget.LinearLayout/android.view.View"
x_time = "./android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.view.View"

x_red = "./android.widget.LinearLayout/android.widget.RelativeLayout/android.widget.TextView"


def time_to_24h_str(time_str):
    """
    将带时段（早上/上午/下午/晚上/凌晨/中午/午间等）的hh:mm格式字符串转换为标准24小时制"hh:mm"字符串，
    不符合hh:mm核心格式的输入直接返回原始字符串。

    核心逻辑：
    1. 识别时段关键词（如早上/晚/下午/中午/午间），匹配对应的24小时制小时偏移量
    2. 清理字符串，提取纯hh:mm格式的时间部分并验证合法性
    3. 计算24小时制小时数，格式化小时/分钟为两位数字，输出"hh:mm"
    4. 非法格式直接返回原始输入字符串

    Examples:
    >>> time_to_24h_str("早上8:12")  # 基础时段-早上
    '08:12'
    >>> time_to_24h_str("中午11:59") # 新增时段-中午（无偏移）
    '11:59'
    >>> time_to_24h_str("午间12:00") # 新增时段-午间（无偏移）
    '12:00'
    >>> time_to_24h_str("午间3:05")  # 新增时段-午间（单数字小时）
    '03:05'
    >>> time_to_24h_str("上午8:12")  # 扩展时段-上午（等价早上）
    '08:12'
    >>> time_to_24h_str("下午4:16")  # 基础时段-下午
    '16:16'
    >>> time_to_24h_str("晚上8:14")  # 基础时段-晚上
    '20:14'
    >>> time_to_24h_str("晚08:14")   # 变体-简写时段+补0小时
    '20:14'
    >>> time_to_24h_str("午4:16")    # 变体-简写时段（午=下午）
    '16:16'
    >>> time_to_24h_str("早8:12")    # 变体-简写时段（早=早上）
    '08:12'
    >>> time_to_24h_str("8:12")      # 无时段原始格式
    '08:12'
    >>> time_to_24h_str("16:16")     # 24小时制原始格式
    '16:16'
    >>> time_to_24h_str("08:12")     # 24小时制补0格式
    '08:12'
    >>> time_to_24h_str("昨天")      # 非法格式-无hh:mm
    '昨天'
    >>> time_to_24h_str("11-9日")    # 非法格式-日期
    '11-9日'
    >>> time_to_24h_str("8:12:30")   # 非法格式-多分隔符
    '8:12:30'
    >>> time_to_24h_str("晚上8点14") # 非法格式-无冒号
    '晚上8点14'
    >>> time_to_24h_str("晚上a:14")  # 非法格式-非数字小时
    '晚上a:14'
    >>> time_to_24h_str("早上0:00")  # 边界值-凌晨0点
    '00:00'
    >>> time_to_24h_str("下午12:00") # 边界值-下午12点（无偏移）
    '00:00'
    >>> time_to_24h_str("晚上12:00") # 边界值-晚上12点（转0点）
    '00:00'
    >>> time_to_24h_str("凌晨3:45")  # 扩展时段-凌晨
    '03:45'
    >>> time_to_24h_str("")          # 空字符串（返回原字符串）
    ''
    >>> time_to_24h_str(" 晚上 9:05 ") # 变体-含空格
    '21:05'
    >>> time_to_24h_str("下午0:5")   # 变体-分钟单数字
    '12:05'
    >>> time_to_24h_str("晚23:59")   # 变体-晚上23点（23+12=35→35%24=11）
    '11:59'
    """
    # 定义时段与24小时制小时偏移量的映射（新增“中午”“午间”，无偏移）
    period_mapping = {
        "早上": 0,
        "上午": 0,
        "凌晨": 0,
        "早": 0,
        "中午": 0,  # 新增：中午无偏移
        "午间": 0,  # 新增：午间无偏移
        "下午": 12,
        "午": 12,
        "晚上": 12,
        "晚": 12,
    }

    # 初始化偏移量，清理输入字符串（去除首尾空格）
    hour_offset = 0
    clean_str = time_str.strip()
    original_str = time_str  # 保存原始输入，用于非法格式返回

    # 识别时段并提取偏移量，同时移除时段关键词
    for period, offset in period_mapping.items():
        if period in clean_str:
            hour_offset = offset
            clean_str = clean_str.replace(period, "").strip()  # 移除时段后再次清理空格
            break  # 只匹配第一个时段（避免多时段冲突）

    # 验证并解析hh:mm格式
    if ":" in clean_str and len(clean_str.split(":")) == 2:
        try:
            hour, minute = map(int, clean_str.split(":"))
            # 计算24小时制小时数（处理12/24进制边界，如晚上12点转0点）
            total_hour = (hour + hour_offset) % 24
            # 格式化小时和分钟为两位数字（补前导0）
            return f"{total_hour:02d}:{minute:02d}"
        except ValueError:
            # 无法转换为整数（如字母、特殊字符），返回原始字符串
            return original_str

    # 非hh:mm格式，返回原始字符串
    return original_str


def time_to_minutes(time_str):
    """
    将带时段（早上/上午/下午/晚上/凌晨等）的hh:mm格式字符串转换为总分钟数，非法格式返回np.nan。

    核心逻辑：
    1. 识别时段关键词（如早上/晚/下午），匹配对应的24小时制小时偏移量
    2. 清理字符串，提取纯hh:mm格式的时间部分
    3. 验证时间格式并转换为总分钟数

    Examples:
    >>> time_to_minutes("早上8:12")  # 基础时段
    492
    >>> time_to_minutes("上午8:12")  # 扩展时段（上午=早上）
    492
    >>> time_to_minutes("下午4:16")
    976
    >>> time_to_minutes("晚上8:14")
    1214
    >>> time_to_minutes("晚08:14")   # 变体格式（晚+08）
    1214
    >>> time_to_minutes("午4:16")    # 简写变体（午=下午）
    976
    >>> time_to_minutes("早8:12")    # 简写变体（早=早上）
    492
    >>> time_to_minutes("8:12")      # 无时段原始格式
    492
    >>> time_to_minutes("16:16")     # 24小时制原始格式
    976
    >>> time_to_minutes("昨天")      # 非法格式（无hh:mm）
    nan
    >>> time_to_minutes("11-9日")    # 非法格式（日期）
    nan
    >>> time_to_minutes("8:12:30")   # 非法格式（多分隔符）
    nan
    >>> time_to_minutes("晚上8点14") # 非法格式（无冒号）
    nan
    >>> time_to_minutes("晚上a:14")  # 非法格式（非数字）
    nan
    >>> time_to_minutes("早上0:00")  # 边界值（凌晨0点）
    0
    >>> time_to_minutes("下午12:00") # 边界值（下午12点）
    1440
    >>> time_to_minutes("凌晨3:45")  # 扩展时段（凌晨）
    225
    >>> time_to_minutes("")          # 空字符串
    nan
    >>> time_to_minutes(" 晚上 9:05 ") # 含空格的变体
    1265
    """
    # 定义时段与24小时制小时偏移量的映射（覆盖常见变体）
    period_mapping = {
        "早上": 0,
        "上午": 0,
        "凌晨": 0,
        "早": 0,
        "下午": 12,
        "午": 12,
        "晚上": 12,
        "晚": 12,
    }

    # 初始化偏移量，清理输入字符串（去除首尾空格）
    hour_offset = 0
    clean_str = time_str.strip()

    # 识别时段并提取偏移量，同时移除时段关键词
    for period, offset in period_mapping.items():
        if period in clean_str:
            hour_offset = offset
            clean_str = clean_str.replace(period, "").strip()  # 移除时段后再次清理空格
            break  # 只匹配第一个时段（避免多时段冲突）

    # 复用原逻辑验证hh:mm格式并转换
    if ":" in clean_str and len(clean_str.split(":")) == 2:
        try:
            hour, minute = map(int, clean_str.split(":"))
            # 计算24小时制总分钟数
            total_min = (hour + hour_offset) * 60 + minute
            return total_min
        except ValueError:
            # 无法转换为整数（如字母、特殊字符）
            return numpy.nan

    # 非hh:mm格式直接返回nan
    return numpy.nan


def 获取列表详情(results):
    e = results[0]
    rect_nav = bounds_to_rect(e.elem.xpath(x_nav)[0].attrib.get("bounds"))
    rect_head = bounds_to_rect(e.elem.xpath(x_head)[0].attrib.get("bounds"))
    top_most = rect_head.bottom
    bottom_most = rect_nav.top
    data = []
    for e in results:
        d = {}
        rect = bounds_to_rect(e.bounds)
        x = e.elem.xpath(x_session)
        if not x:
            continue
        d["session_name"] = x[0].attrib.get("text")
        x = e.elem.xpath(x_subtitle)
        if not x:
            continue
        d["subtitle"] = x[0].attrib.get("text")
        x = e.elem.xpath(x_time)
        if not x:
            continue
        d["time"] = time_to_24h_str(x[0].attrib.get("text"))
        x = e.elem.xpath(x_red)
        if x:
            d["red"] = x[0].attrib.get("text")
        else:
            d["red"] = "0"
        d["top"] = rect.top
        d["bottom"] = rect.bottom
        d["height"] = rect.height
        d["center"] = rect.center
        data.append(d)
    df = pandas.DataFrame(data)
    df["valid"] = (df.top >= top_most) & (df.bottom <= bottom_most)
    df["today"] = df["time"].str.match(r"^\d{2}:\d{2}$", na=False)
    df["s3p"] = df["session_name"].str.match(r"^[A-Z]{6}$", na=False)
    df["up"] = top_most
    df["down"] = bottom_most
    return df


def 获取3P列表详情(results):
    df = 获取列表详情(results)
    df = df[(df.valid) & (df.today) & (df.s3p)]
    return df[["session_name", "subtitle", "red", "time"]]


def get_short_text(txt, max_length=20):
    return txt[:max_length] + ("..." if txt[max_length:] else "")


def get_xpath(node, root=None, include_pos=True):
    """
    递归获取节点的xpath全路径的函数
    """
    xpath_components = []
    while node is not None:
        if node == root:
            break

        if node.tag == etree.Comment:  # 跳过注释节点，可不处理注释节点的路径情况
            node = node.getparent()
            continue

        if node.getparent() is None:
            break

        siblings = node.getparent().getchildren()
        pos = None
        for index, sibling in enumerate(siblings):
            if sibling == node:
                pos = index + 1
                break

        element_name = f"""{node.tag}[@class="{node.attrib.get("class")}"]"""
        if pos > 1 and include_pos:
            element_name += f"[{pos}]"

        xpath_components.append(element_name)

        node = node.getparent()
    return "/".join(xpath_components[::-1])


class SingleContainer(object):

    def __init__(self, e):
        self.e = e

    @property
    def text(self):
        pass

    @property
    def 所有可识别元素(self):
        rtn = []
        for e in self.e.xpath(".//*"):
            if e.attrib.get("content-desc") or e.attrib.get("text"):
                rtn.append(e)


class 单条容器(list):
    def __init__(self, rect_big, rect, *args, **kwargs):
        self.rect_big = rect_big
        self.rect = rect
        super().__init__(*args, **kwargs)

    def 是否顶部探头(self):
        return self.rect.top <= self.rect_big.top and len(self) >= 2

    def 是否底部触底(self):
        return self.rect.bottom >= self.rect_big.bottom and self.类型 != "文本"

    def 是否非文本容器超长(self):
        v = self.rect.height / self.rect_big.height
        print(f"容器高度占比: {v:.2f}")
        return self.类型 != "文本" and (self.rect.height / self.rect_big.height) >= 0.40

    @property
    def 和微信容器底边间距(self):
        return abs(self.rect_big.bottom - self.rect.bottom)

    def 是否底部被截断(self):
        return self.和微信容器底边间距 <= 0

    @property
    def list(self):
        return [x.dict for x in self]

    @cached_property
    def 头像(self):
        e = first(
            filter(
                lambda x: "头像" in x.类型 and x.描述 and x.描述.endswith("头像"), self
            )
        )
        return e

    # def 是否自己消息(self):
    #     return (
    #         self.头像 is not None
    #         and bounds_to_rect(self.头像.bounds).left > self.rect_big.center_x
    #     )

    def 是否自己消息(self):
        return self.是否靠右侧消息容器()

    def 是否已处理(self):
        if self.是否自己消息():
            return True

        if self.类型 == "图片":
            return False

        if self.语音转文字控件 is not None:
            return False

        if self.类型 == "语音":
            # print('============', [self.语音转文字文本])
            return bool(self.语音转文字文本)

        return True

    @property
    def 语音转文字控件(self):
        if self.类型 != "语音":
            return
        e = self.get_first_type("语音转文字")

        if e is None:
            return

        if e.文本 != "转文字":
            return

        if numpy.isclose(e.rect.center_y, self.头像.rect.center_y, rtol=0, atol=2):
            return e

    @cached_property
    def 发言者(self):
        if self.头像 is not None:
            return self.头像.描述[:-2]
        if self.类型 == "系统提示":
            return "系统"

    @property
    def 发言者_无别名(self):
        return cutoff_renamed_suffix(self.发言者)

    @cached_property
    def 类型列表(self):
        rtn = []
        for x in self:
            rtn.extend(x.类型)
        return list(set(rtn))

    def find_type_prop_value(self, type_name, prop_name):
        for ys in self:
            d = ys.dict
            if type_name in ys.dict.get("type"):
                if d.get(prop_name):
                    return d.get(prop_name)

    def get_first_type(self, type_name):
        for ys in self:
            if type_name in ys.类型:
                return ys

    def get_all_type(self, type_name):
        return filter(lambda x: type_name in x.类型, self)

    @property
    def 语音秒数(self):
        l = self.get_all_type("语音描述")
        l = list(filter(lambda x: re.match('\d+"', x.文本), l))
        return int(l[0].文本[:-1]) if l else 0

    def 获取第一个元素(self, type_name):
        for x in self:
            if type_name in x.类型:
                return x

    def 获取所有文本或描述(self, type_name=None, not_inlcude=("时间", "头像")):
        rtn = []
        for x in self:
            if type_name is None or type_name in x.类型:
                if not list(filter(lambda t: t in x.类型, not_inlcude)):
                    # if "头像" not in x.类型:
                    rtn.append(x)
        return " ".join([x.文本或者描述 for x in rtn if x.文本或者描述])

    @classmethod
    def 判断类型(cls, l):
        """
        >>> 单条容器.判断类型(['语音描述', '头像'])
        '语音'
        >>> 单条容器.判断类型(['时间', '语音描述', '头像'])
        '语音'
        >>> 单条容器.判断类型(['时间', '语音描述', '头像', '语音转文字', '昵称'])
        '语音'
        >>> 单条容器.判断类型(['时间', '正文', '头像', '昵称'])
        '文本'
        >>> 单条容器.判断类型(['正文', '头像', '昵称'])
        '文本'
        >>> 单条容器.判断类型(['时间', '语音转文字', '头像', '昵称', '语音描述'])
        '语音'
        >>> 单条容器.判断类型(['时间', '头像', '昵称'])
        '未知'
        >>> 单条容器.判断类型(['系统提示', '时间'])
        '系统提示'
        >>> 单条容器.判断类型(['头像', '正文'])
        '文本'
        >>> 单条容器.判断类型(['视频文件下载图标', '正文', '昵称', '时间', '头像', '视频文件封面'])
        '视频文件'
        >>> 单条容器.判断类型(['时间', '头像', '昵称', '图片'])
        '图片'
        >>> 单条容器.判断类型(['小视频播放按钮', '昵称', '未知', '时间', '头像', '图片', '小视频号名'])
        '小视频'
        >>> 单条容器.判断类型(['机构名', '文章封面', '昵称', '未知', '分割条', '时间', '公众号文章标题', '头像'])
        '公众号文章'
        >>> 单条容器.判断类型(['公众号文章标题', '头像', '分割条', '未知', '小程序卡片注脚'])
        '小程序'
        >>> 单条容器.判断类型(['昵称', '头像', '未知', '图片', '公众号名片'])
        '公众号名片'
        """
        text = ",".join(l)
        if "微信转账" in l:
            return "微信转账"

        if "微信红包" in l:
            return "微信红包"

        if "语音描述" in l:
            return "语音"

        if "小程序卡片注脚" in l:
            return "小程序"

        if "公众号文章标题" in l:
            return "公众号文章"

        if "公众号名片" in l:
            return "公众号名片"

        if "视频文件" in text:
            return "视频文件"

        if "小视频" in text:
            return "小视频"

        if "图片" in l:
            return "图片"

        if "正文" in text:
            return "文本"

        if "文件尺寸" in l:
            return "文件"

        if "视频时长" in l:
            return "小视频文件"
        
        if "系统提示" in l:
            return "系统提示"

        return "未知"

    # 文本或者描述
    @cached_property
    def 类型(self):
        return self.判断类型(self.类型列表)

    # @property
    # def 图片唯一值正文(self):
    #     return self.唯一值

    @property
    def 语音转文字文本(self):
        if self.类型 == "语音":
            return self.获取所有文本或描述("语音转文字")

    @cached_property
    def 正文(self):
        if self.是否自己消息():
            return self.获取所有文本或描述()

        if self.类型 == "微信转账":
            return f"[发起转账]{self.获取所有文本或描述('微信转账')}"

        if self.类型 == "微信红包":
            return "[发了一个微信红包]"

        if self.类型 == "公众号文章":
            return f"""[分享了一个链接]《{self.获取所有文本或描述('公众号文章标题')};{self.获取所有文本或描述('公众号文章副标题')}》"""

        if self.类型 == "文本":
            return f"""{self.获取所有文本或描述('正文')}"""

        if self.类型 == "语音":
            txt = self.获取所有文本或描述("语音转文字")
            return f"""[发了一条{self.语音秒数}秒语音]{txt or ''}"""

        if self.类型 == "图片":
            e = self.获取第一个元素("图片")
            if e is not None:
                w, h = e.尺寸
                return f"[分享了一张图片<{w}x{h}>]"

        if self.类型 == "小视频":
            return f"""[分享了一个小视频]{self.获取所有文本或描述('小视频名')}"""

        if self.类型 == "文件":
            return f"""[分享了一个文件, 文件大小:{self.获取所有文本或描述('文件尺寸')}]{self.获取所有文本或描述('公众号文章副标题')}"""

        if self.类型 == "小视频文件":
            return f"""[分享了一个小视频文件, 时长：{self.获取所有文本或描述('视频时长')}]"""

        if self.类型 == "小程序":
            return f"""[分享了一个小程序]{self.获取所有文本或描述()}"""

        if self.类型 == "公众号名片":
            return f"""[分享了一个公众号名片]{self.获取所有文本或描述('公众号名片')}"""
        
        if self.类型 == "系统提示":
            return f"""[系统提示]{self.获取所有文本或描述()}"""

    @property
    def 时间(self):
        e = first(filter(lambda x: "时间" in x.类型, self))
        if e is not None and e.文本:
            return convert_chinese_datetime(e.文本).strftime("%Y-%m-%d %H:%M:%S")
        return numpy.nan

    def 是否包含时间(self):
        return pandas.notna(self.时间)

    def 是否合法容器(self, 忽略顶部探头=False):
        if self.类型 == "文本":
            return (
                bool(self.发言者)
                and bool(self.正文)
                and (not self.是否顶部探头() or 忽略顶部探头 or self.是否包含时间())
                # and not self.是否底部触底()
            )
        return (
            bool(self.发言者)
            and bool(self.正文)
            and (not self.是否顶部探头() or 忽略顶部探头)
            and not self.是否底部触底()
        )

    @property
    def 上下文(self):
        return f"{self.发言者}:{self.正文}".replace("\n", "").strip()

    @property
    def 唯一值(self):
        if self.类型 == "语音":
            上下文 = f"{self.发言者_无别名}:{self.语音秒数}".replace("\n", "").strip()
        else:
            上下文 = f"{self.发言者_无别名}:{self.正文}".replace("\n", "").strip()
        return get_hash(f"{上下文}_{self.时间}")

    @property
    def 代表矩形(self):
        return self.rect

    @property
    def 代表高宽(self):
        return self.代表矩形.shape

    @property
    def 容器字典(self):
        return {
            "上下文": self.上下文,
            "时间": self.时间,
            "探头": self.是否顶部探头(),
            "自己": self.是否自己消息(),
            "类型": self.类型,
            "容器矩形": self.rect.to_bounds(),
            "唯一值": self.唯一值,
            "xy": self.点选中心,
            "xy头像": self.xy头像,
            "已处理": self.是否已处理(),
            "链接": None,
            "图片key": None,
            # "重试次数": 0,
            "内容":None,
        }

    @property
    def xy头像(self):
        头像 = self.头像
        return bounds_to_rect(头像.bounds).center if 头像 is not None else None

    @property
    def 点选中心(self):
        if self.类型 == "语音":
            # if self.是否自己消息():
            #     return bounds_to_rect(self.头像.bounds).offset(-1, 0.5)
            # elif self.头像 is not None:
            #     e = self.语音转文字控件
            #     if e is not None:
            #         return bounds_to_rect(e.bounds).offset(0, 0)
            #     # return bounds_to_rect(self.头像.bounds).offset(1, 0.5)
            if self.是否自己消息() or self.头像 is None:
                return None, None
            return self.头像.rect.offset(1, 0.5)

            # if (
            #     not self.是否自己消息()
            #     and self.头像 is not None
            #     and self.语音转文字控件 is not None
            # ):
            #     return self.语音转文字控件.rect.offset(0, 0)
            #     # return bounds_to_rect(self.头像.bounds).offset(1, 0.5)
            # return None, None
        elif self.类型 == "图片":
            if self.是否自己消息():
                return bounds_to_rect(self.头像.bounds).offset(-1.1, 0.5)
            elif self.头像 is not None:
                return bounds_to_rect(self.头像.bounds).offset(1.1, 0.5)
            else:
                return None, None
        return self.rect.center

    @property
    def most_right(self):
        return max([x.rect.right for x in self]) if self else 0

    def 是否靠右侧消息容器(self):
        return self.most_right > self.rect_big.width * 0.95

    @property
    def 所有图片(self):
        return [x for x in self if x.类型 == "图片"]


class 元素(object):
    _types = {
        "正文": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.TextView"]',
            'node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
            'node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.TextView"]',
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        ],
        "时间": 'node[@class="android.widget.TextView"]',
        "头像": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.ImageView"]',
            'node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.ImageView"]',
            """node[@class="android.widget.LinearLayout"]/node[@class="android.widget.ImageView"]""",
        ],
        "微信红包": 'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.TextView"]',
        # """node[@class="android.widget.LinearLayout"]/node[@class="android.widget.ImageView"][re:match(@content-desc,'.*头像')]""",
        # '正文(自己)':'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        "图片": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.ImageView"]',
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.ImageView"]',
        ],
        "视频时长": 'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        "语音描述": [
            'node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.TextView"]',
            'node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.TextView"]',
            """node[@class="android.widget.TextView"][re:match(@text,'\d+"')][@resource-id="com.tencent.mm:id/bkl"]""",
        ],
        "语音转文字": [
            'node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.TextView"]',
            'node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.TextView"]',
        ],
        "系统提示": 'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        "封面": 'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.ImageView"]',
        "公众号文章标题": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        ],
        "文章封面": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.ImageView"]',
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.ImageView"]',
        ],
        "分割条": 'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.ImageView"]',
        "机构名": 'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.TextView"]',
        "公众号名片": 'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        "昵称": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
            'node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.TextView"]',
        ],
        "视频文件下载图标": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.ImageView"]',
        ],
        "视频文件封面": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.ImageView"]',
        ],
        "小视频号名": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        ],
        "小视频播放按钮": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.ImageView"]',
        ],
        "小视频名": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]',
        ],
        "公众号文章副标题": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        ],
        "文件尺寸": 'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        "小程序卡片注脚": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        ],
        "微信转账": [
            'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.TextView"]',
        ],
        # "文件图片": [
        #     'node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.FrameLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.LinearLayout"]/node[@class="android.widget.RelativeLayout"]/node[@class="android.widget.ImageView"]',
        # ]
    }

    types = {}

    for k, v in _types.items():
        # if type(v) == list:
        if isinstance(v, list):
            for x in v:
                types.setdefault(x, set()).add(k)
        else:
            types.setdefault(v, set()).add(k)

    types = {k: list(v) for k, v in types.items()}

    def __init__(self, e, root):
        self.e = e
        self.root = root

    def __str__(self):
        return str(self.dict)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if self.是否未知() or other.是否未知():
            return False
        if self.是否图片() and other.是否图片() and self.bounds == other.bounds:
            return True
        return self.dict == other.dict

    @cached_property
    def xpath(self):
        return get_xpath(self.e, self.root, False)

    @property
    def cls(self):
        return self.e.attrib.get("class")

    @property
    def bounds(self):
        return self.e.attrib.get("bounds")

    @property
    def rect(self):
        return bounds_to_rect(self.bounds)

    @property
    def 类型(self):
        return 元素.types.get(self.xpath, ["未知"])

    def 是否未知(self):
        return self.类型 == ["未知"]

    def 是否图片(self):
        return self.cls == "android.widget.ImageView"

    @property
    def 文本(self):
        return self.e.attrib.get("text")

    @property
    def 描述(self):
        return self.e.attrib.get("content-desc")

    def 文本或者描述不为空(self):
        return bool(self.文本) or bool(self.描述)

    @property
    def 文本或者描述(self):
        return self.文本 or self.描述

    @property
    def 尺寸(self):
        return bounds_to_rect(self.e.attrib.get("bounds")).shape

    @property
    def dict(self):
        d = {
            "type": self.类型,
            "text": get_short_text(self.e.attrib.get("text")),
            "content-desc": get_short_text(self.e.attrib.get("content-desc")),
        }

        # if '时间' in d.get('type'):
        #     d.update(shape=bounds_to_rect(self.e.attrib.get('bounds')).shape)
        # else:
        #     d['text'] = convert_chinese_datetime(d.get('text')).strftime("%Y-%m-%d %H:%M:%S")

        if d.get("type") == ["未知"]:
            d.update(xpath=self.xpath)
            d.update(bounds=self.e.attrib.get("bounds"))
        return {k: v for k, v in d.items() if v}


class 解析器(object):
    def __init__(self, xml=None, fpath=None):
        if xml is None:
            with open(fpath, "r", encoding="utf8") as fp:
                xml = fp.read()
        self.tree = etree.fromstring(xml.encode("utf8"))
        self.xml = xml
        l = self.tree.xpath(ptn_root)
        if l:
            self.rect = bounds_to_rect(
                self.tree.xpath(ptn_root)[0].attrib.get("bounds")
            )
        else:
            self.rect = None

    @classmethod
    def get_big_df(cls, xmls):
        l = map(lambda x: cls(xml=x).上下文df, xmls)
        df = pandas.concat(list(l))
        return df.drop_duplicates(
            subset=[
                "上下文",
            ]
        )

        # df = pandas.concat(list(l)).sort_values(by='时间')
        # # if not df.empty:
        # #     df.时间 = df.时间.ffill()
        # #     df = df.dropna(subset=['时间'], how='all').reset_index(drop=True)
        # return df.drop_duplicates(subset=['上下文',])

    @property
    def df(self):
        l = map(lambda x: dict(ChainMap(*map(lambda y: y.dict, x))), self.elements)
        return pandas.DataFrame(data=l)

    @classmethod
    def get_paths(cls, fname):
        fpath_xml = f"ut/{fname}.xml"
        fpath_img = f"ut/{fname}.jpg"
        return fpath_xml, fpath_img

    # def save_ut(self):
    #     fname = int(time.time())
    #     self.fpath_xml, self.fpath_img = self.get_paths(fname)

    #     with open(self.fpath_xml, "wb") as fp:
    #         fp.write(self.xml.encode("utf8"))
    #     adb = BaseAdb.first_adb()
    #     cv2.imwrite(self.fpath_img, adb.screen_shot())

    @classmethod
    def from_ut(cls, fname):
        fpath_xml, fpath_img = cls.get_paths(fname)
        j = cls(fpath=fpath_xml)
        j.fpath_img = fpath_img
        return j

    @cached_property
    def img(self):
        return cv2.imread(self.fpath_img)

    def show(self, bounds=None):
        from tool_img import show

        if bounds is None:
            img = self.img
        else:
            img = bounds_to_rect(bounds).crop_img(self.img)
        show(img)

    # @classmethod
    # def 内存快照(cls):
    #     adb = BaseAdb.first_adb()
    #     return cls(xml=adb.get_page().decode("utf8"))

    @cached_property
    def containers(self):
        return self.tree.xpath(ptn_container, namespaces=namespaces)

    def 是否第一页(self):
        if self.containers:
            e = self.elements[-1]
            distance = e.和微信容器底边间距
            # print('和微信容器底边间距:', distance)
            return distance > 20
        return False

    @cached_property
    def elements(self):
        l = []
        for x in self.containers:
            tmp = 单条容器(self.rect, bounds_to_rect(x.attrib.get("bounds")))
            for y in x.xpath(ptn_elements):
                e = 元素(y, x)
                if e not in tmp:
                    tmp.append(e)
            l.append(tmp)
        return l

    def 是否初次会话(self):
        c = self.elements[-1]
        return c.rect.bottom < c.rect_big.height / 2

    @property
    def 上下文df(self):
        忽略顶部探头 = self.是否初次会话()
        dl = filter(lambda x: x.是否合法容器(忽略顶部探头=忽略顶部探头), self.elements)
        dl = map(lambda x: x.容器字典, dl)
        df = pandas.DataFrame(data=dl)
        df['容器key'] = get_hash_df(df)
        return df

    def 是否包含顶部探头容器(self):
        # l = [x.是否顶部探头() for x in self.elements]
        # print(l)
        return any([x.是否顶部探头() for x in self.elements])

    def 是否包含靠右侧消息容器(self):
        for c in self.elements:
            if c.是否靠右侧消息容器():
                return True
        return False

    # @property
    # def key(self):
    #     recycler = self.tree.xpath(ptn_recycler, namespaces=namespaces)
    #     assert recycler, "没有找到recycler"
    #     return get_hash_bytes(etree.tostring(recycler[0]))

    @property
    def key(self):
        # recycler = self.tree.xpath(ptn_recycler, namespaces=namespaces)
        # assert recycler, "没有找到recycler"
        # return get_hash_bytes(etree.tostring(recycler[0]))
        return get_hash_df(self.上下文df)

    def 是否一半向下翻页(self):
        return (
            self.elements
            and self.elements[-1].是否底部触底()
            and self.elements[-1].是否非文本容器超长()
        )


if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
