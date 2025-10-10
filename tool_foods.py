from datetime import datetime, time, timedelta
import re
import random

from django.utils import timezone

from tool_calculate_calories import calculate_calories

import tool_date

import copy


def extract_value(value_str):
    """
    从字符串中提取数值部分，去除单位后缀

    参数:
    value_str (str): 包含数值和单位的字符串，如 '15g', '123ml', '333kcal'

    返回:
    float: 提取的数值部分，如果无法提取则返回 0

    >>> extract_value('15g')
    15.0
    >>> extract_value('123.45ml')
    123.45
    >>> extract_value('-333kcal')
    -333.0
    >>> extract_value('0.5kg')
    0.5
    >>> extract_value('+78.9%')
    78.9
    >>> extract_value('abc')
    0
    >>> extract_value('123.45.67')
    123.45
    >>> extract_value('  -25.5g ')
    -25.5
    >>> extract_value('1,000ml')
    1000.0
    >>> extract_value('15.')
    15.0
    >>> extract_value('0.5kg')
    0.5
    >>> extract_value('123')
    123.0
    """
    # 使用正则表达式匹配数字部分
    # 匹配可能的负号、整数、小数点和小数部分
    match = re.match(r"^([-+]?\d+(?:\.\d+)?)(.*)$", value_str.replace(",", "").strip())

    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return 0
    return 0


def classify_meal_time(dt: datetime) -> str:
    """
    根据输入的datetime对象判断对应的餐别

    参数:
    dt (datetime): 需要判断的日期时间对象

    返回:
    str: 餐别分类结果，可能为 "早餐", "午餐", "晚餐", "加餐"

    >>> classify_meal_time(datetime(2023, 1, 1, 7, 30))
    '早餐'
    >>> classify_meal_time(datetime(2023, 1, 1, 9, 0))
    '早餐'
    >>> classify_meal_time(datetime(2023, 1, 1, 11, 0))
    '午餐'
    >>> classify_meal_time(datetime(2023, 1, 1, 14, 0))
    '午餐'
    >>> classify_meal_time(datetime(2023, 1, 1, 18, 0))
    '晚餐'
    >>> classify_meal_time(datetime(2023, 1, 1, 20, 0))
    '晚餐'
    >>> classify_meal_time(datetime(2023, 1, 1, 10, 0))
    '加餐'
    >>> classify_meal_time(datetime(2023, 1, 1, 21, 30))
    '加餐'
    """
    # 定义三餐的时间范围（可根据实际需求调整）
    BREAKFAST_START = time(6, 0)  # 早餐开始时间：6:00
    BREAKFAST_END = time(9, 0)  # 早餐结束时间：9:00
    LUNCH_START = time(11, 0)  # 午餐开始时间：11:00
    LUNCH_END = time(14, 0)  # 午餐结束时间：14:00
    DINNER_START = time(17, 0)  # 晚餐开始时间：17:00
    DINNER_END = time(20, 0)  # 晚餐结束时间：20:00

    # 获取当前时间的时间部分
    current_time = dt.time()

    # 判断所属餐别
    if BREAKFAST_START <= current_time <= BREAKFAST_END:
        return "早餐"
    elif LUNCH_START <= current_time <= LUNCH_END:
        return "午餐"
    elif DINNER_START <= current_time <= DINNER_END:
        return "晚餐"
    else:
        return "加餐"


