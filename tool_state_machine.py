import pandas as pd

def 列表处理状态计算函数(df: pd.DataFrame, session_name: str = None, subtitle: str = None, time: str = None, red: str = None):
    """
    根据给定的DataFrame和最后一条处理记录的字段，计算返回状态（翻页/处理/结束）及对应参数。

    算法逻辑：
    0. 是否到顶部：df第一条记录的session_name为"智康安医养服务平台"则为True，否则False。
    1. 用最后一条处理记录的字段比对df。
    2. 最后一条记录为空，且df最后一行today=True → 返回（翻页，1）。
    3. 最后一条记录非空，df最后一行today=True，且记录不在df中 → 返回（翻页，1）。
    4. 最后一条记录非空且在df中：
       - 筛选df中时间大于该记录、valid/today/s3p均为True的结果集。
       - 结果集非空 → 返回（处理，结果集最后一条的index）。
       - 结果集为空且未到顶部 → 返回（翻页，-1）。
       - 否则 → 返回（结束，None）。

    参数:
        df: 包含会话记录的DataFrame，结构见问题描述
        session_name: 最后一条处理记录的会话名称
        subtitle: 最后一条处理记录的副标题
        time: 最后一条处理记录的时间
        red: 最后一条处理记录的red字段（字符串类型）

    返回:
        tuple: (状态类型, 参数)，状态类型包括"翻页"/"处理"/"结束"

    Doctest示例：
    >>> # 构造核心测试数据（匹配问题描述的结构）
    >>> df_core = pd.DataFrame(core_data)

    # 测试步骤2：最后一条记录为空 + df最后一行today=True
    >>> df_test2 = df_core.iloc[:-1].copy()  # 移除最后一行（today=False），新最后一行today=True
    >>> 列表处理状态计算函数(df_test2)
    ('翻页', 1)

    # 测试步骤3：最后一条记录非空 + df最后一行today=True + 记录不在df中
    >>> 列表处理状态计算函数(df_test2, "不存在的会话", "不存在的副标题", "22:00", "0")
    ('翻页', 1)

    # 测试步骤4-1：记录在df中 + 结果集非空 → 返回处理+最后一条index
    >>> # 匹配time=20:23的AHLUBP行，大于该时间的有效行最后一条是index4
    >>> 列表处理状态计算函数(df_test2, "AHLUBP", '你将"宋刚"移出了群聊', "20:23", "0")
    ('处理', 4)

    # 测试步骤4-2：结果集为空 + 未到顶部 → 返回翻页-1
    >>> df_test4_2 = pd.DataFrame([
    ...     {"session_name": "测试会话", "subtitle": "测试1", "time": "22:00", "red": 0, 
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "测试会话2", "subtitle": "测试2", "time": "21:00", "red": 1, 
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数(df_test4_2, "测试会话", "测试1", "22:00", "0")
    ('翻页', -1)

    # 测试步骤4-3：结果集为空 + 已到顶部 → 返回结束None
    >>> df_test4_3 = pd.DataFrame([
    ...     {"session_name": "智康安医养服务平台", "subtitle": "顶部记录", "time": "22:00", "red": 0, 
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "测试会话2", "subtitle": "测试2", "time": "21:00", "red": 1, 
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数(df_test4_3, "智康安医养服务平台", "顶部记录", "22:00", "0")
    ('结束', None)

    # 测试边界情况：df为空
    >>> 列表处理状态计算函数(pd.DataFrame())
    ('结束', None)

    # 测试边界情况：最后一条记录为空但df最后一行today=False
    >>> 列表处理状态计算函数(df_core)  # df最后一行today=False
    ('结束', None)

    # 测试red字段类型转换（字符串转数字）
    >>> df_red_test = pd.DataFrame([
    ...     {"session_name": "测试", "subtitle": "测试red", "time": "10:00", "red": 8, 
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数(df_red_test, "测试", "测试red", "10:00", "8")  # red传字符串"8"
    ('结束', None)
    """
    # 步骤0：计算是否到顶部（处理df为空的边界情况）
    if df.empty:
        is_top = False
    else:
        is_top = df.iloc[0]['session_name'] == '智康安医养服务平台'

    # 判断最后一条处理记录是否为空（所有关键参数都为None）
    last_record_empty = all(v is None for v in [session_name, subtitle, time, red])

    # 处理df为空的边界情况
    if df.empty:
        return ("结束", None)

    # 获取df最后一行
    df_last_row = df.iloc[-1]

    # 步骤2：最后一条记录为空 + df最后一行today=True → 翻页1
    if last_record_empty:
        if df_last_row['today'] is True:
            return ("翻页", 1)

    # 步骤3/4：最后一条记录非空的情况
    if not last_record_empty:
        # 转换red类型（传入的是字符串，df中是数字）
        try:
            red_val = int(red) if red is not None else None
        except (ValueError, TypeError):
            red_val = red

        # 判断记录是否存在于df中（四字段完全匹配）
        match_conditions = (
            (df['session_name'] == session_name) &
            (df['subtitle'] == subtitle) &
            (df['time'] == time) &
            (df['red'] == red_val)
        )
        record_in_df = match_conditions.any()

        # 步骤3：df最后一行today=True + 记录不在df中 → 翻页1
        if df_last_row['today'] is True and not record_in_df:
            return ("翻页", 1)

        # 步骤4：记录在df中
        if record_in_df:
            # 获取匹配行的时间
            matched_row = df[match_conditions].iloc[0]
            matched_time = matched_row['time']

            # 筛选：时间大于匹配行 + valid/today/s3p均为True
            filter_conditions = (
                (df['time'] > matched_time) &
                (df['valid'] == True) &
                (df['today'] == True) &
                (df['s3p'] == True)
            )
            filtered_df = df[filter_conditions]

            # 结果集非空 → 返回处理+最后一条index
            if not filtered_df.empty:
                return ("处理", filtered_df.index[-1])
            # 结果集为空
            else:
                if not is_top:
                    return ("翻页", -1)
                else:
                    return ("结束", None)

    # 所有未匹配的情况默认返回结束
    return ("结束", None)

