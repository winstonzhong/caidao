#!/usr/bin/env python3
"""
测试入口: 根据视频数据生成评论

用法:
    python test_comment_generator.py -d "目标描述" -v video_data.json
    python test_comment_generator.py -d "拼多多维权" (使用默认video_data)
"""

import argparse
import json
import sys

# 添加项目路径
sys.path.insert(0, '/home/yka-003/workspace/caidao')

from dy_text_classifier.prompt_generator import PromptGenerator


# 默认测试用的 video_data
DEFAULT_VIDEO_DATA = {
    '作者': '@23797136149',
    '文案': '即然拼多多商家不愿抵制平台的压榨，那么我就用魔法打魔法，我也是消费者，我也可以去薅有运费险商家的羊毛，这样做虽然不对，但也是没办法的办法！#拼多...',
    '音乐': '魂！！',
    '点赞': '26',
    '评论': '36',
    '收藏': '3',
    '分享': '0',
    '类型': '视频'
}


class MockTask:
    """
    模拟基本任务类，用于测试根据视频数据生成评论函数
    """
    
    def __init__(self):
        # 模拟配置
        self.config = {
            '目标视频描述': '拼多多维权、假货、薅羊毛',
            'sys_prompt_comment': None
        }
    
    def 获取回答数据(self, sys_prompt: str, question: str, partial_content=None):
        """
        模拟获取回答数据，实际测试时打印请求信息
        
        在真实环境中，这会调用Redis队列提交给LLM处理
        在测试中，我们展示将要发送的数据
        """
        print("\n" + "=" * 70)
        print("【模拟API调用】获取回答数据")
        print("=" * 70)
        print(f"\n【系统提示词前500字符】: \n{sys_prompt[:500]}...")
        print(f"\n【问题/内容前500字符】: \n{question[:500]}...")
        print("\n【说明】实际环境中将调用LLM生成评论")
        
        # 返回模拟结果
        return {
            'result': f'[模拟评论] 基于"{self.config.get("目标视频描述")}"主题生成的测试评论...'
        }
    
    def 根据视频数据生成评论(self, 目标描述: str, video_data: dict, sys_prompt: str = None) -> str:
        """
        根据视频数据生成评论（核心公用函数，不做匹配检查）
        
        从 tool_xpath.py 中提取的公用函数实现
        """
        print(f"\n[生成评论] 目标描述: {目标描述}")
        print(f"[生成评论] video_data: {json.dumps(video_data, ensure_ascii=False)}")
        
        # 1. 将video_data转换为JSON字符串作为content
        content = json.dumps(video_data, ensure_ascii=False, indent=2)
        
        # 2. 获取或生成系统提示词
        if not sys_prompt:
            sys_prompt = PromptGenerator._生成默认评论提示词(目标描述, video_data)
            print(f"\n[生成评论] 使用自动生成的提示词")
        else:
            print(f"\n[生成评论] 使用自定义提示词")
        
        # 3. 调用API生成评论
        result = self.获取回答数据(sys_prompt, content)
        comment = result.get('result')
        
        if comment:
            print(f"\n[生成评论] 成功生成评论: {comment[:50]}...")
        else:
            print(f"\n[生成评论] 生成评论失败")
        
        return comment


def main():
    parser = argparse.ArgumentParser(
        description='测试根据视频数据生成评论函数',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认video_data测试
  python test_comment_generator.py -d "拼多多维权、假货、薅羊毛"
  
  # 使用自定义目标描述
  python test_comment_generator.py -d "Blender 3D建模教程"
  
  # 从JSON文件加载video_data
  python test_comment_generator.py -d "美食探店" -v video_data.json
  
  # 显示完整提示词
  python test_comment_generator.py -d "健身减脂" -f
        """
    )
    
    parser.add_argument(
        '-d', '--desc',
        type=str,
        default='拼多多维权、假货、薅羊毛',
        help='目标视频描述（默认：拼多多维权、假货、薅羊毛）'
    )
    
    parser.add_argument(
        '-v', '--video-data',
        type=str,
        metavar='FILE',
        help='从JSON文件加载video_data（默认使用内置测试数据）'
    )
    
    parser.add_argument(
        '-f', '--full',
        action='store_true',
        help='显示完整的提示词和内容'
    )
    
    parser.add_argument(
        '--sys-prompt',
        type=str,
        help='自定义系统提示词文件路径'
    )
    
    args = parser.parse_args()
    
    # 加载video_data
    if args.video_data:
        with open(args.video_data, 'r', encoding='utf-8') as f:
            video_data = json.load(f)
        print(f"✅ 已从 {args.video_data} 加载video_data")
    else:
        video_data = DEFAULT_VIDEO_DATA
        print("✅ 使用默认测试video_data")
    
    # 加载自定义系统提示词
    sys_prompt = None
    if args.sys_prompt:
        with open(args.sys_prompt, 'r', encoding='utf-8') as f:
            sys_prompt = f.read()
        print(f"✅ 已从 {args.sys_prompt} 加载自定义提示词")
    
    # 创建模拟任务实例
    task = MockTask()
    task.config['目标视频描述'] = args.desc
    
    # 打印测试信息
    print("\n" + "=" * 70)
    print("【测试】根据视频数据生成评论")
    print("=" * 70)
    print(f"\n【目标描述】{args.desc}")
    print(f"\n【video_data】")
    for k, v in video_data.items():
        print(f"  {k}: {v}")
    
    # 调用测试函数
    comment = task.根据视频数据生成评论(args.desc, video_data, sys_prompt)
    
    # 打印结果
    print("\n" + "=" * 70)
    print("【测试结果】")
    print("=" * 70)
    if comment:
        print(f"\n生成的评论: {comment}")
    else:
        print("\n生成评论失败")
    
    # 如果需要显示完整提示词
    if args.full and not sys_prompt:
        print("\n" + "=" * 70)
        print("【完整系统提示词】")
        print("=" * 70)
        full_prompt = PromptGenerator._生成默认评论提示词(args.desc, video_data)
        print(full_prompt)
    
    print("\n✅ 测试完成!")


if __name__ == "__main__":
    main()
