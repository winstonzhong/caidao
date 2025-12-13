import pandas as pd
from tool_wx_container import 获取列表详情
import re
import numpy as np

session_name_top = "智康安医养服务平台"

namespaces = {"re": "http://exslt.org/regular-expressions"}


def 比对历史记录并返回(df: pd.DataFrame, dict_list: list):
    """
    依次遍历dict_list中的字典项，在DataFrame中查找完全匹配session_name/subtitle/time/red字段的行，返回第一个匹配行的索引。

    参数:
        df: 包含会话记录的DataFrame，需包含session_name、subtitle、time、red字段
        dict_list: 待匹配的字典列表，格式为[{"session_name":"xx", "subtitle":"xx", "time":"xx", "red":"xx"}]
                   若列表为空/非列表/第一个元素非字典，则视为无匹配记录，返回None

    返回:
        int/None: 第一个匹配行的索引（int）；无匹配项或参数不合法时返回None

    Doctest示例：
    >>> # 构造基础测试数据
    >>> test_data = [
    ...     {"session_name": "会话1", "subtitle": "消息1", "time": "09:00", "red": "0", "valid": True},
    ...     {"session_name": "会话2", "subtitle": "消息2", "time": "10:00", "red": "1", "valid": True},
    ...     {"session_name": "会话3", "subtitle": "消息3", "time": "11:00", "red": "2", "valid": False},
    ...     {"session_name": "会话2", "subtitle": "消息2", "time": "10:00", "red": "1", "valid": True}  # 重复行
    ... ]
    >>> df = pd.DataFrame(test_data)

    # 测试1：正常匹配（单个item匹配）
    >>> 比对历史记录并返回(df, [{"session_name": "会话2", "subtitle": "消息2", "time": "10:00", "red": "1"}])
    1

    # 测试2：多个item，第一个不匹配，第二个匹配
    >>> 比对历史记录并返回(df, [
    ...     {"session_name": "会话0", "subtitle": "消息0", "time": "08:00", "red": "0"},
    ...     {"session_name": "会话3", "subtitle": "消息3", "time": "11:00", "red": "2"}
    ... ])
    2

    # 测试3：匹配多行，返回第一个匹配的索引
    >>> 比对历史记录并返回(df, [{"session_name": "会话2", "subtitle": "消息2", "time": "10:00", "red": "1"}])
    1

    # 测试4：部分字段不匹配（red字段不同）
    >>> 比对历史记录并返回(df, [{"session_name": "会话2", "subtitle": "消息2", "time": "10:00", "red": "0"}])


    # 测试5：dict_list为空，返回None
    >>> 比对历史记录并返回(df, [])


    # 测试6：dict_list非列表类型（字符串），返回None
    >>> 比对历史记录并返回(df, "非法类型")


    # 测试7：dict_list第一个元素非字典（数字），返回None
    >>> 比对历史记录并返回(df, [123, {"session_name": "会话1"}])


    # 测试8：df为空，返回None
    >>> 比对历史记录并返回(pd.DataFrame(), [{"session_name": "会话1", "subtitle": "消息1", "time": "09:00", "red": "0"}])


    # 测试9：item缺失部分字段（red字段），视为匹配df中red为None的行（无匹配）
    >>> 比对历史记录并返回(df, [{"session_name": "会话1", "subtitle": "消息1", "time": "09:00"}])


    # 测试10：item字段值类型不匹配（red为数字8 vs df中字符串"8"）
    >>> df_type = pd.DataFrame([{"session_name": "会话4", "subtitle": "消息4", "time": "12:00", "red": "8"}])
    >>> 比对历史记录并返回(df_type, [{"session_name": "会话4", "subtitle": "消息4", "time": "12:00", "red": 8}])


    # 测试11：item字段完全匹配（含空值场景）
    >>> df_null = pd.DataFrame([{"session_name": None, "subtitle": "空会话", "time": "13:00", "red": None}])
    >>> 比对历史记录并返回(df_null, [{"session_name": None, "subtitle": "空会话", "time": "13:00", "red": None}])

    # 测试12：dict_list中有空字典，返回None
    >>> 比对历史记录并返回(df, [{}])
    """
    # 边界条件1：df为空，直接返回None
    if df.empty:
        return None

    # 边界条件2：dict_list不合法（非列表/空列表/第一个元素非字典），返回None
    if (
        not isinstance(dict_list, list)
        or len(dict_list) == 0
        or not isinstance(dict_list[0], dict)
    ):
        return None

    # 遍历dict_list中的每个待匹配项
    for item in dict_list:
        # 提取item中的四个关键字段（缺失则为None）
        target_session = item.get("session_name")
        target_subtitle = item.get("subtitle")
        target_time = item.get("time")
        target_red = item.get("red")

        # 构建匹配条件：四个字段完全相等
        match_condition = (
            (df["session_name"] == target_session)
            & (df["subtitle"] == target_subtitle)
            & (df["time"] == target_time)
            & (df["red"] == target_red)
        )

        # 筛选匹配的行
        matched_rows = df[match_condition]

        # 找到第一个匹配行，返回其索引
        if not matched_rows.empty:
            return matched_rows.index[0]

    # 所有item都未匹配到，返回None
    return None


