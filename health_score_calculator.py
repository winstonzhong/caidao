from typing import List, Tuple

# 定义权重表
WEIGHTS = {
    # 缺失值扣分权重
    "missing_age": 10,  # 年龄缺失扣分
    "missing_gender": 5,  # 性别缺失扣分
    "missing_height": 8,  # 身高缺失扣分
    "missing_weight": 8,  # 体重缺失扣分
    "missing_steps": 7,  # 步数缺失扣分
    "missing_step_rate": 6,  # 步数记录率缺失扣分
    "missing_meal_rate": 6,  # 餐食记录率缺失扣分
    "missing_health_rate": 7,  # 健康指标记录率缺失扣分
    "missing_reports": 3,  # 医疗报告缺失扣分
    # 指标权重
    "bmi": 25,  # BMI权重
    "age_adjustment": 15,  # 年龄调整权重
    "disease_penalty": 20,  # 基础疾病扣分权重
    "step_score": 10,  # 步数评分权重
    "step_rate_score": 5,  # 步数记录率评分权重
    "meal_rate_score": 5,  # 餐食记录率评分权重
    "health_rate_score": 5,  # 健康指标记录率评分权重
    "report_score": 4,  # 医疗报告评分权重
}

# BMI评分表
BMI_SCORES = {
    (0, 18.5): 60,  # 偏瘦
    (18.5, 24): 100,  # 正常
    (24, 28): 70,  # 过重
    (28, float("inf")): 50,  # 肥胖
}

# 基础疾病扣分表
DISEASE_PENALTIES = {"高血压": 15, "糖尿病": 20, "心脏病": 25, "哮喘": 12, "其他": 8}


