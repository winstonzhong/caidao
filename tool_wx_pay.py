from functools import cached_property
import re


from tool_rect import Rect

import tool_time

import numpy

import tool_date

import pandas

import helper_hash

time_pattern = re.compile(
    r"((\d{1,2}月\d{1,2}日|今天|昨天|前天|\d{4}-\d{1,2}-\d{1,2})\s*)?((上午|下午|晚上)\s*)?\d{1,2}:\d{1,2}"
)


def parse_payment_info(lines):
    """
    解析支付相关信息
    :param lines: 多行文本
    :return: 包含时间、类别、金额和今日批次的字典

    >>> example1 = ['3月31日 上午10:44', '剪映', ' 使用零钱支付￥45.00账单详情', '使用零钱支付', '￥', '45.00', '账单详情', '收单机构', '财付通支付科技有限公司']
    >>> parse_payment_info(example1)
    {'时间': '3月31日 上午10:44', '类别': '其他', '金额': '45.00', '今日批次': '', '收款方备注': ''}

    >>> example2 = ['昨天 10:50', '收款到账通知', ' 收款金额￥0.10', '收款金额', '￥', '0.10', '收款方备注', 'add', '汇总', '今日第1笔收款，共计￥0.10', '备注', '收款成功，已存入零钱。点击可查看详情']
    >>> parse_payment_info(example2)
    {'时间': '昨天 10:50', '类别': '收款到账通知', '金额': '0.10', '今日批次': '1', '收款方备注': 'add'}

    >>> example3 = ['收款到账通知', ' 收款金额￥0.10', '收款金额', '￥', '0.10', '收款方备注', 'add', '汇总', '今日第2笔收款，共计￥0.20', '备注', '收款成功，已存入零钱。点击可查看详情', '收款小账本']
    >>> parse_payment_info(example3)
    {'时间': '', '类别': '收款到账通知', '金额': '0.10', '今日批次': '2', '收款方备注': 'add'}

    >>> example4 = ['昨天 10:50 ', '收款到账通知 ', ' 收款金额￥0.10', '收款金额 ', '￥ ', '0.10 ', '收款方备注 ', 'add ', '汇总 ', '今日第1笔收款，共计￥0.10 ', '备注 ', '收款成功，已存入零钱。点击可查看详情 ', '收款小账本 ']
    >>> parse_payment_info(example4)
    {'时间': '昨天 10:50', '类别': '收款到账通知', '金额': '0.10', '今日批次': '1', '收款方备注': 'add'}

    >>> example5 = ['收款到账通知 ', ' 收款金额￥0.10', '收款金额 ', '￥ ', '0.10 ', '收款方备注 ', 'test ', '汇总 ', '今日第2笔收款，共计￥0.20 ', '备注 ', '收款成功，已存入零钱。点击可查看详情 ', '收款小账本 ']
    >>> parse_payment_info(example5)
    {'时间': '', '类别': '收款到账通知', '金额': '0.10', '今日批次': '2', '收款方备注': 'test'}

    >>> example6 = ['10:45 ', '收款到账通知 ', ' 收款金额￥30.00', '收款金额 ', '￥ ', '30.00 ', '收款方备注 ', 'aTAYr5zSTxx_ ', '汇总 ', '今日第3笔收款，共计￥30.20 ', '备注 ', '收款成功，已存入零钱。点击可查看详情 ', '收款小账本 ']
    >>> parse_payment_info(example6)
    {'时间': '10:45', '类别': '收款到账通知', '金额': '30.00', '今日批次': '3', '收款方备注': 'aTAYr5zSTxx_'}

    >>> example7 = ['周四 10:45 ', '收款到账通知 ', ' 收款金额￥30.00', '收款金额 ', '￥ ', '30.00 ', '收款方备注 ', 'aTAYr5zSTxx_ ', '汇总 ', '今日第3笔收款，共计￥30.20 ', '备注 ', '收款成功，已存入零钱。点击可查看详情 ', '收款小账本 ']
    >>> parse_payment_info(example7)
    {'时间': '周四 10:45', '类别': '收款到账通知', '金额': '30.00', '今日批次': '3', '收款方备注': 'aTAYr5zSTxx_'}
    """

    time = ""
    category = "其他"
    amount = ""
    batch = ""
    remark = ""

    if not lines:
        return {
            "时间": time,
            "类别": category,
            "金额": amount,
            "今日批次": batch,
            "收款方备注": remark,
        }

    first_line = lines[0].strip()

    if (
        time_pattern.match(first_line)
        or tool_time.convert_chinese_datetime(first_line) is not None
    ):
        time = first_line
        lines = lines[1:]
    else:
        time = ""

    # 确定类别
    category_line = lines[0].strip() if lines else ""
    if category_line == "收款到账通知":
        category = "收款到账通知"
    else:
        category = "其他"

    # 提取金额
    amount_pattern = re.compile(r"￥\s*(\d+\.\d{2})")
    amount_found = False
    for line in lines:
        match = amount_pattern.search(line)
        if match:
            amount = match.group(1)
            amount_found = True
            break
    # 如果没有找到金额，尝试另一种模式
    if not amount_found:
        amount_pattern_alt = re.compile(r"(\d+\.\d{2})")
        for line in lines:
            match = amount_pattern_alt.search(line)
            if match and "共计" not in line:
                amount = match.group(1)
                break

    # 提取今日批次
    if category == "收款到账通知":
        batch_pattern = re.compile(r"今日第(\d+)笔收款")
        for line in lines:
            match = batch_pattern.search(line)
            if match:
                batch = match.group(1)
                break

        # 提取收款方备注
        remark_pattern = re.compile(r"收款方备注\s*")
        remark_index = -1
        for i, line in enumerate(lines):
            if remark_pattern.match(line):
                remark_index = i
                break
        if remark_index != -1 and remark_index + 1 < len(lines):
            remark = lines[remark_index + 1].strip()

    return {
        "时间": time,
        "类别": category,
        "金额": amount,
        "今日批次": batch,
        "收款方备注": remark,
    }


