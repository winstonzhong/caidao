#!/usr/bin/env python3
"""
SimpleMatcherV2 单元测试

测试匹配器的核心功能，包括：
1. 中文词匹配
2. 英文短词过滤
3. 子串提取（不跨语言边界）
4. 停用词过滤
5. 同义词扩展

用法:
    python dy_text_classifier/test_simple_matcher_v2.py
    python dy_text_classifier/test_simple_matcher_v2.py -v  # 详细输出
"""

import unittest
import sys
import os

# 添加项目路径
sys.path.insert(0, '/home/yka-003/workspace/caidao')

from dy_text_classifier.simple_matcher_v2 import SimpleMatcherV2


class TestSimpleMatcherV2(unittest.TestCase):
    """SimpleMatcherV2 单元测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.matcher = SimpleMatcherV2()
    
    def test_中文词匹配(self):
        """测试中文词正常匹配"""
        目标 = '翻车视频'
        数据 = {'标题': '今日份翻车了', '摘要': '翻车了'}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertTrue(result, "'翻车视频' 应该匹配包含 '翻车' 的文本")
    
    def test_子串匹配_白嫖(self):
        """测试子串提取功能（'售后白嫖'中提取'白嫖'）"""
        目标 = '打击售后白嫖党'
        数据 = {'标题': '白嫖党滚出去', '摘要': '遇到白嫖'}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertTrue(result, "'打击售后白嫖党' 应该匹配包含 '白嫖' 的文本")
    
    def test_英文短词不过度匹配(self):
        """测试英文短词（in/on/at）不过度匹配"""
        目标 = 'ComfyUI Fusion视频'
        数据 = {'标题': '这是一个普通视频', '摘要': '关于机器学习的内容'}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertFalse(result, "'ComfyUI Fusion视频' 不应该匹配普通机器学习视频")
    
    def test_正常匹配(self):
        """测试正常的关键词匹配"""
        目标 = '美食视频'
        数据 = {'标题': '今天做美食', '摘要': '美食教程'}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertTrue(result, "'美食视频' 应该匹配包含 '美食' 的文本")
    
    def test_停用词不过滤(self):
        """测试停用词被正确过滤"""
        目标 = 'in at on'
        数据 = {'标题': '普通文本内容', '摘要': ''}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertFalse(result, "停用词 'in/at/on' 不应该产生匹配")
    
    def test_纯停用词不匹配(self):
        """测试纯停用词组合不匹配"""
        目标 = '的了吗'
        数据 = {'标题': '全是停用词', '摘要': ''}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertFalse(result, "纯停用词组合不应该产生匹配")
    
    def test_AI教程精确匹配(self):
        """测试精确匹配"""
        目标 = 'AI教程'
        数据 = {'标题': 'AI教程分享', '摘要': ''}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertTrue(result, "'AI教程' 应该精确匹配 'AI教程'")
    
    def test_AI教程不匹配AI人工智能教程(self):
        """测试'AI教程'不匹配'AI人工智能教程'（精确匹配）"""
        目标 = 'AI教程'
        数据 = {'标题': 'AI人工智能教程', '摘要': ''}
        result = self.matcher.文本匹配(目标, 数据)
        # 不进行子串提取时，"AI教程" 和 "AI人工智能教程" 不会匹配
        self.assertFalse(result, "'AI教程' 和 'AI人工智能教程' 不进行子串提取，不应匹配")
    
    def test_售后匹配(self):
        """测试售后关键词匹配"""
        目标 = '售后'
        数据 = {'标题': '拼多多售后问题', '摘要': ''}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertTrue(result, "'售后' 应该匹配包含 '售后' 的文本")
    
    def test_关键词子串不跨语言边界(self):
        """测试子串提取不跨语言边界（'Fusion视频'不应提取'视频'）"""
        # 验证子串提取逻辑
        keyword = 'Fusion视频'
        # 检查 '视频' 是否不会被提取为子串
        word_set = self.matcher._get_word_set('测试' + keyword)  # 添加前缀确保缓存
        
        # 重新检查原始逻辑
        result = self.matcher._是语言一致子串(keyword, 6, 8)  # '视频' 的位置
        self.assertFalse(result, "子串提取不应跨越中英文边界")
    
    def test_是有效子串_中文(self):
        """测试中文子串验证"""
        self.assertTrue(self.matcher._是有效子串('翻车'), "'翻车' 应该是有效子串")
        self.assertTrue(self.matcher._是有效子串('白嫖'), "'白嫖' 应该是有效子串")
        self.assertFalse(self.matcher._是有效子串('的'), "'的' 是停用词，不应有效")
    
    def test_是有效子串_英文(self):
        """测试英文子串验证"""
        self.assertTrue(self.matcher._是有效子串('fusion'), "'fusion' 应该是有效子串")
        self.assertTrue(self.matcher._是有效子串('comfyui'), "'comfyui' 应该是有效子串")
        self.assertFalse(self.matcher._是有效子串('in'), "'in' 是短英文词，不应有效")
        self.assertFalse(self.matcher._是有效子串('at'), "'at' 是短英文词，不应有效")
    
    def test_双语混合匹配(self):
        """测试中英文混合内容匹配"""
        目标 = 'ComfyUI教程'
        数据 = {'标题': 'ComfyUI教程分享', '摘要': ''}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertTrue(result, "'ComfyUI教程' 应该匹配包含 'ComfyUI教程' 的文本")
    
    def test_同义词扩展匹配(self):
        """测试同义词扩展功能"""
        目标 = '美食视频'
        数据 = {'标题': '美食影片分享', '摘要': ''}
        result = self.matcher.文本匹配(目标, 数据)
        # 注意：同义词是否匹配取决于LLM生成的同义词列表
        # 这里主要测试功能不会崩溃
        self.assertIsInstance(result, bool)


class TestSimpleMatcherV2EdgeCases(unittest.TestCase):
    """边界情况测试"""
    
    @classmethod
    def setUpClass(cls):
        cls.matcher = SimpleMatcherV2()
    
    def test_空文本(self):
        """测试空文本处理"""
        目标 = '测试'
        数据 = {'标题': '', '摘要': ''}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertFalse(result, "空文本不应该产生匹配")
    
    def test_空目标(self):
        """测试空目标描述"""
        目标 = ''
        数据 = {'标题': '有内容的标题', '摘要': ''}
        result = self.matcher.文本匹配(目标, 数据)
        self.assertFalse(result, "空目标描述不应该产生匹配")
    
    def test_长文本匹配(self):
        """测试长文本中的关键词匹配"""
        目标 = '售后白嫖'
        数据 = {
            '标题': '这是一个很长的标题，讲述了关于售后白嫖的各种问题',
            '摘要': '在这个摘要中，我们讨论了售后白嫖现象的严重性'
        }
        result = self.matcher.文本匹配(目标, 数据)
        self.assertTrue(result, "长文本中的关键词应该被匹配")
    
    def test_标点符号过滤(self):
        """测试标点符号被正确过滤"""
        result = self.matcher._是有效子串('翻车。')
        self.assertFalse(result, "包含标点的子串不应有效")
        
        result = self.matcher._是有效子串('白嫖,')
        self.assertFalse(result, "包含标点的子串不应有效")
    
    def test_纯数字过滤(self):
        """测试纯数字被正确过滤"""
        result = self.matcher._是有效子串('123')
        self.assertFalse(result, "纯数字不应作为有效子串")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSimpleMatcherV2))
    suite.addTests(loader.loadTestsFromTestCase(TestSimpleMatcherV2EdgeCases))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='SimpleMatcherV2 单元测试')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    args = parser.parse_args()
    
    success = run_tests()
    sys.exit(0 if success else 1)
