from datetime import datetime, time, timedelta
import re
import random

# from django.utils import timezone

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


def generate_heart_rate(start_date, end_date):
    """
    生成指定日期范围内的心率记录数据

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期

    返回:
        list: 包含心率记录的列表，每个元素为包含心率信息和日期时间的字典
    """
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")

    output_data = []
    current_date = start_date

    # 心率记录模板
    tpl = {
        "data_list": [
            {"name": "心率", "value": 75, "unit": "次/分钟"},
            {"name": "状态", "value": "静息", "unit": ""},
            {"name": "测量时段", "value": "上午", "unit": ""}
        ],
        "summary": "",
    }

    # 可能的状态和测量时段选项
    status_options = ["静息", "日常活动", "轻度运动后", "睡眠中"]
    time_periods = ["凌晨", "上午", "下午", "晚上"]

    while current_date <= end_date:
        # 生成正常范围的心率（60-100次/分钟）
        heart_rate = random.randint(60, 100)
        # 随机选择状态（静息状态概率更高）
        status = random.choices(
            status_options,
            weights=[0.5, 0.2, 0.1, 0.2],  # 权重分配，静息占比最高
            k=1
        )[0]
        # 随机选择测量时段
        time_period = random.choice(time_periods)

        # 复制模板并替换数据
        tmp = copy.deepcopy(tpl)
        tmp["data_list"][0]["value"] = heart_rate
        tmp["data_list"][1]["value"] = status
        tmp["data_list"][2]["value"] = time_period
        # 设置创建时间（使用工具函数生成随机北京时间）
        tmp["create_time"] = tool_date.日期转随机北京时间(current_date)
        tmp["是否测试数据"] = True
        tmp["类型"] = "心率记录"
        tmp["图片识别内容"] = "-"

        output_data.append(tmp)
        current_date += timedelta(days=1)

    return output_data



def generate_blood_oxygen(start_date, end_date):
    """
    生成指定日期范围内的血氧记录数据

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期

    返回:
        list: 包含血氧记录的列表，每个元素为包含血氧信息和日期时间的字典
    """
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")

    output_data = []
    current_date = start_date

    # 血氧记录模板
    tpl = {
        "data_list": [
            {"name": "血氧饱和度", "value": 98, "unit": "%"},
            {"name": "状态", "value": "静息", "unit": ""},
            {"name": "测量环境", "value": "室内", "unit": ""}
        ],
        "summary": "",
    }

    # 可能的状态和测量环境选项
    status_options = ["静息", "日常活动后", "睡眠中", "轻度运动后"]
    environment_options = ["室内", "室外", "空调房", "运动后"]

    while current_date <= end_date:
        # 生成正常范围的血氧值（95%-100%）
        oxygen_level = random.randint(95, 100)
        # 随机选择状态（静息状态概率更高）
        status = random.choices(
            status_options,
            weights=[0.5, 0.2, 0.2, 0.1],  # 权重分配，静息占比最高
            k=1
        )[0]
        # 随机选择测量环境
        environment = random.choice(environment_options)

        # 复制模板并替换数据
        tmp = copy.deepcopy(tpl)
        tmp["data_list"][0]["value"] = oxygen_level
        tmp["data_list"][1]["value"] = status
        tmp["data_list"][2]["value"] = environment
        # 设置创建时间（使用工具函数生成随机北京时间）
        tmp["create_time"] = tool_date.日期转随机北京时间(current_date)
        tmp["是否测试数据"] = True
        tmp["类型"] = "血氧记录"
        tmp["图片识别内容"] = "-"

        output_data.append(tmp)
        current_date += timedelta(days=1)

    return output_data




