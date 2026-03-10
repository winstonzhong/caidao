# encoding: utf-8
"""
同义词缓存管理器

职责：
1. 计算目标描述的MD5 Hash作为唯一标识
2. 检查本地缓存是否存在
3. 如不存在，调用API生成同义词库并保存
4. 如存在，直接读取本地缓存
"""

import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Set


# 模块所在目录（用于确定默认缓存位置）
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class SynonymCacheManager:
    """
    同义词缓存管理器
    
    职责：
    1. 计算目标描述的MD5 Hash作为唯一标识
    2. 检查本地缓存是否存在
    3. 如不存在，调用API生成同义词库并保存
    4. 如存在，直接读取本地缓存
    """
    
    # 同义词生成器版本号 - 修改生成逻辑后必须更新
    SYNONYM_GENERATOR_VERSION = "1.0.0"
    
    def __init__(self, cache_dir: str = "synonym_cache"):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径。如果是相对路径，则相对于当前模块所在目录。
                      默认为 "synonym_cache"
        """
        # 如果使用相对路径，则基于模块位置转换为绝对路径
        if not os.path.isabs(cache_dir):
            cache_dir = os.path.join(_MODULE_DIR, cache_dir)
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    @staticmethod
    def compute_hash(description: str) -> str:
        """
        计算目标描述的MD5 Hash（包含版本号）
        
        Args:
            description: 目标描述文本
        
        Returns:
            32位小写hex字符串
        """
        # 使用 版本号 + 目标描述 作为Hash输入
        hash_input = f"{SynonymCacheManager.SYNONYM_GENERATOR_VERSION}:{description}"
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    def get_cache_path(self, hash_id: str) -> Path:
        """获取缓存文件路径"""
        # 使用完整hash作为目录名
        cache_subdir = self.cache_dir / hash_id
        cache_subdir.mkdir(exist_ok=True)
        return cache_subdir / "synonyms.json"
    
    def exists(self, hash_id: str) -> bool:
        """检查缓存是否存在"""
        cache_path = self.get_cache_path(hash_id)
        return cache_path.exists()
    
    def load(self, hash_id: str) -> Optional[Dict[str, List[str]]]:
        """
        从缓存加载同义词库
        
        Args:
            hash_id: Hash ID
        
        Returns:
            同义词字典 {关键词: [同义词列表]}，如不存在返回None
        """
        cache_path = self.get_cache_path(hash_id)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('synonyms', {})
        except Exception as e:
            print(f"[SynonymCacheManager] 加载缓存失败: {e}")
            return None
    
    def save(self, hash_id: str, description: str, synonyms: Dict[str, List[str]]):
        """
        保存同义词库到缓存
        
        Args:
            hash_id: Hash ID
            description: 原始目标描述
            synonyms: 同义词字典 {关键词: [同义词列表]}
        """
        cache_path = self.get_cache_path(hash_id)
        
        # 计算统计信息
        total_words = len(synonyms)
        total_synonyms = sum(len(v) for v in synonyms.values())
        
        data = {
            "hash_id": hash_id,
            "目标描述": description,
            "版本": self.SYNONYM_GENERATOR_VERSION,
            "生成时间": datetime.now().isoformat(),
            "synonyms": synonyms,
            "统计信息": {
                "关键词数": total_words,
                "同义词总数": total_synonyms,
                "平均每词同义词数": round(total_synonyms / total_words, 2) if total_words > 0 else 0
            }
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[SynonymCacheManager] 同义词库已缓存: {cache_path}")
        except Exception as e:
            print(f"[SynonymCacheManager] 保存缓存失败: {e}")
    
    def get_or_create(
        self, 
        description: str,
        keywords: List[str] = None
    ) -> tuple:
        """
        获取或创建同义词库（核心方法）
        
        逻辑：
        1. 计算description的hash
        2. 检查缓存是否存在
        3. 存在则直接返回
        4. 不存在则调用API生成并缓存
        
        Args:
            description: 目标描述
            keywords: 关键词列表（如不提供则自动提取）
        
        Returns:
            (hash_id, synonyms_dict, is_from_cache)
        """
        # 1. 计算Hash
        hash_id = self.compute_hash(description)
        
        # 2. 检查缓存
        synonyms = self.load(hash_id)
        if synonyms is not None:
            print(f"[SynonymCacheManager] 命中缓存: {hash_id[:8]}...")
            return hash_id, synonyms, True
        
        # 3. 缓存未命中，调用API生成
        print(f"[SynonymCacheManager] 缓存未命中，生成同义词库: {hash_id[:8]}...")
        
        synonyms = self._generate_synonyms(description, keywords)
        
        # 4. 保存到缓存
        self.save(hash_id, description, synonyms)
        
        return hash_id, synonyms, False
    
    def _generate_synonyms(
        self, 
        description: str,
        keywords: List[str] = None
    ) -> Dict[str, List[str]]:
        """
        调用API生成同义词库
        
        Args:
            description: 目标描述
            keywords: 关键词列表（如不提供则自动提取）
        
        Returns:
            同义词字典 {关键词: [同义词列表]}
        """
        # 延迟导入，避免循环依赖
        import sys
        sys.path.insert(0, '/home/yka-003/workspace/caidao')
        sys.path.insert(0, '/home/yka-003/workspace/sg')
        from helper_task_redis2 import GLOBAL_REDIS
        
        # 如果没有提供关键词，从描述中提取
        if not keywords:
            # 简单提取：按标点分割，过滤短词
            import re
            words = re.split(r'[、，,；;。\s]+', description)
            keywords = [w.strip() for w in words if len(w.strip()) >= 2]
        
        # 构建提示词
        keywords_str = "、".join(keywords[:30])  # 最多处理30个关键词
        
        sys_prompt = """你是一个专业的同义词扩展助手。

