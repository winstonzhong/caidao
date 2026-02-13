from functools import cached_property
import re
import tool_env
import pandas as pd
import numpy as np
from pandas._config.config import OptionError

try:
    pd.set_option("future.no_silent_downcasting", True)
except OptionError:
    pass


def 转历史(df, 是否群聊=False):
    """
    转历史 的 Docstring

    :param df: 说明

    >>> l = 转历史(df_single1)
    >>> l[0]
    {'content': '##this is the command and req', 'role': 'assistant'}
    >>> l[1]
    {'content': '这是我的信息', 'role': 'user'}
    >>> l = 转历史(df_single1, True)
    >>> l[0]
    {'content': '##this is the command and req', 'role': 'assistant'}
    >>> l[1]
    {'content': '数字人生:这是我的信息', 'role': 'user'}
    """
    if df is None or df.empty:
        return []
    
    if "内容" not in df.columns:
        df["内容"] = None

    if "上下文" not in df.columns and "唯一值" in df.columns:
        df = df.rename(columns={"唯一值": "上下文"})

    assert "上下文" in df.columns and "自己" in df.columns, "必须有上下文列和自己列"

    df.内容 = df.内容.where(df.内容.notna(), np.nan).fillna("").astype(str)

    群聊标识数组 = np.full((len(df),), 是否群聊, dtype=bool)

    分割条件 = (~群聊标识数组) | (df.自己)

    处理后的上下文 = np.where(
        分割条件,  # 判断条件
        df.上下文.str.split(":", n=1).str[-1],  # 满足条件：分割取最后一部分
        df.上下文,  # 不满足条件：保留原始上下文
    )

    s = 处理后的上下文 + df.内容

    s.name = "content"

    role = df.自己.map({False: "user", True: "assistant"})

    role.name = "role"

    data_list = pd.concat([s, role], axis=1).to_dict("records")

    return [x for x in data_list if x["content"]]


