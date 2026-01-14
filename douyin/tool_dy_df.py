import re


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
    """
    # 提取核心字段，默认空字符串避免键不存在报错
    content_desc = d.get("content-desc", "")
    text = d.get("text", "")

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
    elif content_desc.startswith("##"):
        return "文本"
    else:
        return "系统文本"


# 执行单元测试
if __name__ == "__main__":
    import doctest

    # verbose=True 会输出详细的测试过程
    print(doctest.testmod(verbose=False, report=False))