def parse_quantity(line):
    """
    解析包含数值和单位的字符串，返回平均值和单位。

    参数:
    line (str): 包含数值和单位的字符串，数值部分可以是单个值或范围

    返回:
    tuple: (平均值, 单位)

    示例:
    >>> parse_quantity("1100-1400g")
    (1250.0, 'g')
    >>> parse_quantity('1000-1200kcal')
    (1100.0, 'kcal')
    >>> parse_quantity('1000kcal')
    (1000.0, 'kcal')
    >>> parse_quantity('1,230kcal')
    (1230.0, 'kcal')
    >>> parse_quantity('5.5-7.5mg')
    (6.5, 'mg')
    >>> parse_quantity('5.5-7.5')
    (6.5, '')
    >>> parse_quantity('100%')
    (100.0, '%')
    >>> parse_quantity('1,000,000ml')
    (1000000.0, 'ml')
    >>> parse_quantity('1-5g')
    (3.0, 'g')
    >>> parse_quantity('1-5')
    (3.0, '')
    >>> parse_quantity('未知')
    (0.0, '')
    """
    import re

    # print(line)

    # 提取数值部分（处理范围和千分位逗号）
    m = re.search(r"^[\d\.,\-]+", line)
    num_part = m.group(0) if m else "0"

    # 提取单位部分（可能为空）
    unit_part = line[len(num_part) :].strip() if m else ""

    # 处理范围
    if "-" in num_part and not num_part.startswith("-"):
        bounds = num_part.split("-", 1)
        lower = float(bounds[0].replace(",", ""))
        upper = float(bounds[1].replace(",", ""))
        average = (lower + upper) / 2
    else:
        # 处理单个数值（可能包含千分位逗号）
        average = float(num_part.replace(",", ""))

    return average, unit_part


def transform_food_data(input_data, meal_type=None):

    # print(input_data)
    # 初始化返回数据结构
    output_data = {
        "data_list": [
            {"name": "碳水", "value": "0", "unit": "g"},
            {"name": "蛋白质", "value": "0", "unit": "g"},
            {"name": "脂肪", "value": "0", "unit": "g"},
            {"name": "总热量", "value": "0", "unit": "千卡"},
        ],
        "summary": input_data.get("summary", ""),
        "meal_data": {
            "total_calories": 0,
            "dishes": [],
            "intake_calories": 0,
            "type": meal_type,
            "intake_rate": 0,
        },
    }

    # 营养素映射表
    nutrient_map = {"碳水": 0, "蛋白质": 1, "脂肪": 2, "总热量": 3}

    total_calories = 0

    # 处理每个菜品
    for dish in input_data.get("foods", []):
        # 提取和验证单位
        # weight = dish.get("weight", "")
        # if not weight.endswith("g"):
        #     raise ValueError(f"无效的重量单位: {weight}")

        # calories = dish.get("calories", "")
        # if not calories.endswith("kcal"):
        #     raise ValueError(f"无效的热量单位: {calories}")

        # # 转换为数值
        # weight_value = float(weight[:-1])
        # calories_value = float(calories[:-4])
        weight_value, u = parse_quantity(dish.get("weight", ""))
        if weight_value:
            assert u == "g", f"无效的重量单位: {u}"
        else:
            u = "g"

        calories_value, u = parse_quantity(dish.get("calories", ""))
        if calories_value:
            assert u == "kcal", f"无效的热量单位: {u}"
        else:
            u = "kcal"

        total_calories += calories_value

        # 构建菜品数据
        dish_data = {
            "name": dish.get("name", ""),
            "heat_level": dish.get("heat_level", ""),
            "calories": calories_value,
            "intake_rate": 100,
            "weight": weight_value,
            "is_selected": True,  # 默认全部选中
            "nutrition_list": [],
        }
        output_data["meal_data"]["dishes"].append(dish_data)

        # 处理营养成分
        for nutrient in dish.get("nutrition_list", []):
            nutrient_name = nutrient.get("name", "")
            nutrient_value = extract_value(nutrient.get("value", "0"))
            nutrient_unit = nutrient.get("unit", "")
            dish_data["nutrition_list"].append(
                {
                    "name": nutrient_name,
                    "value": f"{nutrient_value}",
                    "unit": nutrient_unit,
                }
            )

            if nutrient_name in nutrient_map:
                idx = nutrient_map[nutrient_name]
                assert nutrient_unit == output_data["data_list"][idx]["unit"]
                current_value = float(output_data["data_list"][idx]["value"])
                output_data["data_list"][idx]["value"] = str(
                    current_value + nutrient_value
                )

    # 设置总热量
    output_data["data_list"][nutrient_map["总热量"]]["value"] = str(total_calories)
    output_data["meal_data"]["total_calories"] = total_calories
    output_data["meal_data"]["intake_calories"] = total_calories

    # 计算摄入率
    if total_calories > 0:
        output_data["meal_data"]["intake_rate"] = 100

    return output_data


