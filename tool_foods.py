from datetime import datetime, time
import re


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
    match = re.match(r"^([-+]?\d+(?:\.\d+)?)(.*)$", value_str.replace(',','').strip())

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


def transform_food_data(input_data, meal_type=None):
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
        weight = dish.get("weight", "")
        if not weight.endswith("g"):
            raise ValueError(f"无效的重量单位: {weight}")

        calories = dish.get("calories", "")
        if not calories.endswith("kcal"):
            raise ValueError(f"无效的热量单位: {calories}")

        # 转换为数值
        weight_value = float(weight[:-1])
        calories_value = float(calories[:-4])
        total_calories += calories_value

        # 构建菜品数据
        dish_data = {
            "name": dish.get("name", ""),
            "heat_level": dish.get("heat_level", ""),
            "calories": calories_value,
            "intake_rate": 100,
            "weight": weight_value,
            "is_selected": True,  # 默认全部选中
            "nutrition_list":[],
        }
        output_data["meal_data"]["dishes"].append(dish_data)

        # 处理营养成分
        for nutrient in dish.get("nutrition_list", []):
            nutrient_name = nutrient.get("name", "")
            nutrient_value = extract_value(nutrient.get("value", "0"))
            nutrient_unit = nutrient.get("unit", "")
            dish_data["nutrition_list"].append({"name": nutrient_name, "value": f'{nutrient_value}', "unit": nutrient_unit})

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
    print(json.dumps(transformed_data, ensure_ascii=False, indent=2))
    import doctest
    print(doctest.testmod(verbose=False, report=False))
