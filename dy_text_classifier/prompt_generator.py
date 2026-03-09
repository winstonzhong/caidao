"""
提示词生成器 - 根据目标视频描述自动生成评论助手提示词

【重要变更】
- 分类匹配已完全交给dy_text_classifier处理
- 本模块只负责生成评论助手的System Prompt
"""
import json
import time
from typing import Optional, Dict

# 从sg项目导入Redis任务队列
import sys
sys.path.insert(0, '/home/yka-003/workspace/sg')
from helper_task_redis2 import GLOBAL_REDIS


class PromptGenerator:
    """
    根据目标视频描述生成评论助手的System Prompt
    
    【注意】分类功能已由dy_text_classifier.SimpleMatcher独立完成，
    不再需要生成分类提示词(sys_prompt_cls/partial_content_cls)
    """
    
    # 通用评论生成指南（不含具体主题内容）
    COMMENT_GUIDELINES = """## 评论助手生成指南

### 人设定位原则
根据目标视频描述的主题，选择或定义合适的人设：
- 技术/教程类：热爱分享的技术爱好者、学习者、创作者
- 电商/消费类：理性消费者、经验分享者、避坑指南者
- 娱乐/游戏类：热情玩家、同好、圈内人
- 生活/日常类：生活记录者、经验交流者、情感共鸣者
- 知识/科普类：求知者、探讨者、知识分享者

### 评论要求（通用）
1. **相关性**：评论必须与视频内容紧密相关，不能泛泛而谈
2. **深度性**：要有观点、有态度，能引发思考，不是简单附和
3. **人设一致性**：评论风格要符合定义的人设定位
4. **互动性**：能引起视频作者和其他观众的注意和回应

### 评论风格（通用）
- 语气真诚、有温度、不偏激
- 字数控制在 50-150 字之间，简洁有力
- 可适当使用网络流行语和 emoji 表情增加亲和力
- 直接输出评论内容，不要添加解释或 markdown 标记

### 输出要求
生成的 System Prompt 必须：
- 完全围绕【目标视频描述】的主题
- 不包含与目标主题无关的内容
- 提供 2-3 条符合主题的示例评论"""

    # 用于让LLM生成评论助手提示词的System Prompt
    SYS_PROMPT_FOR_COMMENT = """你是一个专业的提示词工程师，擅长为AI助手生成高质量的System Prompt。

你的任务是根据用户提供的【目标视频描述】，生成一个用于抖音视频评论的AI助手系统提示词。

## 关键要求（必须遵守）

1. **完全基于目标视频描述**
   - 生成的提示词必须完全围绕用户提供的【目标视频描述】
   - 人设、分析维度、关键词、示例评论都必须符合目标描述的主题
   - 严禁引入与目标描述无关的内容

2. **人设定义**
   - 根据目标视频描述，定义一个合适的评论者人设
   - 人设要自然、真实，符合该领域的特点

3. **分析维度**
   - 根据目标主题，定义视频内容分析的关键维度
   - 例如：技术类关注技巧/难点，生活类关注情感/共鸣等

4. **示例评论**
   - 提供 2-3 条符合目标主题的示例评论
   - 示例要体现人设特点和评论风格

## 输出格式

直接输出生成的 System Prompt 文本，不需要额外的解释或 markdown 标记。"""

    @classmethod
    def 生成评论助手提示词(cls, 目标视频描述: str) -> str:
        """
        根据目标视频描述生成评论助手的System Prompt
        
        Args:
            目标视频描述: 用户配置的目标视频描述
            
        Returns:
            sys_prompt_comment: 用于生成评论的系统提示词
        """
        question = f"""请为以下目标视频描述生成评论助手的 System Prompt：

【目标视频描述】
{目标视频描述}

【生成指南】
{cls.COMMENT_GUIDELINES}

【重要提醒】
1. 评论助手的人设必须完全基于"目标视频描述"的主题
2. 分析维度、关键词、场景描述都必须围绕"目标视频描述"
3. 提供的示例评论也必须符合"目标视频描述"的主题
4. 严禁包含任何与"目标视频描述"无关的内容
5. 生成的 System Prompt 应该可以直接使用，不需要额外修改

请直接输出生成的 System Prompt 文本。"""
        
        key_back = f"prompt_cmt_{int(time.time() * 1000)}"
        
        result = GLOBAL_REDIS.提交数据并阻塞等待结果(
            key_back=key_back,
            sys_prompt=cls.SYS_PROMPT_FOR_COMMENT,
            question=question
        )
        
        if result and result.get("result"):
            return result["result"]
        
        return cls._生成默认评论提示词(目标视频描述)
    
    @classmethod
    def _生成默认评论提示词(cls, 目标视频描述: str, video_data: dict = None) -> str:
        """
        生成评论助手提示词（备用方案）
        
        Args:
            目标视频描述: 用户配置的目标视频描述
            video_data: 视频结构化数据，包含作者、文案、点赞、评论等字段
        """
        # 基础提示词
        base_prompt = f"""你是一个专注于{目标视频描述}的视频博主，热衷于在该领域分享观点和经验。

## 你的核心人设
- 对该领域有深入了解和热情
- 善于发现内容的亮点和价值
- 乐于与创作者和观众互动交流

## 视频内容分析
用户将提供关于{目标视频描述}相关视频的描述，你需要：
- 理解视频的核心内容和价值点
- 识别视频的独特之处
- 判断内容的受众和场景

## 评论要求
1. **相关性**：评论必须与视频内容紧密相关
2. **深度性**：有观点、有态度，能引发思考
3. **人设一致性**：符合你的博主身份和专业度
4. **互动性**：能引起作者和其他观众的注意

## 评论风格
- 语气真诚、有温度、不偏激
- 字数控制在 50-150 字之间
- 可适当使用 emoji 表情
- 直接输出评论，不加解释

## 输出格式
直接输出评论内容。"""

        # 如果有video_data，添加结构化数据使用指南
        if video_data:
            structured_guide = cls._生成结构化数据使用指南(video_data)
            return base_prompt + "\n\n" + structured_guide
        
        return base_prompt
    
    @classmethod
    def _生成结构化数据使用指南(cls, video_data: dict) -> str:
        """
        根据video_data生成结构化数据使用指南
        告诉LLM可以利用哪些维度来生成更好的评论
        """
        # 构建可用字段说明
        字段说明 = []
        
        if video_data.get('作者'):
            作者名 = video_data['作者'].lstrip('@')
            字段说明.append(f"- **作者**: @{作者名} - 可以在评论中@作者或提及作者")
        if video_data.get('文案'):
            文案预览 = video_data['文案'][:50] + "..." if len(video_data['文案']) > 50 else video_data['文案']
            字段说明.append(f"- **文案**: {文案预览} - 核心内容，评论应围绕此展开")
        if video_data.get('音乐'):
            字段说明.append(f"- **音乐**: {video_data['音乐']} - 可以提及背景音乐")
        if video_data.get('点赞'):
            字段说明.append(f"- **点赞**: {video_data['点赞']} - 可以评论受欢迎程度")
        if video_data.get('评论'):
            字段说明.append(f"- **评论**: {video_data['评论']} - 可以提及讨论热度")
        if video_data.get('收藏'):
            字段说明.append(f"- **收藏**: {video_data['收藏']} - 可以表示内容有价值值得收藏")
        if video_data.get('分享'):
            字段说明.append(f"- **分享**: {video_data['分享']} - 可以提及内容的传播价值")
        if video_data.get('类型'):
            字段说明.append(f"- **类型**: {video_data['类型']} - 内容形式")
        
        字段说明文本 = "\n".join(字段说明) if 字段说明 else "（无具体字段信息）"
        
        # 生成使用建议
        建议 = []
        if video_data.get('作者'):
            建议.append("- 可以适当@作者，增加互动感")
        if video_data.get('文案'):
            建议.append("- 深入分析文案内容，提出有见地的观点")
        if video_data.get('点赞') and video_data.get('评论'):
            try:
                点赞数 = int(video_data['点赞'].replace(',', '').replace('w', '0000').replace('万', '0000'))
                评论数 = int(video_data['评论'].replace(',', '').replace('w', '0000').replace('万', '0000'))
                if 点赞数 > 1000:
                    建议.append("- 可以提及这个视频很受欢迎，表达共鸣")
                if 评论数 > 100:
                    建议.append("- 可以表示这个视频引发了热议")
            except:
                pass
        if video_data.get('收藏'):
            建议.append("- 可以表达这个内容值得收藏或已经收藏")
        
        建议文本 = "\n".join(建议) if 建议 else "- 根据视频内容自然发挥"
        
        return f"""## 结构化视频数据使用指南

### 可用数据字段
{字段说明文本}

### 评论生成建议
{建议文本}
- 结合数据字段和文案内容，生成有针对性、有深度的评论
- 评论要自然融入数据信息，不要生硬堆砌
- 可以引用文案中的观点或话题进行延伸讨论

### 示例评论风格（参考）
- "@作者 这个视频太有共鸣了！{{文案核心观点}}说得很对，[个人延伸观点] 👍"
- "{{点赞数}}个赞实至名归！关于[文案话题]我也有类似经历...[分享观点]"
- "看完这个视频真的[情感反应]，特别是[文案亮点]，值得收藏反复看！"""


