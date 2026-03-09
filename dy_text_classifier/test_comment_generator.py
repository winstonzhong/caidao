#!/usr/bin/env python3
"""
集成测试入口: 根据视频数据生成评论

通过命令行调用真实的系统接口进行测试。

用法:
    # 使用默认video_data测试
    python test_comment_generator.py -d "拼多多维权、假货、薅羊毛"
    
    # 使用自定义目标描述
    python test_comment_generator.py -d "Blender 3D建模教程"
    
    # 从JSON文件加载video_data
    python test_comment_generator.py -d "美食探店" -v video_data.json
    
    # 使用自定义系统提示词
    python test_comment_generator.py -d "健身减脂" --sys-prompt prompt.txt

注意:
    此测试会真实调用LLM服务生成评论，请确保:
    1. Redis服务可用
    2. LLM服务（豆包队列）正常运行
"""

import argparse
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, '/home/yka-003/workspace/caidao')

# 设置Django环境（某些模块可能需要）
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg.settings')

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


def create_test_job(目标描述: str, sys_prompt: str = None):
    """
    创建测试任务实例
    
    创建一个最小化的基本任务配置，用于调用根据视频数据生成评论函数
    """
    from adb_tools.tool_xpath import 基本任务
    
    # 最小化任务配置
    job_config = {
        "name": "测试评论生成",
        "package": "com.ss.android.ugc.aweme",
        "activity": "com.ss.android.ugc.aweme.main.MainActivity",
        "paras": {
            "目标视频描述": 目标描述,
            "sys_prompt_comment": sys_prompt,
            "行业": "default"
        },
        "blocks": [],
        "device": {
            "ip_port": None  # 不需要真实设备，仅用于生成评论
        }
    }
    
    job = 基本任务(job_config, device_pointed=None)
    return job


def main():
    parser = argparse.ArgumentParser(
        description='集成测试：根据视频数据生成评论（真实API调用）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认video_data测试（真实调用LLM）
  python test_comment_generator.py -d "拼多多维权、假货、薅羊毛"
  
  # 使用自定义目标描述
  python test_comment_generator.py -d "Blender 3D建模教程"
  
  # 从JSON文件加载video_data
  python test_comment_generator.py -d "美食探店" -v video_data.json
  
  # 使用自定义系统提示词
  python test_comment_generator.py -d "健身减脂" --sys-prompt prompt.txt
  
  # 只生成提示词，不调用API（快速测试）
  python test_comment_generator.py -d "测试主题" --dry-run

警告:
  此脚本会真实调用LLM服务，可能产生费用！
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
        '--sys-prompt',
        type=str,
        help='自定义系统提示词文件路径'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='只生成提示词，不实际调用API（快速测试）'
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
    
    # 打印测试信息
    print("\n" + "=" * 70)
    print("【集成测试】根据视频数据生成评论")
    print("=" * 70)
    print(f"\n【目标描述】{args.desc}")
    print(f"\n【video_data】")
    for k, v in video_data.items():
        print(f"  {k}: {v}")
    
    if args.dry_run:
        # 只生成提示词，不调用API
        print("\n" + "=" * 70)
        print("【Dry Run模式】只生成提示词，不调用API")
        print("=" * 70)
        
        if sys_prompt:
            print(f"\n【使用自定义提示词】\n{sys_prompt[:500]}...")
        else:
            prompt = PromptGenerator._生成默认评论提示词(args.desc, video_data)
            print(f"\n【自动生成的提示词】\n{prompt}")
        
        print("\n【将要发送的content】")
        content = json.dumps(video_data, ensure_ascii=False, indent=2)
        print(content)
        
        print("\n✅ Dry Run完成，未实际调用API")
        return
    
    # 创建真实任务实例
    print("\n" + "=" * 70)
    print("【创建测试任务实例】")
    print("=" * 70)
    
    try:
        job = create_test_job(args.desc, sys_prompt)
        print(f"✅ 任务实例创建成功")
        print(f"   任务名称: {job.name}")
        print(f"   目标描述: {job.config.get('目标视频描述')}")
    except Exception as e:
        print(f"❌ 创建任务实例失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 调用真实的根据视频数据生成评论函数
    print("\n" + "=" * 70)
    print("【调用根据视频数据生成评论】")
    print("⚠️  注意：这将真实调用LLM服务！")
    print("=" * 70)
    
    try:
        comment = job.根据视频数据生成评论(args.desc, video_data, sys_prompt)
        
        # 打印结果
        print("\n" + "=" * 70)
        print("【测试结果】")
        print("=" * 70)
        if comment:
            print(f"\n✅ 生成的评论:\n{comment}")
        else:
            print("\n❌ 生成评论失败（返回None）")
    except Exception as e:
        print(f"\n❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ 集成测试完成!")


if __name__ == "__main__":
    main()