# {"data_list": [{"name": "微信步数", "value": 8984, "unit": "步"}, {"name": "强度", "value": "中速", "unit": ""}], "summary": "2025-10-09走了8984步"}


def generate_wx_steps(start_date, end_date):
    """
    生成指定日期范围内的微信步数数据

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期

    返回:
        list: 包含微信步数记录的列表，每个元素为包含"steps"和"datetime"的字典
    """
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")

    output_data = []
    current_date = start_date

    tpl = {
        "data_list": [
            {"name": "微信步数", "value": 8984, "unit": "步"},
            {"name": "强度", "value": "中速", "unit": ""},
            {"name": "耗能", "value": 0, "unit": "千卡"}
        ],
        "summary": "",
    }

    while current_date <= end_date:
        steps = random.randint(1000, 20000)
        burned = calculate_calories(
            40,
            "male",
            170,
            90,
            steps,
            walk_type="medium",
        )

        tmp = copy.deepcopy(tpl)
        tmp["data_list"][0]["value"] = steps
        tmp["data_list"][-1]["value"] = burned
        tmp["create_time"] = tool_date.日期转随机北京时间(current_date)
        tmp["是否测试数据"] = True
        tmp["类型"] = "微信步数"
        tmp["图片识别内容"] = "-"
        output_data.append(tmp)
        current_date += timedelta(days=1)

    return output_data


def generate_calorie_intake(
    start_date,
    end_date,
    meal_fast_prob=0.2,
    all_day_fast_prob=0.05,
    binge_eating_prob=0.1,  # 新增：每餐暴食概率，默认10%
):
    """
    生成指定日期范围内的随机热量摄入数据（含暴食概率）

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期
        meal_fast_prob (float): 单餐断食概率 (0-1), 默认0.2
        all_day_fast_prob (float): 全天断食概率 (0-1), 默认0.05
        binge_eating_prob (float): 每餐暴食概率 (0-1), 默认0.1（10%概率）

    返回:
        list: 包含热量摄入记录的列表，每个元素为包含"total_calories"和"datetime"的字典
    """
    # 输入验证（新增暴食概率验证）
    if not (0 <= meal_fast_prob <= 1):
        raise ValueError("单餐断食概率必须在0到1之间")
    if not (0 <= all_day_fast_prob <= 1):
        raise ValueError("全天断食概率必须在0到1之间")
    if not (0 <= binge_eating_prob <= 1):
        raise ValueError("暴食概率必须在0到1之间")
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")

    output_data = []
    current_date = start_date

    # 定义三餐的配置：包含正常热量范围、暴食热量范围、时间范围
    # 暴食热量设置为正常范围的1.5-3倍（符合实际暴食场景）
    meal_configs = [
        {
            "time_range": (6, 9),
            "normal_calorie": (200, 500),  # 正常早餐
            "binge_calorie": (600, 1500),  # 暴食早餐（显著高于正常）
        },
        {
            "time_range": (11, 14),
            "normal_calorie": (300, 800),  # 正常午餐
            "binge_calorie": (900, 2200),  # 暴食午餐
        },
        {
            "time_range": (17, 20),
            "normal_calorie": (200, 700),  # 正常晚餐
            "binge_calorie": (800, 2000),  # 暴食晚餐
        },
    ]

    tpl = {
        "data_list": [
            {"name": "碳水", "value": "0", "unit": "g"},
            {"name": "蛋白质", "value": "0", "unit": "g"},
            {"name": "脂肪", "value": "0", "unit": "g"},
            {"name": "总热量", "value": "0", "unit": "千卡"},
        ],
        # "summary": input_data.get("summary", ""),
        "meal_data": {
            "total_calories": 0,
            "dishes": [],
            "intake_calories": 0,
            # "type": meal_type,
            "intake_rate": 100,
        },
    }

    while current_date <= end_date:
        # 检查是否全天断食
        if random.random() < all_day_fast_prob:
            current_date += timedelta(days=1)
            continue

        # 处理当天的每一餐
        for config in meal_configs:
            # 检查是否单餐断食（断食则跳过）
            if random.random() < meal_fast_prob:
                continue

            # 生成随机时间（时分）
            start_hour, end_hour = config["time_range"]
            # hour = random.randint(start_hour, end_hour)
            # minute = random.randint(0, 59)
            # meal_datetime = datetime.combine(current_date, time(hour, minute))

            # meal_datetime = timezone.make_aware(
            #     meal_datetime,
            #     timezone=timezone.get_current_timezone()  # 使用 Django 配置的时区（如 Asia/Shanghai）
            # )
            meal_datetime = tool_date.日期转随机北京时间(current_date)

            # 确定热量范围：判断是否触发暴食
            if random.random() < binge_eating_prob:
                # 暴食场景：使用暴食热量范围
                min_cal, max_cal = config["binge_calorie"]
            else:
                # 正常场景：使用正常热量范围
                min_cal, max_cal = config["normal_calorie"]

            # 生成随机热量（整数）
            calories = random.randint(min_cal, max_cal)

            # 添加到结果列表
            # tmp = tpl.copy()
            tmp = copy.deepcopy(tpl)
            tmp["meal_data"]["total_calories"] = calories
            tmp["meal_data"]["intake_calories"] = calories
            tmp["data_list"][-1]["value"] = str(calories)
            tmp["create_time"] = meal_datetime
            tmp["是否测试数据"] = True
            tmp["类型"] = "热量记录"
            tmp["图片识别内容"] = "-"
            output_data.append(tmp)

        current_date += timedelta(days=1)

    # 按时间排序
    # output_data.sort(key=lambda x: x["datetime"])
    return output_data


