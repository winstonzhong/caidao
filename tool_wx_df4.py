import pandas
import numpy


def 转历史(df, 是否群聊=False):
    """
    转历史 的 Docstring

    :param df: 说明

    >>> l = 转历史(df0)
    >>> sum([x.get('role') == 'user' for x in l])
    5
    >>> l[0]
    {'content': '[2025-12-23 08:11:00][分享了一个文件, 文件大小:25.4 MB]周二健康资讯每日听.mp3', 'role': 'user'}
    >>> l = 转历史(df1, True)
    >>> l[0]
    {'content': '群公告[文件]111027.txt[文件]远程诊疗系统对接方案.doc了解更多', 'role': 'assistant'}
    >>> l[-1]
    {'content': '[2025-12-16 22:02:00]Winston:[分享了一张图片<405x226>]', 'role': 'user'}
    """

    s = df.上下文.str.split(":", n=1).str[-1] if not 是否群聊 else df.上下文

    群聊标识数组 = numpy.full((len(df),), 是否群聊, dtype=bool)

    分割条件 = (~群聊标识数组) | (df.自己)

    处理后的上下文 = numpy.where(
        分割条件,  # 判断条件
        df.上下文.str.split(":", n=1).str[-1],  # 满足条件：分割取最后一部分
        df.上下文,  # 不满足条件：保留原始上下文
    )
    st = df.时间.fillna("").apply(lambda x: f"[{x}]" if x else "")

    s = st + 处理后的上下文

    s.name = "content"

    role = df.自己.map({False: "user", True: "assistant"})

    role.name = "role"

    return pandas.concat([s, role], axis=1).to_dict("records")


if __name__ == "__main__":
    import doctest
    import tool_file

    df0 = tool_file.加载utdf("1766925458.78781.json")
    df1 = tool_file.加载utdf("1766931091.6697454.json")
    df1.时间 = df1.时间.replace({None: numpy.nan})
    print(doctest.testmod(verbose=False, report=False))