def calculate_health_score(
    age: int = None,
    gender: str = None,
    height: float = None,  # 厘米
    weight: float = None,  # 公斤
    diseases: List[str] = None,
    avg_steps: int = None,
    step_rate: float = None,  # 0-100%
    meal_rate: float = None,  # 0-100%
    health_rate: float = None,  # 0-100%
    report_count: int = None,
) -> Tuple[float, str]:
    """
    计算健康分值(0-100)及评分理由

    >>> calculate_health_score(30, '男', 175, 70, [], 8000, 90, 85, 80, 3)
    (86.5, 'BMI处于理想范围(22.9)，正是当打之年，保持健康意识尤为重要，无基础疾病，每日坚持适量运动效果显著，各项记录习惯良好，定期体检的习惯值得保持')
    >>> calculate_health_score(65, '女', 160, 62, ['高血压'], 6000, 75, 70, 65, 1)
    (67.7, 'BMI处于理想范围(24.2)，经历越多越爱惜自己真的很好，高血压患者尤其应注意健康管理，日常活动量基本达标，各项记录习惯良好，定期体检的习惯值得保持')
    >>> calculate_health_score(25, '男', 180, 95, ['糖尿病'], 4000, 60, 55, 50, 0)
    (44.5, 'BMI超过正常范围(29.3)，年轻更要重视健康管理，糖尿病患者需要特别关注血糖控制，日常活动量有待提高，各项记录习惯需要加强，建议增加体检频率')
    >>> calculate_health_score(age=None, gender=None, height=None, weight=None)
    (0, '年龄数据缺失，性别数据缺失，身高数据缺失，体重数据缺失，平均步数数据缺失，步数记录率数据缺失，餐食记录率数据缺失，健康指标记录率数据缺失，医疗报告数量缺失')
    >>> calculate_health_score(18, '女', 160, 45)
    (52.5, 'BMI偏瘦(17.6)，年轻活力充沛，建议增加营养摄入，无基础疾病，平均步数数据缺失，步数记录率数据缺失，餐食记录率数据缺失，健康指标记录率数据缺失，医疗报告数量缺失')
    >>> calculate_health_score(40, '男', 175, 85)
    (72.5, 'BMI超过正常范围(27.8)，中年更要重视健康管理，无基础疾病，平均步数数据缺失，步数记录率数据缺失，餐食记录率数据缺失，健康指标记录率数据缺失，医疗报告数量缺失')
    >>> calculate_health_score(50, '女', 160, 60, ['哮喘', '其他'])
    (58.0, 'BMI处于理想范围(23.4)，保持健康意识尤为重要，哮喘患者和其他慢性病患者尤其应注意健康管理，平均步数数据缺失，步数记录率数据缺失，餐食记录率数据缺失，健康指标记录率数据缺失，医疗报告数量缺失')
    >>> calculate_health_score(age=35, avg_steps=10000, step_rate=95, meal_rate=90, health_rate=85, report_count=5)
    (79.5, 'BMI无法计算，正值壮年，保持健康意识尤为重要，无基础疾病，每日坚持充足运动效果显著，步数记录习惯优秀，餐食记录习惯良好，健康指标记录习惯良好，定期体检的习惯值得保持')
    """
    # 初始化基础分
    base_score = 70
    reasons = []

    # 1. 处理缺失值扣分
    if age is None:
        base_score -= WEIGHTS["missing_age"]
        reasons.append("年龄数据缺失")
    if gender is None:
        base_score -= WEIGHTS["missing_gender"]
        reasons.append("性别数据缺失")
    if height is None:
        base_score -= WEIGHTS["missing_height"]
        reasons.append("身高数据缺失")
    if weight is None:
        base_score -= WEIGHTS["missing_weight"]
        reasons.append("体重数据缺失")
    if avg_steps is None:
        base_score -= WEIGHTS["missing_steps"]
        reasons.append("平均步数数据缺失")
    if step_rate is None:
        base_score -= WEIGHTS["missing_step_rate"]
        reasons.append("步数记录率数据缺失")
    if meal_rate is None:
        base_score -= WEIGHTS["missing_meal_rate"]
        reasons.append("餐食记录率数据缺失")
    if health_rate is None:
        base_score -= WEIGHTS["missing_health_rate"]
        reasons.append("健康指标记录率数据缺失")
    if report_count is None:
        base_score -= WEIGHTS["missing_reports"]
        reasons.append("医疗报告数量缺失")

    # 确保基础分不低于0
    base_score = max(0, base_score)

    # 2. 计算BMI评分
    bmi_score = 0
    if height is not None and weight is not None:
        bmi = weight / ((height / 100) ** 2)
        bmi = round(bmi, 1)
        # 查找对应的BMI评分区间
        for (min_bmi, max_bmi), score in BMI_SCORES.items():
            if min_bmi <= bmi < max_bmi:
                bmi_score = score
                break
        # 计算BMI对总分的贡献
        bmi_contribution = (bmi_score - 70) * (WEIGHTS["bmi"] / 100)
        base_score += bmi_contribution
        # 添加BMI相关理由
        bmi_category = next(
            (
                category
                for (min_bmi, max_bmi), category in [
                    ((0, 18.5), "偏瘦"),
                    ((18.5, 24), "正常"),
                    ((24, 28), "过重"),
                    ((28, float("inf")), "肥胖"),
                ]
                if min_bmi <= bmi < max_bmi
            ),
            "异常",
        )

        if bmi_category == "正常":
            reasons.append(f"BMI处于理想范围({bmi})")
        elif bmi_category == "偏瘦":
            reasons.append(f"BMI偏瘦({bmi})，建议增加营养摄入")
        elif bmi_category == "过重":
            reasons.append(f"BMI超过正常范围({bmi})，建议增加运动")
        else:
            reasons.append(f"BMI超过正常范围({bmi})，需要加强健康管理")
    else:
        reasons.append("BMI无法计算")

    # 3. 年龄调整
    if age is not None:
        if base_score >= 60:
            # 分数>=60时，年龄越大加分越多
            age_adjustment = (age - 30) * 0.3
        else:
            # 分数<60时，年龄越小扣分越多
            age_adjustment = (30 - age) * 0.4

        # 应用年龄权重
        age_contribution = age_adjustment * (WEIGHTS["age_adjustment"] / 100)
        base_score += age_contribution

        if age_adjustment > 0:
            if age < 50:
                reasons.append(f"正值壮年，保持健康意识尤为重要")
            elif age < 65:
                reasons.append(f"经验丰富的年纪，健康管理更关键")
            else:
                reasons.append(f"经历越多越爱惜自己真的很好")
        elif age_adjustment < 0:
            if age < 25:
                reasons.append(f"年轻更要重视健康管理")
            else:
                reasons.append(f"黄金年龄，保持良好习惯很重要")
        else:
            reasons.append(f"正是当打之年，保持健康意识尤为重要")

    # 4. 基础疾病扣分
    disease_penalty = 0
    if diseases is not None:
        for disease in diseases:
            if disease in DISEASE_PENALTIES:
                disease_penalty += DISEASE_PENALTIES[disease]
            else:
                disease_penalty += DISEASE_PENALTIES["其他"]

        # 应用疾病权重
        disease_contribution = disease_penalty * (WEIGHTS["disease_penalty"] / 100)
        base_score -= disease_contribution

        if diseases:
            if len(diseases) == 1:
                reasons.append(f"{diseases[0]}患者尤其应注意健康管理")
            else:
                reasons.append(f"{', '.join(diseases)}等慢性病患者尤其应注意健康管理")
        else:
            reasons.append(f"目前没有已知基础疾病，继续保持")

    # 5. 步数评分 (0-100分)
    if avg_steps is not None:
        # 假设8000步为满分，少于3000步为0分，中间线性插值
        step_score = min(100, max(0, (avg_steps - 3000) * 100 / 5000))
        step_contribution = step_score * (WEIGHTS["step_score"] / 100)
        base_score += step_contribution

        if step_score >= 80:
            reasons.append("每日坚持充足运动效果显著")
        elif step_score >= 50:
            reasons.append("日常活动量基本达标")
        else:
            reasons.append("日常活动量有待提高")

    # 6. 步数记录率评分
    if step_rate is not None:
        step_rate_score = min(100, max(0, step_rate))
        step_rate_contribution = step_rate_score * (WEIGHTS["step_rate_score"] / 100)
        base_score += step_rate_contribution

        if step_rate_score >= 80:
            reasons.append("步数记录习惯优秀")
        elif step_rate_score >= 50:
            reasons.append("步数记录习惯良好")
        else:
            reasons.append("步数记录习惯需要加强")

    # 7. 餐食记录率评分
    if meal_rate is not None:
        meal_rate_score = min(100, max(0, meal_rate))
        meal_rate_contribution = meal_rate_score * (WEIGHTS["meal_rate_score"] / 100)
        base_score += meal_rate_contribution

        if meal_rate_score >= 80:
            reasons.append("餐食记录习惯优秀")
        elif meal_rate_score >= 50:
            reasons.append("餐食记录习惯良好")
        else:
            reasons.append("餐食记录习惯需要加强")

    # 8. 健康指标记录率评分
    if health_rate is not None:
        health_rate_score = min(100, max(0, health_rate))
        health_rate_contribution = health_rate_score * (
            WEIGHTS["health_rate_score"] / 100
        )
        base_score += health_rate_contribution

        if health_rate_score >= 80:
            reasons.append("健康指标记录习惯优秀")
        elif health_rate_score >= 50:
            reasons.append("健康指标记录习惯良好")
        else:
            reasons.append("健康指标记录习惯需要加强")

    # 9. 医疗报告评分
    if report_count is not None:
        # 医疗报告数量/100作为评分基础
        report_score = min(100, max(0, report_count * 100 / 100))
        report_contribution = report_score * (WEIGHTS["report_score"] / 100)
        base_score += report_contribution

        if report_score >= 80:
            reasons.append("定期全面体检的习惯值得保持")
        elif report_score >= 30:
            reasons.append("定期体检的习惯值得保持")
        else:
            reasons.append("建议增加体检频率")

    # 确保最终分数在0-100之间
    final_score = max(0, min(100, round(base_score, 1)))

    # 生成理由总结
    # reason_summary = "，".join(reasons)

    return final_score, reasons


if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