class NoticeContainer(object):
    """
    >>> NoticeContainer(normal_element).height
    915
    >>> NoticeContainer(normal_element).width
    1080
    """

    def __init__(self, e):
        self.e = e
        self.rect = Rect.from_ltrb(*e.bounds)

    def __str__(self):
        return f"{self.dict_date}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, NoticeContainer) and self.dict_date == other.dict_date

    def parse_element(self):
        rtn = []
        for x in self.e.elem.xpath(".//*"):
            text = x.attrib.get("text") or ""
            desc = x.attrib.get("content-desc") or ""
            if text or desc:
                rtn.append(f"{text} {desc}")
        return rtn

    @cached_property
    def dict(self):
        return parse_payment_info(self.parse_element())

    @cached_property
    def dict_date(self):
        d = self.dict
        dt = tool_time.convert_chinese_datetime(d.pop("时间", None) or None)
        d["日期"] = tool_date.dash_date(dt) if dt is not None else numpy.nan
        # d['key'] = helper_hash.get_hash_jsonable(d)
        return d

    @classmethod
    def to_containers(cls, elements, only_ok=True):
        el = map(lambda x: cls(x), elements)
        el = el if not only_ok else filter(lambda x: x.is_ok(), el)
        return list(el)

    @classmethod
    def to_df(cls, elements, only_ok=True):
        return pandas.DataFrame(
            [x.dict_date for x in cls.to_containers(elements, only_ok)]
        )

    @classmethod
    def print_results(cls, results, only_ok=True, show_raw=False):
        for i, x in enumerate(cls.to_containers(results, only_ok)):
            print("=" * 50)
            print(x.rect, x.e.bounds, x.hegitht_ratio, x.is_ok())
            print(x.parse_element()) if show_raw else None
            print("\n")
            print(x.dict_date)
            print("=" * 50)

    @property
    def height(self):
        return self.rect.height

    @property
    def width(self):
        return self.rect.width

    @property
    def top(self):
        return self.rect.top

    @property
    def bottom(self):
        return self.rect.bottom

    @property
    def left(self):
        return self.rect.left

    @property
    def right(self):
        return self.rect.right

    @cached_property
    def parent(self):
        return NoticeContainer(self.e.parent())

    @property
    def hegitht_ratio(self):
        """
        >>> numpy.isclose(NoticeContainer(headed_element).hegitht_ratio,0.26897605705552724)
        True
        >>> numpy.isclose(NoticeContainer(normal_element).hegitht_ratio, 0.4661232806928171)
        True
        >>> numpy.isclose(NoticeContainer(tailed_element).hegitht_ratio, 0.26490066225165565)
        True
        >>> NoticeContainer(tailed_ok_element).hegitht_ratio >= 0.45
        True
        >>> NoticeContainer(debug_element).hegitht_ratio >= 0.40
        True
        """
        return self.height / self.parent.height

    def is_headed(self):
        """
        >>> NoticeContainer(headed_element).is_headed()
        True
        >>> NoticeContainer(normal_element).is_headed()
        False
        >>> NoticeContainer(tailed_element).is_headed()
        False
        """
        return self.top <= self.parent.top

    def is_tailed(self):
        """
        >>> NoticeContainer(headed_element).is_tailed()
        False
        >>> NoticeContainer(normal_element).is_tailed()
        False
        >>> NoticeContainer(tailed_element).is_tailed()
        True
        """
        return self.bottom >= self.parent.bottom

    def is_ok(self):
        """
        >>> NoticeContainer(headed_element).is_ok()
        False
        >>> NoticeContainer(normal_element).is_ok()
        True
        >>> NoticeContainer(tailed_element).is_ok()
        False
        >>> NoticeContainer(tailed_ok_element).is_ok()
        True
        >>> NoticeContainer(debug_element).is_ok()
        True
        >>> NoticeContainer(top_element).is_ok()
        True
        """
        if self.is_headed():
            return bool(self.dict.get("时间"))
        else:
            return not self.is_tailed() or self.hegitht_ratio >= 0.4