def generate_blood_pressure(start_date, end_date):
    """
    生成指定日期范围内的血压记录数据

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期

    返回:
        list: 包含血压记录的列表，每个元素为包含血压信息和日期时间的字典
    """
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")

    output_data = []
    current_date = start_date

    # 血压记录模板（严格遵循指定格式）
    tpl = {
        "data_list": [
            {"name": "高压", "value": 135, "unit": "mmHg"},
            {"name": "低压", "value": 94, "unit": "mmHg"},
            {"name": "脉搏", "value": 83, "unit": "次/分"}
        ],
        "summary": "血压正常，继续监测。"
    }

    while current_date <= end_date:
        # 生成正常范围血压值：
        # 高压（收缩压）：90-139 mmHg
        # 低压（舒张压）：60-89 mmHg
        # 脉搏：60-100 次/分
        systolic = random.randint(90, 169)
        diastolic = random.randint(60, 109)
        pulse = random.randint(60, 100)

        # 根据血压值生成summary描述
        if systolic < 120 and diastolic < 80:
            summary = "血压正常，继续保持健康生活方式。"
        elif 120 <= systolic <= 139 or 80 <= diastolic <= 89:
            summary = "血压处于正常高值，建议定期监测。"
        else:
            summary = "血压略高，注意休息，减少盐分摄入。"

        # 复制模板并替换数据
        tmp = copy.deepcopy(tpl)
        tmp["data_list"][0]["value"] = systolic  # 高压值
        tmp["data_list"][1]["value"] = diastolic  # 低压值
        tmp["data_list"][2]["value"] = pulse  # 脉搏值
        tmp["summary"] = summary  # 更新summary
        # 设置创建时间（使用工具函数生成随机北京时间）
        tmp["create_time"] = tool_date.日期转随机北京时间(current_date)
        tmp["是否测试数据"] = True
        tmp["类型"] = "血压记录"
        tmp["图片识别内容"] = "-"

        output_data.append(tmp)
        current_date += timedelta(days=1)

    return output_data


def generate_blood_glucose(start_date, end_date):
    """
    生成指定日期范围内的血糖记录数据

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期

    返回:
        list: 包含血糖记录的列表，每个元素为包含血糖信息、状态和日期时间的字典
    """
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")

    output_data = []
    current_date = start_date

    # 血糖记录模板（严格遵循补充后的数据格式）
    tpl = {
        "data_list": [
            {"name": "血糖", "value": "6.4", "unit": "mmol/L"},
            {"name": "状态", "value": "空腹", "unit": ""}  # 新增状态字段
        ],
        "summary": "血糖正常，继续保持。"
    }

    # 测量状态选项及对应正常范围（mmol/L）
    measure_states = ["空腹", "餐后1小时", "餐后2小时", "随机"]
    state_ranges = {
        "空腹": (3.9, 6.1),
        "餐后1小时": (3.9, 9.0),
        "餐后2小时": (3.9, 7.8),
        "随机": (3.9, 11.1)
    }

    while current_date <= end_date:
        # 随机选择测量状态
        state = random.choice(measure_states)
        # 根据状态生成对应范围的血糖值（保留1位小数）
        min_val, max_val = state_ranges[state]
        glucose = round(random.uniform(min_val, max_val), 1)

        # 根据血糖值和状态生成summary
        if state == "空腹":
            if glucose < 3.9:
                summary = "空腹血糖偏低，建议适当补充碳水化合物。"
            elif glucose <= 6.1:
                summary = "空腹血糖正常，继续保持规律饮食。"
            else:
                summary = "空腹血糖略高，建议控制精制糖摄入并监测变化。"
        elif state == "餐后2小时":
            if glucose <= 7.8:
                summary = "餐后2小时血糖正常，饮食搭配合理。"
            else:
                summary = "餐后2小时血糖略高，建议减少主食量并增加膳食纤维。"
        else:  # 餐后1小时或随机
            if glucose <= max_val:
                summary = f"{state}血糖正常，继续保持健康生活方式。"
            else:
                summary = f"{state}血糖略高，注意控制饮食总量。"

        # 复制模板并替换数据
        tmp = copy.deepcopy(tpl)
        tmp["data_list"][0]["value"] = f"{glucose}"  # 血糖值（字符串类型）
        tmp["data_list"][1]["value"] = state  # 填充状态字段
        tmp["summary"] = summary
        # 设置创建时间
        tmp["create_time"] = tool_date.日期转随机北京时间(current_date)
        tmp["是否测试数据"] = True
        tmp["类型"] = "血糖记录"
        tmp["图片识别内容"] = "-"

        output_data.append(tmp)
        current_date += timedelta(days=1)

    return output_data




