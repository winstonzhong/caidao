# -*- coding: utf-8 -*-
"""
制图描述提示词生成模块
调用 GLOBAL_REDIS 来生成图像/制图的描述提示词
"""

import json
import time
from typing import Optional, List, Dict, Any

from helper_task_redis2 import GLOBAL_REDIS


# 默认的图像生成系统提示词
DEFAULT_IMAGE_SYS_PROMPT = """你是一位专业的AI图像提示词工程师。你的任务是根据用户的描述，生成高质量、详细的图像生成提示词。

请遵循以下规则：
1. 将用户的简单描述扩展为详细、生动的图像描述
2. 包含风格、光线、色彩、构图、细节等要素
3. 使用英文输出（大多数AI绘图模型对英文理解更好）
4. 提示词应该具体、清晰，避免模糊词汇
5. 可以添加适当的艺术风格修饰词

输出格式：直接输出优化后的提示词文本，不需要解释。"""


class ImagePromptGenerator:
    """图像提示词生成器"""
    
    def __init__(self, redis_handler=GLOBAL_REDIS):
        """
        初始化图像提示词生成器
        
        Args:
            redis_handler: Redis任务处理器，默认使用 GLOBAL_REDIS
        """
        self.redis = redis_handler
    
    def generate_prompt(
        self,
        description: str,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        timeout: int = 60,
        **extra_params
    ) -> Dict[str, Any]:
        """
        生成图像描述提示词
        
        Args:
            description: 用户的图像描述
            style: 图像风格（如：写实、动漫、油画、水彩等）
            aspect_ratio: 图像比例（如：16:9, 1:1, 9:16 等）
            timeout: 超时时间（秒）
            **extra_params: 其他额外参数
            
        Returns:
            包含生成结果的字典
        """
        # 构建问题描述
        question = f"请为以下描述生成专业的AI绘图提示词：\n\n描述：{description}"
        
        if style:
            question += f"\n风格要求：{style}"
        if aspect_ratio:
            question += f"\n图像比例：{aspect_ratio}"
        
        # 生成唯一的回调key
        key_back = f"image_prompt_result:{int(time.time() * 1000)}"
        
        # 提交任务并等待结果
        result = self.redis.提交数据并阻塞等待结果(
            key_back=key_back,
            sys_prompt=DEFAULT_IMAGE_SYS_PROMPT,
            question=question,
            timeout=timeout,
            **extra_params
        )
        
        return result
    
    def generate_prompts_batch(
        self,
        descriptions: List[str],
        style: Optional[str] = None,
        timeout: int = 120
    ) -> List[Dict[str, Any]]:
        """
        批量生成图像描述提示词
        
        Args:
            descriptions: 用户图像描述列表
            style: 图像风格
            timeout: 每个任务的超时时间（秒）
            
        Returns:
            生成结果列表
        """
        results = []
        for desc in descriptions:
            result = self.generate_prompt(description=desc, style=style, timeout=timeout)
            results.append(result)
        return results
    
    def generate_prompt_with_template(
        self,
        description: str,
        template: str,
        variables: Optional[Dict[str, str]] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        使用自定义模板生成图像描述提示词
        
        Args:
            description: 用户的图像描述
            template: 自定义提示词模板
            variables: 模板变量替换字典
            timeout: 超时时间（秒）
            
        Returns:
            包含生成结果的字典
        """
        # 替换模板变量
        sys_prompt = template
        if variables:
            for key, value in variables.items():
                sys_prompt = sys_prompt.replace(f"{{{key}}}", value)
        
        key_back = f"image_prompt_result:{int(time.time() * 1000)}"
        
        result = self.redis.提交数据并阻塞等待结果(
            key_back=key_back,
            sys_prompt=sys_prompt,
            question=f"请为以下描述生成图像提示词：\n\n{description}",
            timeout=timeout
        )
        
        return result


# 全局实例
generator = ImagePromptGenerator()


def generate_image_prompt(
    description: str,
    style: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    timeout: int = 60
) -> str:
    """
    便捷函数：生成图像描述提示词
    
    Args:
        description: 用户的图像描述
        style: 图像风格
        aspect_ratio: 图像比例
        timeout: 超时时间（秒）
        
    Returns:
        生成的提示词文本（如果失败返回空字符串）
    """
    result = generator.generate_prompt(
        description=description,
        style=style,
        aspect_ratio=aspect_ratio,
        timeout=timeout
    )
    
    if result and result.get("result"):
        return result["result"]
    return ""


def generate_prompts_batch(
    descriptions: List[str],
    style: Optional[str] = None,
    timeout: int = 120
) -> List[str]:
    """
    便捷函数：批量生成图像描述提示词
    
    Args:
        descriptions: 用户图像描述列表
        style: 图像风格
        timeout: 每个任务的超时时间（秒）
        
    Returns:
        生成的提示词文本列表
    """
    results = generator.generate_prompts_batch(
        descriptions=descriptions,
        style=style,
        timeout=timeout
    )
    
    return [r.get("result", "") for r in results if r and r.get("result")]


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("测试图像提示词生成模块")
    print("=" * 60)
    
    # 测试1：单条提示词生成
    print("\n【测试1】单条提示词生成")
    test_description = "一只可爱的橘猫在窗台上晒太阳"
    print(f"输入描述: {test_description}")
    
    try:
        result = generator.generate_prompt(
            description=test_description,
            style="写实风格",
            aspect_ratio="16:9"
        )
        print(f"返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")
    
    # 测试2：使用便捷函数
    print("\n【测试2】使用便捷函数")
    try:
        prompt = generate_image_prompt(
            description="星空下的古城",
            style="油画风格",
            timeout=30
        )
        print(f"生成的提示词: {prompt}")
    except Exception as e:
        print(f"测试失败: {e}")
    
    # 测试3：批量生成
    print("\n【测试3】批量生成")
    test_descriptions = [
        "樱花树下的少女",
        "未来城市夜景",
        "山间小溪流水"
    ]
    try:
        results = generate_prompts_batch(
            descriptions=test_descriptions,
            style="动漫风格",
            timeout=30
        )
        for i, (desc, prompt) in enumerate(zip(test_descriptions, results), 1):
            print(f"{i}. {desc} -> {prompt[:50] if prompt else '无结果'}...")
    except Exception as e:
        print(f"测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