if __name__ == "__main__":
    import doctest

    class DummyX(object):
        def __init__(self, s):
            self.attrib = {"text": s}

    class DummyElement(object):
        def __init__(self, bounds, parent=None, raw=None):
            self.bounds = bounds
            self._parent = parent
            self.raw = (
                [
                    # "3月12日 下午17:51 ",
                    "收款到账通知 ",
                    " 收款金额￥0.01",
                    "收款金额 ",
                    "￥ ",
                    "0.01 ",
                    "汇总 ",
                    "今日第2笔收款，共计￥1.11 ",
                    "备注 ",
                    "收款成功，已存入零钱。点击可查看详情 ",
                    "收款小账本 ",
                ]
                if raw is None
                else raw
            )

        def parent(self):
            return self._parent

        @property
        def elem(self):
            return self

        def xpath(self, *a, **kw):
            return [DummyX(i) for i in self.raw]

    parent_element = DummyElement((0, 226, 1080, 2189))

    headed_element = DummyElement((0, 226, 1080, 754), parent_element)

    normal_element = DummyElement((0, 754, 1080, 1669), parent_element)

    tailed_element = DummyElement((0, 1669, 1080, 2189), parent_element)

    tailed_ok_element = DummyElement((0, 1290, 1080, 2189), parent_element)

    debug_element = DummyElement((0, 1369, 1080, 2189), parent_element)

    top_element = DummyElement(
        (0, 226, 1080, 1149),
        parent_element,
        [
            "3月12日 下午17:51 ",
            "收款到账通知 ",
            " 收款金额￥0.01",
            "收款金额 ",
            "￥ ",
            "0.01 ",
            "汇总 ",
            "今日第2笔收款，共计￥1.11 ",
            "备注 ",
            "收款成功，已存入零钱。点击可查看详情 ",
            "收款小账本 ",
        ],
    )

    print(doctest.testmod(verbose=False, report=False))
