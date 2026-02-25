# encoding: utf-8
"""
同义词生成工具模块 (增强版)

支持从文本描述中提取关键词，生成带权重的同义词库。
用于支持文本分类器的关键词扩展。

核心特性:
1. 文本分词 + 停用词过滤 → 提取核心关键词
2. 为每个关键词生成同义词，带权重区分（原始词权重 > 扩展词权重）
3. 自动过滤包含关系的重复词（如"拼多多"和"拼多多购物"去重）
4. 支持短语/长文本输入

用法:
    >>> from helper_synonym import 生成关键词库
    >>> result = 生成关键词库("拼多多购物平台，优惠多多")
    >>> print(result)
    {
        '核心词': {'拼多多': 1.0, '购物': 1.0, '平台': 1.0, '优惠': 1.0},
        '扩展词': {'PDD': 0.6, '拼夕夕': 0.6, '网购': 0.6, '折扣': 0.6}
    }

依赖:
    - helper_task_redis2.py 中的 GLOBAL_REDIS
    - jieba (中文分词)
"""

import json
import re
import time
import random
import uuid
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, asdict

# 导入 Redis 任务处理器
try:
    from helper_task_redis2 import GLOBAL_REDIS
except ImportError:
    GLOBAL_REDIS = None
    print("警告: 无法导入 GLOBAL_REDIS，同义词生成功能将不可用")

# 尝试导入jieba分词
try:
    import jieba
    import jieba.posseg as pseg
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("警告: jieba未安装，将使用简单分词。建议: pip install jieba")


# ============== 停用词表 ==============
# 常见的无意义词汇，在分词后过滤掉
DEFAULT_STOPWORDS = {
    '的', '了', '和', '是', '在', '有', '我', '都', '个', '与', '也', '对',
    '为', '能', '很', '可以', '就', '不', '会', '要', '没有', '我们的',
    '这个', '上', '他', '而', '及', '与', '或', '但是', '因为', '所以',
    '如果', '那么', '虽然', '但是', '然而', '而且', '并且', '或者', '还是',
    '等', '等等', '之类', '之一', '一下', '一些', '一下', '一种', '第一',
    '对于', '关于', '由于', '根据', '按照', '通过', '经过', '随着', '为了',
    '为着', '除了', '除开', '除去', '有关', '相关', '涉及', '至于', '就是',
    '即', '便', '即使', '哪怕', '尽管', '不管', '无论', '不要', '不能',
    '不会', '不可', '不得', '不必', '不用', '应该', '应当', '应', '须',
    '必须', '必要', '需要', '得', '需', '须得', '别', '不要', '毋', '勿',
    '不', '没', '没有', '未', '无', '非', '莫', '勿', '别', '甭', '不必',
    '未必', '也许', '或许', '大概', '大约', '约', '差不多', '几乎', '简直',
    '根本', '决', '绝对', '完全', '都', '全', '总', '一概', '一律', '总是',
    '一直', '一向', '从来', '始终', '毕竟', '究竟', '到底', '终归', '终究',
    '结果', '后果', '成果', '然后', '而后', '之后', '后来', '随即', '随手',
    '随手', '立刻', '立即', '马上', '赶紧', '赶快', '连忙', '急忙', '匆忙',
    '仓促', '临时', '暂时', '暂', '且', '姑且', '权且', '且慢', '慢说',
    '别说', '不但', '不仅', '不只', '不光', '不单', '不独', '而且', '并且',
    '况且', '何况', '再说', '再者', '否则', '不然', '要不', '要不然',
    '要么', '因为', '由于', '因此', '因而', '从而', '于是', '所以', '可见',
    '足见', '以致', '以至于', '以至', '直到', '甚至', '甚而', '乃至', '以及',
    '和', '跟', '同', '与', '及', '而', '或', '或者', '还是', '既', '既然',
    '基于', '鉴于', '问', '请问', '借问', '请问', '请问', '请问', '敢问',
    '请问', '请问', '请问', '请问', '请问', '请问', '请问', '请问', '请问',
}


