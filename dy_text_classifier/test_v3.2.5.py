#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PromptGenerator V3.2.5 回归测试主程序

用法：
    python test_v3.2.5.py --input-dir /mnt/56T/logs/mdata/2026-03-16 --limit 10
    python test_v3.2.5.py --input-dir /mnt/56T/logs/mdata/2026-03-16 --output report.json --dry-run
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/home/yka-003/workspace/caidao')
sys.path.insert(0, '/home/yka-003/workspace/sg')

from dy_text_classifier.prompt_generator import PromptGenerator
from helper_task_redis2 import GLOBAL_REDIS


def 加载历史记录(目录: str, 限制数量: int = 10) -> list:
    """加载历史执行记录"""
    记录列表 = []
    目录路径 = Path(目录)
    
    if not 目录路径.exists():
        print(f"[错误] 目录不存在: {目录}")
        return 记录列表
    
    # 按文件修改时间排序（最早的在前），避免加载到最新的测试结果
    json文件列表 = sorted(
        目录路径.glob("result_*.json"),
        key=lambda p: p.stat().st_mtime  # 按修改时间排序
    )
    print(f"[信息] 找到 {len(json文件列表)} 个历史记录文件（按时间从早到晚排序）")
    
    for i, 文件 in enumerate(json文件列表[:限制数量], 1):
        try:
            with open(文件, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            # 提取 video_data
            question_str = 数据.get('meta', {}).get('question', '{}')
            video_data = json.loads(question_str)
            
            # 提取目标描述（从sys_prompt中推断或使用默认值）
            sys_prompt_old = 数据.get('meta', {}).get('sys_prompt', '')
            目标描述 = 推断目标描述(sys_prompt_old, video_data)
            
            记录列表.append({
                '序号': i,
                '文件名': 文件.name,
                'video_data': video_data,
                '目标描述': 目标描述,
                '旧评论': 数据.get('output', {}).get('text', ''),
                '旧sys_prompt': sys_prompt_old[:200] + '...' if len(sys_prompt_old) > 200 else sys_prompt_old
            })
        except Exception as e:
            print(f"[警告] 加载文件失败 {文件.name}: {e}")
    
    return 记录列表


def 推断目标描述(sys_prompt: str, video_data: dict) -> str:
    """从旧sys_prompt中推断目标描述"""
    # 尝试从sys_prompt第一行提取
    # 格式: "你是一个专注于{目标描述}的视频博主"
    match = re.search(r'你是一个专注于(.+?)的视频博主', sys_prompt)
    if match:
        return match.group(1).strip()
    
    # 默认根据文案内容推断
    文案 = video_data.get('文案', '')
    if '豆包' in 文案 or 'AI' in 文案 or '大模型' in 文案:
        return "AI大模型、豆包、ChatGPT等"
    elif '建模' in 文案 or 'Blender' in 文案 or '3D' in 文案:
        return "3D建模、Blender、渲染等"
    elif '麻将' in 文案:
        return "麻将、雀魂、棋牌策略等"
    elif '拼多多' in 文案 or '淘宝' in 文案 or '客服' in 文案:
        return "拼多多维权、电商客服等"
    else:
        return "相关领域内容"  # 默认


def 生成新评论(video_data: dict, 目标描述: str, dry_run: bool = False) -> dict:
    """
    使用 V3.2.5 生成新的提示词和评论
    
    Args:
        video_data: 视频数据
        目标描述: 目标视频描述
        dry_run: 如果为True，则不调用LLM，返回模拟数据
    
    Returns:
        dict: 包含 sys_prompt 和 评论
    """
    # 1. 生成新的 sys_prompt（V3.2.5）
    sys_prompt = PromptGenerator.获取评论助手提示词(目标描述, video_data)
    
    if dry_run:
        # 模拟模式：不调用LLM
        return {
            'sys_prompt': sys_prompt,
            '评论': f"[模拟评论] 针对 @{video_data.get('作者', '')} 的视频",
            '是否模拟': True
        }
    
    # 2. 调用 LLM API 生成评论
    try:
        question = json.dumps(video_data, ensure_ascii=False)
        
        key_back = f"test_v3.2.5_{int(datetime.now().timestamp() * 1000)}"
        result = GLOBAL_REDIS.提交数据并阻塞等待结果(
            key_back=key_back,
            sys_prompt=sys_prompt,
            question=question,
            timeout=30
        )
        
        if result and result.get("result"):
            comment = result["result"]
        else:
            comment = "[错误] LLM调用失败"
        
        return {
            'sys_prompt': sys_prompt,
            '评论': comment,
            '是否模拟': False
        }
    
    except Exception as e:
        print(f"[错误] LLM调用失败: {e}")
        return {
            'sys_prompt': sys_prompt,
            '评论': f"[错误] {str(e)}",
            '是否模拟': False
        }


def 检查视频信息正确性(sys_prompt: str, video_data: dict) -> tuple:
    """
    检查生成的提示词中的视频信息是否与实际的 video_data 一致
    
    Returns:
        (是否通过, 详情说明)
    """
    # 提取实际的作者和文案
    实际作者 = video_data.get('作者', '').lstrip('@')
    实际文案 = video_data.get('文案', '')[:50]  # 前50字符
    
    # 从 sys_prompt 中提取视频信息
    # 格式："- 作者: @xxx" "- 文案: xxx"
    
    提示词作者匹配 = re.search(r'- 作者:\s*@?(\S+)', sys_prompt)
    提示词作者 = 提示词作者匹配.group(1) if 提示词作者匹配 else None
    
    提示词文案匹配 = re.search(r'- 文案:\s*(.+?)(?:\n|$)', sys_prompt)
    提示词文案 = 提示词文案匹配.group(1)[:50] if 提示词文案匹配 else None
    
    # 对比
    作者正确 = 提示词作者 == 实际作者
    文案正确 = 提示词文案 and 实际文案 and (提示词文案 in 实际文案 or 实际文案 in 提示词文案)
    
    if 作者正确 and 文案正确:
        return True, f"作者和文案均正确（作者:{提示词作者}）"
    elif 作者正确:
        return False, f"作者正确但文案不匹配（提示词文案:{提示词文案}, 实际:{实际文案[:30]}...）"
    elif 文案正确:
        return False, f"文案正确但作者不匹配（提示词作者:{提示词作者}, 实际:{实际作者}）"
    else:
        return False, f"作者和文案均不匹配（提示词作者:{提示词作者}, 实际作者:{实际作者}）"


def 计算emoji数量(text: str) -> int:
    """计算文本中的emoji数量"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", 
        flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(text)
    return len(emojis)


def 评分(新结果: dict, video_data: dict) -> dict:
    """
    根据评分标准进行评分
    
    评分维度：
    - D1: 视频信息正确性（30分）- BUG-001验证
    - D2: "很好奇"句式检查（20分）
    - D3: 字数合规（10分）
    - D4: 禁止@任何人（15分）
    - D5: 禁止hashtag（15分）
    - D6: emoji数量（10分）
    """
    得分 = 0
    详情 = []
    
    评论 = 新结果.get('评论', '')
    sys_prompt = 新结果.get('sys_prompt', '')
    
    # D1: 视频信息正确性（关键项）
    d1通过, d1说明 = 检查视频信息正确性(sys_prompt, video_data)
    if d1通过:
        得分 += 30
        详情.append({"维度": "D1", "检查项": "视频信息正确性", "结果": "通过", "得分": 30, "说明": d1说明})
    else:
        详情.append({"维度": "D1", "检查项": "视频信息正确性", "结果": "失败", "得分": 0, "说明": d1说明})
    
    # D2: "很好奇"句式检查
    if "很好奇" not in 评论:
        得分 += 20
        详情.append({"维度": "D2", "检查项": "很好奇句式", "结果": "通过", "得分": 20, "说明": "未使用'很好奇'句式"})
    else:
        详情.append({"维度": "D2", "检查项": "很好奇句式", "结果": "失败", "得分": 0, "说明": "使用了'很好奇'句式"})
    
    # D3: 字数合规
    字数 = len(评论)
    if 30 <= 字数 <= 150:
        得分 += 10
        详情.append({"维度": "D3", "检查项": "字数合规", "结果": "通过", "得分": 10, "说明": f"字数{字数}在范围内(30-150)"})
    else:
        详情.append({"维度": "D3", "检查项": "字数合规", "结果": "失败", "得分": 0, "说明": f"字数{字数}超出范围(30-150)"})
    
    # D4: 禁止@任何人
    if "@" not in 评论:
        得分 += 15
        详情.append({"维度": "D4", "检查项": "禁止@用户", "结果": "通过", "得分": 15, "说明": "未@任何人"})
    else:
        详情.append({"维度": "D4", "检查项": "禁止@用户", "结果": "失败", "得分": 0, "说明": "评论中包含@"})
    
    # D5: 禁止hashtag
    if "#" not in 评论:
        得分 += 15
        详情.append({"维度": "D5", "检查项": "禁止hashtag", "结果": "通过", "得分": 15, "说明": "未使用hashtag"})
    else:
        详情.append({"维度": "D5", "检查项": "禁止hashtag", "结果": "失败", "得分": 0, "说明": "评论中包含hashtag"})
    
    # D6: emoji数量
    emoji_count = 计算emoji数量(评论)
    if emoji_count <= 1:
        得分 += 10
        详情.append({"维度": "D6", "检查项": "emoji数量", "结果": "通过", "得分": 10, "说明": f"emoji数量{emoji_count}合规(≤1)"})
    else:
        详情.append({"维度": "D6", "检查项": "emoji数量", "结果": "失败", "得分": 0, "说明": f"emoji数量{emoji_count}超出限制(≤1)"})
    
    # 判断是否通过：总分≥60 且 D1必须通过
    是否通过 = (得分 >= 60) and d1通过
    
    return {
        "总分": 得分,
        "满分": 100,
        "通过率": 得分 / 100,
        "是否通过": 是否通过,
        "详情": 详情
    }


def 生成报告(测试结果列表: list, 输出文件: str = None, 输入目录: str = ""):
    """生成测试报告"""
    总计 = len(测试结果列表)
    通过数 = sum(1 for r in 测试结果列表 if r.get('评分', {}).get('是否通过', False))
    通过率 = 通过数 / 总计 if 总计 > 0 else 0
    
    # BUG-001验证统计
    d1通过数 = sum(1 for r in 测试结果列表 
                  if any(d.get('维度') == 'D1' and d.get('结果') == '通过' 
                         for d in r.get('评分', {}).get('详情', [])))
    
    # 各维度统计
    维度统计 = {}
    for r in 测试结果列表:
        for d in r.get('评分', {}).get('详情', []):
            维度 = d.get('维度')
            if 维度 not in 维度统计:
                维度统计[维度] = {"通过": 0, "失败": 0}
            if d.get('结果') == '通过':
                维度统计[维度]["通过"] += 1
            else:
                维度统计[维度]["失败"] += 1
    
    报告 = {
        "测试版本": "V3.2.5",
        "测试时间": datetime.now().isoformat(),
        "输入目录": 输入目录,
        "测试样本数": 总计,
        "通过数": 通过数,
        "失败数": 总计 - 通过数,
        "整体通过率": f"{通过率:.1%}",
        "BUG-001修复验证": {
            "视频信息正确率": f"{d1通过数}/{总计} ({d1通过数/总计:.1%})" if 总计 > 0 else "N/A",
            "是否修复": "是" if d1通过数 == 总计 else "否"
        },
        "各维度统计": 维度统计,
        "详细结果": 测试结果列表
    }
    
    # 输出到控制台
    print("\n" + "=" * 70)
    print("PromptGenerator V3.2.5 回归测试报告")
    print("=" * 70)
    print(f"测试样本数: {总计}")
    print(f"通过数: {通过数}")
    print(f"失败数: {总计 - 通过数}")
    print(f"整体通过率: {通过率:.1%}")
    print("-" * 70)
    print("BUG-001修复验证:")
    print(f"  视频信息正确率: {报告['BUG-001修复验证']['视频信息正确率']}")
    print(f"  是否修复: {报告['BUG-001修复验证']['是否修复']}")
    print("-" * 70)
    print("各维度统计:")
    for 维度, 统计 in 维度统计.items():
        维度通过率 = 统计['通过'] / (统计['通过'] + 统计['失败']) if (统计['通过'] + 统计['失败']) > 0 else 0
        print(f"  {维度}: {统计['通过']}/{统计['通过'] + 统计['失败']} ({维度通过率:.0%})")
    print("=" * 70)
    
    # 失败项详情
    失败项 = [r for r in 测试结果列表 if not r.get('评分', {}).get('是否通过', False)]
    if 失败项:
        print("\n失败项详情:")
        for r in 失败项:
            print(f"\n  [{r['序号']}] {r['文件名']}")
            print(f"      作者: {r['video_data'].get('作者', 'N/A')}")
            print(f"      总分: {r['评分']['总分']}")
            for d in r['评分']['详情']:
                if d['结果'] == '失败':
                    print(f"      - {d['维度']} {d['检查项']}: {d['说明']}")
    
    # 保存到文件
    if 输出文件:
        with open(输出文件, 'w', encoding='utf-8') as f:
            json.dump(报告, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存: {输出文件}")
    
    return 报告


def main():
    parser = argparse.ArgumentParser(description='PromptGenerator V3.2.5 回归测试')
    parser.add_argument('--input-dir', '-i', required=True, help='历史记录目录')
    parser.add_argument('--limit', '-l', type=int, default=10, help='测试样本数量（默认10）')
    parser.add_argument('--output', '-o', help='输出报告文件路径')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不调用LLM')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("PromptGenerator V3.2.5 回归测试")
    print("=" * 70)
    print(f"输入目录: {args.input_dir}")
    print(f"测试数量: {args.limit}")
    print(f"模拟模式: {args.dry_run}")
    print("=" * 70)
    
    # 1. 加载历史记录
    print("\n[1/4] 加载历史记录...")
    记录列表 = 加载历史记录(args.input_dir, args.limit)
    print(f"      成功加载 {len(记录列表)} 条记录")
    
    if not 记录列表:
        print("[错误] 没有加载到任何记录，退出")
        return
    
    # 2. 生成新评论
    print(f"\n[2/4] 使用 V3.2.5 生成新提示词和评论...")
    if args.dry_run:
        print("      [模拟模式] 不调用LLM API")
    
    测试结果列表 = []
    for i, 记录 in enumerate(记录列表, 1):
        print(f"\n      处理 {i}/{len(记录列表)}: {记录['文件名']}")
        print(f"      作者: {记录['video_data'].get('作者', 'N/A')}")
        print(f"      目标描述: {记录['目标描述'][:50]}...")
        
        新结果 = 生成新评论(记录['video_data'], 记录['目标描述'], args.dry_run)
        
        if 新结果.get('是否模拟'):
            print(f"      [模拟] 评论: {新结果['评论'][:50]}...")
        else:
            print(f"      新评论: {新结果['评论'][:50]}...")
        
        # 评分
        评分结果 = 评分(新结果, 记录['video_data'])
        print(f"      评分: {评分结果['总分']}/100 ({'通过' if 评分结果['是否通过'] else '失败'})")
        
        测试结果列表.append({
            '序号': i,
            '文件名': 记录['文件名'],
            'video_data': 记录['video_data'],
            '目标描述': 记录['目标描述'],
            '新结果': 新结果,
            '评分': 评分结果
        })
    
    # 3. 生成报告
    print(f"\n[3/4] 生成测试报告...")
    生成报告(测试结果列表, args.output, args.input_dir)
    
    # 4. 结论
    print(f"\n[4/4] 测试完成")
    d1通过数 = sum(1 for r in 测试结果列表 
                  if any(d.get('维度') == 'D1' and d.get('结果') == '通过' 
                         for d in r.get('评分', {}).get('详情', [])))
    
    if d1通过数 == len(测试结果列表):
        print("\n✅ BUG-001 修复验证: 通过（所有视频信息正确）")
    else:
        print(f"\n❌ BUG-001 修复验证: 失败（{d1通过数}/{len(测试结果列表)} 视频信息正确）")


if __name__ == '__main__':
    main()
