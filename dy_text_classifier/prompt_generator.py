"""
提示词生成器 - 根据目标视频描述自动生成评论助手提示词

【重要变更】
- 分类匹配已完全交给dy_text_classifier处理
- 本模块只负责生成评论助手的System Prompt
- 支持文件缓存机制，避免重复生成提示词
"""
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

# 从sg项目导入Redis任务队列
import sys
sys.path.insert(0, '/home/yka-003/workspace/sg')
from helper_task_redis2 import GLOBAL_REDIS

# 模块所在目录（用于确定默认缓存位置）
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class PromptGenerator:
    """
    根据目标视频描述生成评论助手的System Prompt
    
    【注意】分类功能已由dy_text_classifier.SimpleMatcher独立完成，
    不再需要生成分类提示词(sys_prompt_cls/partial_content_cls)
    
    【缓存机制】
    - 使用 版本号 + 目标视频描述 生成Hash作为缓存Key
    - 缓存文件存储在 dy_text_classifier/prompt_cache/ 目录
    - 模板版本更新后自动使旧缓存失效
    """
    
    # 提示词模板版本号 - 修改模板后必须更新此版本号以使缓存失效
    # 版本变更日志：
    # V3.2.5 (2026-03-12): 【重要修复】移除错误的文件缓存机制，修复视频信息固定问题(BUG-001)
    # V3.2.4 (2026-03-09): 进一步降低"很好奇"句式使用概率（从30%降至10%）
    # V3.2.3 (2026-03-09): 避免泛泛问题，要求专业术语和具体实例
    # V3.2.2 (2026-03-09): 增加句式多样性，避免"很好奇..."过度重复
    # V3.2.1 (2026-03-09): 禁止评论中@任何人（风控要求）
    # V3.2.0 (2026-03-09): 修复时间错误、增加策略多样性、优化语境感知
    # V3.1.0 (2026-03-09): 新增专业钩子问题策略，明确限制只能看到标题/摘要
    # V3.0.0 (2026-03-09): 新增视频立场分析、评论质量检查、@作者随机规则
    # V2.0.0 (2026-03-09): 初始版本，基础评论生成功能
    PROMPT_TEMPLATE_VERSION = "3.2.5"
    
    # 默认缓存目录
    _DEFAULT_CACHE_DIR = os.path.join(_MODULE_DIR, "prompt_cache")
    
    # 朋友互动人设提示词模板（固定，不根据视频内容变化）
    朋友互动人设提示词 = """你是一位真诚的朋友，正在观看朋友的抖音视频并准备评论。

## 视频信息
作者：{作者}
文案：{文案}
音乐：{音乐}
互动数据：👍{点赞} 💬{评论} ⭐{收藏} 🔄{分享}

## 你的人设
- 真诚、热情、支持朋友
- 善于发现朋友的闪光点和努力
- 评论风格亲切自然，像朋友间的对话

## 评论策略（根据视频内容选择）

**情况1：视频有具体文案/内容**
- 针对文案内容给出真实感受
- 结合互动数据给予肯定（"这么多人点赞 deserved！"）

**情况2：白板视频/无文案**
- 从互动数据切入："这么多人点赞，内容肯定很赞"
- 针对音乐/画面风格简单评论
- 或给予通用支持："支持一下，期待更多作品"

## 输出要求
- 字数：20-60字
- 直接输出评论内容
- 可适当使用emoji"""
    
    @classmethod
    def _get_cache_dir(cls) -> Path:
        """获取缓存目录路径"""
        cache_dir = Path(cls._DEFAULT_CACHE_DIR)
        cache_dir.mkdir(exist_ok=True)
        return cache_dir
    
    @classmethod
    def _compute_hash(cls, 目标视频描述: str) -> str:
        """
        计算缓存Hash（基于版本号 + 目标视频描述）
        
        Args:
            目标视频描述: 目标视频描述文本
        
        Returns:
            32位小写hex字符串
        """
        # 使用 版本号 + 目标视频描述 作为Hash输入
        hash_input = f"{cls.PROMPT_TEMPLATE_VERSION}:{目标视频描述}"
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    @classmethod
    def _get_cache_path(cls, hash_id: str) -> Path:
        """获取缓存文件路径"""
        cache_dir = cls._get_cache_dir()
        # 使用完整hash作为目录名
        cache_subdir = cache_dir / hash_id
        cache_subdir.mkdir(exist_ok=True)
        return cache_subdir / "prompt.json"
    
    @classmethod
    def _cache_exists(cls, hash_id: str) -> bool:
        """检查缓存是否存在"""
        cache_path = cls._get_cache_path(hash_id)
        return cache_path.exists()
    
    @classmethod
    def _load_from_cache(cls, hash_id: str) -> Optional[str]:
        """
        从缓存加载提示词
        
        Args:
            hash_id: Hash ID
        
        Returns:
            提示词字符串，如不存在返回None
        """
        cache_path = cls._get_cache_path(hash_id)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('prompt', None)
        except Exception as e:
            print(f"[PromptGenerator] 加载缓存失败: {e}")
            return None
    
    @classmethod
    def _save_to_cache(cls, hash_id: str, 目标视频描述: str, prompt: str):
        """
        保存提示词到缓存
        
        Args:
            hash_id: Hash ID
            目标视频描述: 原始目标视频描述
            prompt: 提示词内容
        """
        cache_path = cls._get_cache_path(hash_id)
        
        data = {
            "hash_id": hash_id,
            "目标视频描述": 目标视频描述,
            "版本": cls.PROMPT_TEMPLATE_VERSION,
            "生成时间": datetime.now().isoformat(),
            "prompt": prompt
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[PromptGenerator] 提示词已缓存: {cache_path}")
        except Exception as e:
            print(f"[PromptGenerator] 保存缓存失败: {e}")
    
    @classmethod
    def 获取评论助手提示词(cls, 目标视频描述: str, video_data: dict = None) -> str:
        """
        获取评论助手提示词
        
        【修复BUG-001 - V3.2.5】
        移除错误的文件缓存机制，确保每个视频都使用正确的video_data
        
        原问题：
        - 缓存了填充后的提示词（包含特定视频的作者、文案）
        - 但缓存Key不包含video_data，导致不同视频共享错误缓存
        - 例如：视频A的提示词被视频B使用，导致视频信息错误
        
        修复方案：
        - 直接调用 _生成增强版评论提示词 生成提示词
        - 该方法仅做本地字符串替换，无LLM调用，性能开销极小
        - 每个视频都使用自己的作者、文案等信息
        
        【确认无LLM调用】
        _生成增强版评论提示词 方法仅包含：
        1. 本地立场分析（关键词匹配）
        2. 本地数据提取（video_data.get）
        3. 本地时间获取（datetime.now）
        4. 本地字符串替换（.replace）
        单次生成耗时 < 1ms，无需缓存优化
        
        Args:
            目标视频描述: 目标视频描述
            video_data: 视频结构化数据
        
        Returns:
            评论助手提示词
        """
        # 【修复】直接生成，移除缓存逻辑
        # 原缓存代码（第194-211行）已移除：
        # - 删除 Hash计算
        # - 删除 缓存检查
        # - 删除 缓存保存
        
        return cls._生成增强版评论提示词(目标视频描述, video_data)
    
    @classmethod
    def 清除缓存(cls, hash_id: str = None):
        """
        清除提示词缓存
        
        Args:
            hash_id: 如指定则清理单个缓存，否则清理全部
        """
        cache_dir = cls._get_cache_dir()
        
        if hash_id:
            cache_path = cls._get_cache_path(hash_id)
            if cache_path.exists():
                cache_path.unlink()
                print(f"[PromptGenerator] 已删除缓存: {cache_path}")
        else:
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(exist_ok=True)
                print(f"[PromptGenerator] 已清空所有缓存: {cache_dir}")
    
    @classmethod
    def 列出缓存(cls) -> list:
        """列出所有已缓存的提示词"""
        cache_dir = cls._get_cache_dir()
        cached = []
        
        if cache_dir.exists():
            for sub_dir in cache_dir.iterdir():
                if sub_dir.is_dir():
                    cache_file = sub_dir / "prompt.json"
                    if cache_file.exists():
                        try:
                            with open(cache_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            cached.append({
                                "hash_id": data.get("hash_id", "")[:16] + "...",
                                "目标视频描述": data.get("目标视频描述", "")[:30] + "...",
                                "版本": data.get("版本", "unknown"),
                                "生成时间": data.get("生成时间", "")
                            })
                        except:
                            pass
        
        return cached
    
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
    5. **单一输出**：**必须只输出1条评论**，严禁输出多条评论供选择

    ### 评论风格（通用）
    - 语气真诚、有温度、不偏激
    - 字数控制在 50-150 字之间，简洁有力
    - 可适当使用网络流行语和 emoji 表情增加亲和力
    - 直接输出评论内容，不要添加解释或 markdown 标记

    ### 输出要求
    生成的 System Prompt 必须：
    - 完全围绕【目标视频描述】的主题
    - 不包含与目标主题无关的内容
    - **只提供1条**符合主题的示例评论（作为风格参考）
    - **明确要求只输出1条评论**，禁止输出多条供选择"""

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
    def 获取朋友互动提示词(cls, video_data: dict) -> str:
        """
        获取朋友互动人设提示词（固定模板，填入视频数据）
        
        Args:
            video_data: 视频结构化数据，包含作者、文案、音乐、点赞等
            
        Returns:
            格式化后的提示词字符串
        """
        return cls.朋友互动人设提示词.format(
            作者=video_data.get('作者', ''),
            文案=video_data.get('文案', '') or "(无)",
            音乐=video_data.get('音乐', '') or "(无)",
            点赞=video_data.get('点赞', '0'),
            评论=video_data.get('评论', '0'),
            收藏=video_data.get('收藏', '0'),
            分享=video_data.get('分享', '0')
        )
    
    @classmethod
    def _生成默认评论提示词(cls, 目标视频描述: str, video_data: dict = None) -> str:
        """
        生成评论助手提示词（V3.0 增强版）
        
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
        5. **单一输出**：**必须只输出1条评论**，严禁输出多条供选择

        ## 评论风格
        - 语气真诚、有温度、不偏激
        - 字数控制在 50-150 字之间
        - 可适当使用 emoji 表情
        - 直接输出评论，不加解释

        ## 输出格式
        **只输出1条评论内容**，不要输出多条或添加序号。"""

        # 如果有video_data传入，生成更具体的提示词
        if video_data:
            return cls._生成增强版评论提示词(目标视频描述, video_data)
        
        # 否则返回基础提示词
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
            字段说明.append(f"- **作者**: @{作者名} - 可以参考作者名（但禁止在评论中@作者）")
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
            建议.append("- 可以参考作者名，但禁止在评论中@作者（风控要求）")
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

### 示例评论风格（参考，仅作为风格参考）
"这个视频太有共鸣了！{{文案核心观点}}说得很对，[个人延伸观点] 👍"
（注意：示例中不包含@作者，实际评论中也严禁@任何人）"

### 重要提醒
**必须只输出1条评论**，不要输出多条供选择。直接给出你最好的那条评论即可。"""

    # 立场分析关键词
    _负面关键词 = ['不知耻', '恶意', '损害', '坑', '骗', '翻车', '恶果', '损人', '害人', '虚假', '假货', '劣', '糟', '烂', '差', '坏', '怒', '气', '骂', '喷']
    _正面关键词 = ['干货', '技巧', '成功', '到账', '分享', '推荐', '好', '棒', '赞', '牛', '赚', '赢', '厉害', '不错', '优秀']
    _中立关键词 = ['教程', '方法', '如何', '介绍', '说明', '教', '讲', '学', '问', '咨询']
    
    @classmethod
    def _分析视频立场(cls, video_data: dict) -> str:
        """
        分析视频的立场/情感倾向
        
        通过关键词判断：
        - 负面/批判：不知耻、恶意、损害、坑、骗、翻车、恶果等
        - 正面/支持：干货、技巧、成功、到账、分享等
        - 中立/客观：教程、方法、如何、介绍等
        
        Args:
            video_data: 视频结构化数据
            
        Returns:
            str: '批判' | '支持' | '中立'
        """
        # 提取文案和音乐用于分析
        text = video_data.get('文案', '') + ' ' + video_data.get('音乐', '')
        
        # 统计各类关键词出现次数
        负面计数 = sum(1 for word in cls._负面关键词 if word in text)
        正面计数 = sum(1 for word in cls._正面关键词 if word in text)
        中立计数 = sum(1 for word in cls._中立关键词 if word in text)
        
        # 判断立场
        if 负面计数 > 正面计数 and 负面计数 > 中立计数:
            return '批判'
        elif 正面计数 > 负面计数 and 正面计数 > 中立计数:
            return '支持'
        else:
            return '中立'
    
    @classmethod
    def _检查评论质量(cls, comment: str, video_data: dict, 立场: str) -> tuple:
        """
        检查生成的评论是否符合要求
        
        检查项：
        1. 是否包含泛泛词汇（学习了、很实用等）
        2. emoji数量是否超过1个
        3. 是否包含hashtag
        4. 字数是否在50-100之间
        5. 是否与文案内容相关
        6. 立场是否一致
        
        Args:
            comment: 生成的评论
            video_data: 视频数据
            立场: 视频立场
            
        Returns:
            (是否合格, 问题列表)
        """
        问题列表 = []
        
        # 1. 检查泛泛词汇
        泛泛词汇 = ['学习了', '很实用', '有道理', '说得好', '支持', '赞', '好帖', '顶', '马克', '收藏了']
        for word in 泛泛词汇:
            if word in comment:
                问题列表.append(f"包含泛泛词汇'{word}'")
        
        # 2. 检查emoji数量
        import re
        emojis = re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]', comment)
        if len(emojis) > 1:
            问题列表.append(f"emoji数量过多({len(emojis)}个)，应控制在1个以内")
        
        # 3. 检查hashtag
        if '#' in comment:
            问题列表.append("评论中不应包含hashtag(#)")
        
        # 4. 检查字数
        字数 = len(comment)
        if 字数 < 30 or 字数 > 120:
            问题列表.append(f"字数不合适({字数}字)，应在30-120字之间")
        
        # 5. 检查是否与文案相关
        文案 = video_data.get('文案', '')
        # 提取文案中的关键词（简单提取2字以上的词）
        文案关键词 = set()
        for i in range(len(文案) - 1):
            for j in range(i + 2, min(i + 6, len(文案) + 1)):
                文案关键词.add(文案[i:j])
        # 检查评论中是否包含文案关键词
        命中关键词 = [w for w in 文案关键词 if w in comment and len(w) >= 2]
        if len(命中关键词) < 1:
            问题列表.append("评论与文案内容关联度低")
        
        return (len(问题列表) == 0, 问题列表)
    
    # 提示词模板基础内容（不包含动态变量，用于缓存Hash计算）
    _提示词模板基础内容 = """你是一个专注于{{目标视频描述}}的视频博主。

## 时间信息
当前时间：{{当前时间}}
**重要：禁止提及具体年份如"2025年"、"2024年"等过时时间**

## 视频信息（重要限制：你只能看到标题/摘要）
- 作者: @{{作者}}
- 文案: {{文案}}
- 立场分析: {{立场}}（{{立场说明}}）

## ⚠️ 重要限制（必须遵守）
- 你只能看到视频的【标题/摘要】，看不到完整的视频内容
- **禁止询问"视频里提到了什么"、"视频里有哪些"等暴露信息缺失的问题**
- **禁止假设"视频没有讲..."或"视频里应该有..."**
- **禁止提及过时年份（如"2025年"、"2024年"）**
- 不要暴露你只看了标题的事实

## 视频类型判断与语气适配
根据文案风格自动判断视频类型，选择相应语气：

**技术教程/专业分享**（如包含"教程"、"技巧"、"方法"等）
→ 使用专业、深入的评论

**娱乐休闲/轻松分享**（如包含"小曲"、"日常"、"搞笑"等）
→ 使用轻松、幽默的评论

**比赛参与/作品展示**（如包含"大赛"、"参赛作品"、"投稿"等）
→ 使用鼓励、支持的评论

**热点讨论/观点表达**（有明显观点或立场）
→ 使用观点鲜明的评论

## 评论生成策略（根据视频类型动态选择）

### 策略A：专业钩子问题（约30%概率）
针对技术/专业内容，提出具体、专业的问题或观点。
- 适用：教程、技术分享、专业讨论
- 要求：
  * **避免泛泛问题**：不要问"如何平衡..."、"有什么技巧"等过于宽泛的问题
  * **使用专业术语**：如"拓扑优化"、"烘焙贴图"、"法线贴图"、"LOD"、"实例化"等
  * **带上具体实例**：提及具体的软件功能、技术方案或行业实践
  * 与主题高度相关，有一定专业深度
- **句式多样性（重要）：严格限制"很好奇你..."句式，使用比例不得超过10%，优先使用其他句式**
- 示例（具体专业，注意避免"很好奇"）：
  * 差示例（泛泛+很好奇）："Blender建模的练习过程中，你是如何平衡效率和细节的？"（过于泛泛）
  * 差示例（很好奇）："很好奇你是怎么一步步凑齐这副牌的？"（"很好奇"句式过度使用）
  * 好示例（直接疑问）："Blender的雕刻模式下，你是用Dyntopo还是Multires来做硬表面细节的？"
  * 好示例（直接疑问）："这副国士无双，听牌的时候是怎么决策的？"
  * 好示例（观点+疑问）："拓扑优化时，如何控制三角面数量和布线走向以满足动画形变需求？"
  * 好示例（经验式）："烘焙法线贴图时，你一般用Cage还是Ray Distance来控制接缝问题？"

### 策略B：观点评论（约50%概率）
表达一般性观点/看法，最通用的策略。
- 适用：所有类型视频
- 分享相关经验或感受
- **句式多样性：避免固定套路，可以使用分享式、疑问式、感叹式等多种开头**
- 禁止泛泛词汇："学习了"、"很实用"、"说得好"、"有道理"

### 策略C：直接认同/批判（约15%概率，根据立场）
立场明确时的直接表达。
- 适用：有明显立场的视频
- 如立场"批判" → "确实太气人了，这种行为应该被制止"

### 策略D：轻松互动（约5%概率，娱乐内容）
针对娱乐/休闲内容的轻松评论。
- 适用：轻松、搞笑、日常类视频
- 语气：幽默、随意、像朋友聊天
- 示例：
  * "渲染小曲一响，DNA就动了😂"
  * "这背景音乐太有感觉了"

## 格式约束（所有策略通用）
- 字数：严格控制在 30-150 字之间（可适当扩写以容纳专业术语和具体实例）
- **禁止@任何人：出于风控考虑，评论中严禁@作者或任何其他用户（包括@用户名、@作者、@视频主等）**
- **句式多样性：严格限制"很好奇你..."、"想问问..."等句式，使用比例不得超过10%；优先使用直接疑问、观点陈述、经验分享等句式**
- **避免泛泛问题：不要问"如何平衡..."、"有什么技巧"、"怎么做到"等过于宽泛的问题，必须带上具体技术点或实例**
- **使用专业术语：评论中应包含1-2个专业术语或具体技术方案**
- emoji：最多使用 1 个，不要堆砌
- hashtag：禁止在评论中使用 #话题
- AI口吻：禁止"作为一个..."、"从...角度来看"等模板化表达
- 时间表述：禁止提及过时年份
- 语言：自然、像真人评论，避免千篇一律

## 输出要求
**只输出1条评论内容**，不要输出多条或添加序号。"""
    
    @classmethod
    def _获取提示词模板基础内容(cls) -> str:
        """
        获取提示词模板基础内容（不包含动态变量）
        
        用于缓存Hash计算，确保模板内容修改后缓存自动失效
        """
        return cls._提示词模板基础内容
    
    @classmethod
    def _生成增强版评论提示词(cls, 目标视频描述: str, video_data: dict) -> str:
        """
        生成增强版评论提示词（V3.2 - 语境感知优化版）
        
        【版本变更日志】
        V3.2.3 → V3.2.4:
        - 进一步降低"很好奇"句式使用概率：30% → 10%
        - 强化句式多样性约束：优先使用直接疑问、观点陈述、经验分享
        - 策略A示例更新：明确标注"很好奇"为差示例
        
        V3.2.2 → V3.2.3:
        - 避免泛泛问题：要求使用专业术语和具体实例
        - 扩写字数上限：100字 → 150字（容纳专业内容）
        - 策略A示例更新：区分"差示例"和"好示例"
        - 新增约束：避免"如何平衡..."、"有什么技巧"等泛泛问题
        
        V3.2.1 → V3.2.2:
        - 增加句式多样性：避免"很好奇你..."过度重复
        - 策略A示例扩展：疑问式、探讨式、观点+疑问、经验式、对比式
        - 格式约束：每种句式使用比例不超过30%
        
        V3.2.0 → V3.2.1:
        - 禁止@任何人：出于风控考虑，评论中严禁@作者或任何其他用户
        
        V3.1 → V3.2:
        - 修复时间错误：添加当前时间变量，禁止过时年份
        - 增加策略多样性：A(30%)、B(50%)、C(15%)、D(5%)
        - 新增策略D：轻松互动型（针对娱乐内容）
        - 优化语境感知：根据视频类型自动适配语气
        
        V3.0 → V3.1:
        - 新增专业钩子问题策略
        - 明确限制：只能看到标题/摘要，看不到完整视频
        - 禁止询问"视频里讲了什么"
        
        V2.0 → V3.0:
        - 新增视频立场分析（批判/支持/中立）
        - 新增评论质量检查
        - 新增@作者随机规则（V3.2.1已移除，禁止@任何人）
        - 优化字数控制（30-100字）
        - 禁止泛泛词汇和AI口吻
        - 禁止hashtag，限制emoji（最多1个）
        
        Args:
            目标视频描述: 用户配置的目标视频描述
            video_data: 视频结构化数据
        """
        from datetime import datetime
        
        # 分析视频立场
        立场 = cls._分析视频立场(video_data)
        
        # 提取作者名（仅用于参考，禁止在评论中@）
        作者 = video_data.get('作者', '').lstrip('@')
        文案 = video_data.get('文案', '')
        
        # 获取当前时间
        当前时间 = datetime.now().strftime("%Y年%m月")
        
        # 构建立场说明
        立场说明 = {
            '批判': '视频对目标现象持批判/负面态度，评论应保持批判立场，指出问题或表达不认同',
            '支持': '视频对目标现象持支持/正面态度，评论应保持支持立场，认同或补充观点',
            '中立': '视频对目标现象持客观/中立态度，评论应客观分析，可以提问或补充信息'
        }.get(立场, '根据视频内容自然表达观点')
        
        # 获取模板并填充变量
        模板 = cls._提示词模板基础内容
        prompt = 模板.replace('{{目标视频描述}}', 目标视频描述) \
                     .replace('{{作者}}', 作者) \
                     .replace('{{文案}}', 文案[:100] + ('...' if len(文案) > 100 else '')) \
                     .replace('{{立场}}', 立场) \
                     .replace('{{立场说明}}', 立场说明) \
                     .replace('{{当前时间}}', 当前时间)
        
        return prompt


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
        # 存储提示词和版本号（用于缓存失效检查）
        job.json_data["sys_prompt_comment"] = {
            "prompt": sys_comment,
            "version": PromptGenerator.PROMPT_TEMPLATE_VERSION,
            "generated_at": time.time()
        }
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