def 字典类型判断(d: dict) -> str:
    """
    根据输入的字典信息判断对应的元素类型，判断规则按优先级排序：

    1. content-desc 为 "视频" → 返回 "视频"
    2. content-desc 包含 "的头像" → 返回 "头像"
    3. text 或 content-desc 符合 HH:MM 时间格式 → 返回 "时间"
    4. content-desc 为 "图片,按钮" → 返回 "图片"
    5. content-desc 以 "##" 开头 → 返回 "文本"
    6. 其他所有情况 → 返回 "系统文本"

    >>> 字典类型判断({'tag': 'android.widget.ImageView', 'text': '', 'content-desc': '视频', 'bounds': '[168,257][404,351]'})
    '视频'
    >>> 字典类型判断({'tag': 'android.widget.ImageView', 'text': '', 'content-desc': '视频', 'bounds': '[676,411][912,831]'})
    '视频'
    >>> 字典类型判断({'tag': 'android.widget.Button', 'text': '', 'content-desc': '数字人生的头像', 'bounds': '[936,399][1044,507]'})
    '头像'
    >>> 字典类型判断({'tag': 'android.widget.Button', 'text': '', 'content-desc': '开心姐姐的头像', 'bounds': '[36,879][144,987]'})
    '头像'
    >>> 字典类型判断({'tag': 'android.widget.ImageView', 'text': '', 'content-desc': '视频', 'bounds': '[168,891][404,1311]'})
    '视频'
    >>> 字典类型判断({'tag': 'android.widget.TextView', 'text': '15:58', 'content-desc': '15:58', 'bounds': '[469,1353][610,1414]'})
    '时间'
    >>> 字典类型判断({'tag': 'android.widget.Button', 'text': '', 'content-desc': '开心姐姐的头像', 'bounds': '[36,1456][144,1564]'})
    '头像'
    >>> 字典类型判断({'tag': 'com.bytedance.ies.dmt.ui.widget.DmtTextView', 'text': '', 'content-desc': '图片,按钮', 'bounds': '[168,1468][588,1704]'})
    '图片'
    >>> 字典类型判断({'tag': 'android.widget.TextView', 'text': '再连续互聊 2 天 可点亮火花，和对方合养精灵', 'content-desc': '', 'bounds': '[148,1746][931,1807]'})
    '系统文本'
    >>> 字典类型判断({'tag': 'android.widget.Button', 'text': '', 'content-desc': '开心姐姐的头像', 'bounds': '[36,1849][144,1957]'})
    '头像'
    >>> 字典类型判断({'tag': 'com.bytedance.ies.dmt.ui.widget.DmtTextView', 'text': '', 'content-desc': '##this is the command and req', 'bounds': '[168,1861][840,2040]'})
    '文本'
    >>> 字典类型判断({'tag': 'android.widget.TextView', 'text': '##this is the command and req', 'content-desc': '', 'bounds': '[204,1885][804,2016]'})
    '系统文本'
    >>> 字典类型判断({'tag': 'android.widget.TextView', 'text': '暂时没有更多了', 'content-desc': '', 'bounds': '[0,1343][1080,1523]'})
    '系统文本'
    >>> 字典类型判断({'tag': 'com.bytedance.ies.dmt.ui.widget.DmtTextView', 'text': '', 'content-desc': '早上好 表情包', 'bounds': '[0,1625][1080,2040]'})
    '表情包'
    >>> 字典类型判断({'tag': 'android.widget.TextView', 'text': '关注', 'content-desc': '', 'bounds': '[690,1061][870,1145]'})
    '关注按钮'
    """
    # 提取核心字段，默认空字符串避免键不存在报错
    content_desc = d.get("content-desc", "")
    text = d.get("text", "")
    tag = d.get("tag", "")

    # 定义时间格式正则（匹配 HH:MM 格式）
    time_pattern = re.compile(r"^\d{2}:\d{2}$")

    # 按优先级依次判断类型
    if content_desc == "视频":
        return "视频"
    elif "的头像" in content_desc:
        return "头像"
    elif time_pattern.match(content_desc) or time_pattern.match(text):
        return "时间"
    elif content_desc == "图片,按钮":
        return "图片"
    # elif content_desc.startswith("##"):
    elif tag.endswith(".DmtTextView"):
        if content_desc.endswith(" 表情包") and len(content_desc) < 10:
            return "表情包"
        return "文本"
    elif tag.endswith("android.widget.TextView") and text == "关注":
        return "关注按钮"
    else:
        return "系统文本"


class 元素(object):
    def __init__(self, data: dict):
        self.data = {
            "tag": data.get("tag"),
            "text": data.get("text"),
            "content-desc": data.get("content-desc"),
            "bounds": data.get("bounds"),
        }

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return str(self.data)

    @classmethod
    def from_dict(cls, d: dict):
        if isinstance(d, dict) and (d.get("text") or d.get("content-desc")):
            return cls(d)

    @classmethod
    def from_e(cls, e):
        if not e.attrib.get("text") and not e.attrib.get("content-desc"):
            return
        d = {
            "tag": e.tag,
            "text": e.attrib.get("text"),
            "content-desc": e.attrib.get("content-desc"),
            "bounds": e.attrib.get("bounds"),
        }
        return cls(d)

    @cached_property
    def 类型(self):
        return 字典类型判断(self.data)

    @cached_property
    def rect(self):
        return tool_env.bounds_to_rect(self.data.get("bounds"))

    @property
    def 尺寸(self):
        return f"{self.rect.width}x{self.rect.height}"

    @property
    def 文本(self):
        return self.data.get("text")

    @property
    def 内容描述(self):
        return self.data.get("content-desc")

    @property
    def 内容(self):
        if self.类型 == "文本":
            return self.data.get("content-desc")

        if self.类型 == "表情包":
            txt = self.data.get("content-desc").split(" 表情包")[0]
            return f"[发了一个表情包]{txt}"

        if self.类型 == "图片":
            return f"[发了一张图片, 宽高: {self.尺寸}]"

        if self.类型 == "视频":
            return f"[发了一个视频, 宽高: {self.尺寸}]"

        if self.类型 == "头像":
            return self.data.get("content-desc")[:-3]

        if self.类型 == "关注按钮":
            return "[发了一张求关注的名片]"

        # if self.类型 == "已关注名片":
        #     return "[发了一张名片, 你已关注]"

        # raise ValueError(f"未知类型: {self.类型}")
        return " ".join(filter(lambda x: x, (self.文本, self.内容描述)))

    def 是否头像靠左(self):
        assert self.类型 == "头像", "类型不是头像"
        return self.rect.left < 300