# ============== 系统提示词 ==============
# 用于指导LLM批量生成同义词
SYS_PROMPT_BATCH_SYNONYM = """你是一个专业的关键词同义词生成助手。

任务：为给定的关键词列表中的**每个词**生成同义词、近义词、变体词或相关表达。

输入：关键词列表（已过滤停用词）
输出：JSON格式，每个关键词对应一个同义词列表

生成规则（按优先级排序）：
1. **常用缩写/简写**：如"拼多多"→"PDD"、"电子商务"→"电商"
2. **口语化/网络用语**：如"拼多多"→"拼夕夕"、"购物"→"买买买"
3. **同义词替换**：如"优惠"→"折扣"、"便宜"→"实惠"
4. **相关概念**：如"购物"→"网购"、"消费"
5. **英文表达**：如"直播"→"live"、"streaming"

重要约束：
- **不要生成包含原词的短语**（如"拼多多"的扩展词不能有"拼多多购物"）
- **不要生成被原词包含的词**（如"电商"的扩展词不能有"商"）
- 每个关键词生成3-6个同义词，不要过多
- 只返回JSON，不要解释

返回格式：
{"同义词库": {"关键词1": ["同义词1", "同义词2", ...], "关键词2": ["同义词1", ...], ...}}
"""

# 用于从文本描述提取关键词
SYS_PROMPT_EXTRACT = """你是一个关键词提取专家。

任务：从给定的文本描述中提取核心关键词/关键短语。

提取规则：
1. 提取有实际意义的名词、动词、专有名词
2. 去除停用词（的、了、是、在等）
3. 保留业务相关的专业术语
4. 如果文本已经很短（≤4个字），直接作为关键词返回
5. 关键词长度建议2-6个字，不要太长

返回格式：
{"关键词": ["词1", "词2", "词3", ...]}
"""


@dataclass
class SynonymResult:
    """同义词生成结果数据结构"""
    原始词: str
    同义词列表: List[str]
    带权重的词库: Dict[str, float]  # 词 -> 权重
    
    def to_dict(self) -> dict:
        return asdict(self)


# ============== 文本预处理 ==============

def 简单分词(文本: str) -> List[str]:
    """
    简单的基于规则的分词（当jieba不可用时使用）
    
    按非中文字符分割，保留2字以上的词
    """
    # 清理文本
    文本 = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', 文本)
    # 简单的N-gram分词（2-4字）
    文本 = 文本.strip()
    结果 = []
    
    # 滑动窗口提取词
    for length in range(4, 1, -1):  # 优先长词
        i = 0
        while i <= len(文本) - length:
            词 = 文本[i:i+length]
            if not any(s in 词 for s in [' ', '\n', '\t']):
                结果.append(词)
            i += length if length > 2 else 1
    
    # 去重并保持顺序
    seen = set()
    去重结果 = []
    for 词 in 结果:
        if 词 not in seen and len(词) >= 2:
            seen.add(词)
            去重结果.append(词)
    
    return 去重结果[:10]  # 限制数量


def 分词并过滤(文本: str, 停用词: Optional[Set[str]] = None) -> List[str]:
    """
    对输入文本进行分词并过滤停用词
    
    Args:
        文本: 输入文本描述
        停用词: 自定义停用词集合，默认使用内置停用词表
    
    Returns:
        过滤后的关键词列表
    
    Examples:
        >>> words = 分词并过滤("拼多多购物平台优惠多多")
        >>> len(words) > 0
        True
        >>> all(len(w) >= 2 for w in words)
        True
    """
    if not 文本 or not isinstance(文本, str):
        return []
    
    停用词 = 停用词 or DEFAULT_STOPWORDS
    文本 = 文本.strip()
    
    # 如果文本很短，直接返回
    if len(文本) <= 4:
        return [文本] if 文本 not in 停用词 else []
    
    if JIEBA_AVAILABLE:
        # 使用jieba分词，保留名词、动词、形容词
        words = []
        for word, flag in pseg.cut(文本):
            # 保留: n(名词), v(动词), a(形容词), ns(地名), nr(人名), nt(机构名), nw(新词)
            if (flag.startswith(('n', 'v', 'a')) or flag in ['ns', 'nr', 'nt', 'nw', 'nz']) \
               and len(word) >= 2 \
               and word not in 停用词:
                words.append(word)
        
        # 如果没有提取到词，尝试提取所有非停用词
        if not words:
            words = [w for w in jieba.lcut(文本) if len(w) >= 2 and w not in 停用词]
        
        return words
    else:
        # 使用简单分词
        return 简单分词(文本)


