import time
import pandas
import itertools

import tool_env

import tool_file

import json


def 记录日志(
    上一页: pandas.DataFrame,
    当前页: pandas.DataFrame,
    结果页: pandas.DataFrame,
    base_dir=tool_file.LOG_DIR,
):
    """
    将三个DataFrame转为JSON后存入字典，并保存到指定目录的时间命名JSON文件中

    参数:
        base_dir: str - 日志文件保存的基础目录
        上一页: pd.DataFrame - 要记录的上一页数据
        当前页: pd.DataFrame - 要记录的当前页数据
        结果页: pd.DataFrame - 要记录的结果页数据
    """
    from datetime import datetime

    try:
        # 1. 确保基础目录存在，不存在则创建

        # 2. 获取当前日期时间，生成文件名（格式：YYYYMMDD_HHMMSS.json）
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{current_time}.json"
        file_path = base_dir / file_name

        # 3. 构建包含三个DataFrame JSON数据的字典
        log_dict = {
            "上一页": 上一页.to_json(orient="records"),
            "当前页": 当前页.to_json(orient="records"),
            "结果页": 结果页.to_json(orient="records"),
        }

        # 4. 将字典写入JSON文件（ensure_ascii=False支持中文，indent=4增强可读性）
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(log_dict, f, ensure_ascii=False, indent=4)

        print(f"日志文件已成功保存至: {file_path}")

    except Exception as e:
        # 捕获并提示异常，避免程序崩溃
        print(f"记录日志时发生错误: {str(e)}")
        raise  # 可选：重新抛出异常，让调用方感知错误


def 加载日志(filepath: str):
    """
    从指定的JSON日志文件中加载数据，还原为包含DataFrame的字典

    参数:
        filepath: str - 日志文件的完整路径（如 ./log/20260108_153045.json）

    返回:
        dict - 包含三个DataFrame的字典，键为'上一页'、'当前页'、'结果页'

    异常:
        捕获文件不存在、JSON解析错误、DataFrame还原失败等异常并提示
    """
    import io

    try:
        # 1. 读取JSON文件内容
        with open(filepath, "r", encoding="utf-8") as f:
            log_data = json.load(f)

        # 2. 验证日志文件结构是否符合预期
        required_keys = ["上一页", "当前页", "结果页"]
        for key in required_keys:
            if key not in log_data:
                raise ValueError(f"日志文件缺少必要的键: {key}")

        # 3. 将JSON字符串还原为DataFrame
        result_dict = {
            "上一页": pandas.read_json(
                io.StringIO(log_data["上一页"]), orient="records"
            ),
            "当前页": pandas.read_json(
                io.StringIO(log_data["当前页"]), orient="records"
            ),
            "结果页": pandas.read_json(
                io.StringIO(log_data["结果页"]), orient="records"
            ),
        }

        # print(f"日志文件 {filepath} 加载成功")
        return result_dict

    except FileNotFoundError:
        print(f"错误：找不到指定的日志文件 - {filepath}")
        raise
    except json.JSONDecodeError:
        print(f"错误：{filepath} 不是有效的JSON文件")
        raise
    except ValueError as e:
        print(f"错误：DataFrame还原失败或文件结构异常 - {str(e)}")
        raise
    except Exception as e:
        print(f"加载日志时发生未知错误 - {str(e)}")
        raise


def 是否匹配(上一页, 当前页):
    """
    >>> 是否匹配(load_ut_df(0), load_ut_df(1))
    True
    >>> 是否匹配(load_ut_df(0), load_ut_df(1747730460))
    False
    """
    if len(上一页) != len(当前页):
        return False

    v = (
        上一页.唯一值.reset_index(drop=True) == 当前页.唯一值.reset_index(drop=True)
    ).all()

    if "上下文" in 上一页.columns:
        v = (
            v
            or (
                上一页.上下文.reset_index(drop=True)
                == 当前页.上下文.reset_index(drop=True)
            ).all()
        )

    return v


def 串行后拆分(上一页, 当前页):
    df = pandas.concat([上一页, 当前页], ignore_index=True)
    df["行id"] = df.index
    i = len(上一页)
    return df.iloc[:i], df.iloc[i:], df


def 寻找交叉范围(上一页, 当前页, debug=False):
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
    >>> 寻找交叉范围(d_test.get('上一页'), d_test.get('当前页'), debug=False).to_dict('records')
    [{'start': 3, 'end': 16, 'delta': 13, 'equals': True}]
    >>> 寻找交叉范围(d_test2.get('上一页'), d_test2.get('当前页'), debug=False).to_dict('records')
    [{'end': 14}]
    """
    # num = len(上一页)
    if 当前页 is None or 当前页.empty:
        return

    if 上一页 is None or 上一页.empty:
        return

    上一页, 当前页, whole = 串行后拆分(上一页, 当前页)

    ends = 当前页[当前页.唯一值 == 上一页.iloc[-1].唯一值].index.tolist()

    starts = 上一页[上一页.唯一值 == 当前页.iloc[0].唯一值].index.tolist()

    df = pandas.DataFrame(
        list(itertools.product(starts, ends)), columns=["start", "end"]
    )

    if not ends:
        return

    df["delta"] = df.end - df.start

    if debug:
        print("ends:", ends)
        print("starts:", starts)
        print("=======================上一页")
        print(上一页[["上下文", "唯一值", "时间"]])
        print("=======================当前页")
        print(当前页[["上下文", "唯一值", "时间"]])
        print("=======================df")
        print(df)

    df = df[df.delta > 0].copy()

    df["equals"] = df.apply(
        lambda x: 是否匹配(上一页.loc[x.start :], 当前页.loc[: x.end]),
        axis=1,
    )

    tmp = df[df["equals"]]

    if not tmp.empty:
        df = tmp.sort_values(by="delta", ascending=False)
        return df

    return pandas.DataFrame([{"end": ends[-1]}])


def 是否重合(上一页, 当前页):
    df = 寻找交叉范围(上一页, 当前页)
    return df is not None and not df.empty


def 得到新增部分df(df_history, df_current):
    """
    得到新增部分df 的 Docstring

    :param df_history: 说明
    :param df_current: 说明
    >>> 得到新增部分df(d_test.get('上一页'), d_test.get('当前页')).empty
    True
    """
    df = 寻找交叉范围(df_history, df_current)
    if df is not None and not df.empty:
        当前页截断位置 = df.iloc[0].end - len(df_history)
        新页 = df_current.iloc[当前页截断位置 + 1 :]
    else:
        新页 = df_current
    return 新页


def 合并上下两个df(上一页, 当前页):
    新页 = 得到新增部分df(上一页, 当前页)

    changed = not 新页.empty

    if changed:
        结果页 = pandas.concat([上一页, 新页], ignore_index=True)
    else:
        结果页 = 上一页

    if tool_env.U4080 and changed:
        记录日志(上一页, 当前页, 结果页)

    return 结果页, changed


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

    d_test = 加载日志(UT_DIR / "20260110_070421.json")
    # 20260110_123226.json
    d_test2 = 加载日志(UT_DIR / "20260110_123733.json")

    print(doctest.testmod(verbose=False, report=False))
    # print(d_test.keys())
    # print(d_test2.get('上一页'))
    # print(d_test2.get('当前页'))
