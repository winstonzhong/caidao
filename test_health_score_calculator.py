import unittest
from health_score_calculator import calculate_health_score, WEIGHTS, BMI_SCORES, DISEASE_PENALTIES

class TestHealthScoreCalculator(unittest.TestCase):

    def test_full_data_high_score(self):
        score, reason = calculate_health_score(
            age=30, gender='男', height=175, weight=70,
            diseases=[], avg_steps=8000, step_rate=90,
            meal_rate=85, health_rate=80, report_count=3
        )
        self.assertEqual(score, 86.5)
        self.assertIn("BMI正常(22.9)", reason)
        self.assertIn("年龄中等", reason)
        self.assertIn("无基础疾病", reason)
        self.assertIn("步数良好", reason)

    def test_full_data_medium_score(self):
        score, reason = calculate_health_score(
            age=65, gender='女', height=160, weight=62,
            diseases=['高血压'], avg_steps=6000, step_rate=75,
            meal_rate=70, health_rate=65, report_count=1
        )
        self.assertEqual(score, 67.7)
        self.assertIn("BMI正常(24.2)", reason)
        self.assertIn("年龄较大有加分", reason)
        self.assertIn("患高血压有扣分", reason)
        self.assertIn("步数中等", reason)

    def test_full_data_low_score(self):
        score, reason = calculate_health_score(
            age=25, gender='男', height=180, weight=95,
            diseases=['糖尿病'], avg_steps=4000, step_rate=60,
            meal_rate=55, health_rate=50, report_count=0
        )
        self.assertEqual(score, 44.5)
        self.assertIn("BMI肥胖(29.3)", reason)
        self.assertIn("年龄较小有扣分", reason)
        self.assertIn("患糖尿病有扣分", reason)
        self.assertIn("步数较少", reason)

    def test_missing_data(self):
        score, reason = calculate_health_score()
        self.assertEqual(score, 0)
        self.assertIn("年龄数据缺失", reason)
        self.assertIn("性别数据缺失", reason)
        self.assertIn("身高数据缺失", reason)
        self.assertIn("BMI无法计算", reason)

    def test_bmi_calculation(self):
        # 偏瘦
        score, _ = calculate_health_score(height=170, weight=50)
        self.assertLess(score, 70)
        
        # 正常
        score, _ = calculate_health_score(height=170, weight=65)
        self.assertEqual(score, 70 + (100 - 70) * (WEIGHTS['bmi'] / 100))
        
        # 过重
        score, _ = calculate_health_score(height=170, weight=75)
        self.assertGreater(score, 70)
        self.assertLess(score, 80)
        
        # 肥胖
        score, _ = calculate_health_score(height=170, weight=90)
        self.assertLess(score, 70)

    def test_age_adjustment_high_base(self):
        # 基础分高时，年龄越大加分越多
        score1, _ = calculate_health_score(age=30, height=170, weight=65)
        score2, _ = calculate_health_score(age=60, height=170, weight=65)
        self.assertGreater(score2, score1)

    def test_age_adjustment_low_base(self):
        # 基础分低时，年龄越小扣分越多
        score1, _ = calculate_health_score(age=30, height=170, weight=90, diseases=['高血压'])
        score2, _ = calculate_health_score(age=20, height=170, weight=90, diseases=['高血压'])
        self.assertLess(score2, score1)

    def test_disease_penalties(self):
        # 无疾病
        score1, _ = calculate_health_score(diseases=[])
        # 有高血压
        score2, _ = calculate_health_score(diseases=['高血压'])
        # 有糖尿病
        score3, _ = calculate_health_score(diseases=['糖尿病'])
        # 多种疾病
        score4, _ = calculate_health_score(diseases=['高血压', '糖尿病'])
        
        self.assertGreater(score1, score2)
        self.assertGreater(score2, score3)
        self.assertGreater(score3, score4)

    def test_step_score(self):
        # 步数越多，分数越高
        score1, _ = calculate_health_score(avg_steps=3000)
        score2, _ = calculate_health_score(avg_steps=6000)
        score3, _ = calculate_health_score(avg_steps=10000)
        
        self.assertLess(score1, score2)
        self.assertLess(score2, score3)

    def test_report_score(self):
        # 报告越多，分数越高
        score1, _ = calculate_health_score(report_count=0)
        score2, _ = calculate_health_score(report_count=50)
        score3, _ = calculate_health_score(report_count=100)
        
        self.assertLess(score1, score2)
        self.assertLess(score2, score3)

if __name__ == '__main__':
    unittest.main()    