# 使用示例
if __name__ == "__main__":
    # 这里应该使用实际的input_data
    # 为简化示例，此处省略具体数据
    # transformed_data = transform_food_data(input_data)
    # print(transformed_data)
    import json

    input_data = {
        "foods": [
            {
                "name": "清炒圆白菜",
                "weight": "225g",
                "calories": "50kcal",
                "heat_level": "放心吃",
                "material": "圆白菜",
                "nutrition_list": [
                    {"name": "碳水", "value": "10", "unit": "g"},
                    {"name": "蛋白质", "value": "2", "unit": "g"},
                    {"name": "脂肪", "value": "0.2", "unit": "g"},
                ],
            },
            {
                "name": "清炒空心菜",
                "weight": "225g",
                "calories": "40kcal",
                "heat_level": "放心吃",
                "material": "空心菜",
                "nutrition_list": [
                    {"name": "碳水", "value": "5", "unit": "g"},
                    {"name": "蛋白质", "value": "3", "unit": "g"},
                    {"name": "脂肪", "value": "0.3", "unit": "g"},
                ],
            },
            {
                "name": "蘑菇海带炖肉汤",
                "weight": "500g",
                "calories": "300kcal",
                "heat_level": "适量",
                "material": "蘑菇, 海带, 肉",
                "nutrition_list": [
                    {"name": "碳水", "value": "20", "unit": "g"},
                    {"name": "蛋白质", "value": "30", "unit": "g"},
                    {"name": "脂肪", "value": "20", "unit": "g"},
                ],
            },
            {
                "name": "红椒炒饭",
                "weight": "225g",
                "calories": "300kcal",
                "heat_level": "适量",
                "material": "红椒, 米饭",
                "nutrition_list": [
                    {"name": "碳水", "value": "40", "unit": "g"},
                    {"name": "蛋白质", "value": "5", "unit": "g"},
                    {"name": "脂肪", "value": "10", "unit": "g"},
                ],
            },
        ],
        "summary": "热量适中，营养均衡，放心吃",
    }

    transformed_data = transform_food_data(input_data)
    # print(json.dumps(transformed_data, ensure_ascii=False, indent=2))
    import doctest

    print(doctest.testmod(verbose=False, report=False))
