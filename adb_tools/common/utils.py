import math

import re


def parse_bounds(bounds_str):
    """
    >>> parse_bounds('[25,2208][175,2249]')
    [25, 2208, 175, 2249]
    """
    return [int(i) for i in re.compile('(\d+)').findall(bounds_str)]




def swipe_safe(width, height, start_x, start_y, end_x, end_y):
    """
    安全区域滑动: 为避免在手机边缘滑动和系统操作冲突, 把滑动移动至屏幕中心操作,可能会涉及到一次滑动拆分为多次滑动
    :param width: 屏幕宽度
    :param height: 屏幕高度
    :param start_x: 开始X坐标
    :param start_y: 开始Y坐标
    :param end_x: 结束X坐标
    :param end_y: 结束Y坐标
    :return: [(start_x1, start_y1, end_x1, end_x1), (start_x2, start_y2, end_x2, end_x2),...]
    >>> swipe_safe(600, 800, 500, 100, 0, 100)
    [[300, 100, 0, 100], [300, 100, 100, 100]]
    >>> swipe_safe(600, 800, 0, 100, 500, 100)
    [[300, 100, 600, 100], [300, 100, 500, 100]]

    >>> swipe_safe(600, 800, 100, 100, 100, 600)
    [[100, 400, 100, 800], [100, 400, 100, 500]]
    >>> swipe_safe(600, 800, 100, 600, 100, 100)
    [[100, 400, 100, 0], [100, 400, 100, 300]]

    """
    # start_x = int(width/2)
    # start_y = int(height/2)
    # distance_x = abs(end_x - start_x)
    # distance_y = abs(start_y - end_y)
    # direction_x = 1 if end_x > start_x else 0
    # direction_y = 1 if end_y > start_y else 0
    #
    # max_swipe_distance_x = width - start_x
    # max_swipe_distance_y = height -start_y
    #
    # item_list = []
    #
    # while distance_x or distance_y:
    #
    #     if direction_x > 0:
    #         if distance_x > max_swipe_distance_x:
    #             end_x_tmp = width
    #             distance_x -= max_swipe_distance_x
    #         else:
    #             end_x_tmp = distance_x
    #             distance_x = 0
    #     else:
    #         if distance_x > max_swipe_distance_x:
    #             end_x_tmp = 0
    #             distance_x -= max_swipe_distance_x
    #         else:
    #             end_x_tmp = max_swipe_distance_x - distance_x
    #             distance_x = 0
    #
    #     if distance_y == 0:
    #         start_y = start_y
    #         end_y_tmp =
    #
    #     if distance_y > max_swipe_distance_y:
    #         end_y_tmp = width
    #         distance_y += max_swipe_distance_y
    #     else:
    #         end_y_tmp = distance_y
    #         distance_y = 0
    #     item = [start_x, end_y_tmp, end_x, end_y_tmp]
    #     item_list.append(item)
    # return item_list
    item_x = swipe_split(width, start_x, end_x)
    item_y = swipe_split(height, start_y, end_y)
    ret_list = []
    for i in range(2):
        if item_x[i][0] == item_x[i][1] and item_y[i][0] == item_y[i][1]:
            continue
        item = [item_x[i][0], item_y[i][0], item_x[i][1], item_y[i][1]]
        ret_list.append(item)
    return ret_list




def swipe_split(total, start, end):
    """

    :param total:
    :param start:
    :param end:
    :return:
    >>> swipe_split(600, 0, 100)
    [[300, 400], [400, 400]]
    >>> swipe_split(600, 400, 500)
    [[300, 400], [400, 400]]
    >>> swipe_split(600, 0, 500)
    [[300, 600], [300, 500]]
    >>> swipe_split(600, 100, 0)
    [[300, 200], [200, 200]]
    >>> swipe_split(600, 500, 400)
    [[300, 200], [200, 200]]
    >>> swipe_split(600, 500, 0)
    [[300, 0], [300, 100]]
    >>> swipe_split(600, 100, 100)
    [[100, 100], [100, 100]]
    """
    half = math.ceil(total/2)
    distance = end - start
    ret_list = []
    if distance == 0:
        ret_list = [[start, end], [end, end]]
    elif distance > 0:
        if distance > half:
            start1 = start2 = half
            end1 = total
            end2 = distance
            ret_list = [[start1, end1], [start2, end2]]
        else:
            start = half
            end = half + distance
            ret_list = [[start, end], [end, end]]
    else:
        if abs(distance) > half:
            start1 = start2 = half
            end1 = 0
            end2 = half*2 + distance
            ret_list = [[start1, end1], [start2, end2]]
        else:
            start = half
            end = half + distance
            ret_list = [[start, end], [end, end]]
    return ret_list

if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))