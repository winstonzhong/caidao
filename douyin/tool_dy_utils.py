import pandas as pd
import re
import tool_time
import numpy as np


def 网友评论解析(line: str) -> list[dict]:
    """
    解析单行网友评论文本，提取关键信息并返回字典列表

    参数:
        line: 单行评论文本，包含网友信息、行为、时间、bounds box等

    返回:
        list[dict]: 包含以下字段的字典列表：
            - 网友名称: str，网友的昵称（无则为空字符串）
            - 评论内容: str，评论/回复的具体内容（无则为空字符串）
            - 是否需回复: bool，是否包含"回复评论 回复,按钮"特征
            - left: int，bounds box左坐标
            - top: int，bounds box上坐标
            - right: int，bounds box右坐标
            - bottom: int，bounds box下坐标

    Doctest测试用例:
    >>> # 测试1：仅包含bounds box的空行
    >>> 网友评论解析(" (0, 2167, 1080, 2236)")
    {'网友名称': '', '评论内容': '', '是否需回复': False, 'left': 0, 'top': 2167, 'right': 1080, 'bottom': 2236}
    >>> # 测试2：赞了你的评论，无回复按钮
    >>> line2 = "魏晓樱Queen的头像 魏晓樱Queen 赞了你的评论 1分钟前 (0, 204, 1080, 447)"
    >>> 网友评论解析(line2)
    {'网友名称': '魏晓樱Queen', '评论内容': '', '是否需回复': False, 'left': 0, 'top': 204, 'right': 1080, 'bottom': 447}
    >>> # 测试3：评论了你，包含回复按钮（需回复）
    >>> line3 = "唯有欢喜的头像 唯有欢喜 粉丝 评论了你: 新年快乐 1分钟前 回复评论 回复,按钮 赞 赞,按钮 (0, 447, 1080, 709)"
    >>> res3 = 网友评论解析(line3)
    >>> res3['网友名称'], res3['评论内容'], res3['是否需回复']
    ('唯有欢喜', '新年快乐', True)
    >>> res3['left'], res3['top'], res3['right'], res3['bottom']
    (0, 447, 1080, 709)
    >>> # 测试4：带表情的评论内容
    >>> line4 = "花木蓝的头像 花木蓝 评论了你: 我也不知道有啥用[大笑][大笑] 23分钟前 回复评论 回复,按钮 赞 赞,按钮 (0, 622, 1080, 1136)"
    >>> d = 网友评论解析(line4)
    >>> d['评论内容']
    '我也不知道有啥用[大笑][大笑]'
    >>> d["是否需回复"]
    True
    >>> # 测试5：作者回复的场景
    >>> line5 = "花木蓝的头像 花木蓝 作者 回复: 是的，人间烟火气息[大笑] 32分钟前 回复评论 回复,按钮 赞 赞,按钮 (0, 1379, 1080, 1711)"
    >>> res5 = 网友评论解析(line5)
    >>> res5['网友名称'], res5['评论内容']
    ('花木蓝', '是的，人间烟火气息[大笑]')
    >>> res5['是否需回复']
    False
    >>> # 测试6：名称含特殊字符的场景
    >>> line6 = "农村阿娟带娃记（新人起步）的头像 农村阿娟带娃记（新人起步） 赞了你的评论 7分钟前 (0, 1195, 1080, 1438)"
    >>> 网友评论解析(line6)['网友名称']
    '农村阿娟带娃记（新人起步）'
    >>> # 测试7：赞了你的图文场景
    >>> line7 = "花木蓝的头像 花木蓝 赞了你的图文 23分钟前 (0, 1136, 1080, 1379)"
    >>> 网友评论解析(line7)['评论内容']
    ''
    >>> 网友评论解析(line7)['是否需回复']
    False
    """
    # 初始化返回结果

    # 正则匹配行末尾的bounds box（捕获left/top/right/bottom）
    bounds_pattern = re.compile(r"\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)$")
    bounds_match = bounds_pattern.search(line)

    # 提取bounds box坐标（默认0，防止匹配失败）
    left = int(bounds_match.group(1)) if bounds_match else 0
    top = int(bounds_match.group(2)) if bounds_match else 0
    right = int(bounds_match.group(3)) if bounds_match else 0
    bottom = int(bounds_match.group(4)) if bounds_match else 0

    # 去掉bounds box后的纯文本内容（用于提取其他信息）
    text_without_bounds = bounds_pattern.sub("", line).strip()

    # 1. 提取网友名称：匹配"的头像"后的名称（直到遇到粉丝/作者/赞了/评论了你/回复:等关键词）
    # name_pattern = re.compile(
    #     r"的头像\s+([^(\s+粉丝|\s+作者|\s+赞了|\s+评论了你|\s+回复:)]+)"
    # )
    name_pattern = re.compile(r"(.+?)的头像")
    name_match = name_pattern.search(text_without_bounds)
    网友名称 = name_match.group(1).strip() if name_match else ""

    # 2. 提取评论内容：优先匹配"评论了你:"，其次匹配"回复:"，无则为空
    content_pattern1 = re.compile(r"评论了你:\s*(.+?)\s+\d+分钟前")  # 评论你的场景
    content_pattern2 = re.compile(r"回复:\s*(.+?)\s+\d+分钟前")  # 作者回复的场景
    content_match1 = content_pattern1.search(text_without_bounds)
    content_match2 = content_pattern2.search(text_without_bounds)
    if content_match1:
        评论内容 = content_match1.group(1).strip()
    elif content_match2:
        评论内容 = content_match2.group(1).strip()
    else:
        评论内容 = ""

    # 3. 判断是否需要回复：精确匹配"回复评论 回复,按钮"
    是否需回复 = (
        "回复评论 回复,按钮" in text_without_bounds and content_match1 is not None
    )

    # 构建结果字典并添加到列表
    return {
        "网友名称": 网友名称,
        "评论内容": 评论内容,
        "是否需回复": 是否需回复,
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
    }


