import time
import pandas
from pathlib import Path

import itertools
import tool_env

UT_DIR = Path(__file__).parent.resolve() / "ut"

# SELF_MAP = {
#     "True": 1,
#     "False": 0,
#     True: 1,
#     False: 0,
# }


def load_ut_df(name):
    return pandas.read_csv(UT_DIR / f"{str(name).split('.', maxsplit=1)[0]}.csv")


def save_ut_df(df, name=None):
    name = name if name else f"{time.time():.0f}"
    df.to_csv(UT_DIR / f"{name}.csv", index=False)
    return name


def save_ut_df_phone(phone, name=None):
    return save_ut_df(phone.微信_获取当前页df(), name)


def 是否匹配(上一页, 当前页):
    """
    >>> 是否匹配(load_ut_df(0), load_ut_df(1))
    True
    >>> 是否匹配(load_ut_df(0), load_ut_df(1747730460))
    False
    """
    if len(上一页) != len(当前页):
        return False
    return (
        上一页.唯一值.reset_index(drop=True) == 当前页.唯一值.reset_index(drop=True)
    ).all()


def 串行后拆分(上一页, 当前页):
    df = pandas.concat([上一页, 当前页], ignore_index=True)
    df["行id"] = df.index
    i = len(上一页)
    return df.iloc[:i], df.iloc[i:], df


def 寻找交叉范围(上一页, 当前页):
    """
    >>> 当前页 = load_ut_df(0)
    >>> 上一页 = load_ut_df(1)
    >>> 寻找交叉范围(上一页, 当前页)
       start  end  delta  equals
    0      0   11     11    True
    >>> 当前页 = pandas.DataFrame([{"唯一值": "2"}, {"唯一值": "1"}])
    >>> 上一页 = pandas.DataFrame([{"唯一值": "3"}, {"唯一值": "2"}])
    >>> 寻找交叉范围(上一页, 当前页)
       start  end  delta  equals
    0      1    2      1    True
    >>> 上一页 = pandas.DataFrame([{"唯一值": "2"}, {"唯一值": "3"}, {"唯一值": "2"}])
    >>> 当前页 = pandas.DataFrame([{"唯一值": "2"}, {"唯一值": "1"}])
    >>> 寻找交叉范围(上一页, 当前页)
       start  end  delta  equals
    1      2    3      1    True
    >>> 上一页 = pandas.DataFrame([{"唯一值": "2"}, {"唯一值": "3"}, {"唯一值": "2"}, {"唯一值": "1"}])
    >>> 当前页 = pandas.DataFrame([{"唯一值": "2"}, {"唯一值": "1"}, {"唯一值": "0"}])
    >>> 寻找交叉范围(上一页, 当前页)
       start  end  delta  equals
    1      2    5      3    True
    >>> 上一页 = pandas.DataFrame([{"唯一值": "2"}, {"唯一值": "3"}, {"唯一值": "2"}, {"唯一值": "1"}])
    >>> 当前页 = pandas.DataFrame([{"唯一值": "2"}, {"唯一值": "1"}, {"唯一值": "1"}])
    >>> 寻找交叉范围(上一页, 当前页)
       start  end  delta  equals
    2      2    5      3    True
    >>> 寻找交叉范围(上一页, None)
    >>> 寻找交叉范围(pandas.DataFrame(), pandas.DataFrame())
    >>> 寻找交叉范围(pandas.DataFrame(), None)
    >>> 寻找交叉范围(None, None)
    """
    # num = len(上一页)
    if 当前页 is None or 当前页.empty:
        return

    if 上一页 is None or 上一页.empty:
        return

    上一页, 当前页, _ = 串行后拆分(上一页, 当前页)

    ends = 当前页[当前页.唯一值 == 上一页.iloc[-1].唯一值].index.tolist()
    starts = 上一页[上一页.唯一值 == 当前页.iloc[0].唯一值].index.tolist()

    df = pandas.DataFrame(
        list(itertools.product(starts, ends)), columns=["start", "end"]
    )

    df["delta"] = df.end - df.start

    df = df[df.delta > 0].copy()

    df["equals"] = df.apply(
        lambda x: 是否匹配(上一页.loc[x.start :], 当前页.loc[: x.end]),
        axis=1,
    )

    tmp = df[df["equals"]]

    if not tmp.empty:
        df = tmp.sort_values(by="delta", ascending=False)
        return df