def clean_last(d):
    return {k: d.get(k) for k in ["session_name", "subtitle", "time", "red"]}


def 获取群持久对象(job):
    return job.持久对象.获取其他记录("微信_创建备用群")


def 得到群df(job):
    obj = 获取群持久对象(job)
    df = obj.df_数据记录
    if "已设置进群确认" not in df.columns:
        df["已设置进群确认"] = False
    if "二维码" not in df.columns:
        df["二维码"] = np.nan
    return df


def 得到一个一人群(job):
    df = 得到群df(job)
    tmp = df[(~df.已设置进群确认) & (df.二维码.isna())]
    return tmp.iloc[0] if not tmp.empty else None


def 得到可用群id(job):
    df = 得到群df(job)
    tmp = df[(df.二维码.notna())]
    return len(tmp) + 66


def 更新群(job, name, **k):
    obj = 获取群持久对象(job)
    obj.更新记录(query={"name": name}, update=k)


def 完成群设置用户已经进群(job):
    # 可用空群 = models.BooleanField(default=True)
    # 已占用 = models.BooleanField(default=False)
    session_name = job.持久对象.获取字段值("正在处理").get("session_name")
    # 群 = 获取群(job, session_name)
    # 群['已占用'] = True
    # obj = 获取群持久对象(job)
    # obj.更新记录(query={"name": session_name}, update={"已设置进群确认": True})
    更新群(job, session_name, 已设置进群确认=True)
    处理列表完成(job)


def 获取群(job, session_name):
    obj = 获取群持久对象(job)
    d = obj.查找数据记录(name=session_name)
    print("群记录为:", d)
    return d


def 处理3p群(job, results):
    print("处理3p群")
    x = '//android.view.ViewGroup/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView[re:match(@text,"[A-Z]{6}\(\d+\)")]'
    e = results[0].elem.xpath(x, namespaces=namespaces)
    e = e[0] if e else None
    if e is not None:
        m = re.match("([A-Z]{6})\((\d+)\)", e.attrib.get("text"))
        num = int(m.groups()[1])
        session_name = m.groups()[0]
        print(f"当前群:{session_name}, 人数:{num}")
        assert session_name == job.持久对象.获取字段值("正在处理").get(
            "session_name"
        ), "群名不一致"
        群 = 获取群(job, session_name)
        if num <= 2 or not 群:
            print("当前群人数不足, 不处理")
        elif not 群:
            print("当前群不是已记录的3人群, 不处理")
        elif 群.get("已设置进群确认"):
            print("当前群不是可用空群, 不处理")
        else:
            # raise NotImplementedError
            job.status = "初始化3人群"
            return
    else:
        print("群名称不是期望的([A-Z]{6})\((\d+)\), 非法群, 不处理")
    job.回退()
    job.status = None
    处理列表完成(job)


def 处理列表完成(job):
    v = job.持久对象.获取字段值("正在处理", 弹出=True)
    if v:
        job.持久对象.设置字段值("最后已处理", v)


def 处理通讯列表(job, results, save_ut=False):
    df = 获取列表详情(results)
    df = 时间列表Bug修正(df)
    print(df)
    最后已处理 = job.持久对象.获取字段值("最后已处理") or {}
    print(最后已处理)
    # raise ValueError

    if save_ut:
        import time
        import json

        fpath = f"ut/{time.time()}.json"
        print("保存ut 到 {}".format(fpath))
        d = {
            "df": df.to_dict(),
            "最后已处理": 最后已处理,
        }
        with open(fpath, "w") as f:
            json.dump(d, f)

    # paras = {k: 最后已处理[k] for k in ["session_name", "subtitle", "time", "red"]}
    paras = 列表处理状态计算函数(df, **clean_last(最后已处理))
    列表处理函数(job, df, paras)


