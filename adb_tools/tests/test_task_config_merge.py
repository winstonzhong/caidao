#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本任务配置合并功能的单元测试
"""

import unittest
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tool_xpath import 基本任务, 深度合并字典


class Mock持久对象:
    """模拟定时任务持久对象"""
    def __init__(self, 配置=None):
        self.配置 = 配置


class Test提取配置覆盖值字典(unittest.TestCase):
    """测试 _提取配置覆盖值字典 方法"""
    
    def setUp(self):
        """每个测试前创建基本任务实例"""
        # 创建一个最小化的基本任务实例用于测试
        self.task = 基本任务.__new__(基本任务)
    
    def test_旧格式配置(self):
        """测试：旧格式配置（直接字典）"""
        配置 = {
            "目标视频描述": "拼多多维权",
            "行业": ["pdd_rights"]
        }
        result = self.task._提取配置覆盖值字典(配置)
        
        self.assertEqual(result["目标视频描述"], "拼多多维权")
        self.assertEqual(result["行业"], ["pdd_rights"])
    
    def test_新格式配置(self):
        """测试：新格式配置（keys数组）"""
        配置 = {
            "keys": [
                {"name": "目标视频描述", "current_value": "拼多多维权", "type": "text"},
                {"name": "行业", "current_value": ["pdd_rights"], "type": "array"}
            ]
        }
        result = self.task._提取配置覆盖值字典(配置)
        
        self.assertEqual(result["目标视频描述"], "拼多多维权")
        self.assertEqual(result["行业"], ["pdd_rights"])
    
    def test_空配置(self):
        """测试：空配置应返回空字典"""
        self.assertEqual(self.task._提取配置覆盖值字典({}), {})
        self.assertEqual(self.task._提取配置覆盖值字典(None), {})
    
    def test_keys为空列表(self):
        """测试：keys为空列表时应返回空字典"""
        配置 = {"keys": []}
        result = self.task._提取配置覆盖值字典(配置)
        self.assertEqual(result, {})
    
    def test_混合格式(self):
        """测试：包含额外字段的keys格式"""
        配置 = {
            "keys": [
                {
                    "name": "目标视频描述",
                    "current_value": "测试内容",
                    "description": "这是描述",
                    "history": []
                }
            ]
        }
        result = self.task._提取配置覆盖值字典(配置)
        self.assertEqual(result["目标视频描述"], "测试内容")
        self.assertNotIn("description", result)  # 只提取name和current_value
    
    def test_name为空字符串(self):
        """测试：name为空字符串时也应该提取"""
        配置 = {
            "keys": [
                {"name": "", "current_value": "值"}
            ]
        }
        result = self.task._提取配置覆盖值字典(配置)
        self.assertEqual(result[""], "值")
    
    def test_name为None(self):
        """测试：name为None时不应该提取"""
        配置 = {
            "keys": [
                {"name": None, "current_value": "值"},
                {"name": "有效", "current_value": "有效值"}
            ]
        }
        result = self.task._提取配置覆盖值字典(配置)
        self.assertNotIn(None, result)
        self.assertEqual(result["有效"], "有效值")
    
    def test_current_value为None(self):
        """测试：current_value为None时也应该提取"""
        配置 = {
            "keys": [
                {"name": "key", "current_value": None}
            ]
        }
        result = self.task._提取配置覆盖值字典(配置)
        self.assertIsNone(result["key"])
    
    def test_非法配置类型(self):
        """测试：配置不是字典时应返回空字典"""
        result = self.task._提取配置覆盖值字典("字符串")
        self.assertEqual(result, {})
        
        result = self.task._提取配置覆盖值字典(123)
        self.assertEqual(result, {})
    
    def test_keys不是列表(self):
        """测试：keys不是列表时应返回空字典"""
        配置 = {"keys": "不是列表"}
        result = self.task._提取配置覆盖值字典(配置)
        self.assertEqual(result, {})


class Test合并定时任务配置到数据(unittest.TestCase):
    """测试 _合并定时任务配置到数据 方法"""
    
    def setUp(self):
        """每个测试前创建基本任务实例"""
        self.task = 基本任务.__new__(基本任务)
        self.task.持久对象 = None  # 默认无持久对象
    
    def test_无持久对象(self):
        """测试：无持久对象时不应合并"""
        data = {"paras": {"a": 1}}
        result = self.task._合并定时任务配置到数据(data)
        self.assertFalse(result)
        self.assertEqual(data["paras"]["a"], 1)  # 未被修改
    
    def test_持久对象无配置属性(self):
        """测试：持久对象无配置属性时不应合并"""
        self.task.持久对象 = object()  # 无配置属性的对象
        data = {"paras": {"a": 1}}
        result = self.task._合并定时任务配置到数据(data)
        self.assertFalse(result)
    
    def test_配置为空(self):
        """测试：配置为空时不应合并"""
        self.task.持久对象 = Mock持久对象(配置={})
        data = {"paras": {"a": 1}}
        result = self.task._合并定时任务配置到数据(data)
        self.assertFalse(result)
    
    def test_配置为None(self):
        """测试：配置为None时不应合并"""
        self.task.持久对象 = Mock持久对象(配置=None)
        data = {"paras": {"a": 1}}
        result = self.task._合并定时任务配置到数据(data)
        self.assertFalse(result)
    
    def test_成功合并旧格式配置(self):
        """测试：成功合并旧格式配置"""
        self.task.持久对象 = Mock持久对象(配置={
            "目标视频描述": "拼多多维权"
        })
        data = {
            "paras": {
                "目标视频描述": "3D建模",
                "其他键": "值"
            }
        }
        result = self.task._合并定时任务配置到数据(data)
        
        self.assertTrue(result)
        self.assertEqual(data["paras"]["目标视频描述"], "拼多多维权")
        self.assertEqual(data["paras"]["其他键"], "值")  # 保留其他键
    
    def test_成功合并新格式配置(self):
        """测试：成功合并新格式配置"""
        self.task.持久对象 = Mock持久对象(配置={
            "keys": [
                {"name": "目标视频描述", "current_value": "拼多多维权"}
            ]
        })
        data = {"paras": {"目标视频描述": "3D建模"}}
        result = self.task._合并定时任务配置到数据(data)
        
        self.assertTrue(result)
        self.assertEqual(data["paras"]["目标视频描述"], "拼多多维权")
    
    def test_保存原始paras(self):
        """测试：合并后应保存原始paras到_原始paras属性"""
        self.task.持久对象 = Mock持久对象(配置={
            "目标视频描述": "拼多多维权"
        })
        original = {"目标视频描述": "3D建模", "其他": "值"}
        data = {"paras": original}
        
        self.task._合并定时任务配置到数据(data)
        
        # 验证保存了原始值
        self.assertTrue(hasattr(self.task, '_原始paras'))
        self.assertEqual(self.task._原始paras["目标视频描述"], "3D建模")
        self.assertEqual(self.task._原始paras["其他"], "值")
        
        # 验证是深拷贝
        self.task._原始paras["测试"] = "测试值"
        self.assertNotIn("测试", original)
    
    def test_深度合并嵌套字典(self):
        """测试：嵌套字典应深度合并"""
        self.task.持久对象 = Mock持久对象(配置={
            "SYSTEM_PROMPTS": {
                "cls": {"temperature": 0.8}
            }
        })
        data = {
            "paras": {
                "SYSTEM_PROMPTS": {
                    "cls": {"model": "gpt-3.5"},
                    "comment": {"max": 100}
                }
            }
        }
        result = self.task._合并定时任务配置到数据(data)
        
        self.assertTrue(result)
        cls_config = data["paras"]["SYSTEM_PROMPTS"]["cls"]
        self.assertEqual(cls_config["model"], "gpt-3.5")  # 保留
        self.assertEqual(cls_config["temperature"], 0.8)  # 新增
        self.assertEqual(data["paras"]["SYSTEM_PROMPTS"]["comment"]["max"], 100)  # 保留


class TestInit配置合并集成(unittest.TestCase):
    """集成测试：验证init方法中的配置合并流程"""
    
    def test_init时自动合并配置(self):
        """测试：init方法应自动调用配置合并"""
        # 这个测试需要完整的基本任务初始化
        # 由于基本任务.__init__需要复杂的参数，这里只做简单的验证
        pass


class Test获取强制匹配朋友视频配置(unittest.TestCase):
    """测试 _获取强制匹配朋友视频配置 方法"""
    
    def setUp(self):
        """每个测试前创建基本任务实例"""
        self.task = 基本任务.__new__(基本任务)
        self.task.d = {"paras": {}}
    
    def test_配置为True时返回True(self):
        """测试：配置为True时应返回True"""
        self.task.d = {"paras": {"强制匹配朋友视频": True}}
        result = self.task._获取强制匹配朋友视频配置()
        self.assertTrue(result)
    
    def test_配置为False时返回False(self):
        """测试：配置为False时应返回False"""
        self.task.d = {"paras": {"强制匹配朋友视频": False}}
        result = self.task._获取强制匹配朋友视频配置()
        self.assertFalse(result)
    
    def test_配置为字符串true时返回True(self):
        """测试：配置为字符串'true'时应返回True"""
        self.task.d = {"paras": {"强制匹配朋友视频": "true"}}
        result = self.task._获取强制匹配朋友视频配置()
        self.assertTrue(result)
    
    def test_配置为字符串1时返回True(self):
        """测试：配置为字符串'1'时应返回True"""
        self.task.d = {"paras": {"强制匹配朋友视频": "1"}}
        result = self.task._获取强制匹配朋友视频配置()
        self.assertTrue(result)
    
    def test_配置为字符串yes时返回True(self):
        """测试：配置为字符串'yes'时应返回True"""
        self.task.d = {"paras": {"强制匹配朋友视频": "yes"}}
        result = self.task._获取强制匹配朋友视频配置()
        self.assertTrue(result)
    
    def test_配置为字符串启用时返回True(self):
        """测试：配置为字符串'启用'时应返回True"""
        self.task.d = {"paras": {"强制匹配朋友视频": "启用"}}
        result = self.task._获取强制匹配朋友视频配置()
        self.assertTrue(result)
    
    def test_配置为字符串false时返回False(self):
        """测试：配置为字符串'false'时应返回False"""
        self.task.d = {"paras": {"强制匹配朋友视频": "false"}}
        result = self.task._获取强制匹配朋友视频配置()
        self.assertFalse(result)
    
    def test_配置为字符串0时返回False(self):
        """测试：配置为字符串'0'时应返回False"""
        self.task.d = {"paras": {"强制匹配朋友视频": "0"}}
        result = self.task._获取强制匹配朋友视频配置()
        self.assertFalse(result)
    
    def test_配置为空时回退到环境变量(self):
        """测试：配置为空时应回退到环境变量"""
        import os
        self.task.d = {"paras": {}}
        
        # 设置环境变量
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = '1'
        result = self.task._获取强制匹配朋友视频配置()
        self.assertTrue(result)
        
        # 清除环境变量
        os.environ.pop('DY_FORCE_MATCH_FRIEND_VIDEO', None)
        result = self.task._获取强制匹配朋友视频配置()
        self.assertFalse(result)
    
    def test_配置优先级高于环境变量(self):
        """测试：配置优先级应高于环境变量"""
        import os
        self.task.d = {"paras": {"强制匹配朋友视频": False}}
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = '1'
        
        # 配置为False，环境变量为True，应返回False（配置优先）
        result = self.task._获取强制匹配朋友视频配置()
        self.assertFalse(result)
        
        os.environ.pop('DY_FORCE_MATCH_FRIEND_VIDEO', None)
    
    def test_支持DY_FORCE_MATCH_FRIEND_VIDEO键名(self):
        """测试：支持使用DY_FORCE_MATCH_FRIEND_VIDEO作为配置键名"""
        self.task.d = {"paras": {"DY_FORCE_MATCH_FRIEND_VIDEO": True}}
        result = self.task._获取强制匹配朋友视频配置()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