def 更新任务提示词(job_id: int, 目标视频描述: str) -> bool:
    """
    当目标视频描述更新时，自动调用此函数生成并保存评论助手提示词
    
    流程：生成提示词 → 保存到数据库
    
    Args:
        job_id: 任务ID
        目标视频描述: 新的目标视频描述
        
    Returns:
        是否成功
    """
    try:
        # 步骤1：生成评论助手提示词（调用LLM）
        print(f"[Job {job_id}] 步骤1/2: 调用LLM生成提示词...")
        sys_comment = PromptGenerator.生成评论助手提示词(目标视频描述)
        
        # 步骤2：更新到数据库
        print(f"[Job {job_id}] 步骤2/2: 保存到数据库...")
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg.settings')
        import django
        django.setup()
        
        from tasks.models import Job
        
        job = Job.objects.get(id=job_id)
        job.json_data["sys_prompt_comment"] = sys_comment
        job.save(update_fields=['json_data'])
        
        print(f"[Job {job_id}] ✅ 提示词生成并保存完成")
        return True
    except Exception as e:
        print(f"[Job {job_id}] ❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
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
    
    parser = argparse.ArgumentParser(description='测试评论提示词生成器')
    parser.add_argument(
        '--with-video-data', '-v',
        action='store_true',
        help='使用带 video_data 的 _生成默认评论提示词 函数进行测试'
    )
    parser.add_argument(
        '--desc', '-d',
        type=str,
        default='拼多多维权、假货、薅羊毛',
        help='目标视频描述（默认：拼多多维权、假货、薅羊毛）'
    )
    parser.add_argument(
        '--full', '-f',
        action='store_true',
        help='显示完整的提示词（默认只显示前2000字符）'
    )
    
    args = parser.parse_args()
    
    if args.with_video_data:
        # 使用带 video_data 的测试
        print("\n" + "=" * 70)
        print("【测试】_生成默认评论提示词(目标描述, video_data)")
        print(f"【目标描述】{args.desc}")
        print("【video_data】")
        for k, v in DEFAULT_VIDEO_DATA.items():
            print(f"  {k}: {v}")
        print("=" * 70)
        
        sys_prompt = PromptGenerator._生成默认评论提示词(args.desc, DEFAULT_VIDEO_DATA)
        
        print("\n【生成的评论助手提示词】")
        if args.full:
            print(sys_prompt)
        else:
            print(sys_prompt[:2000], "..." if len(sys_prompt) > 2000 else "")
        print(f"\n【总长度】{len(sys_prompt)} 字符")
        print("\n" + "-" * 70)
    else:
        # 原有测试：使用 LLM 生成提示词（不带 video_data）
        test_cases = [
            ("Blender, 3D建模, 动漫, 游戏", "技术类：Blender/3D建模相关的评论助手"),
            ("拼多多维权、假货、薅羊毛", "电商类：电商维权相关的评论助手"),
            ("美食探店、烹饪教程", "生活类：美食相关的评论助手"),
        ]
        
        for desc, expected_theme in test_cases:
            print("\n" + "=" * 70)
            print(f"【测试】{expected_theme}")
            print(f"【输入】{desc}")
            print("=" * 70)
            
            sys_prompt = PromptGenerator.生成评论助手提示词(desc)
            
            print("\n【生成的评论助手提示词】")
            print(sys_prompt[:1000], "..." if len(sys_prompt) > 1000 else "")
            print(f"\n【总长度】{len(sys_prompt)} 字符")
            print("\n" + "-" * 70)