def generate_respiratory_rate(start_date, end_date):
    """
    生成指定日期范围内的呼吸率记录数据

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期

    返回:
        list: 包含呼吸率记录的列表，每个元素为包含呼吸率信息、状态和日期时间的字典
    """
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")

    output_data = []
    current_date = start_date

    # 呼吸率记录模板
    tpl = {
        "data_list": [
            {"name": "呼吸率", "value": 16, "unit": "次/分钟"},
            {"name": "状态", "value": "静息", "unit": ""}
        ],
        "summary": "呼吸率正常，心肺功能稳定。"
    }

    # 可能的状态选项（影响呼吸率波动）
    status_options = ["静息", "日常活动中", "睡眠中", "轻度运动后"]
    # 不同状态下的呼吸率正常范围（次/分钟）
    # 参考标准：成人静息12-20，活动后可能略高但通常不超过24
    status_ranges = {
        "静息": (12, 20),
        "日常活动中": (14, 22),
        "睡眠中": (12, 18),
        "轻度运动后": (16, 24)
    }

    while current_date <= end_date:
        # 随机选择状态（静息状态概率更高）
        status = random.choices(
            status_options,
            weights=[0.5, 0.2, 0.2, 0.1],
            k=1
        )[0]
        # 根据状态生成对应范围的呼吸率
        min_rate, max_rate = status_ranges[status]
        respiratory_rate = random.randint(min_rate, max_rate)

        # 根据呼吸率和状态生成summary
        if status == "静息":
            if 12 <= respiratory_rate <= 20:
                summary = "静息状态呼吸率正常，呼吸平稳。"
            else:
                summary = f"静息状态呼吸率{respiratory_rate}次/分钟，略偏离正常范围，建议观察。"
        elif status == "睡眠中":
            if 12 <= respiratory_rate <= 18:
                summary = "睡眠中呼吸率正常，睡眠质量良好。"
            else:
                summary = f"睡眠中呼吸率{respiratory_rate}次/分钟，若伴随打鼾建议关注。"
        else:  # 日常活动或轻度运动后
            if respiratory_rate <= max_rate:
                summary = f"{status}呼吸率正常，身体适应状态良好。"
            else:
                summary = f"{status}呼吸率{respiratory_rate}次/分钟，略快，建议适当休息。"

        # 复制模板并替换数据
        tmp = copy.deepcopy(tpl)
        tmp["data_list"][0]["value"] = respiratory_rate  # 呼吸率值
        tmp["data_list"][1]["value"] = status  # 状态值
        tmp["summary"] = summary
        # 设置创建时间
        tmp["create_time"] = tool_date.日期转随机北京时间(current_date)
        tmp["是否测试数据"] = True
        tmp["类型"] = "呼吸率记录"
        tmp["图片识别内容"] = "-"

        output_data.append(tmp)
        current_date += timedelta(days=1)

    return output_data


def generate_uric_acid(start_date, end_date):
    """
    生成指定日期范围内的尿酸记录数据（不含性别字段）

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期

    返回:
        list: 包含尿酸记录的列表，每个元素为包含尿酸信息、状态和日期时间的字典
    """
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")

    output_data = []
    current_date = start_date

    # 尿酸记录模板（不含性别，新增测量状态字段）
    tpl = {
        "data_list": [
            {"name": "尿酸", "value": 350, "unit": "μmol/L"},
            {"name": "测量状态", "value": "空腹", "unit": ""}
        ],
        "summary": "尿酸值正常，建议保持低嘌呤饮食。"
    }

    # 测量状态选项（不影响数值范围，仅用于场景模拟）
    status_options = ["空腹", "随机", "餐后2小时"]
    # 通用成人尿酸正常范围（μmol/L）：150-420（覆盖男女常规正常区间）
    uric_range = (150, 420)

    while current_date <= end_date:
        # 随机选择测量状态
        status = random.choice(status_options)
        # 生成正常范围的尿酸值（整数，符合检测精度）
        uric_acid = random.randint(uric_range[0], uric_range[1])

        # 根据尿酸值生成summary
        if uric_acid < 150:
            summary = f"尿酸值{uric_acid}μmol/L，略偏低，建议适当增加蛋白质摄入。"
        elif 150 <= uric_acid <= 420:
            summary = f"{status}尿酸值{uric_acid}μmol/L，在正常范围内，建议多饮水、少饮酒。"
        else:
            summary = f"尿酸值{uric_acid}μmol/L，略偏高，建议减少高嘌呤食物（如动物内脏、海鲜）摄入。"

        # 复制模板并替换数据
        tmp = copy.deepcopy(tpl)
        tmp["data_list"][0]["value"] = uric_acid  # 尿酸值
        tmp["data_list"][1]["value"] = status  # 测量状态
        tmp["summary"] = summary
        # 设置创建时间
        tmp["create_time"] = tool_date.日期转随机北京时间(current_date)
        tmp["是否测试数据"] = True
        tmp["类型"] = "尿酸记录"
        tmp["图片识别内容"] = "-"

        output_data.append(tmp)
        current_date += timedelta(days=1)

    return output_data

