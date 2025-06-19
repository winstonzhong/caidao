def calculate_step_length(
    age: int, gender: str, height: float, weight: float, walk_type: str
) -> float:
    """
    计算不同行走类型的平均步长(米)

    参数:
    age (int): 年龄(岁)
    gender (str): 性别("male"或"female")
    height (float): 身高(厘米)
    weight (float): 体重(公斤)
    walk_type (str): 行走类型("slow", "medium", "fast", "uphill")

    返回:
    float: 平均步长(米)

    公式说明:
    - 基础步长基于身高和性别的经验关系
    - 不同行走类型会对基础步长进行调整
    - 年龄和体重的影响已包含在基础步长公式中

    单元测试:

    # 测试年龄变化的影响（其他参数保持不变）
    >>> calculate_step_length(20, "male", 175, 70, "medium")
    0.721
    >>> calculate_step_length(40, "male", 175, 70, "medium")
    0.721
    >>> calculate_step_length(60, "male", 175, 70, "medium")
    0.721
    >>> calculate_step_length(61, "male", 175, 70, "medium")
    0.717
    >>> calculate_step_length(80, "male", 175, 70, "medium")
    0.649

    # 测试性别变化的影响（其他参数保持不变）
    >>> calculate_step_length(30, "male", 175, 70, "medium")
    0.721
    >>> calculate_step_length(30, "female", 175, 70, "medium")
    0.685

    # 测试身高变化的影响（其他参数保持不变）
    >>> calculate_step_length(30, "male", 160, 70, "medium")
    0.652
    >>> calculate_step_length(30, "male", 170, 70, "medium")
    0.698
    >>> calculate_step_length(30, "male", 180, 70, "medium")
    0.743
    >>> calculate_step_length(30, "male", 190, 70, "medium")
    0.785
    >>> calculate_step_length(30, "male", 200, 70, "medium")
    0.826

    # 测试体重变化的影响（其他参数保持不变）
    >>> calculate_step_length(30, "male", 175, 50, "medium")
    0.723
    >>> calculate_step_length(30, "male", 175, 60, "medium")
    0.723
    >>> calculate_step_length(30, "male", 175, 70, "medium")
    0.721
    >>> calculate_step_length(30, "male", 175, 80, "medium")
    0.714
    >>> calculate_step_length(30, "male", 175, 90, "medium")
    0.706

    # 测试行走类型变化的影响（其他参数保持不变）
    >>> calculate_step_length(30, "male", 175, 70, "slow")
    0.649
    >>> calculate_step_length(30, "male", 175, 70, "medium")
    0.721
    >>> calculate_step_length(30, "male", 175, 70, "fast")
    0.793
    >>> calculate_step_length(30, "male", 175, 70, "uphill")
    0.613
    >>> calculate_step_length(30, "male", 175, 70, "SLOW")
    0.649
    """
    # 基础步长计算(米) - 基于身高的经验公式
    if gender.lower() == "male":
        base_step_length = 0.413 * height / 100
    elif gender.lower() == "female":
        base_step_length = 0.413 * height / 100 * 0.95  # 女性平均步长比男性短约5%
    else:
        raise ValueError("性别参数必须为'male'或'female'")

    # 体重校正 - 基于身高的标准体重计算
    # 身高(米)的平方 × 22（标准体重系数）
    height_meters = height / 100
    standard_weight = height_meters**2 * 22

    # 体重对步长的影响因子
    # 体重超过标准体重时，步长逐渐缩短
    weight_factor = 1 - max(0, weight - standard_weight) * 0.001
    # weight_factor = 1

    # 行走类型对步长的调整系数
    walk_type_factors = {
        "slow": 0.9,  # 慢速行走步长缩短
        "medium": 1.0,  # 中速行走使用基础步长
        "fast": 1.1,  # 快速行走步长增加
        "uphill": 0.85,  # 爬坡时步长通常更短
    }

    if walk_type.lower() not in walk_type_factors:
        raise ValueError("行走类型必须为'slow', 'medium', 'fast'或'uphill'")

    # 计算最终步长
    final_step_length = (
        base_step_length * weight_factor * walk_type_factors[walk_type.lower()]
    )

    # 年龄校正（针对老年人步长缩短）
    if age > 60:
        age_factor = 1 - (age - 60) * 0.005  # 60岁后每增加1岁步长减少0.5%
        final_step_length = max(
            0.4, final_step_length * age_factor
        )  # 确保步长不低于0.4米

    return round(final_step_length, 3)  # 保留3位小数


def calculate_calories(
    age: int, gender: str, height: float, weight: float, steps: int, walk_type: str
) -> float:
    """
    计算不同行走类型的热量消耗

    参数:
    age (int): 年龄(岁)
    gender (str): 性别("male"或"female")
    height (float): 身高(厘米)
    weight (float): 体重(公斤)
    steps (int): 行走步数
    walk_type (str): 行走类型("slow", "medium", "fast", "uphill")

    返回:
    float: 估计的热量消耗(千卡)

    示例:
    >>> calculate_calories(30, "male", 175, 70, 5000, "medium")
    2108.73
    >>> calculate_calories(30, "female", 175, 70, 5000, "medium")
    1909.35
    >>> calculate_calories(30, "male", 175, 70, 5000, "fast")
    2155.31
    >>> calculate_calories(30, "male", 175, 70, 5000, "uphill")
    2394.89
    >>> calculate_calories(25, "female", 160, 60, 6000, "medium")
    1697.05
    """

    # 计算基础代谢率(BMR) - 使用Mifflin-St Jeor公式
    if gender.lower() == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    elif gender.lower() == "female":
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        raise ValueError("性别参数必须为'male'或'female'")

    # 计算平均步长(米)
    step_length = calculate_step_length(age, gender, height, weight, walk_type)

    # 计算总距离(公里)
    distance = steps * step_length / 1000

    # 不同行走类型的MET值
    met_values = {"slow": 2.5, "medium": 3.5, "fast": 5.0, "uphill": 7.0}

    if walk_type.lower() not in met_values:
        raise ValueError("行走类型必须为'slow', 'medium', 'fast'或'uphill'")

    # 计算运动时间(小时)
    speeds = {"slow": 2.5, "medium": 4.5, "fast": 6.0, "uphill": 3.0}
    exercise_time = distance / speeds[walk_type.lower()]

    # 计算运动消耗的热量
    exercise_calories = met_values[walk_type.lower()] * weight * exercise_time

    # 计算久坐时间（一天24小时 - 运动时间）
    sedentary_time = 24 - exercise_time

    # 使用BMR计算久坐活动消耗的热量
    # 久坐时的活动系数通常为1.2（轻度活动）
    sedentary_calories = bmr * (sedentary_time / 24) * 1.2

    # 全天总热量消耗
    total_calories = exercise_calories + sedentary_calories

    # print(exercise_calories, sedentary_calories)
    return round(total_calories, 2)


# 运行doctest单元测试
if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))