if __name__ == "__main__":
    import doctest
    # 执行doctest并输出详细结果
    core_data = [
    {"session_name": "智康安医养服务平台", "subtitle": "[链接] 欢迎来到健康档案～", "time": "10月29日", "red": 0, 
     "top": 226, "bottom": 420, "height": 194, "valid": True, "today": True, "s3p": False, "up": False, "down": 226, "col2189": 2189},
    {"session_name": "VUKMBO", "subtitle": "你将\"老许\"移出了群聊", "time": "21:07", "red": 0, 
     "top": 420, "bottom": 614, "height": 194, "valid": True, "today": True, "s3p": True, "up": True, "down": 226, "col2189": 2189},
    {"session_name": "富贵杠上花", "subtitle": "你将\"柳斜斜_EXFI\"移出了群聊", "time": "21:04", "red": 0, 
     "top": 614, "bottom": 808, "height": 194, "valid": True, "today": True, "s3p": True, "up": True, "down": 226, "col2189": 2189},
    {"session_name": "独立游戏开发第 _BEHA", "subtitle": "火火羊: 加了", "time": "20:50", "red": 8, 
     "top": 808, "bottom": 1002, "height": 194, "valid": True, "today": True, "s3p": True, "up": True, "down": 226, "col2189": 2189},
    {"session_name": "内部机器人测试群_OAKK", "subtitle": "听涛济沧海_PWHE: [图片]", "time": "20:42", "red": 3, 
     "top": 1002, "bottom": 1196, "height": 194, "valid": True, "today": True, "s3p": True, "up": True, "down": 226, "col2189": 2189},
    {"session_name": "AHLUBP", "subtitle": "你将\"宋刚\"移出了群聊", "time": "20:23", "red": 0, 
     "top": 1196, "bottom": 1390, "height": 194, "valid": True, "today": True, "s3p": True, "up": True, "down": 226, "col2189": 2189},
    {"session_name": "李强", "subtitle": "[图片]", "time": "19:17", "red": 0, 
     "top": 1390, "bottom": 1584, "height": 194, "valid": True, "today": True, "s3p": True, "up": True, "down": 226, "col2189": 2189},
    {"session_name": "服务通知", "subtitle": "微信收款助手：微信支付收款30.00元", "time": "17:19", "red": 0, 
     "top": 1584, "bottom": 1778, "height": 194, "valid": True, "today": True, "s3p": True, "up": True, "down": 226, "col2189": 2189},
    {"session_name": "微信支付", "subtitle": "已支付¥31.59", "time": "15:55", "red": 1, 
     "top": 1778, "bottom": 1972, "height": 194, "valid": True, "today": True, "s3p": True, "up": True, "down": 226, "col2189": 2189},
    {"session_name": "AAAAAA @朴朴超市", "subtitle": "对方为企业微信用户，了解更多。", "time": "15:51", "red": 0, 
     "top": 1972, "bottom": 2166, "height": 194, "valid": True, "today": True, "s3p": True, "up": True, "down": 226, "col2189": 2189},
    {"session_name": "ABCDEF", "subtitle": "钟北川: 啊🩷", "time": "15:20", "red": 0, 
     "top": 2166, "bottom": 2264, "height": 98, "valid": False, "today": False, "s3p": True, "up": True, "down": 226, "col2189": 2189}
    ]
    print(doctest.testmod(verbose=False, report=False))