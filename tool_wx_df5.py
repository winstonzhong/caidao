import time
import pandas
import itertools



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


def 合并上下两个df(上一页, 当前页):
    df = 寻找交叉范围(上一页, 当前页)
    if df is not None and not df.empty:
        当前页截断位置 = df.iloc[0].end - len(上一页)
        当前页 = 当前页.iloc[当前页截断位置+1:]

    changed = not 当前页.empty
    if changed:
        return pandas.concat([上一页, 当前页], ignore_index=True), True
    return 上一页, False

if __name__ == "__main__":
    import doctest

    from pathlib import Path


    UT_DIR = Path(__file__).parent.resolve() / "ut"



    def load_ut_df(name):
        return pandas.read_csv(UT_DIR / f"{str(name).split('.', maxsplit=1)[0]}.csv")


    def save_ut_df(df, name=None):
        name = name if name else f"{time.time():.0f}"
        df.to_csv(UT_DIR / f"{name}.csv", index=False)
        return name


    def save_ut_df_phone(phone, name=None):
        return save_ut_df(phone.微信_获取当前页df(), name)

    print(doctest.testmod(verbose=False, report=False))