class 消息体(object):
    def __init__(self, data: list[dict], rect=None):
        self.container = list(
            filter(lambda x: x is not None, map(元素.from_dict, data))
        )
        self.big_rect = rect

    def __str__(self):
        return self.正文

    def __repr__(self):
        return f"{self.正文}|{self.类型}|{self.rect}"

    @cached_property
    def 主体元素(self):
        for x in self.container:
            if x.类型 == self.类型:
                return x

    @cached_property
    def 正文(self):
        if self.主体元素:
            return self.主体元素.内容
        # data_list = filter(lambda x:x.类型 != '头像', self.container)
        # return ' '.join(map(lambda x:x.内容, data_list))

    @cached_property
    def rect(self):
        if self.主体元素:
            return self.主体元素.rect
        rect = None
        for x in self.container:
            if rect is None:
                rect = x.rect
            elif x.rect.contains(rect):
                rect = x.rect
        return rect

    def 是否冒头(self):
        return self.big_rect is None or self.rect.top <= self.big_rect.top

    def 是否触底(self):
        return self.big_rect is None or self.rect.bottom >= self.big_rect.bottom

    @cached_property
    def 字典(self):
        return {
            "发言者": self.发言者,
            "正文": self.正文,
            "bounds": str(self.rect.to_bounds()),
            "类型": self.类型,
            "自己": self.是否自己(),
            "冒头": self.是否冒头(),
            "触底": self.是否触底(),
        }

    @cached_property
    def 类型列表(self):
        return list(map(lambda x: x.类型, self.container))

    def 是否有效(self):
        """
        是否有效 的 Docstring

        :param self: 说明
        >>> 消息体([{'tag': 'android.widget.ImageView', 'text': '', 'content-desc': '视频', 'bounds': '[676,257][912,557]'}]).是否有效()
        True
        >>> 消息体([]).是否有效()
        False
        >>> 消息体([{'tag': 'android.widget.Button', 'text': '', 'content-desc': '开心姐姐的头像', 'bounds': '[36,605][144,713]'}, {'tag': 'android.widget.ImageView', 'text': '', 'content-desc': '视频', 'bounds': '[168,617][404,1037]'}]).是否有效()
        True
        >>> 消息体([{'tag': 'android.widget.TextView', 'text': '暂时没有更多了', 'content-desc': '', 'bounds': '[0,1343][1080,1523]'}]).是否有效()
        False
        >>> 消息体([{'tag': 'android.widget.TextView', 'text': '再连续互聊 2 天 可点亮火花，和对方合养精灵', 'content-desc': '', 'bounds': '[148,1472][931,1533]'}]).是否有效()
        False
        >>> 消息体([{'tag': 'android.widget.TextView', 'text': '23:19', 'content-desc': '23:19', 'bounds': '[469,831][610,892]'}, {'tag': 'android.widget.Button', 'text': '', 'content-desc': '@徐二妹《普欣》的头像', 'bounds': '[36,934][144,1042]'}, {'tag': 'android.widget.TextView', 'text': '@徐二妹《普欣》', 'content-desc': '', 'bounds': '[168,934][455,983]'}, {'tag': 'android.widget.TextView', 'text': '@徐二妹《普欣》', 'content-desc': '', 'bounds': '[372,1072][666,1133]'}, {'tag': 'android.widget.TextView', 'text': '关注', 'content-desc': '', 'bounds': '[690,1061][870,1145]'}]).类型
        '关注按钮'
        """
        return (
            len(self.container) > 0
            # and "头像" in self.类型列表
            and self.类型 is not None
            # and (self.big_rect is None or (self.rect.top > self.big_rect.top and self.rect.bottom < self.big_rect.bottom))
        )

    @cached_property
    def 头像(self):
        for x in self.container:
            if x.类型 == "头像":
                return x

    @property
    def 发言者(self):
        return self.头像.内容 if self.头像 else np.nan

    def 是否自己(self):
        return not self.头像.是否头像靠左() if self.头像 else np.nan

    def 是否包含文本(self, text):
        return any([x.文本 == text for x in self.container])

    @property
    def 类型(self):
        """
        类型 的 Docstring

        :param self: 说明
        >>> 消息体([{'tag': 'android.widget.ImageView', 'text': '', 'content-desc': '视频', 'bounds': '[676,257][912,557]'}]).类型
        '视频'
        >>> 消息体([{'tag': 'android.widget.Button', 'text': '', 'content-desc': '开心姐姐的头像', 'bounds': '[36,605][144,713]'}, {'tag': 'android.widget.ImageView', 'text': '', 'content-desc': '视频', 'bounds': '[168,617][404,1037]'}]).类型
        '视频'
        >>> 消息体([{'tag': 'android.widget.TextView', 'text': '15:58', 'content-desc': '15:58', 'bounds': '[469,1079][610,1140]'}, {'tag': 'android.widget.Button', 'text': '', 'content-desc': '开心姐姐的头像', 'bounds': '[36,1182][144,1290]'}, {'tag': 'com.bytedance.ies.dmt.ui.widget.DmtTextView', 'text': '', 'content-desc': '图片,按钮', 'bounds': '[168,1194][588,1430]'}]).类型
        '图片'
        >>> 消息体([{'tag': 'android.widget.Button', 'text': '', 'content-desc': '开心姐姐的头像', 'bounds': '[36,1575][144,1683]'}, {'tag': 'com.bytedance.ies.dmt.ui.widget.DmtTextView', 'text': '', 'content-desc': '##this is the command and req', 'bounds': '[168,1587][840,1766]'}, {'tag': 'android.widget.TextView', 'text': '##this is the command and req', 'content-desc': '', 'bounds': '[204,1611][804,1742]'}]).类型
        '文本'
        >>> 消息体([{'tag': 'android.widget.TextView', 'text': '刚刚', 'content-desc': '刚刚', 'bounds': '[480,1808][600,1869]'}, {'tag': 'android.widget.TextView', 'text': '装扮', 'content-desc': '', 'bounds': '[405,1951][489,2008]'}, {'tag': 'com.bytedance.ies.dmt.ui.widget.DmtTextView', 'text': '', 'content-desc': '这是我的信息', 'bounds': '[552,1923][912,2036]'}, {'tag': 'android.widget.TextView', 'text': '这是我的信息', 'content-desc': '', 'bounds': '[588,1947][876,2012]'}, {'tag': 'android.widget.Button', 'text': '', 'content-desc': '数字人生的头像', 'bounds': '[936,1911][1044,2019]'}]).类型
        '文本'
        >>> 消息体([{'tag': 'android.widget.TextView', 'text': '刚刚', 'content-desc': '刚刚', 'bounds': '[480,1625][600,1686]'}, {'tag': 'android.widget.Button', 'text': '', 'content-desc': '数字人生的头像', 'bounds': '[936,1728][1044,1836]'}, {'tag': 'com.bytedance.ies.dmt.ui.widget.DmtTextView', 'text': '', 'content-desc': '早上好 表情包', 'bounds': '[0,1625][1080,2040]'}]).类型
        '表情包'

        #>>> 消息体([{'tag': 'android.widget.Button', 'text': '', 'content-desc': '再次见到你的头像', 'bounds': '[36,501][144,609]'}, {'tag': 'android.widget.TextView', 'text': '再次见到你', 'content-desc': '', 'bounds': '[168,501][348,550]'}, {'tag': 'android.widget.TextView', 'text': '再次见到你', 'content-desc': '', 'bounds': '[372,639][597,700]'}]).类型
        #'已关注名片'
        """
        if "视频" in self.类型列表:
            return "视频"
        if "图片" in self.类型列表:
            return "图片"
        if "文本" in self.类型列表:
            return "文本"
        if "表情包" in self.类型列表:
            return "表情包"
        if "关注按钮" in self.类型列表:
            return "关注按钮"

        # if self.头像 and self.是否包含文本(self.发言者):
        #     return "已关注名片"