def 进行组内字段合并(group):
    d = {}
    for index, row in group.iterrows():
        for k, v in row.to_dict().items():
            if not pandas.isnull(v) and bool(v) and v != "False":
                if k == "上下文":
                    if not d.get("上下文"):
                        d.update({k: v})
                    elif len(d.get("上下文")) < len(v):
                        d.update({k: v})
                else:
                    d.update({k: v})
    return d


def 直接暴力合并(上一页, 当前页):
    """
    >>> page_current = pandas.DataFrame([{"唯一值": "2"}, {"唯一值": "1"}])
    >>> page_pre = pandas.DataFrame([{"唯一值": "3"}, {"唯一值": "2"}])
    >>> 直接暴力合并(page_pre, page_current)
      唯一值
    0   3
    1   2
    2   2
    3   1
    """
    # return 串行(page_pre, page_current)
    return pandas.concat([上一页, 当前页], ignore_index=True)


def 是否重合(上一页, 当前页):
    df = 寻找交叉范围(上一页, 当前页)
    return df is not None and not df.empty


def 得到新增部分df(df_history, df_current):
    df = 寻找交叉范围(df_history, df_current)
    if df is not None and not df.empty:
        _, _, whole = 串行后拆分(df_history, df_current)
        end = df.iloc[0].end
        return whole.loc[end + 1 :]
    return df_current


def 合并上下两个df(上一页, 当前页, safe=False):
    """
    >>> 上一页 = pandas.DataFrame([{"唯一值": "2", "上下文":"2"}, {"唯一值": "3", "上下文":"3"}, {"唯一值": "2", "上下文":"2 long"}, {"唯一值": "1", "上下文":"1 same"}])
    >>> 当前页 = pandas.DataFrame([{"唯一值": "2", "上下文":"2"}, {"唯一值": "1", "上下文":"1 same", "已处理":True,}, {"唯一值": "other", "上下文":"other"}])
    >>> 合并上下两个df(上一页, 当前页)
         唯一值     上下文    已处理
    0      2       2  False
    1      3       3  False
    4      2  2 long  False
    5      1  1 same   True
    6  other   other  False
    >>> 上一页 = pandas.DataFrame([{"唯一值": "2", "上下文":"2"}, {"唯一值": "3", "上下文":"3"}, {"唯一值": "2", "上下文":"2 long"}, {"唯一值": "1", "上下文":"1 same"}])
    >>> 当前页 = pandas.DataFrame([{"唯一值": "21", "上下文":"2"}, {"唯一值": "1", "上下文":"1 same", "已处理":True,}, {"唯一值": "other", "上下文":"other"}])
    >>> 合并上下两个df(上一页, 当前页)
    >>> 上一页 = pandas.DataFrame([{"唯一值": "2", "上下文":"2"}, {"唯一值": "3", "上下文":"3"}, {"唯一值": "2", "上下文":"2 long", "已处理":True}, {"唯一值": "1", "上下文":"1 same"}])
    >>> 当前页 = pandas.DataFrame([{"唯一值": "2", "上下文":"2 very long", "已处理":False}, {"唯一值": "1", "上下文":"1 same", "已处理":False}, {"唯一值": "other", "上下文":"other"}])
    >>> 合并上下两个df(上一页, 当前页)
         唯一值          上下文    已处理
    0      2            2  False
    1      3            3  False
    4      2  2 very long   True
    5      1       1 same  False
    6  other        other  False
    >>> get_hash_df(合并上下两个df(上一页=load_ut_df('1747730460.csv'), 当前页=load_ut_df('1747730206.csv')))
    '05b7e673bdded1d09875861bd0f82597551db29766209d96a5da936baaee2dc8'
    >>> cache = load_ut_df(1747797992)
    >>> current = load_ut_df(1747798049)
    >>> get_hash_df(合并上下两个df(current, cache)[["唯一值", "已处理", "上下文"]])
    '411ea705f2ef57a3c81d6a8c64585a9653efc4947d3b2718bf36103830985e4f'
    """
    df = 寻找交叉范围(上一页, 当前页)

    if df is not None and not df.empty:
        start = df.iloc[0].start
        end = df.iloc[0].end
        上一页, 当前页, whole = 串行后拆分(上一页, 当前页)
        others = whole[~whole.index.isin(whole.loc[start:end].index)]
        # print(others)
        上一页 = 上一页.loc[start:].reset_index(drop=True)
        当前页 = 当前页.loc[:end].reset_index(drop=True)
        上一页.行id = 当前页.行id
        # df = 串行(上一页, 当前页)
        df = pandas.concat([上一页, 当前页], ignore_index=True)
        # print(df)
        g = df.groupby("行id")
        tmp = pandas.DataFrame(g.apply(进行组内字段合并).to_list())
        tmp = tmp.set_index("行id", drop=True)
        # return tmp
        rtn = pandas.concat([others, tmp], axis=0)
        rtn.pop("行id")
        if "已处理" in rtn.columns:
            rtn.已处理.fillna(False, inplace=True)

        return rtn.sort_index()
    elif safe:
        return 直接暴力合并(上一页, 当前页)