def 提取关键词(文本: str, top_k: int = 5) -> List[str]:
    """
    从文本中提取最重要的关键词
    
    如果jieba可用，使用TF-IDF提取关键词；否则使用简单规则
    
    Args:
        文本: 输入文本
        top_k: 返回关键词数量
    
    Returns:
        关键词列表
    """
    if not 文本:
        return []
    
    文本 = 文本.strip()
    
    # 短文本直接返回
    if len(文本) <= 6:
        return [文本]
    
    if JIEBA_AVAILABLE:
        try:
            import jieba.analyse
            # 使用TF-IDF提取关键词
            keywords = jieba.analyse.extract_tags(文本, topK=top_k, withWeight=False)
            return keywords if keywords else 分词并过滤(文本)[:top_k]
        except:
            pass
    
    # 回退到简单分词
    return 分词并过滤(文本)[:top_k]


# ============== 包含关系检测 ==============

def 是包含关系(短词: str, 长词: str) -> bool:
    """
    检查两个词是否存在包含关系
    
    Args:
        短词: 较短的词
        长词: 较长的词
    
    Returns:
        如果短词被长词包含（且不是相等），返回True
    
    Examples:
        >>> 是包含关系("拼多多", "拼多多购物")
        True
        >>> 是包含关系("购物", "拼多多购物")
        True
        >>> 是包含关系("拼多多", "拼夕夕")
        False
        >>> 是包含关系("PDD", "pdd")
        False
    """
    if not 短词 or not 长词:
        return False
    
    短词, 长词 = 短词.lower().strip(), 长词.lower().strip()
    
    if 短词 == 长词:
        return False  # 相等不算包含
    
    # 检查短词是否在长词中
    return 短词 in 长词 or 长词 in 短词


def 过滤包含关系(词列表: List[str], 原始词: str) -> List[str]:
    """
    过滤掉与原始词有包含关系的词
    
    同时去除列表内部的包含关系（保留较短的词）
    
    Args:
        词列表: 待过滤的同义词列表
        原始词: 原始关键词（用于检查包含关系）
    
    Returns:
        过滤后的词列表
    
    Examples:
        >>> words = ["PDD", "拼多多购物", "拼夕夕", "多多"]
        >>> 过滤包含关系(words, "拼多多")
        ['PDD', '拼夕夕']
    """
    if not 词列表:
        return []
    
    # 第一步：过滤与原始词有包含关系的
    结果 = []
    for 词 in 词列表:
        词 = 词.strip()
        if not 词 or 词 == 原始词:
            continue
        if not 是包含关系(原始词, 词):
            结果.append(词)
    
    # 第二步：列表内部去包含（保留较短的）
    最终 = []
    for i, 词A in enumerate(结果):
        被包含 = False
        for j, 词B in enumerate(结果):
            if i != j and len(词B) > len(词A) and 词A in 词B:
                被包含 = True
                break
        if not 被包含:
            最终.append(词A)
    
    return 最终


# ============== API调用 ==============

def 生成唯一回调键() -> str:
    """
    生成全局唯一的回调队列键名
    
    使用 时间戳 + 随机数 + UUID 的组合确保唯一性，
    防止并发调用时串路。
    
    Returns:
        唯一的键名字符串，如 "synonym_1648623000_12345_a1b2c3d4"
    """
    时间戳 = int(time.time() * 1000)  # 毫秒级时间戳
    随机数 = random.randint(1000, 9999)
    短uuid = uuid.uuid4().hex[:8]
    return f"synonym_{时间戳}_{随机数}_{短uuid}"


