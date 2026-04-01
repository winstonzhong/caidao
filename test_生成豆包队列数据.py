#!/usr/bin/env python3
"""
命令行测试工具: 生成豆包队列数据

用于测试 生成豆包队列数据 函数，随机选择 UT 目录中的 XML/JSON 数据，
生成可直接推入豆包队列的数据字典。

用法:
    # 随机选择 UT 中的数据测试
    python test_生成豆包队列数据.py
    
    # 指定目标描述
    python test_生成豆包队列数据.py -d "美食探店"
    
    # 使用指定的 JSON 文件
    python test_生成豆包队列数据.py -j ut/xmls/20260225_164300.json
    
    # 指定 XML 文件（会自动解析）
    python test_生成豆包队列数据.py -x ut/xmls/20260225_164300.xml
    
    # 使用自定义系统提示词
    python test_生成豆包队列数据.py --sys-prompt prompt.txt

输出:
    - 打印使用的 video_data
    - 打印生成的 DataDictionary（队列数据）
    - 显示提示词预览
"""

import argparse
import json
import sys
import os
import random

# 添加项目路径
sys.path.insert(0, '/home/yka-003/workspace/caidao')

from tool_dy_xml import 提取结构化数据


# UT 测试数据目录
UT_XML_DIR = '/home/yka-003/workspace/caidao/ut/xmls'


def get_random_test_data():
    """随机获取一个 UT 中的测试数据"""
    json_files = [f for f in os.listdir(UT_XML_DIR) if f.endswith('.json')]
    if not json_files:
        raise FileNotFoundError(f"未在 {UT_XML_DIR} 找到 JSON 测试数据文件")
    
    # 随机选择一个文件
    selected_file = random.choice(json_files)
    file_path = os.path.join(UT_XML_DIR, selected_file)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        video_data = json.load(f)
    
    return video_data, selected_file


