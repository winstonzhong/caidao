"""
Created on 2023年12月13日

@author: lenovo
"""

import re

import random

import numpy


ptn_pair = re.compile("[^:]+:[^:^\s]+")
ptn_device_info = re.compile("^([^\s]+)\s+[^\n]+device:([^\s]+)", re.M)


def parse_line_to_dict(line):
    """
    >>> d = parse_line_to_dict('192.168.0.115:7002     device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:3')
    >>> d.get('id')
    '192.168.0.115:7002'
    >>> d.get('name')
    'HWALP'
    >>> d.get('offline')
    >>> parse_line_to_dict('192.168.0.190:7080     offline product:OCE-AN10 model:OCE_AN10 device:HWOCE-L transport_id:33').get('offline')
    True
    """
    l = re.split("\s+", line)
    d = {"id": l[0]}
    for x in l[1:]:
        tmp = re.split(":", x, maxsplit=1)
        if len(tmp) == 2:
            d[tmp[0]] = tmp[1]
        elif tmp[0].strip() == "offline":
            d["offline"] = True

    d["name"] = d.get("device")
    d["transport_id"] = int(d.get("transport_id"))

    return d


def parse_devices(txt):
    """
    >>> list(parse_devices(txt0))
    []
    >>> l = list(parse_devices(txt1))
    >>> len(l) == 1
    True
    >>> l[0].get('id')
    '192.168.0.115:7002'
    >>> l = list(parse_devices(txt2))
    >>> len(l) == 2
    True
    >>> l[0].get('id')
    'D3H7N18126007114'
    >>> l[1].get('id')
    '192.168.0.115:7002'
    >>> l[1].get('name')
    'HWALP'
    >>> l[1].get('transport_id')
    3
    >>> l[0].get('transport_id')
    5
    """

    l = [x.strip() for x in txt.splitlines() if x.strip()]

    for line in l[1:]:
        yield parse_line_to_dict(line)

def 修正滑动起始(起始点, 结束点, 模拟人工=False):
    """
    修正滑动的起始点和结束点，模拟人工滑动的随机偏差

    参数:
        起始点: 元组/列表，格式为(x, y)，表示滑动起始坐标
        结束点: 元组/列表，格式为(x, y)，表示滑动结束坐标
        模拟人工: 布尔值，是否添加±5%的随机坐标偏差

    返回:
        元组，格式为(修正后起始点, 修正后结束点)，均为元组类型

    Doctest测试用例（固定随机种子保证可复现）:
    >>> random.seed(42)  # 固定随机种子，确保测试结果一致

    >>> # 测试1：模拟人工为False，返回原始坐标
    >>> start1 = (100, 200)
    >>> end1 = (500, 200)
    >>> 修正滑动起始(start1, end1, False)
    ((100, 200), (500, 200))
    >>> # 测试2：模拟人工为True，x方向滑动（修正y坐标）
    >>> corrected1 = 修正滑动起始(start1, end1, True)
    >>> round(corrected1[0][1], 2)  # 修正后的起始点y坐标（保留2位小数）
    202.79
    >>> round(corrected1[1][1], 2)  # 修正后的结束点y坐标（保留2位小数）
    190.5
    >>> # 测试3：模拟人工为True，y方向滑动（修正x坐标）
    >>> start2 = (200, 100)
    >>> end2 = (200, 500)
    >>> corrected2 = 修正滑动起始(start2, end2, True)
    >>> round(corrected2[0][0], 2)  # 修正后的起始点x坐标（保留2位小数）
    195.5
    >>> round(corrected2[1][0], 2)  # 修正后的结束点x坐标（保留2位小数）
    194.46
    """
    # 非人工模拟：直接返回原始坐标（转元组避免修改原数据）
    if not 模拟人工:
        return tuple(起始点), tuple(结束点)

    # 计算x/y方向的位移量
    dx = 结束点[0] - 起始点[0]
    dy = 结束点[1] - 起始点[1]

    # 复制坐标避免修改原始数据
    修正后起始点 = list(起始点)
    修正后结束点 = list(结束点)

    def random_offset(v1, v2):
        avg = numpy.mean((v1, v2))
        return v1 + avg * random.uniform(-0.05, 0.05), v2 + avg * random.uniform(-0.05, 0.05)

    # 判断滑动方向：x方向（dx绝对值更大）或y方向（dy绝对值更大）
    if abs(dx) > abs(dy):
        修正后起始点[1], 修正后结束点[1] = random_offset(修正后起始点[1], 修正后结束点[1])
    else:
        修正后起始点[0], 修正后结束点[0] = random_offset(修正后起始点[0], 修正后结束点[0])

    # 转元组返回（保持不可变特性）
    return tuple(修正后起始点), tuple(修正后结束点)


if __name__ == "__main__":
    import doctest

    txt0 = "List of devices attached\n"
    txt1 = "List of devices attached\n192.168.0.115:7002     device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:3\n\n"
    txt2 = "List of devices attached\nD3H7N18126007114       device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:5\n192.168.0.115:7002     device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:3\n\n"
    print(doctest.testmod(verbose=False, report=False))