def 批量调用同义词API(关键词列表: List[str], timeout: int = 120) -> Dict[str, List[str]]:
    """
    批量调用LLM API为多个关键词生成同义词
    
    一次性将所有关键词传给API，批量返回同义词，避免多次网络调用。
    
    Args:
        关键词列表: 需要生成同义词的关键词列表
        timeout: API超时时间（秒），批量调用适当增加超时
    
    Returns:
        字典，键为关键词，值为同义词列表
        如：{"拼多多": ["PDD", "拼夕夕"], "电商": ["网购", ...]}
    """
    if not GLOBAL_REDIS:
        print("错误: GLOBAL_REDIS 未初始化")
        return {}
    
    # 过滤无效关键词
    有效关键词 = [k.strip() for k in 关键词列表 if k and len(k.strip()) >= 2]
    if not 有效关键词:
        return {}
    
    try:
        # 生成唯一的回调键，防止并发串路
        key_back = 生成唯一回调键()
        
        # 构建问题：将关键词列表转为JSON格式
        question = json.dumps({"关键词列表": 有效关键词}, ensure_ascii=False)
        
        result = GLOBAL_REDIS.提交数据并阻塞等待结果(
            key_back=key_back,
            sys_prompt=SYS_PROMPT_BATCH_SYNONYM,
            question=question,
            partial_content='{"同义词库":',
            timeout=timeout
        )
        
        if result and result.get("result"):
            data = result["result"]
            
            # 解析结果
            if isinstance(data, dict):
                同义词库 = data.get("同义词库", {})
            elif isinstance(data, str):
                try:
                    parsed = json.loads(data)
                    同义词库 = parsed.get("同义词库", {})
                except json.JSONDecodeError:
                    return {}
            else:
                return {}
            
            # 清理和验证结果
            清理后的库 = {}
            for 关键词, 同义词列表 in 同义词库.items():
                if isinstance(同义词列表, list):
                    清理后的库[关键词] = [
                        str(w).strip() 
                        for w in 同义词列表 
                        if w and isinstance(w, (str, int, float))
                    ]
            
            return 清理后的库
        
        return {}
    
    except Exception as e:
        print(f"批量API调用失败: {e}")
        return {}


# ============== 主功能 ==============

def 批量生成同义词(
    关键词列表: List[str], 
    原始权重: float = 1.0, 
    扩展权重: float = 0.6
) -> Dict[str, SynonymResult]:
    """
    批量为多个关键词生成同义词库
    
    一次性API调用，为所有关键词生成同义词，效率远高于逐个调用。
    
    Args:
        关键词列表: 关键词列表
        原始权重: 原始关键词的匹配权重
        扩展权重: 扩展同义词的匹配权重
    
    Returns:
        字典，键为关键词，值为SynonymResult对象
    """
    if not 关键词列表:
        return {}
    
    # 批量调用API获取所有同义词（仅一次网络调用）
    批量同义词库 = 批量调用同义词API(关键词列表)
    
    # 构建结果
    结果 = {}
    for 关键词 in 关键词列表:
        关键词 = 关键词.strip()
        if not 关键词 or len(关键词) < 2:
            continue
        
        # 获取该词的同义词列表
        原始同义词 = 批量同义词库.get(关键词, [])
        
        # 过滤包含关系
        过滤后同义词 = 过滤包含关系(原始同义词, 关键词)
        
        # 构建带权重的词库
        词库 = {关键词: 原始权重}
        for 词 in 过滤后同义词:
            if 词 and 词 not in 词库:
                词库[词] = 扩展权重
        
        结果[关键词] = SynonymResult(
            原始词=关键词,
            同义词列表=过滤后同义词,
            带权重的词库=词库
        )
    
    return 结果


