#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度合并字典函数的单元测试
"""

import unittest
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tool_xpath import 深度合并字典


class Test深度合并字典(unittest.TestCase):
    """测试深度合并字典函数"""
    
    def test_空基础字典(self):
        """测试：基础字典为空时，应返回覆盖字典的拷贝"""
        base = {}
        override = {'a': 1, 'b': 2}
        result = 深度合并字典(base, override)
        
        self.assertEqual(result, override)
        self.assertIsNot(result, override)  # 应该是拷贝，不是原对象
    
    def test_空覆盖字典(self):
        """测试：覆盖字典为空时，应返回基础字典的拷贝"""
        base = {'a': 1, 'b': 2}
        override = {}
        result = 深度合并字典(base, override)
        
        self.assertEqual(result, base)
        self.assertIsNot(result, base)  # 应该是拷贝，不是原对象
    
    def test_两个字典都为空(self):
        """测试：两个字典都为空时，应返回空字典"""
        result = 深度合并字典({}, {})
        self.assertEqual(result, {})
    
    def test_基础字典为None(self):
        """测试：基础字典为None时，应返回覆盖字典"""
        override = {'a': 1}
        result = 深度合并字典(None, override)
        self.assertEqual(result, override)
    
    def test_覆盖字典为None(self):
        """测试：覆盖字典为None时，应返回基础字典的拷贝"""
        base = {'a': 1}
        result = 深度合并字典(base, None)
        self.assertEqual(result, base)
    
    def test_简单键覆盖(self):
        """测试：简单键的覆盖"""
        base = {'a': 1, 'b': 2}
        override = {'b': 99, 'c': 3}
        result = 深度合并字典(base, override)
        
        expected = {'a': 1, 'b': 99, 'c': 3}
        self.assertEqual(result, expected)
    
    def test_嵌套字典合并(self):
        """测试：嵌套字典的递归合并"""
        base = {
            'paras': {
                '目标视频描述': '3D建模',
                'SYSTEM_PROMPTS': {
                    'cls': {'model': 'gpt-3.5'}
                }
            }
        }
        override = {
            'paras': {
                '目标视频描述': '拼多多维权',
                'SYSTEM_PROMPTS': {
                    'cls': {'temperature': 0.7}
                }
            }
        }
        result = 深度合并字典(base, override)
        
        # 验证嵌套合并结果
        self.assertEqual(result['paras']['目标视频描述'], '拼多多维权')
        self.assertEqual(result['paras']['SYSTEM_PROMPTS']['cls']['model'], 'gpt-3.5')  # 保留
        self.assertEqual(result['paras']['SYSTEM_PROMPTS']['cls']['temperature'], 0.7)  # 新增
    
    def test_嵌套字典完全覆盖(self):
        """测试：嵌套字典被非字典值覆盖"""
        base = {'a': {'b': 1}}
        override = {'a': '字符串值'}
        result = 深度合并字典(base, override)
        
        self.assertEqual(result['a'], '字符串值')
    
    def test_不修改原始字典(self):
        """测试：合并过程不应修改原始字典"""
        base = {'a': 1, 'b': {'c': 2}}
        override = {'b': {'d': 3}}
        
        original_base = base.copy()
        original_override = override.copy()
        
        result = 深度合并字典(base, override)
        
        # 验证原始字典未被修改
        self.assertEqual(base, original_base)
        self.assertEqual(override, original_override)
        
        # 修改结果不应影响原始字典
        result['b']['d'] = 999
        self.assertEqual(base['b'].get('d'), None)  # 原字典不受影响
    
    def test_多层嵌套合并(self):
        """测试：多层嵌套字典的合并"""
        base = {
            'level1': {
                'level2': {
                    'level3': {
                        'a': 1,
                        'b': 2
                    }
                }
            }
        }
        override = {
            'level1': {
                'level2': {
                    'level3': {
                        'b': 99,
                        'c': 3
                    }
                }
            }
        }
        result = 深度合并字典(base, override)
        
        level3 = result['level1']['level2']['level3']
        self.assertEqual(level3['a'], 1)   # 保留
        self.assertEqual(level3['b'], 99)  # 覆盖
        self.assertEqual(level3['c'], 3)   # 新增
    
    def test_列表值覆盖(self):
        """测试：列表值应直接覆盖，不是追加"""
        base = {'行业': ['3d_modeling']}
        override = {'行业': ['pdd_rights']}
        result = 深度合并字典(base, override)
        
        self.assertEqual(result['行业'], ['pdd_rights'])
    
    def test_复杂配置场景(self):
        """测试：模拟真实配置合并场景"""
        base = {
            '目标视频描述': '3D建模内容',
            '行业': ['3d_modeling'],
            'SYSTEM_PROMPTS': {
                'cls': {
                    'model': 'gpt-3.5-turbo',
                    'temperature': 0.5
                },
                'comment': {
                    'max_tokens': 150
                }
            },
            '视频评论提示词_3d_modeling': '你是3D建模专家...'
        }
        
        override = {
            '目标视频描述': '拼多多维权内容',
            '行业': ['pdd_rights'],
            'SYSTEM_PROMPTS': {
                'cls': {
                    'temperature': 0.8,  # 覆盖
                    'top_p': 0.9         # 新增
                }
            },
            '视频评论提示词_pdd_rights': '你是维权专家...'  # 新增
        }
        
        result = 深度合并字典(base, override)
        
        # 验证顶层覆盖
        self.assertEqual(result['目标视频描述'], '拼多多维权内容')
        self.assertEqual(result['行业'], ['pdd_rights'])
        
        # 验证嵌套合并
        self.assertEqual(result['SYSTEM_PROMPTS']['cls']['model'], 'gpt-3.5-turbo')  # 保留
        self.assertEqual(result['SYSTEM_PROMPTS']['cls']['temperature'], 0.8)        # 覆盖
        self.assertEqual(result['SYSTEM_PROMPTS']['cls']['top_p'], 0.9)              # 新增
        self.assertEqual(result['SYSTEM_PROMPTS']['comment']['max_tokens'], 150)     # 保留
        
        # 验证原配置保留
        self.assertEqual(result['视频评论提示词_3d_modeling'], '你是3D建模专家...')
        self.assertEqual(result['视频评论提示词_pdd_rights'], '你是维权专家...')


if __name__ == '__main__':
    unittest.main()