def 将当前页和缓存融合并匹配历史表(当前页df, 历史df=None, 缓存df=None):
    """
    >>> df = 将当前页和缓存融合并匹配历史表(当前页df=load_ut_df('1747730206.csv'))[0]
    >>> get_hash_df(df) == 'dec031e9c3fd75fa7c25416c46b9289a29a25beb579d046cf5c42ce819ad099e'
    True
    >>> df, b = 将当前页和缓存融合并匹配历史表(当前页df=load_ut_df('1747730206.csv'), 历史df=load_ut_df('1747730460.csv'))
    >>> b
    True
    """
    是否和历史重合 = False
    if 缓存df is not None:
        df = 合并上下两个df(当前页df, 缓存df, safe=True)
    else:
        df = 当前页df

    if 历史df is None:
        pass
    else:
        是否和历史重合 = (
            合并上下两个df(上一页=历史df, 当前页=df, safe=False) is not None
        )
    return df, 是否和历史重合


# def 将当前页和缓存页的交叉部分设置为已处理(当前页df, 缓存df=None):
#     pass


def 将当前页和历史页的交叉部分设置为已处理(当前页df, 历史df=None):
    """
    >>> current = load_ut_df(1747816625)
    >>> history = load_ut_df(1747816677)
    >>> df = 将当前页和历史页的交叉部分设置为已处理(当前页df=current, 历史df=history)
    >>> get_hash_df(df)
    '1c88941abd102b9ab7e7041f0571c6161d87c19f7236f396bb778866a0856878'
    """
    if 历史df is None or 历史df.empty:
        return 当前页df
    df = 寻找交叉范围(上一页=历史df, 当前页=当前页df)
    if df is not None and not df.empty:
        start = df.iloc[0].start
        end = df.iloc[0].end
        _, 当前页df, _ = 串行后拆分(上一页=历史df, 当前页=当前页df)
        当前页df.loc[start:end, "已处理"] = True
        当前页df = 当前页df.reset_index(drop=True)
    return 当前页df


# def 处理图片或语音(df, phone):
#     pass
def 获得最后一个未处理的图片索引(df):
    if df is not None and not df.empty:
        tmp = df[~(df.已处理) & (df.类型.isin(["图片"]))]
        if not tmp.empty:
            return tmp.index[-1]
        df.已处理 = True


def 是否有未处理的图片(df):
    return 获得最后一个未处理的图片索引(df) is not None