class 页面(object):
    def __init__(self, element_recycle):
        x = "//androidx.recyclerview.widget.RecyclerView/*"
        x = "./*"
        self.elements = element_recycle.elem.xpath(x)
        # self.elements = element_recycle.elem.xpath(".//*")
        self.rect = tool_env.bounds_to_rect(element_recycle.bounds)

        print("rect of recycle:", self.rect)

    def get_data(self, debug=True):
        rtn = []
        for x in self.elements:
            tmp = []
            results = [i for i in x.xpath(".//*")]
            results.append(x)

            for e in results:
                if not e.attrib.get("text") and not e.attrib.get("content-desc"):
                    continue
                d = {
                    "tag": e.tag,
                    "text": e.attrib.get("text"),
                    "content-desc": e.attrib.get("content-desc"),
                    "bounds": e.attrib.get("bounds"),
                }
                tmp.append(d)
            if debug:
                print("=" * 40)
                print(tmp)
            rtn.append(tmp)
        return rtn

    @property
    def messages(self):
        return list(
            filter(
                lambda y: y.是否有效(),
                map(lambda x: 消息体(x, self.rect), self.get_data()),
            )
        )

    @property
    def df_full(self):
        df = pd.DataFrame(data=[x.字典 for x in self.messages])
        # print(df)
        if df.empty:
            return
        df["发言者"] = df["发言者"].ffill()
        df["自己"] = df["自己"].ffill()
        df = df[(~df.冒头) & (~df.触底) & (~pd.isna(df.发言者))]
        # print(df)
        if df.empty:
            return
        df["唯一值"] = df.发言者 + ":" + df.正文
        # df.drop(columns=['冒头', '触底', 'bounds', '类型', '发言者', '正文'], inplace=True)
        return df[["唯一值", "自己", "bounds", "类型", "发言者", "正文"]]


    @cached_property
    def df(self):
        df = self.df_full
        return self.df_full[["唯一值", "自己"]] if df is not None else df
        # df = pd.DataFrame(data=[x.字典 for x in self.messages])
        # # print(df)
        # if df.empty:
        #     return
        # df["发言者"] = df["发言者"].ffill()
        # df["自己"] = df["自己"].ffill()
        # df = df[(~df.冒头) & (~df.触底) & (~pd.isna(df.发言者))]
        # # print(df)
        # if df.empty:
        #     return
        # df["唯一值"] = df.发言者 + ":" + df.正文
        # # df.drop(columns=['冒头', '触底', 'bounds', '类型', '发言者', '正文'], inplace=True)
        # return df[["唯一值", "自己", "bounds"]]


# 执行单元测试
if __name__ == "__main__":
    import doctest

    df_single1 = pd.DataFrame(
        [
            {"唯一值": "开心姐姐:##this is the command and req", "自己": True},
            {"唯一值": "数字人生:这是我的信息", "自己": False},
            {"唯一值": "数字人生:[发了一个表情包]早上好", "自己": False},
            {"唯一值": "数字人生:12345", "自己": False},
            {"唯一值": "数字人生:56789", "自己": False},
            {"唯一值": "数字人生:发反反复复", "自己": False},
            {"唯一值": "数字人生:[发了一个表情包]比心", "自己": False},
        ]
    )
    print(doctest.testmod(verbose=False, report=False))