def 列表处理函数(job, df, paras):
    action, parm = paras
    if action == "处理":
        s = df.loc[parm]
        群 = 获取群(job, s["session_name"])
        if s.s3p and 群 and not 群.get("已设置进群确认"):
            print("================处理3p群")
            print(s)
            job.持久对象.设置字段值("正在处理", s.to_dict())
            job.status = "处理3p群"
            job.点击(s.center)
        else:
            print("================非3p群 或 没有登记  或 已占用")
            print(s)
            job.持久对象.设置字段值("最后已处理", s.to_dict())

    elif action == "翻页":
        if parm == -1:
            print("向上翻页")
            job.向上翻页()
        else:
            print("向下翻页")
            job.向下翻页()
        print()
    elif action == "结束":
        print("本轮列表处理结束!")
        import time

        time.sleep(3)
    else:
        raise Exception(f"未知操作:{action}")


def 列表处理状态计算函数(
    df: pd.DataFrame,
    session_name: str = None,
    subtitle: str = None,
    time: str = None,
    red: str = None,
):
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
    ('处理', 1)

    # 测试步骤4-2：结果集为空 + 未到顶部 → 返回翻页-1
    >>> df_test4_2 = pd.DataFrame([
    ...     {"session_name": "测试会话", "subtitle": "测试1", "time": "22:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "测试会话2", "subtitle": "测试2", "time": "21:00", "red":"1",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数(df_test4_2, "测试会话", "测试1", "22:00", "0")
    ('翻页', -1)

    # 测试步骤4-3：结果集为空 + 已到顶部 → 返回结束None
    >>> df_test4_3 = pd.DataFrame([
    ...     {"session_name": "智康安医养服务平台", "subtitle": "顶部记录", "time": "22:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话2", "subtitle": "测试2", "time": "21:00", "red":"1",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数(df_test4_3, "测试会话2", "测试2", "21:00", "1")
    ('结束', None)

    >>> 列表处理状态计算函数(df_test4_3)
    ('翻页', 1)

    >>> df_test4_4 = pd.DataFrame([
    ...     {"session_name": "智康安医养服务平台", "subtitle": "顶部记录", "time": "22:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "XOXOXO", "subtitle": "测试2", "time": "21:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "ABABAB", "subtitle": "测试3", "time": "20:59", "red":"0",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数(df_test4_4, "XOXOXO", "测试2", "21:00", "0")
    ('结束', None)
    >>> 列表处理状态计算函数(df_test4_4, "ABABAB", "测试3", "20:59", "0")
    ('处理', 1)

    # 测试边界情况：df为空
    >>> 列表处理状态计算函数(pd.DataFrame())
    ('结束', None)

    # 测试边界情况：最后一条记录为空但df最后一行today=False
    >>> 列表处理状态计算函数(df_core)  # df最后一行today=False
    ('处理', 5)

    # 测试red字段类型相同
    >>> df_red_test = pd.DataFrame([
    ...     {"session_name": "测试", "subtitle": "测试red", "time": "10:00", "red":"8",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数(df_red_test, "测试", "测试red", "10:00", "8")
    ('翻页', -1)

    # 测试red字段类型相同
    >>> df_red_test = pd.DataFrame([
    ...     {"session_name": "测试", "subtitle": "测试red", "time": "10:00", "red":"8",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数(df_red_test, "测试", "测试red", "10:00", "1")
    ('翻页', -1)
    >>> df_red_test = pd.DataFrame([
    ...     {"session_name": "测试", "subtitle": "测试red", "time": "10:00", "red":"8",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "测试1", "subtitle": "测试red1", "time": "09:00", "red":"1",
    ...      "valid": True, "today": False, "s3p": False}
    ... ])
    >>> 列表处理状态计算函数(df_red_test, "测试1", "测试red1", "09:00", "1")
    ('处理', 0)

    # 结果集为空 + 已到顶部 → 返回处理 1
    >>> df_test4_3 = pd.DataFrame([
    ...     {"session_name": "智康安医养服务平台", "subtitle": "顶部记录", "time": "22:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话1", "subtitle": "测试1", "time": "21:30", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话2", "subtitle": "测试2", "time": "21:00", "red":"1",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])

    >>> 列表处理状态计算函数(df_test4_3, "测试会话2", "测试2", "21:00", "1")
    ('处理', 1)

    >>> 列表处理状态计算函数(df_test4_3, "测试会话1", "测试1", "21:30", "0")
    ('结束', None)

    >>> df_test4_3 = pd.DataFrame([
    ...     {"session_name": "智康安医养服务平台", "subtitle": "顶部记录", "time": "22:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话1", "subtitle": "测试1", "time": "21:30", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话2", "subtitle": "测试2", "time": "21:00", "red":"1",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话3", "subtitle": "测试3", "time": "20:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ... ])

    >>> 列表处理状态计算函数(df_test4_3, "测试会话3", "测试3", "20:00", "0")
    ('处理', 1)

    >>> 列表处理状态计算函数(df_bad, **last_bad)
    ('处理', 1)
    """
    # 步骤0：计算是否到顶部（处理df为空的边界情况）

    if df.empty:
        is_top = False
    else:
        is_top = df.iloc[0]["session_name"] == session_name_top

    # 判断最后一条处理记录是否为空（所有关键参数都为None）
    last_record_empty = all(v is None for v in [session_name, subtitle, time, red])

    # 处理df为空的边界情况
    if df.empty:
        return ("结束", None)

    # 获取df最后一行
    df_last_row = df.iloc[-1]
    df_last_row_today = bool(df_last_row["today"])

    if last_record_empty and df_last_row_today:
        return ("翻页", 1)

    base_conditions = (
        (df["valid"]) & (df["today"]) & (df["session_name"] != session_name_top)
    )
    if not last_record_empty:
        match_conditions = (
            (df["session_name"] == session_name)
            & (df["subtitle"] == subtitle)
            & (df["time"] == time)
            # & (df["red"] == red)
        )
        records_in_df = df[match_conditions]

        record_in_df = not records_in_df.empty

        if record_in_df:
            base_conditions_found = base_conditions & (
                df.index < records_in_df.index[0]
            )
            filtered_df = df[base_conditions_found & (df["s3p"])]
            if filtered_df.empty:
                filtered_df = df[base_conditions_found].iloc[:1]
        else:
            filtered_df = df[base_conditions & (df["s3p"])]
            if filtered_df.empty:
                filtered_df = df[base_conditions].iloc[:1]
    else:
        filtered_df = df[base_conditions & (df["s3p"])]
        record_in_df = False
        if filtered_df.empty:
            filtered_df = df[base_conditions].iloc[:1]

    # 步骤4：记录在df中
    if record_in_df:
        # 结果集非空 → 返回处理+最后一条index
        if not filtered_df.empty:
            return ("处理", filtered_df.index[-1])
        # 结果集为空
        else:
            if not is_top:
                return ("翻页", -1)
            else:
                return ("结束", None)
    elif df_last_row_today:
        return ("翻页", 1)
    elif not filtered_df.empty:
        return ("处理", filtered_df.index[-1])
    elif not is_top:
        return ("翻页", -1)
    else:
        return ("结束", None)


def 列表处理状态计算函数2(df: pd.DataFrame, dict_list: list):
    """
    根据给定的DataFrame和最后一条处理记录的字段列表，计算返回状态（翻页/处理/结束）及对应参数。

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
        dict_list: 包含最后一条处理记录的字典列表，格式为[{"session_name":"xx", "subtitle":"xx", "time":"xx", "red":"xx"}]
                   若列表为空/非列表/第一个元素非字典，则视为最后一条记录为空

    返回:
        tuple: (状态类型, 参数)，状态类型包括"翻页"/"处理"/"结束"

    Doctest示例：
    >>> # 构造核心测试数据（补充原代码缺失的定义）
    >>> core_data = [
    ...     {"session_name": "AHLUBP", "subtitle": '你将"宋刚"移出了群聊', "time": "20:23", "red":"0",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "TEST1", "subtitle": "测试1", "time": "20:24", "red":"0",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "TEST2", "subtitle": "测试2", "time": "20:25", "red":"0",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "TEST3", "subtitle": "测试3", "time": "20:26", "red":"0",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "TEST4", "subtitle": "测试4", "time": "20:27", "red":"0",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "TEST5", "subtitle": "测试5", "time": "20:28", "red":"0",
    ...      "valid": True, "today": False, "s3p": True}
    ... ]
    >>> df_core = pd.DataFrame(core_data)

    # 测试边界情况：最后一条记录为空但df最后一行today=False
    >>> 列表处理状态计算函数2(df_core, [])  # df最后一行today=False
    ('处理', 4)

    >>> df_test2 = df_core.iloc[:-1].copy()  # 移除最后一行（today=False），新最后一行today=True

    >>> 列表处理状态计算函数2(df_test2, [{"session_name":"AHLUBP", "subtitle":'你将"宋刚"移出了群聊', "time":"20:23", "red":"0"}])
    ('翻页', -1)


    >>> 列表处理状态计算函数2(df_test2, [])
    ('翻页', 1)

    # 测试步骤3：最后一条记录非空 + df最后一行today=True + 记录不在df中
    >>> 列表处理状态计算函数2(df_test2, [{"session_name":"不存在的会话", "subtitle":"不存在的副标题", "time":"22:00", "red":"0"}])
    ('翻页', 1)


    # 测试步骤4-2：结果集为空 + 未到顶部 → 返回翻页-1
    >>> df_test4_2 = pd.DataFrame([
    ...     {"session_name": "测试会话", "subtitle": "测试1", "time": "22:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "测试会话2", "subtitle": "测试2", "time": "21:00", "red":"1",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数2(df_test4_2, [{"session_name":"测试会话", "subtitle":"测试1", "time":"22:00", "red":"0"}])
    ('翻页', -1)

    # 测试步骤4-3：结果集为空 + 已到顶部 → 返回结束None
    >>> df_test4_3 = pd.DataFrame([
    ...     {"session_name": "智康安医养服务平台", "subtitle": "顶部记录", "time": "22:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话2", "subtitle": "测试2", "time": "21:00", "red":"1",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数2(df_test4_3, [{"session_name":"测试会话2", "subtitle":"测试2", "time":"21:00", "red":"1"}])
    ('结束', None)

    >>> 列表处理状态计算函数2(df_test4_3, [])
    ('翻页', 1)

    >>> df_test4_4 = pd.DataFrame([
    ...     {"session_name": "智康安医养服务平台", "subtitle": "顶部记录", "time": "22:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "XOXOXO", "subtitle": "测试2", "time": "21:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "ABABAB", "subtitle": "测试3", "time": "20:59", "red":"0",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数2(df_test4_4, [{"session_name":"XOXOXO", "subtitle":"测试2", "time":"21:00", "red":"0"}])
    ('结束', None)
    >>> 列表处理状态计算函数2(df_test4_4, [{"session_name":"ABABAB", "subtitle":"测试3", "time":"20:59", "red":"0"}])
    ('处理', 1)

    # 测试边界情况：df为空
    >>> 列表处理状态计算函数2(pd.DataFrame(), [])
    ('结束', None)

    # 测试red字段匹配
    >>> df_red_test = pd.DataFrame([
    ...     {"session_name": "测试", "subtitle": "测试red", "time": "10:00", "red":"8",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数2(df_red_test, [{"session_name":"测试", "subtitle":"测试red", "time":"10:00", "red":"8"}])
    ('翻页', -1)

    # 测试red字段不匹配
    >>> df_red_test = pd.DataFrame([
    ...     {"session_name": "测试", "subtitle": "测试red", "time": "10:00", "red":"8",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数2(df_red_test, [{"session_name":"测试", "subtitle":"测试red", "time":"10:00", "red":"8"}])
    ('翻页', -1)
    >>> df_red_test = pd.DataFrame([
    ...     {"session_name": "测试", "subtitle": "测试red", "time": "10:00", "red":"8",
    ...      "valid": True, "today": True, "s3p": True},
    ...     {"session_name": "测试1", "subtitle": "测试red1", "time": "09:00", "red":"1",
    ...      "valid": True, "today": False, "s3p": False}
    ... ])
    >>> 列表处理状态计算函数2(df_red_test, [{"session_name":"测试1", "subtitle":"测试red1", "time":"09:00", "red":"1"}])
    ('处理', 0)

    # 结果集为空 + 已到顶部 → 返回处理 1
    >>> df_test4_3 = pd.DataFrame([
    ...     {"session_name": "智康安医养服务平台", "subtitle": "顶部记录", "time": "22:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话1", "subtitle": "测试1", "time": "21:30", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话2", "subtitle": "测试2", "time": "21:00", "red":"1",
    ...      "valid": True, "today": True, "s3p": True}
    ... ])
    >>> 列表处理状态计算函数2(df_test4_3, [{"session_name":"测试会话2", "subtitle":"测试2", "time":"21:00", "red":"1"}])
    ('处理', 1)

    >>> 列表处理状态计算函数2(df_test4_3, [{"session_name":"测试会话1", "subtitle":"测试1", "time":"21:30", "red":"0"}])
    ('结束', None)

    >>> df_test4_3 = pd.DataFrame([
    ...     {"session_name": "智康安医养服务平台", "subtitle": "顶部记录", "time": "22:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话1", "subtitle": "测试1", "time": "21:30", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话2", "subtitle": "测试2", "time": "21:00", "red":"1",
    ...      "valid": True, "today": True, "s3p": False},
    ...     {"session_name": "测试会话3", "subtitle": "测试3", "time": "20:00", "red":"0",
    ...      "valid": True, "today": True, "s3p": False},
    ... ])
    >>> 列表处理状态计算函数2(df_test4_3, [{"session_name":"测试会话3", "subtitle":"测试3", "time":"20:00", "red":"0"}])
    ('处理', 1)
    """
    最后处理过的记录idx = 比对历史记录并返回(df, dict_list)
    # 步骤0：计算是否到顶部（处理df为空的边界情况）
    if df.empty:
        is_top = False
    else:
        is_top = df.iloc[0]["session_name"] == session_name_top

    last_record_empty = not dict_list

    # 处理df为空的边界情况
    if df.empty:
        return ("结束", None)

    # 获取df最后一行
    df_last_row = df.iloc[-1]
    df_last_row_today = bool(df_last_row["today"])

    if last_record_empty and df_last_row_today:
        return ("翻页", 1)

    base_conditions = (
        (df["valid"]) & (df["today"]) & (df["session_name"] != session_name_top)
    )
    if not last_record_empty:

        if 最后处理过的记录idx is not None:
            base_conditions_found = base_conditions & (
                df.index < 最后处理过的记录idx
            )
            filtered_df = df[base_conditions_found & (df["s3p"])]
            if filtered_df.empty:
                filtered_df = df[base_conditions_found].iloc[:1]
        else:
            filtered_df = df[base_conditions & (df["s3p"])]
            if filtered_df.empty:
                filtered_df = df[base_conditions].iloc[:1]
    else:
        filtered_df = df[base_conditions & (df["s3p"])]
        # record_in_df = False
        if filtered_df.empty:
            filtered_df = df[base_conditions].iloc[:1]

    # 步骤4：记录在df中
    if 最后处理过的记录idx is not None:
        # 结果集非空 → 返回处理+最后一条index
        if not filtered_df.empty:
            return ("处理", filtered_df.index[-1])
        # 结果集为空
        else:
            if not is_top:
                return ("翻页", -1)
            else:
                return ("结束", None)
    elif df_last_row_today:
        return ("翻页", 1)
    elif not filtered_df.empty:
        return ("处理", filtered_df.index[-1])
    elif not is_top:
        return ("翻页", -1)
    else:
        return ("结束", None)


def 时间列表Bug修正(df: pd.DataFrame) -> pd.DataFrame:
    """
    修正时间列表的Bug：忽略置顶行后，将第一个非倒序位置及之后的today设为False

    参数:
        df: 包含session_name、time、today列的DataFrame

    返回:
        修正后的DataFrame

    Doctest示例:
    >>> # 构造测试用例（与题目示例一致）
    >>> data = {
    ...     'session_name': ['智康安医养服务平台', '独立游戏开发第 _BEHA', 'VUKMBO', 'AHLUBP', 'ProcessOn', '李强', '订阅号消息', '内部机器人测试群_OAKK', '全宏益健康分析师', '富贵杠上花', '服务通知'],
    ...     'time': ['10月29日', '05:57', '22:28', '19:20', '19:02', '17:33', '17:27', '15:53', '08:15', '昨天', '昨天'],
    ...     'today': [False, True, True, True, True, True, True, True, True, False, False]
    ... }
    >>> df = pd.DataFrame(data)
    >>> result = 时间列表Bug修正(df)
    >>> # 验证第一个非倒序位置（索引2）及之后的today均为False
    >>> result.loc[2:, 'today'].tolist()
    [False, False, False, False, False, False, False, False, False]
    >>> # 验证置顶行和第一个非倒序位置前的行未被修改
    >>> result.loc[:1, 'today'].tolist()
    [False, True]

    >>> # 测试无置顶行且时间正常倒序的情况
    >>> data2 = {
    ...     'session_name': ['A', 'B', 'C'],
    ...     'time': ['22:00', '20:00', '18:00'],
    ...     'today': [True, True, True]
    ... }
    >>> df2 = pd.DataFrame(data2)
    >>> result2 = 时间列表Bug修正(df2)
    >>> result2['today'].tolist()  # 无修改
    [True, True, True]

    >>> # 测试无置顶行且第一个非倒序在索引1的情况
    >>> data3 = {
    ...     'session_name': ['A', 'B', 'C'],
    ...     'time': ['10:00', '12:00', '09:00'],
    ...     'today': [True, True, True]
    ... }
    >>> df3 = pd.DataFrame(data3)
    >>> result3 = 时间列表Bug修正(df3)
    >>> result3['today'].tolist()  # 索引1及之后设为False
    [True, False, False]

    >>> # 测试用例1: 基本功能测试（只有hh:mm格式）
    >>> df1 = pd.DataFrame({
    ...     'session_name': ['智康安医养服务平台', 'A', 'B', 'C'],
    ...     'time': ['10:30', '22:28', '19:20', '17:33'],
    ...     'today': [False, True, True, True]
    ... })
    >>> result1 = 时间列表Bug修正(df1)
    >>> result1['today'].tolist()
    [False, True, True, True]

    >>> # 测试用例2: 存在非倒序的情况
    >>> df2 = pd.DataFrame({
    ...     'session_name': ['智康安医养服务平台', 'A', 'B', 'C', 'D'],
    ...     'time': ['10月29日', '05:57', '22:28', '19:20', '17:33'],
    ...     'today': [False, True, True, True, True]
    ... })
    >>> result2 = 时间列表Bug修正(df2)
    >>> result2['today'].tolist()
    [False, True, False, False, False]

    >>> # 测试用例3: 包含非hh:mm格式的时间（应转为nan并跳过）
    >>> df3 = pd.DataFrame({
    ...     'session_name': ['智康安医养服务平台', 'A', 'B', 'C', 'D', 'E'],
    ...     'time': ['10月29日', '23:50', '昨天', '22:28', '19:20', '17:33'],
    ...     'today': [False, True, False, True, True, True]
    ... })
    >>> result3 = 时间列表Bug修正(df3)
    >>> result3['today'].tolist()
    [False, True, False, False, False, False]

    >>> # 测试用例4: 非置顶行，存在非倒序
    >>> df4 = pd.DataFrame({
    ...     'session_name': ['其他平台', 'A', 'B', 'C', 'D'],
    ...     'time': ['10:00', '05:57', '22:28', '19:20', '17:33'],
    ...     'today': [True, True, True, True, True]
    ... })
    >>> result4 = 时间列表Bug修正(df4)
    >>> result4['today'].tolist()
    [True, True, False, False, False]

    >>> # 测试用例5: 空DataFrame
    >>> df5 = pd.DataFrame(columns=['session_name', 'time', 'today'])
    >>> result5 = 时间列表Bug修正(df5)
    >>> len(result5)
    0

    >>> # 测试用例6: 只有一行置顶行
    >>> df6 = pd.DataFrame({
    ...     'session_name': ['智康安医养服务平台'],
    ...     'time': ['10月29日'],
    ...     'today': [False]
    ... })
    >>> result6 = 时间列表Bug修正(df6)
    >>> result6['today'].tolist()
    [False]

    >>> # 测试用例7: 时间全部倒序（hh:mm格式）
    >>> df7 = pd.DataFrame({
    ...     'session_name': ['智康安医养服务平台', 'A', 'B', 'C'],
    ...     'time': ['10月29日', '22:28', '19:20', '17:33'],
    ...     'today': [False, True, True, True]
    ... })
    >>> result7 = 时间列表Bug修正(df7)
    >>> result7['today'].tolist()
    [False, True, True, True]

    >>> # 测试用例8: 非hh:mm格式在hh:mm之后，不应影响比较
    >>> df8 = pd.DataFrame({
    ...     'session_name': ['智康安医养服务平台', 'A', 'B', 'C'],
    ...     'time': ['10:30', '09:20', '昨天', '08:15'],
    ...     'today': [False, True, False, True]
    ... })
    >>> result8 = 时间列表Bug修正(df8)
    >>> result8['today'].tolist()
    [False, True, False, False]

    """
    # 复制原DataFrame，避免修改原数据
    df_copy = df.copy()

    # 步骤1：判断是否有置顶行，确定需要校验的起始索引
    top_row_session = df_copy.iloc[0]["session_name"] if not df_copy.empty else ""
    check_start_idx = 1 if top_row_session == "智康安医养服务平台" else 0
    check_df = df_copy.iloc[check_start_idx:].copy()

    if check_df.empty:
        return df_copy

    def time_to_minutes(time_str):
        if ":" in time_str and len(time_str.split(":")) == 2:
            try:
                hour, minute = map(int, time_str.split(":"))
                return hour * 60 + minute
            except ValueError:
                pass
        return np.nan

    s = check_df["time"].apply(time_to_minutes).diff()

    abnormal_mask = s[s > 0]

    if not abnormal_mask.empty:  # and abnormal_mask.any():
        first_abnormal_idx = abnormal_mask.idxmin()
    else:
        first_abnormal_idx = None

    if first_abnormal_idx is not None:
        df_copy.loc[first_abnormal_idx:, "today"] = False

    false_today_mask = check_df.today[~check_df.today]
    if not false_today_mask.empty:
        first_false_today_idx = false_today_mask.idxmin()  # 第一个today为False的位置
    else:
        first_false_today_idx = None

    if first_false_today_idx is not None:
        df_copy.loc[first_false_today_idx:, "today"] = False

    return df_copy


if __name__ == "__main__":
    import doctest
    import json

    # 执行doctest并输出详细结果
    core_data = [
        {
            "session_name": "智康安医养服务平台",
            "subtitle": "[链接] 欢迎来到健康档案～",
            "time": "10月29日",
            "red": "0",
            "top": 226,
            "bottom": 420,
            "height": 194,
            "valid": True,
            "today": True,
            "s3p": False,
        },
        {
            "session_name": "VUKMBO",
            "subtitle": '你将"老许"移出了群聊',
            "time": "21:07",
            "red": "0",
            "top": 420,
            "bottom": 614,
            "height": 194,
            "valid": True,
            "today": True,
            "s3p": True,
        },
        {
            "session_name": "富贵杠上花",
            "subtitle": '你将"柳斜斜_EXFI"移出了群聊',
            "time": "21:04",
            "red": "0",
            "top": 614,
            "bottom": 808,
            "height": 194,
            "valid": True,
            "today": True,
            "s3p": False,
        },
        {
            "session_name": "独立游戏开发第 _BEHA",
            "subtitle": "火火羊: 加了",
            "time": "20:50",
            "red": "8",
            "top": 808,
            "bottom": 1002,
            "height": 194,
            "valid": True,
            "today": True,
            "s3p": False,
        },
        {
            "session_name": "内部机器人测试群_OAKK",
            "subtitle": "听涛济沧海_PWHE: [图片]",
            "time": "20:42",
            "red": "3",
            "top": 1002,
            "bottom": 1196,
            "height": 194,
            "valid": True,
            "today": True,
            "s3p": False,
        },
        {
            "session_name": "AHLUBP",
            "subtitle": '你将"宋刚"移出了群聊',
            "time": "20:23",
            "red": "0",
            "top": 1196,
            "bottom": 1390,
            "height": 194,
            "valid": True,
            "today": True,
            "s3p": True,
        },
        {
            "session_name": "李强",
            "subtitle": "[图片]",
            "time": "19:17",
            "red": "0",
            "top": 1390,
            "bottom": 1584,
            "height": 194,
            "valid": True,
            "today": True,
            "s3p": False,
        },
        {
            "session_name": "服务通知",
            "subtitle": "微信收款助手：微信支付收款30.00元",
            "time": "17:19",
            "red": "0",
            "top": 1584,
            "bottom": 1778,
            "height": 194,
            "valid": True,
            "today": True,
            "s3p": False,
        },
        {
            "session_name": "微信支付",
            "subtitle": "已支付¥31.59",
            "time": "15:55",
            "red": "1",
            "top": 1778,
            "bottom": 1972,
            "height": 194,
            "valid": True,
            "today": True,
            "s3p": False,
        },
        {
            "session_name": "AAAAAA @朴朴超市",
            "subtitle": "对方为企业微信用户，了解更多。",
            "time": "15:51",
            "red": "0",
            "top": 1972,
            "bottom": 2166,
            "height": 194,
            "valid": True,
            "today": True,
            "s3p": False,
        },
        {
            "session_name": "ABCDEF",
            "subtitle": "钟北川: 啊🩷",
            "time": "15:20",
            "red": "0",
            "top": 2166,
            "bottom": 2264,
            "height": 98,
            "valid": False,
            "today": False,
            "s3p": True,
        },
    ]
    from pathlib import Path

    base_dir = Path(__file__).parent.resolve()

    def get_bad_pair(fpath):
        fpath = base_dir / fpath

        with open(fpath, "r") as f:
            d = json.load(f)

        df_bad = pd.DataFrame(d.get("df")).reset_index(drop=True)
        last_bad = clean_last(d.get("最后已处理"))
        return df_bad, last_bad

    df_bad, last_bad = get_bad_pair("ut/1765442497.4180336.json")
    # ut/1765546838.8218212.json
    # df_bad1, last_bad1 = get_bad_pair("ut/1765546838.8218212.json")

    print(doctest.testmod(verbose=False, report=False))
    # print(df_bad1)

    # print(df_bad)
    # print(df_bad.index)
    # print(last_bad)