def 超级合并函数(当前页df, 缓存df=None, 历史df=None, page=0, max_page=3):
    """
    >>> history = load_ut_df(1747828539)
    >>> current = load_ut_df(1747828708)
    >>> df = 超级合并函数(当前页df=current, 缓存df=None, 历史df=history).get('结果')
    >>> get_hash_df(df[["唯一值", "已处理", "上下文"]])
    'efd183f539ed14e7b3f689180f6cc6223cd4483321d168660b04bb530a417dec'
    >>> current = pandas.DataFrame()
    >>> 超级合并函数(当前页df=current, 缓存df=None, 历史df=history).get('缓存df').empty
    True
    """
    if not 当前页df.empty:
        缓存df = 合并上下两个df(上一页=当前页df, 当前页=缓存df, safe=True)

        是否和历史重合 = 是否重合(上一页=历史df, 当前页=缓存df)
        if 是否和历史重合:
            缓存df = 将当前页和历史页的交叉部分设置为已处理(缓存df, 历史df)

        if not 是否有未处理的图片(缓存df):
            if 是否和历史重合 or page >= max_page:
                缓存df.已处理 = True
                return {
                    "结果": 合并上下两个df(上一页=历史df, 当前页=缓存df, safe=True),
                    "缓存df": 缓存df,
                }
    else:
        缓存df = 当前页df if 缓存df is None else 缓存df
        if page >= max_page:
            return {
                "结果": 合并上下两个df(上一页=历史df, 当前页=缓存df, safe=True),
                "缓存df": 缓存df,
            }

    return {
        "缓存df": 缓存df,
    }


def 填充记录日志字典(func_add_log, d, **kwargs):
    if func_add_log is not None:
        for k, v in kwargs.items():
            if isinstance(v, pandas.DataFrame):
                v = v.to_json()
            d[k] = v


def 记录数据库日志(func_add_log, tmp_log: dict):
    if func_add_log is not None:
        func_add_log(tmp_log)


def 同步消息列表得到完整的会话(phone, 历史df=None, func_add_log=None):
    max_page = 3
    page = 0
    缓存df = None
    while 1:
        当前页df = phone.微信_获取当前页df()

        tmp_log = {}
        # if func_add_log is not None:
        # tmp_log = {
        #     "当前页": 当前页df.to_json() if 当前页df is not None else None,
        #     "缓存df": 缓存df.to_json() if 缓存df is not None else None,
        #     "历史df": 历史df.to_json() if 历史df is not None else None,
        #     "page": page,
        #     "max_page": max_page,
        # }
        填充记录日志字典(
            func_add_log,
            tmp_log,
            当前页=当前页df,
            缓存df=缓存df,
            历史df=历史df,
            page=page,
            max_page=max_page,
        )

        d = 超级合并函数(
            当前页df, 缓存df=缓存df, 历史df=历史df, page=page, max_page=max_page
        )

        # if func_add_log is not None:
        # tmp_log["结果"] = (
        #     d.get("结果").to_json() if d.get("结果") is not None else None
        # )
        # tmp_log["缓存df_result"] = (
        #     d.get("缓存df").to_json() if d.get("缓存df") is not None else None
        # )
        填充记录日志字典(
            func_add_log, tmp_log, 结果=d.get("结果"), 缓存df_result=d.get("缓存df")
        )
        # func_add_log(tmp_log)

        if d.get("结果") is not None:
            记录数据库日志(func_add_log, tmp_log)
            return d

        缓存df = d.get("缓存df")

        i = 获得最后一个未处理的图片索引(缓存df)

        if i is not None:
            phone.微信_保存未处理图片(缓存df, i)
            填充记录日志字典(func_add_log, tmp_log, 缓存df_result=缓存df)
            记录数据库日志(func_add_log, tmp_log)
            continue

        记录数据库日志(func_add_log, tmp_log)
        page += 1
        if page < max_page:
            phone.page_up()

        else:
            return {"缓存df": 缓存df}


# def 拆分消息列表到新消息与历史消息(df):
#     pass

def 转换自己(x):
    if x == "True":
        return 1
    elif x == "False":
        return 0
    return tool_env.to_int(x) or 0

def 标准化df(df):
    if not df.empty:
        if '自己' not in df.columns:
            df['自己'] = False
        else:
            # df.自己 = df.自己.apply(lambda x:SELF_MAP.get(x, 1)).fillna(0).astype(bool)
            df.自己 = df.自己.fillna(0).apply(转换自己).astype(bool)
    return df


def 得到新消息部分df(df):
    tmp = df[df.自己]
    if tmp.empty:
        return df
    return df.loc[tmp.index[-1]+1:]

if __name__ == "__main__":
    from helper_hash import get_hash_df
    import doctest

    print(doctest.testmod(verbose=False, report=False))