任务：为给定的关键词生成同义词/近义词/相关词。

要求：
1. 每个关键词生成5-10个同义词或相关表达
2. 包括口语化、网络用语、行业术语等变体
3. 确保同义词在语义上相关，可以互相替换或表达相近意思
4. 输出格式必须是JSON

输出格式示例：
{
  "关键词1": ["同义词1", "同义词2", "同义词3"],
  "关键词2": ["同义词1", "同义词2", "同义词3"]
}"""
        
        question = f"""请为以下关键词生成同义词库：

目标描述：{description}

关键词：{keywords_str}

请直接输出JSON格式的同义词字典，不要添加任何解释。"""
        
        key_back = f"synonym_{int(time.time() * 1000)}"
        
        result = GLOBAL_REDIS.提交数据并阻塞等待结果(
            key_back=key_back,
            sys_prompt=sys_prompt,
            question=question
        )
        
        if result and result.get("result"):
            try:
                # 尝试解析JSON
                synonyms = json.loads(result["result"])
                if isinstance(synonyms, dict):
                    # 确保值是列表，并将关键词本身加入同义词列表
                    result_dict = {}
                    for k, v in synonyms.items():
                        syn_list = v if isinstance(v, list) else [v]
                        # 确保关键词本身在同义词列表中
                        if k not in syn_list:
                            syn_list.insert(0, k)  # 将关键词本身放到列表首位
                        result_dict[k] = syn_list
                    return result_dict
            except json.JSONDecodeError:
                # JSON解析失败，使用备用方案
                print(f"[SynonymCacheManager] JSON解析失败，使用备用方案")
        
        # 备用方案：简单的字符串相似匹配
        return self._fallback_synonyms(keywords)
    
    def _fallback_synonyms(self, keywords: List[str]) -> Dict[str, List[str]]:
        """
        备用同义词生成方案（当API调用失败时使用）
        
        基于简单的规则生成同义词
        """
        synonyms = {}
        
        # 简单的同义词映射表
        common_synonyms = {
            "白嫖": ["免费拿", "零元购", "不花钱", "占便宜", "白拿", "蹭", "免费领"],
            "薅羊毛": ["捡漏", "省钱", "优惠活动", "福利", "红包", "折扣", "促销", "抢购"],
            "维权": ["投诉", "举报", "申诉", "索赔", "追责", "讨说法", "告", "起诉"],
            "假货": ["山寨", "盗版", "高仿", "A货", "仿品", "假冒", "伪劣", "假货", "冒牌"],
            "仅退款": ["退款", "退货", "退钱", "赔付", "赔偿", "补偿", "售后", "退款成功"],
            "拼多多": ["PDD", "拼夕夕", "多多", "拼单", "砍一刀", "百亿补贴"],
        }
        
        for keyword in keywords:
            if keyword in common_synonyms:
                synonyms[keyword] = common_synonyms[keyword]
            else:
                # 对于未知词，添加一些通用变体
                synonyms[keyword] = [keyword]  # 至少包含自己
        
        return synonyms
    
    def clear_cache(self, hash_id: str = None):
        """
        清除缓存
        
        Args:
            hash_id: 如指定则清理单个缓存，否则清理全部
        """
        if hash_id:
            cache_path = self.get_cache_path(hash_id)
            if cache_path.exists():
                cache_path.unlink()
                print(f"[SynonymCacheManager] 已删除缓存: {cache_path}")
        else:
            if self.cache_dir.exists():
                import shutil
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
                print(f"[SynonymCacheManager] 已清空所有缓存: {self.cache_dir}")
    
    def list_cached(self) -> List[dict]:
        """列出所有已缓存的同义词库"""
        cached = []
        
        if self.cache_dir.exists():
            for sub_dir in self.cache_dir.iterdir():
                if sub_dir.is_dir():
                    cache_file = sub_dir / "synonyms.json"
                    if cache_file.exists():
                        try:
                            with open(cache_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            cached.append({
                                "hash_id": data.get("hash_id", "")[:16] + "...",
                                "目标描述": data.get("目标描述", "")[:30] + "...",
                                "版本": data.get("版本", "unknown"),
                                "生成时间": data.get("生成时间", "")
                            })
                        except:
                            pass
        
        return cached