def 生成关键词库(
    文本描述: str,
    提取核心词: bool = True,
    原始权重: float = 1.0,
    扩展权重: float = 0.6,
    最大核心词数: int = 5
) -> Dict[str, Dict[str, float]]:
    """
    从文本描述生成完整的关键词库（带权重）
    
    这是主要入口函数，支持长文本输入，会自动分词、提取关键词、**一次性批量生成同义词**。
    无论有多少个关键词，只进行一次网络调用。
    
    Args:
        文本描述: 输入的文本描述（可以是长文本）
        提取核心词: 是否使用分词提取核心词，False则直接对原文本生成同义词
        原始权重: 核心词的匹配权重
        扩展权重: 扩展同义词的匹配权重
        最大核心词数: 最多处理多少个核心词（控制API调用复杂度）
    
    Returns:
        分层的关键词库：
        {
            '核心词': {词: 权重, ...},  # 从文本提取的关键词
            '扩展词': {词: 权重, ...}   # AI生成的同义词
        }
    
    Examples:
        >>> # 长文本输入（批量生成，仅一次API调用）
        >>> result = 生成关键词库("拼多多购物平台，优惠多多，低价好物")
        >>> '核心词' in result and '扩展词' in result
        True
        
        >>> # 短文本/单个词
        >>> result = 生成关键词库("拼多多", 提取核心词=False)
        >>> '拼多多' in result['核心词']
        True
    """
    if not 文本描述 or not isinstance(文本描述, str):
        return {'核心词': {}, '扩展词': {}}
    
    文本描述 = 文本描述.strip()
    
    # 确定核心关键词列表
    if 提取核心词 and len(文本描述) > 4:
        核心词列表 = 提取关键词(文本描述, top_k=最大核心词数)
    else:
        核心词列表 = [文本描述]
    
    if not 核心词列表:
        return {'核心词': {}, '扩展词': {}}
    
    # 清理核心词
    有效核心词 = [k.strip() for k in 核心词列表 if k and len(k.strip()) >= 2]
    if not 有效核心词:
        return {'核心词': {}, '扩展词': {}}
    
    # 构建核心词权重映射
    所有核心词 = {词: 原始权重 for 词 in 有效核心词}
    
    # **一次性批量生成所有同义词**（仅一次网络调用！）
    批量结果 = 批量生成同义词(有效核心词, 原始权重, 扩展权重)
    
    # 收集扩展词
    所有扩展词 = {}
    for 核心词, 同义词结果 in 批量结果.items():
        for 词, 权重 in 同义词结果.带权重的词库.items():
            if 词 == 核心词 or 词 in 所有核心词:
                continue
            
            # 检查是否与其他核心词有包含关系
            有冲突 = False
            for 已有核心词 in 所有核心词:
                if 是包含关系(词, 已有核心词) or 是包含关系(已有核心词, 词):
                    有冲突 = True
                    break
            
            if not 有冲突:
                # 如果词已存在，保留较高权重
                if 词 in 所有扩展词:
                    所有扩展词[词] = max(所有扩展词[词], 权重)
                else:
                    所有扩展词[词] = 权重
    
    return {
        '核心词': 所有核心词,
        '扩展词': 所有扩展词
    }