def get_test_data_from_json(json_path):
    """从指定的 JSON 文件加载测试数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        video_data = json.load(f)
    return video_data, os.path.basename(json_path)


def get_test_data_from_xml(xml_path):
    """从指定的 XML 文件解析测试数据"""
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    video_data = 提取结构化数据(xml_content)
    if not video_data:
        raise ValueError(f"无法从 {xml_path} 解析视频数据")
    
    return video_data, os.path.basename(xml_path)


def create_test_job(目标描述: str):
    """创建最小化测试任务实例"""
    from adb_tools.tool_xpath import 基本任务
    
    job_config = {
        "name": "测试生成豆包队列数据",
        "package": "com.ss.android.ugc.aweme",
        "activity": "com.ss.android.ugc.aweme.main.MainActivity",
        "paras": {
            "目标视频描述": 目标描述,
            "行业": "default",
            "评论立场": "支持",
        },
        "blocks": [],
        "device": {"ip_port": None}
    }
    
    return 基本任务(job_config, device_pointed=None)


def main():
    parser = argparse.ArgumentParser(
        description='测试：生成豆包队列数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 随机选择 UT 中的数据测试
  python test_生成豆包队列数据.py
  
  # 指定目标描述
  python test_生成豆包队列数据.py -d "美食探店"
  
  # 使用指定的 JSON 文件
  python test_生成豆包队列数据.py -j ut/xmls/20260225_164300.json
  
  # 指定 XML 文件（会自动解析）
  python test_生成豆包队列数据.py -x ut/xmls/20260225_164300.xml
  
  # 使用自定义系统提示词
  python test_生成豆包队列数据.py --sys-prompt prompt.txt
        """
    )
    
    parser.add_argument(
        '-d', '--desc',
        type=str,
        default='电商运营、拼多多',
        help='目标视频描述（默认：电商运营、拼多多）'
    )
    
    parser.add_argument(
        '-j', '--json',
        type=str,
        metavar='FILE',
        help='指定 JSON 文件路径（默认随机选择 UT 中的文件）'
    )
    
    parser.add_argument(
        '-x', '--xml',
        type=str,
        metavar='FILE',
        help='指定 XML 文件路径（会自动解析为 video_data）'
    )
    
    parser.add_argument(
        '--sys-prompt',
        type=str,
        help='自定义系统提示词文件路径'
    )
    
    parser.add_argument(
        '--full-output',
        action='store_true',
        help='显示完整的提示词内容（默认只显示前 1000 字符）'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("【测试】生成豆包队列数据")
    print("=" * 70)
    
    # 加载测试数据
    try:
        if args.xml:
            video_data, source_file = get_test_data_from_xml(args.xml)
            print(f"\n✅ 已从 XML 加载: {source_file}")
        elif args.json:
            video_data, source_file = get_test_data_from_json(args.json)
            print(f"\n✅ 已从 JSON 加载: {source_file}")
        else:
            video_data, source_file = get_random_test_data()
            print(f"\n✅ 随机选择: {source_file}")
    except Exception as e:
        print(f"\n❌ 加载测试数据失败: {e}")
        sys.exit(1)
    
    # 打印 video_data
    print("\n" + "-" * 70)
    print("【Video Data】")
    print("-" * 70)
    for k, v in video_data.items():
        print(f"  {k}: {v}")
    
    # 加载自定义系统提示词
    sys_prompt = None
    if args.sys_prompt:
        try:
            with open(args.sys_prompt, 'r', encoding='utf-8') as f:
                sys_prompt = f.read()
            print(f"\n✅ 已加载自定义提示词: {args.sys_prompt}")
        except Exception as e:
            print(f"\n⚠️  加载自定义提示词失败: {e}，将使用默认提示词")
    
    # 创建任务实例
    print("\n" + "-" * 70)
    print("【创建测试任务实例】")
    print("-" * 70)
    
    try:
        job = create_test_job(args.desc)
        print(f"✅ 任务实例创建成功")
        print(f"   目标描述: {args.desc}")
    except Exception as e:
        print(f"❌ 创建任务实例失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 调用生成豆包队列数据函数
    print("\n" + "=" * 70)
    print("【调用 生成豆包队列数据】")
    print("=" * 70)
    
    try:
        data = job.生成豆包队列数据(
            video_data=video_data,
            sys_prompt=sys_prompt,
            目标描述=args.desc
        )
        
        print("\n✅ 函数执行成功！")
        
        # 打印 DataDictionary
        print("\n" + "=" * 70)
        print("【生成的 DataDictionary（队列数据）】")
        print("=" * 70)
        print(f"\n数据键: {list(data.keys())}")
        print(f"\n完整数据:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        # 打印提示词预览
        print("\n" + "=" * 70)
        print("【直接提示词 预览】")
        print("=" * 70)
        prompt = data.get("直接提示词", "")
        
        if args.full_output:
            print(f"\n{prompt}")
        else:
            preview_len = 1000
            print(f"\n{prompt[:preview_len]}")
            if len(prompt) > preview_len:
                print(f"\n... (共 {len(prompt)} 字符，使用 --full-output 查看完整内容)")
        
        # 结果分析
        print("\n" + "=" * 70)
        print("【结果分析】")
        print("=" * 70)
        
        if "http" in prompt and "请根据以下链接中的提示词生成评论" in prompt:
            print("✅ 使用了 HTML 模板链接模式")
            # 提取并显示 URL
            import re
            url_match = re.search(r'https?://\S+', prompt)
            if url_match:
                print(f"   HTML URL: {url_match.group()}")
        elif "你是一个" in prompt or "评论助手" in prompt or "生成评论" in prompt:
            print("ℹ️  使用了纯文本提示词模式（HTML 上传可能失败或环境不支持）")
        else:
            print("⚠️  提示词格式未知")
        
        print(f"\n提示词长度: {len(prompt)} 字符")
        
    except Exception as e:
        print(f"\n❌ 函数调用失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("【测试完成】")
    print("=" * 70)
    print("\n此 DataDictionary 可直接用于推入豆包队列:")
    print("  result = self.推入通用豆包任务队列并阻塞获取结果(data)")


if __name__ == "__main__":
    main()
