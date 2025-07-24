from functools import cached_property
import re


from tool_rect import Rect

time_pattern = re.compile(
    r"((\d{1,2}月\d{1,2}日|今天|昨天|前天|\d{4}-\d{1,2}-\d{1,2})\s*)?((上午|下午|晚上)\s*)?\d{1,2}:\d{1,2}"
)


# time_pattern = re.compile(r"(\d{1,2}月\d{1,2}日|今天|昨天|前天|\d{4}-\d{1,2}-\d{1,2})\s*(上午|下午|晚上)?\s*\d{1,2}:\d{1,2}")
def parse_payment_info(lines):
    """
    解析支付相关信息
    :param lines: 多行文本
    :return: 包含时间、类别、金额和今日批次的字典

    >>> example1 = ['3月31日 上午10:44', '剪映', ' 使用零钱支付￥45.00账单详情', '使用零钱支付', '￥', '45.00', '账单详情', '收单机构', '财付通支付科技有限公司']
    >>> parse_payment_info(example1)
    {'时间': '3月31日 上午10:44', '类别': '其他', '金额': '45.00', '今日批次': ''}

    >>> example2 = ['昨天 10:50', '收款到账通知', ' 收款金额￥0.10', '收款金额', '￥', '0.10', '收款方备注', 'add', '汇总', '今日第1笔收款，共计￥0.10', '备注', '收款成功，已存入零钱。点击可查看详情']
    >>> parse_payment_info(example2)
    {'时间': '昨天 10:50', '类别': '收款到账通知', '金额': '0.10', '今日批次': '1'}

    >>> example3 = ['收款到账通知', ' 收款金额￥0.10', '收款金额', '￥', '0.10', '收款方备注', 'add', '汇总', '今日第2笔收款，共计￥0.20', '备注', '收款成功，已存入零钱。点击可查看详情', '收款小账本']
    >>> parse_payment_info(example3)
    {'时间': '', '类别': '收款到账通知', '金额': '0.10', '今日批次': '2'}

    >>> example4 = ['昨天 10:50 ', '收款到账通知 ', ' 收款金额￥0.10', '收款金额 ', '￥ ', '0.10 ', '收款方备注 ', 'add ', '汇总 ', '今日第1笔收款，共计￥0.10 ', '备注 ', '收款成功，已存入零钱。点击可查看详情 ', '收款小账本 ']
    >>> parse_payment_info(example4)
    {'时间': '昨天 10:50', '类别': '收款到账通知', '金额': '0.10', '今日批次': '1'}

    >>> example5 = ['收款到账通知 ', ' 收款金额￥0.10', '收款金额 ', '￥ ', '0.10 ', '收款方备注 ', 'test ', '汇总 ', '今日第2笔收款，共计￥0.20 ', '备注 ', '收款成功，已存入零钱。点击可查看详情 ', '收款小账本 ']
    >>> parse_payment_info(example5)
    {'时间': '', '类别': '收款到账通知', '金额': '0.10', '今日批次': '2'}

    >>> example6 = ['10:45 ', '收款到账通知 ', ' 收款金额￥30.00', '收款金额 ', '￥ ', '30.00 ', '收款方备注 ', 'aTAYr5zSTxx_ ', '汇总 ', '今日第3笔收款，共计￥30.20 ', '备注 ', '收款成功，已存入零钱。点击可查看详情 ', '收款小账本 ']
    >>> parse_payment_info(example6)
    {'时间': '10:45', '类别': '收款到账通知', '金额': '30.00', '今日批次': '3'}
    """

    time = ""
    category = "其他"
    amount = ""
    batch = ""

    if not lines:
        return {"时间": time, "类别": category, "金额": amount, "今日批次": batch}

    first_line = lines[0].strip()
    # 判断第一行是否为时间
    # time_pattern = re.compile(r"(\d{1,2}月\d{1,2}日|今天|昨天|前天|\d{4}-\d{1,2}-\d{1,2})\s*(上午|下午|晚上)?\s*\d{1,2}:\d{1,2}")
    if time_pattern.match(first_line):
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

    return {"时间": time, "类别": category, "金额": amount, "今日批次": batch}


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
        """
        return not self.is_headed() and (not self.is_tailed() or self.hegitht_ratio > 0.45)

if __name__ == "__main__":
    import doctest
    import numpy

    class DummyElement(object):
        def __init__(self, bounds, parent=None):
            self.bounds = bounds
            self._parent = parent

        def parent(self):
            return self._parent

    parent_element = DummyElement((0, 226, 1080, 2189))

    headed_element = DummyElement((0, 226, 1080, 754), parent_element)

    normal_element = DummyElement((0, 754, 1080, 1669), parent_element)

    tailed_element = DummyElement((0, 1669, 1080, 2189), parent_element)

    tailed_ok_element = DummyElement((0, 1290, 1080, 2189), parent_element)

    print(doctest.testmod(verbose=False, report=False))