def generate_height(start_date, end_date, age, gender, initial_height=None):
    """
    生成指定日期范围内的身高记录数据，随年龄和时间动态变化

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期
        age (int): 起始日期时的年龄（岁，需为正数）
        gender (str): 性别，仅支持"男"或"女"

    返回:
        list: 包含身高记录的列表，每个元素为包含身高信息、生长状态和日期时间的字典
    """
    # 参数校验
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")
    if not isinstance(age, int) or age < 0:
        raise ValueError("年龄必须为非负整数")
    if gender not in ["男", "女"]:
        raise ValueError("性别仅支持'男'或'女'")

    output_data = []
    current_date = start_date
    total_days = (end_date - start_date).days + 1  # 总记录天数

    # 1. 定义年龄阶段及身高变化规则（基于通用生长规律）
    # 阶段划分：生长阶段（0-18岁）、成年稳定阶段（18-60岁）、老年衰退阶段（60岁+）
    # 初始身高参考范围（cm）：根据性别和初始年龄设定
    def get_initial_height(age, gender):
        """根据年龄和性别生成合理的初始身高"""
        if age <= 1:
            return random.randint(50, 75)  # 婴儿期
        elif 2 <= age <= 6:
            return random.randint(80, 120)  # 幼儿期
        elif 7 <= age <= 12:
            return random.randint(120, 155) if gender == "男" else random.randint(115, 150)  # 儿童期
        elif 13 <= age <= 18:
            return random.randint(150, 175) if gender == "男" else random.randint(145, 165)  # 青春期
        elif 19 <= age <= 60:
            return random.randint(165, 185) if gender == "男" else random.randint(155, 175)  # 成年期
        else:  # 60岁以上
            return random.randint(160, 180) if gender == "男" else random.randint(150, 170)  # 老年期

    # 2. 计算初始身高及每日变化量
    initial_height = get_initial_height(age, gender) if initial_height is None else initial_height
    current_height = initial_height  # 记录当前身高，随时间动态更新

    # 确定阶段及每日身高变化率（cm/天）
    if age < 18:
        stage = "生长期"
        # 生长阶段：年龄越小增长越快（年增长率随年龄降低）
        if age <= 3:
            yearly_growth = random.uniform(10, 25)  # 婴幼儿期增长最快
        elif 4 <= age <= 12:
            yearly_growth = random.uniform(5, 8)    # 儿童期稳定增长
        else:  # 13-17岁青春期
            yearly_growth = random.uniform(6, 10) if gender == "男" else random.uniform(5, 8)
        daily_change = yearly_growth / 365  # 日均增长量
    elif 18 <= age <= 60:
        stage = "稳定期"
        # 成年期基本稳定，仅微小波动（±0.5cm/年）
        daily_change = random.uniform(-0.5/365, 0.5/365)
    else:  # 60岁以上
        stage = "衰退期"
        # 老年期逐年降低（年降低0.1-0.5cm）
        yearly_decline = random.uniform(0.1, 0.5)
        daily_change = -yearly_decline / 365  # 日均降低量

    # 3. 生成每日记录
    tpl = {
        "data_list": [
            {"name": "身高", "value": round(initial_height, 1), "unit": "cm"},
            {"name": "生长状态", "value": stage, "unit": ""}
        ],
        "summary": f"{stage}，身高变化正常。"
    }

    for day in range(total_days):
        # 更新当前身高（保留1位小数，模拟测量精度）
        current_height += daily_change
        # 老年期身高降低有上限（最多比初始值低5cm）
        if stage == "衰退期" and current_height < (initial_height - 5):
            current_height = initial_height - 5  # 限制最低值

        # 生成summary（根据阶段和变化趋势）
        if stage == "生长期":
            growth_rate = round(daily_change * 365, 1)
            summary = f"{gender}，{age}岁（生长期），身高{round(current_height, 1)}cm，年增长率约{growth_rate}cm，生长发育正常。"
        elif stage == "稳定期":
            summary = f"{gender}，{age}岁（成年稳定期），身高{round(current_height, 1)}cm，身体发育稳定。"
        else:  # 衰退期
            decline_rate = round(-daily_change * 365, 1)
            summary = f"{gender}，{age}岁（老年衰退期），身高{round(current_height, 1)}cm，年降低约{decline_rate}cm，在正常范围内。"

        # 复制模板并更新数据
        tmp = copy.deepcopy(tpl)
        tmp["data_list"][0]["value"] = round(current_height, 1)
        tmp["summary"] = summary
        tmp["create_time"] = tool_date.日期转随机北京时间(current_date)
        tmp["是否测试数据"] = True
        tmp["类型"] = "身高记录"
        tmp["图片识别内容"] = "-"

        output_data.append(tmp)
        current_date += timedelta(days=1)

    return output_data


