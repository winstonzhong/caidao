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
    def _生成默认评论提示词(cls, 目标视频描述: str) -> str:
        """生成评论助手提示词（备用方案）"""
        return f"""你是一个专注于{目标视频描述}的视频博主，热衷于在该领域分享观点和经验。

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
    # 测试用例
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
