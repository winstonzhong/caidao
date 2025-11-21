import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Union, Dict, Optional

# 缓存已查询的日期节假日数据（key：YYYY-MM-DD，value：节假日信息）
HOLIDAY_CACHE: Dict[str, Dict] = {}

# 配置requests重试机制和超时控制
session = requests.Session()
retry_strategy = Retry(
    total=3,  # 最大重试3次
    backoff_factor=0.5,  # 重试间隔（0.5秒、1秒、2秒...）
    status_forcelist=[429, 500, 502, 503, 504],  # 对服务器错误重试
    allowed_methods=["GET"]
)
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})  # 模拟浏览器请求，避免403


def is_weekend(date: Union[str, datetime.date]) -> bool:
    """
    判断日期是否是周末（周六/周日）
    :param date: 日期，支持字符串（如'2025-11-21'）或datetime.date对象
    :return: True=周末，False=非周末
    :raises ValueError: 日期格式错误
    """
    # 统一转换为date对象
    if isinstance(date, str):
        try:
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"日期格式错误：{date}，请使用'YYYY-MM-DD'格式")
    
    # weekday()：0=周一，1=周二...5=周六，6=周日
    return date.weekday() >= 5


def get_holiday_info(date: Union[str, datetime.date]) -> Optional[Dict]:
    """
    调用牛客网API获取日期的节假日信息
    :param date: 日期，支持字符串（如'2025-11-21'）或datetime.date对象
    :return: 节假日信息字典，None=查询失败
    """
    # 统一转换为date对象和标准格式字符串
    if isinstance(date, str):
        try:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"日期格式错误：{date}，请使用'YYYY-MM-DD'格式")
    else:
        date_obj = date
    
    date_str = date_obj.strftime("%Y-%m-%d")  # 缓存key格式
    api_date_str = date_obj.strftime("%Y%m%d")  # API请求格式（无横杠）

    # 优先从缓存获取
    if date_str in HOLIDAY_CACHE:
        return HOLIDAY_CACHE[date_str]

    # 调用牛客网节假日API
    api_url = f"https://api.niukewang.com/api/v1/holiday?date={api_date_str}"
    try:
        response = session.get(api_url, timeout=8)
        response.raise_for_status()  # 抛出HTTP错误（4xx/5xx）
        result = response.json()
        
        # 解析API返回（code=0表示成功）
        if result.get("code") != 0:
            print(f"API返回错误：{result.get('msg', '未知错误')}")
            return None
        
        holiday_data = result.get("data", {})
        # 标准化返回格式（方便后续判断）
        standardized_data = {
            "is_holiday": holiday_data.get("isHoliday", False),
            "is_workday": holiday_data.get("isWorkday", True),
            "holiday_name": holiday_data.get("holidayName", "")
        }
        
        # 存入缓存
        HOLIDAY_CACHE[date_str] = standardized_data
        return standardized_data

    except requests.exceptions.RequestException as e:
        print(f"API调用失败：{str(e)}")
        return None


def judge_date_type(date: Union[str, datetime.date]) -> str:
    """
    综合判断日期类型：正常工作日、调休工作日、周末、节假日
    :param date: 日期，支持字符串（如'2025-11-21'）或datetime.date对象
    :return: 日期类型字符串
    """
    date_str = date if isinstance(date, str) else date.strftime("%Y-%m-%d")
    is_weekend_flag = is_weekend(date)
    holiday_info = get_holiday_info(date)

    # 处理API查询失败的情况
    if not holiday_info:
        return f"{'周末' if is_weekend_flag else '工作日'}（节假日查询失败）"

    # 综合判断逻辑
    if holiday_info["is_holiday"]:
        # 节假日（无论是否周末）
        holiday_name = holiday_info["holiday_name"] or "未知节假日"
        return f"节假日（{holiday_name}）"
    elif is_weekend_flag and holiday_info["is_workday"]:
        # 周末但需要上班（调休）
        return "调休工作日（周末）"
    elif is_weekend_flag and not holiday_info["is_workday"]:
        # 正常周末
        return "周末"
    else:
        # 非周末且非节假日 = 正常工作日
        return "正常工作日"


# ------------------- 测试示例 -------------------
if __name__ == "__main__":
    test_dates = [
        "2025-10-01",  # 国庆节（节假日）
        "2025-11-22",  # 周六（周末）
        "2025-11-21",  # 周五（正常工作日）
        "2025-01-01",  # 元旦（节假日）
        "2025-01-05",  # 周日（2025年元旦调休，需上班）
        "2025-02-01",  # 周六（正常周末，2025年2月1日是周六）
        "2025-02-12",  # 春节（2025年春节，节假日）
        "2024-02-10",  # 春节调休工作日（周六上班）
        "2024-10-07",  # 国庆调休工作日（周一上班）
    ]
    
    for date in test_dates:
        try:
            result = judge_date_type(date)
            print(f"{date} → {result}")
        except ValueError as e:
            print(f"{date} → {str(e)}")