def generate_weight(start_date, end_date, age, gender, initial_weight=None):
    """
    生成指定日期范围内的体重记录数据，随年龄、性别和时间动态变化

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期
        age (int): 起始日期时的年龄（岁，需为非负整数）
        gender (str): 性别，仅支持"男"或"女"

    返回:
        list: 包含体重记录的列表，每个元素为包含体重信息、状态和日期时间的字典
    """
    # 参数校验
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")
    if not isinstance(age, int) or age < 0:
        raise ValueError("年龄必须为非负整数")
    if gender not in ["男", "女"]:
        raise ValueError("性别仅支持'男'或'女'")

    output_data = []
    current_date = start_date
    total_days = (end_date - start_date).days + 1  # 总记录天数

    # 1. 根据年龄和性别生成初始体重（kg，参考通用生长标准）
    def get_initial_weight(age, gender):
        """基于年龄和性别生成合理的初始体重"""
        if age <= 1:
            return round(random.uniform(3.0, 10.0), 1)  # 婴儿期
        elif 2 <= age <= 6:
            return round(random.uniform(10.0, 25.0), 1)  # 幼儿期
        elif 7 <= age <= 12:
            # 儿童期：男略高于女
            return round(random.uniform(22.0, 40.0), 1) if gender == "男" else round(random.uniform(20.0, 38.0), 1)
        elif 13 <= age <= 18:
            # 青春期：性别差异扩大
            return round(random.uniform(45.0, 70.0), 1) if gender == "男" else round(random.uniform(40.0, 60.0), 1)
        elif 19 <= age <= 60:
            # 成年期：男性平均体重更高
            return round(random.uniform(55.0, 85.0), 1) if gender == "男" else round(random.uniform(45.0, 70.0), 1)
        else:  # 60岁以上
            # 老年期：略低于成年期
            return round(random.uniform(50.0, 80.0), 1) if gender == "男" else round(random.uniform(42.0, 65.0), 1)

    # 2. 确定体重变化阶段及每日变化率（kg/天）
    initial_weight = get_initial_weight(age, gender) if initial_weight is None else initial_weight
    current_weight = initial_weight  # 记录当前体重，随时间动态更新

    if age < 18:
        stage = "生长期"
        # 生长阶段：年龄越小增长越快
        if age <= 3:
            yearly_growth = random.uniform(2.0, 5.0)  # 婴幼儿期增长快
        elif 4 <= age <= 12:
            yearly_growth = random.uniform(1.5, 3.0)  # 儿童期稳定增长
        else:  # 13-17岁青春期
            # 青春期体重增长加速，男性略快
            yearly_growth = random.uniform(3.0, 6.0) if gender == "男" else random.uniform(2.0, 5.0)
        daily_change = yearly_growth / 365  # 日均增长量
    elif 18 <= age <= 60:
        stage = "稳定期"
        # 成年期体重波动（受饮食/运动影响，±2-3kg/年）
        yearly_fluctuation = random.uniform(-3.0, 3.0)
        daily_change = yearly_fluctuation / 365  # 日均波动量
    else:  # 60岁以上
        stage = "老年期"
        # 老年期体重可能轻微下降（年降0-2kg）或稳定
        yearly_change = random.uniform(-2.0, 0.5)
        daily_change = yearly_change / 365  # 日均变化量

    # 3. 生成每日记录
    tpl = {
        "data_list": [
            {"name": "体重", "value": initial_weight, "unit": "kg"},
            {"name": "体重状态", "value": stage, "unit": ""}
        ],
        "summary": f"{stage}，体重变化在正常范围内。"
    }

    for day in range(total_days):
        # 更新当前体重（保留1位小数，模拟测量精度）
        current_weight += daily_change
        
        # 限制极端值（避免体重过低/过高）
        if current_weight < 2.0:  # 最低体重限制（新生儿最低约2kg）
            current_weight = 2.0
        # 成年/老年期体重上限（粗略限制，避免不合理值）
        max_weight = 120.0 if gender == "男" else 100.0
        if current_weight > max_weight:
            current_weight = max_weight

        # 生成summary（结合阶段、性别、年龄和变化趋势）
        if stage == "生长期":
            yearly_rate = round(daily_change * 365, 1)
            summary = f"{gender}，{age}岁（生长期），体重{current_weight}kg，年增长约{yearly_rate}kg，生长发育正常。"
        elif stage == "稳定期":
            yearly_fluct = round(daily_change * 365, 1)
            trend = "增长" if yearly_fluct > 0 else "下降" if yearly_fluct < 0 else "稳定"
            summary = f"{gender}，{age}岁（成年稳定期），体重{current_weight}kg，年{trend}{abs(yearly_fluct)}kg，属正常波动。"
        else:  # 老年期
            yearly_trend = round(daily_change * 365, 1)
            summary = f"{gender}，{age}岁（老年期），体重{current_weight}kg，年变化{yearly_trend}kg，身体状态稳定。"

        # 复制模板并更新数据
        tmp = copy.deepcopy(tpl)
        tmp["data_list"][0]["value"] = round(current_weight, 1)
        tmp["summary"] = summary
        tmp["create_time"] = tool_date.日期转随机北京时间(current_date)
        tmp["是否测试数据"] = True
        tmp["类型"] = "体重记录"
        tmp["图片识别内容"] = "-"

        output_data.append(tmp)
        current_date += timedelta(days=1)

    return output_data