def 网友评论提取(job, results: list):
    data = []
    for e in results:
        line = f"{job.元素转字符串(e)}, {e.bounds}"
        # print(line)
        d = 网友评论解析(line)
        d["e"] = e
        d["秒数"] = tool_time.从字符串提取时间并转为秒(line, np.nan)[0]
        d["是否需回复"] = (
            False
            if not d.get("是否需回复")
            else d.get("网友名称") not in job.数据.定长队列
        )
        data.append(d)
    return pd.DataFrame(data)


def 提取链接(txt: str) -> list:
    """
    从输入文本中提取所有HTTP/HTTPS协议的链接

    Doctest单元测试用例：
    >>> 提取链接('1.76 复制打开抖音，看看【河马包包的菜园的作品】昭昭如愿，岁岁安澜# 热门 # 抖音美食推荐官 #... https://v.douyin.com/XrmRMhEVlbk/ 11/20 z@t.eb lcN:/ ')
    ['https://v.douyin.com/XrmRMhEVlbk/']
    >>> 提取链接('无链接的纯文本内容')
    []
    >>> 提取链接('多个链接测试：https://www.baidu.com 测试内容 https://www.google.com/index.html 结尾')
    ['https://www.baidu.com', 'https://www.google.com/index.html']
    >>> 提取链接('http开头的链接：http://example.com/123 abc')
    ['http://example.com/123']
    """
    # 正则表达式模式：匹配http/https开头，直到遇到空白字符为止的所有字符
    # https? 匹配http或https；:// 匹配协议后的固定分隔符；[^\s]+ 匹配任意非空白字符（直到空格结束）
    link_pattern = r"https?://[^\s]+"

    # 查找所有匹配的链接，返回列表
    matched_links = re.findall(link_pattern, txt)

    return matched_links

def 是否无内容(txt: str):
    '''
    是否无内容 的 Docstring

    :param txt: 说明
    :type txt: str
    >>> 是否无内容('由于未提供具体短视频内容，无法生成精准评论~')
    True
    >>> 是否无内容(None)
    True
    >>> 是否无内容('内容')
    False
    '''
    return re.search('(无法生成|链接)', txt) is not None if txt else True

# 运行doctest单元测试
if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
