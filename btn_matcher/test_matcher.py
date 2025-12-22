#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import sys
import os

def create_test_templates():
    """创建测试用的按钮模板"""
    print("创建测试模板...")
    
    # 创建测试目录
    os.makedirs('btn_tmpl', exist_ok=True)
    
    # 创建几个简单的按钮模板
    templates = [
        ('red_button', (0, 0, 255)),
        ('green_button', (0, 255, 0)),
        ('blue_button', (0, 0, 255)),
        ('yellow_button', (0, 255, 255))
    ]
    
    for name, color in templates:
        # 创建按钮图片（80x40的彩色矩形）
        img = np.zeros((40, 80, 3), dtype=np.uint8)
        cv2.rectangle(img, (5, 5), (75, 35), color, -1)
        cv2.imwrite(f'btn_tmpl/{name}.png', img)
        print(f"✓ 已创建: btn_tmpl/{name}.png")
    
    print()

def create_test_screenshot():
    """创建测试用的屏幕截图"""
    print("创建测试截图...")
    
    # 创建屏幕截图（640x480）
    screenshot = np.zeros((480, 640, 3), dtype=np.uint8)
    screenshot[:] = (50, 50, 50)  # 灰色背景
    
    # 添加几个按钮到截图中
    # 红色按钮
    cv2.rectangle(screenshot, (100, 200), (180, 240), (0, 0, 255), -1)
    
    # 绿色按钮
    cv2.rectangle(screenshot, (300, 200), (380, 240), (0, 255, 0), -1)
    
    # 蓝色按钮（缩小一点，测试尺度不变性）
    cv2.rectangle(screenshot, (500, 210), (560, 230), (255, 0, 0), -1)
    
    cv2.imwrite('test_screen.png', screenshot)
    print("✓ 已创建: test_screen.png")
    print()

def test_build_command():
    """测试建库命令"""
    print("测试建库命令...")
    print("-" * 50)
    
    # 导入并测试build_database函数
    sys.path.append('.')
    from button_matcher import build_database
    
    success = build_database('btn_tmpl', 'test.db')
    print("-" * 50)
    
    if success:
        print("✓ 建库测试通过！")
    else:
        print("✗ 建库测试失败！")
        return False
    
    print()
    return True

def test_detect_command():
    """测试检测命令"""
    print("测试检测命令...")
    print("-" * 50)
    
    from button_matcher import detect_buttons
    
    success = detect_buttons('test_screen.png', 'test.db')
    print("-" * 50)
    
    if success:
        print("✓ 检测测试通过！")
    else:
        print("✗ 检测测试失败！")
        return False
    
    print()
    return True

def cleanup():
    """清理测试文件"""
    print("清理测试文件...")
    
    files_to_remove = [
        'test.db',
        'test_screen.png',
        'test_screen_detected.png'
    ]
    
    dirs_to_remove = ['btn_tmpl']
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"✓ 已删除: {file}")
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            for file in os.listdir(dir_name):
                os.remove(os.path.join(dir_name, file))
            os.rmdir(dir_name)
            print(f"✓ 已删除目录: {dir_name}")
    
    print()

def main():
    print("=" * 60)
    print("按钮检测工具 - 功能测试")
    print("=" * 60)
    print()
    
    try:
        # 创建测试数据
        create_test_templates()
        create_test_screenshot()
        
        # 测试建库
        if not test_build_command():
            print("测试失败！")
            return
        
        # 测试检测
        if not test_detect_command():
            print("测试失败！")
            return
        
        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        
        # 显示使用说明
        print("\n现在你可以使用以下命令：")
        print()
        print("1. 建立特征库：")
        print("   python button_matcher.py build <模板目录>")
        print()
        print("2. 检测按钮：")
        print("   python button_matcher.py detect <图片路径>")
        print()
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 询问是否清理测试文件
        print()
        response = input("是否清理测试文件? [Y/n]: ")
        if response.lower() != 'n':
            cleanup()
        else:
            print("保留测试文件。")

if __name__ == '__main__':
    main()