def 获取匹配词字典(
    文本描述: str,
    提取核心词: bool = True,
    扩展权重: float = 0.6,
    总词数: int = 20
) -> Dict[str, float]:
    """
    从文本描述生成匹配词字典（扁平化，原词权重为1，扩展词权重为指定值）
    
    这是用于关键词匹配的简化接口，直接返回 {词: 权重} 字典。
    原词（核心词）权重固定为1.0，扩展同义词权重为指定的扩展权重。
    
    注意：核心词数会动态计算，以确保最终返回的词数尽量接近指定的总词数。
    核心词占总词数的约1/4（向上取整），剩余为扩展词。
    
    Args:
        文本描述: 输入的文本描述（可以是长文本）
        提取核心词: 是否使用分词提取核心词
        扩展权重: 扩展同义词的权重（默认0.6）
        总词数: 期望返回的词汇总数（包括核心词和扩展词），用于统一评估基准
    
    Returns:
        扁平化的匹配词字典，如：
        {'拼多多': 1.0, '购物': 1.0, 'PDD': 0.6, '拼夕夕': 0.6, '网购': 0.6}
    
    Examples:
        >>> result = 获取匹配词字典("拼多多购物", 总词数=10)
        >>> '拼多多' in result
        True
        >>> result['拼多多']  # 原词权重为1
        1.0
        >>> len(result) <= 10  # 不超过指定的总词数
        True
    """
    # 动态计算核心词数（约占总词数的1/4，至少1个）
    核心词数 = max(1, (总词数 + 3) // 4)
    
    # 先生成分层的关键词库
    词库 = 生成关键词库(
        文本描述=文本描述,
        提取核心词=提取核心词,
        原始权重=1.0,  # 原词固定权重为1
        扩展权重=扩展权重,
        最大核心词数=核心词数
    )
    
    # 合并核心词和扩展词为扁平字典
    匹配词字典 = {}
    匹配词字典.update(词库.get('核心词', {}))
    匹配词字典.update(词库.get('扩展词', {}))
    
    # 按权重降序排序，确保优先保留高权重词
    排序后的词 = sorted(匹配词字典.items(), key=lambda x: x[1], reverse=True)
    
    # 截断到指定的总词数
    匹配词字典 = dict(排序后的词[:总词数])
    
    return 匹配词字典


def 合并词库(词库列表: List[Dict[str, Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
    """
    合并多个词库，处理权重冲突
    
    当同一个词出现在多个词库时，取最高权重
    
    Args:
        词库列表: 多个生成关键词库的结果
    
    Returns:
        合并后的词库
    """
    合并核心词 = {}
    合并扩展词 = {}
    
    for 词库 in 词库列表:
        for 词, 权重 in 词库.get('核心词', {}).items():
            if 词 in 合并核心词:
                合并核心词[词] = max(合并核心词[词], 权重)
            else:
                合并核心词[词] = 权重
        
        for 词, 权重 in 词库.get('扩展词', {}).items():
            if 词 in 合并扩展词:
                合并扩展词[词] = max(合并扩展词[词], 权重)
            elif 词 not in 合并核心词:  # 避免与核心词重复
                合并扩展词[词] = 权重
    
    return {
        '核心词': 合并核心词,
        '扩展词': 合并扩展词
    }


def 导出匹配规则(词库: Dict[str, Dict[str, float]]) -> List[Dict]:
    """
    将词库导出为分类器可用的匹配规则列表
    
    Returns:
        规则列表，每个规则包含词和权重：
        [
            {'词': '拼多多', '权重': 1.0, '类型': '核心词'},
            {'词': 'PDD', '权重': 0.6, '类型': '扩展词'},
            ...
        ]
    """
    规则列表 = []
    
    for 词, 权重 in 词库.get('核心词', {}).items():
        规则列表.append({'词': 词, '权重': 权重, '类型': '核心词'})
    
    for 词, 权重 in 词库.get('扩展词', {}).items():
        规则列表.append({'词': 词, '权重': 权重, '类型': '扩展词'})
    
    # 按权重降序排列
    规则列表.sort(key=lambda x: x['权重'], reverse=True)
    
    return 规则列表


# ============== 测试 ==============
if __name__ == "__main__":
    print("=" * 60)
    print("同义词生成工具")
    print("=" * 60)
    
    # 测试分词
    print("\n【测试分词】")
    test_texts = [
        "拼多多购物平台",
        "电商直播带货",
        "3D建模与渲染",
    ]
    
    for text in test_texts:
        words = 提取关键词(text)
        print(f"  输入: {text}")
        print(f"  关键词: {words}")
    
    # 测试包含关系检测
    print("\n【测试包含关系检测】")
    test_cases = [
        ("拼多多", "拼多多购物"),
        ("购物", "拼多多购物"),
        ("PDD", "pdd"),
        ("电商", "电商直播"),
    ]
    for a, b in test_cases:
        result = 是包含关系(a, b) or 是包含关系(b, a)
        print(f"  '{a}' 与 '{b}' 有包含关系: {result}")
    
    # 测试同义词生成（需要Redis）
    if GLOBAL_REDIS:
        print("\n【测试批量同义词生成】")
        test_words = ["拼多多", "电商", "直播"]
        
        # 使用批量生成（一次网络调用）
        批量结果 = 批量生成同义词(test_words)
        for word, result in 批量结果.items():
            print(f"\n  关键词: {word}")
            print(f"  扩展同义词: {result.同义词列表}")
            print(f"  带权重词库: {result.带权重的词库}")
        
        print("\n【测试长文本处理（分层词库）】")
        long_text = "拼多多购物平台，优惠多多，低价好物"
        result = 生成关键词库(long_text)
        print(f"  输入: {long_text}")
        print(f"  核心词: {result['核心词']}")
        print(f"  扩展词: {result['扩展词']}")
        
        print("\n【测试获取匹配词字典（总词数=15）】")
        match_dict = 获取匹配词字典(long_text, 总词数=15)
        print(f"  输入: {long_text}")
        print(f"  匹配词字典（总词数=15）: {match_dict}")
        print(f"  实际返回词数: {len(match_dict)}")
        
        print("\n【测试获取匹配词字典（总词数=10）】")
        match_dict_limited = 获取匹配词字典(long_text, 总词数=10)
        print(f"  输入: {long_text}")
        print(f"  匹配词字典（总词数=10）: {match_dict_limited}")
        print(f"  实际返回词数: {len(match_dict_limited)}")
    else:
        print("\nRedis未配置，跳过API调用测试")
    
    print("\n" + "=" * 60)
    print("执行完成")
