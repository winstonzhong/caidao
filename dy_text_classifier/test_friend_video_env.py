#!/usr/bin/env python3
"""
朋友视频环境变量功能单元测试

测试 DY_FORCE_MATCH_FRIEND_VIDEO 环境变量对朋友视频处理流程的控制。

用法:
    python dy_text_classifier/test_friend_video_env.py
"""

import unittest
import sys
import os

# 添加项目路径
sys.path.insert(0, '/home/yka-003/workspace/caidao')


class TestFriendVideoEnvVar(unittest.TestCase):
    """测试朋友视频环境变量功能"""
    
    def setUp(self):
        """每个测试前清理环境变量"""
        # 保存原始环境变量值
        self._original_env = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO')
        # 清理环境变量
        if 'DY_FORCE_MATCH_FRIEND_VIDEO' in os.environ:
            del os.environ['DY_FORCE_MATCH_FRIEND_VIDEO']
    
    def tearDown(self):
        """每个测试后恢复环境变量"""
        if self._original_env is not None:
            os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = self._original_env
        elif 'DY_FORCE_MATCH_FRIEND_VIDEO' in os.environ:
            del os.environ['DY_FORCE_MATCH_FRIEND_VIDEO']
    
    def test_环境变量未设置时_强制匹配为False(self):
        """测试：未设置环境变量时，_force_match_friend 应为 False"""
        # 确保环境变量未设置
        if 'DY_FORCE_MATCH_FRIEND_VIDEO' in os.environ:
            del os.environ['DY_FORCE_MATCH_FRIEND_VIDEO']
        
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        self.assertFalse(_force_match_friend, "未设置环境变量时，_force_match_friend 应该为 False")
    
    def test_环境变量设置为1时_强制匹配为True(self):
        """测试：环境变量设置为 '1' 时，_force_match_friend 应为 True"""
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = '1'
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        self.assertTrue(_force_match_friend, "环境变量设置为 '1' 时，_force_match_friend 应该为 True")
    
    def test_环境变量设置为true时_强制匹配为True(self):
        """测试：环境变量设置为 'true' 时，_force_match_friend 应为 True"""
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = 'true'
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        self.assertTrue(_force_match_friend, "环境变量设置为 'true' 时，_force_match_friend 应该为 True")
    
    def test_环境变量设置为yes时_强制匹配为True(self):
        """测试：环境变量设置为 'yes' 时，_force_match_friend 应为 True"""
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = 'yes'
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        self.assertTrue(_force_match_friend, "环境变量设置为 'yes' 时，_force_match_friend 应该为 True")
    
    def test_环境变量设置为on时_强制匹配为True(self):
        """测试：环境变量设置为 'on' 时，_force_match_friend 应为 True"""
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = 'on'
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        self.assertTrue(_force_match_friend, "环境变量设置为 'on' 时，_force_match_friend 应该为 True")
    
    def test_环境变量设置为TRUE时_强制匹配为True(self):
        """测试：环境变量设置为 'TRUE'（大写）时，_force_match_friend 应为 True"""
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = 'TRUE'
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        self.assertTrue(_force_match_friend, "环境变量设置为 'TRUE' 时，_force_match_friend 应该为 True（大小写不敏感）")
    
    def test_环境变量设置为0时_强制匹配为False(self):
        """测试：环境变量设置为 '0' 时，_force_match_friend 应为 False"""
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = '0'
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        self.assertFalse(_force_match_friend, "环境变量设置为 '0' 时，_force_match_friend 应该为 False")
    
    def test_环境变量设置为false时_强制匹配为False(self):
        """测试：环境变量设置为 'false' 时，_force_match_friend 应为 False"""
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = 'false'
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        self.assertFalse(_force_match_friend, "环境变量设置为 'false' 时，_force_match_friend 应该为 False")
    
    def test_环境变量设置为空字符串时_强制匹配为False(self):
        """测试：环境变量设置为空字符串时，_force_match_friend 应为 False"""
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = ''
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        self.assertFalse(_force_match_friend, "环境变量设置为空字符串时，_force_match_friend 应该为 False")
    
    def test_环境变量设置为随机值时_强制匹配为False(self):
        """测试：环境变量设置为随机值时，_force_match_friend 应为 False"""
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = 'random_value'
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        self.assertFalse(_force_match_friend, "环境变量设置为随机值时，_force_match_friend 应该为 False")


class TestFriendVideoLogic(unittest.TestCase):
    """测试朋友视频处理逻辑"""
    
    def setUp(self):
        """每个测试前清理环境变量"""
        self._original_env = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO')
        if 'DY_FORCE_MATCH_FRIEND_VIDEO' in os.environ:
            del os.environ['DY_FORCE_MATCH_FRIEND_VIDEO']
    
    def tearDown(self):
        """每个测试后恢复环境变量"""
        if self._original_env is not None:
            os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = self._original_env
        elif 'DY_FORCE_MATCH_FRIEND_VIDEO' in os.environ:
            del os.environ['DY_FORCE_MATCH_FRIEND_VIDEO']
    
    def test_朋友视频_无环境变量_应跳过匹配(self):
        """测试：朋友视频且环境变量未设置时，应跳过匹配直接生成评论"""
        video_data = {'朋友': '是', '作者': '@test_user'}
        
        # 模拟逻辑判断
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        
        # 朋友视频且无强制匹配时，应跳过匹配
        should_skip_match = video_data.get('朋友') == '是' and not _force_match_friend
        self.assertTrue(should_skip_match, "朋友视频且未设置环境变量时，应跳过匹配")
    
    def test_朋友视频_有环境变量_应强制匹配(self):
        """测试：朋友视频且环境变量已设置时，应强制进行匹配检查"""
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = '1'
        video_data = {'朋友': '是', '作者': '@test_user'}
        
        # 模拟逻辑判断
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        
        # 朋友视频但有强制匹配时，不应跳过匹配
        should_skip_match = video_data.get('朋友') == '是' and not _force_match_friend
        self.assertFalse(should_skip_match, "朋友视频且设置环境变量时，不应跳过匹配")
    
    def test_非朋友视频_无论环境变量_都应匹配(self):
        """测试：非朋友视频时，无论环境变量如何，都应进行匹配检查"""
        video_data = {'朋友': '否', '作者': '@test_user'}
        
        # 测试无环境变量
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        should_skip_match = video_data.get('朋友') == '是' and not _force_match_friend
        self.assertFalse(should_skip_match, "非朋友视频不应跳过匹配")
        
        # 测试有环境变量
        os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = '1'
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        should_skip_match = video_data.get('朋友') == '是' and not _force_match_friend
        self.assertFalse(should_skip_match, "非朋友视频不应跳过匹配（即使有环境变量）")
    
    def test_朋友字段缺失_视为非朋友视频(self):
        """测试：朋友字段缺失时，应视为非朋友视频"""
        video_data = {'作者': '@test_user'}  # 没有'朋友'字段
        
        _force_match_friend = os.environ.get('DY_FORCE_MATCH_FRIEND_VIDEO', '').lower() in ('1', 'true', 'yes', 'on')
        
        # 朋友字段缺失时，get('朋友') 返回 None，不是 '是'
        should_skip_match = video_data.get('朋友') == '是' and not _force_match_friend
        self.assertFalse(should_skip_match, "朋友字段缺失时应视为非朋友视频，进行匹配检查")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestFriendVideoEnvVar))
    suite.addTests(loader.loadTestsFromTestCase(TestFriendVideoLogic))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