def generate_sleep_report(start_date, end_date):
    """
    生成指定日期范围内的睡眠报告数据

    参数:
        start_date (datetime.date): 起始日期
        end_date (datetime.date): 结束日期

    返回:
        list: 包含睡眠报告的列表，每个元素为包含睡眠时长、质量及日期时间的字典
    """
    if start_date > end_date:
        raise ValueError("起始日期必须早于或等于结束日期")

    output_data = []
    current_date = start_date

    # 睡眠报告模板
    tpl = {
        "data_list": [
            {"name": "实际睡眠时长", "value": "7.5", "unit": "小时"},
            {"name": "睡眠质量", "value": "良好", "unit": ""}
        ],
        "summary": "睡眠时长充足，质量良好，建议保持规律作息。"
    }

    # 睡眠质量选项及对应时长范围（小时）
    # 参考成人正常睡眠时长：7-9小时，偶尔6-10小时属正常波动
    quality_options = ["优质", "良好", "一般", "较差"]
    # 不同质量对应的时长范围（左闭右开）及概率权重
    quality_params = {
        "优质": {"range": (7.5, 9.0), "weight": 0.3},  # 时长充足且稳定
        "良好": {"range": (7.0, 7.5), "weight": 0.3},   # 时长达标但略短
        "一般": {"range": (6.0, 7.0), "weight": 0.2},   # 时长略不足
        "较差": {"range": (5.0, 6.0), "weight": 0.2}    # 时长不足
    }

    while current_date <= end_date:
        # 1. 随机选择睡眠质量（按权重分布）
        quality = random.choices(
            quality_options,
            weights=[params["weight"] for params in quality_params.values()],
            k=1
        )[0]
        
        # 2. 根据睡眠质量生成对应范围的实际睡眠时长（保留1位小数）
        min_hour, max_hour = quality_params[quality]["range"]
        sleep_hour = round(random.uniform(min_hour, max_hour), 1)
        
        # 3. 生成summary（结合时长和质量）
        if quality == "优质":
            summary = f"实际睡眠时长{sleep_hour}小时，睡眠质量优质，深睡比例高，精力恢复良好。"
        elif quality == "良好":
            summary = f"实际睡眠时长{sleep_hour}小时，睡眠质量良好，基本满足身体恢复需求。"
        elif quality == "一般":
            summary = f"实际睡眠时长{sleep_hour}小时，睡眠质量一般，可能存在轻微夜间醒来，建议减少睡前使用电子设备。"
        else:  # 较差
            summary = f"实际睡眠时长{sleep_hour}小时，睡眠质量较差，时长不足，建议调整作息，保证充足睡眠。"

        # 4. 复制模板并更新数据
        tmp = copy.deepcopy(tpl)
        tmp["data_list"][0]["value"] = f"{sleep_hour}"  # 睡眠时长（字符串类型，保留1位小数）
        tmp["data_list"][1]["value"] = quality          # 睡眠质量
        tmp["summary"] = summary
        # 设置创建时间（对应睡眠结束时间，模拟早上记录）
        tmp["create_time"] = tool_date.日期转随机北京时间(current_date)
        tmp["是否测试数据"] = True
        tmp["类型"] = "睡眠报告"
        tmp["图片识别内容"] = "-"

        output_data.append(tmp)
        current_date += timedelta(days=1)

    return output_data



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
