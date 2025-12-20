"""
Created on 2023年12月19日

@author: lenovo
"""

import numpy
import pandas
from tool_rect import Rect
import cv2
from tool_img import show_in_plt, img2edges


def find_split_points(s, all_split=False, v_min=0, span_min=None):
    """
    >>> find_split_points((0,1,1,1,1,1,0))
       0    1
    0  0  6.0
    >>> find_split_points((0,1,1,0,1,1,0))
       0    1
    0  0  3.0
    3  3  6.0
    """
    s = pandas.Series(s)
    s = s[s <= v_min].index.to_series()
    df = pandas.concat([s, s.shift(-1)], axis=1)
    span = span_min or 1
    df = df[df[1] - df[0] > span]
    if not all_split:
        v = (df[1] - df[0]).std() if span_min is None else span_min
        if not numpy.isnan(v):
            df = df[df[1] - df[0] > v]
    return df


def split_cuizhi(mask, all_split=False, v_min=0, span_min=None):
    df = (
        find_split_points(mask.sum(axis=0), all_split, v_min, span_min)
        .rename(columns={0: "left", 1: "right"})
        .astype(int)
    )
    return df.to_dict("records")


def split_shuiping(mask, all_split=False, v_min=0, span_min=None):
    df = (
        find_split_points(mask.sum(axis=1), all_split, v_min, span_min)
        .rename(columns={0: "top", 1: "bottom"})
        .astype(int)
    )
    return df.to_dict("records")


def split_smart(mask, all_split=False, v_min=0, span_min=None):
    for x in split_shuiping(mask, all_split, v_min, span_min):
        for y in split_cuizhi(mask, all_split, v_min, span_min):
            tmp = y.copy()
            tmp.update(x)
            if Rect(**tmp).crop_img(mask).sum() > 0:
                yield tmp


def 绘制切分结果(img: numpy.ndarray, rlist: list):
    """
    在CV2格式的图片上绘制切分区域的红色矩形框，支持缺省值处理

    Args:
        img: CV2格式的图片数组（np.ndarray），BGR通道
        rlist: 切分区域列表，每个元素是字典，包含top/bottom或left/right（支持缺省）
            - top/bottom缺失时：top=1，bottom=图片高度-1
            - left/right缺失时：left=1，right=图片宽度-1

    Returns:
        np.ndarray: 绘制了红色矩形框的图片（复制原图绘制，不修改输入原图）
    """
    # 1. 复制原图，避免修改输入的原始图片
    img_draw = img.copy()

    # 2. 获取图片的宽高，用于缺省值计算
    img_height = img.shape[0]  # CV2图片shape：(高度, 宽度, 通道数)
    img_width = img.shape[1]

    # 3. 定义绘制参数：红色（BGR格式）、线条粗细2
    rect_color = (0, 0, 255)  # CV2中红色是B=0, G=0, R=255
    rect_thickness = 2

    # 4. 遍历每个切分区域，绘制矩形
    for region in rlist:
        # 提取参数并处理缺省值
        left = region.get("left", 1)  # left缺省为1
        right = region.get("right", img_width - 1)  # right缺省为宽度-1
        top = region.get("top", 1)  # top缺省为1
        bottom = region.get("bottom", img_height - 1)  # bottom缺省为高度-1

        # 绘制矩形：cv2.rectangle(图片, 左上角坐标, 右下角坐标, 颜色, 线条粗细)
        # 左上角：(left, top)，右下角：(right, bottom)
        cv2.rectangle(
            img_draw,
            (int(left), int(top)),  # 确保坐标为整数（防止传入浮点数）
            (int(right), int(bottom)),
            rect_color,
            rect_thickness,
        )

    # 5. 返回绘制后的图片
    show_in_plt(img_draw)

def 绘制水平切分结果(img, all_split=False, v_min=0, span_min=None, low=70, high=200):
    mask = img2edges(img, low, high)
    绘制切分结果(img, split_shuiping(mask, all_split, v_min, span_min))

if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
