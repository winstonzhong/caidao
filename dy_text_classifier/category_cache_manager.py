# encoding: utf-8
"""
类别词库缓存管理器

职责：
1. 计算类别描述的MD5 Hash作为唯一标识
2. 检查本地缓存是否存在
3. 如不存在，调用API生成并保存
4. 如存在，直接读取本地缓存
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


# 模块所在目录（用于确定默认缓存位置）
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class CategoryCacheManager:
    """
    类别词库缓存管理器
    
    职责：
    1. 计算类别描述的MD5 Hash作为唯一标识
    2. 检查本地缓存是否存在
    3. 如不存在，调用API生成并保存
    4. 如存在，直接读取本地缓存
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径。如果是相对路径，则相对于当前模块所在目录。
                      默认为 "cache"，即保存在 dy_text_classifier/cache/
        """
        # 如果使用相对路径，则基于模块位置转换为绝对路径
        if not os.path.isabs(cache_dir):
            cache_dir = os.path.join(_MODULE_DIR, cache_dir)
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    @staticmethod
    def compute_hash(description: str) -> str:
        """
        计算类别描述的MD5 Hash
        
        Args:
            description: 类别描述文本
        
        Returns:
            32位小写hex字符串
        """
        return hashlib.md5(description.encode('utf-8')).hexdigest()
    
    def get_cache_path(self, hash_id: str) -> Path:
        """获取缓存文件路径"""
        # 使用完整hash作为目录名，完全避免冲突
        cache_subdir = self.cache_dir / hash_id
        cache_subdir.mkdir(exist_ok=True)
        return cache_subdir / "word_bank.json"
    
    def exists(self, hash_id: str) -> bool:
        """检查缓存是否存在"""
        cache_path = self.get_cache_path(hash_id)
        return cache_path.exists()
    
    def load(self, hash_id: str) -> Optional[Dict[str, float]]:
        """
        从缓存加载词库
        
        Args:
            hash_id: 类别Hash ID
        
        Returns:
            词库字典，如不存在返回None
        """
        cache_path = self.get_cache_path(hash_id)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('词库', {})
        except Exception as e:
            print(f"加载缓存失败: {e}")
            return None
    
    def save(self, hash_id: str, description: str, word_bank: Dict[str, float]):
        """
        保存词库到缓存
        
        Args:
            hash_id: 类别Hash ID
            description: 原始类别描述
            word_bank: 词库字典
        """
        cache_path = self.get_cache_path(hash_id)
        
        # 分离核心词和扩展词（用于统计信息）
        核心词 = {k: v for k, v in word_bank.items() if v == 1.0}
        扩展词 = {k: v for k, v in word_bank.items() if v < 1.0}
        
        data = {
            "hash_id": hash_id,
            "类别描述": description,
            "生成时间": datetime.now().isoformat(),
            "词库": word_bank,
            "统计信息": {
                "核心词数": len(核心词),
                "扩展词数": len(扩展词),
                "总词数": len(word_bank)
            }
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"词库已缓存: {cache_path}")
    
    def get_or_create(
        self, 
        description: str, 
        total_words: int = 20
    ) -> tuple:
        """
        获取或创建词库（核心方法）
        
        逻辑：
        1. 计算description的hash
        2. 检查缓存是否存在
        3. 存在则直接返回
        4. 不存在则调用API生成并缓存
        
        Args:
            description: 类别描述
            total_words: 词库大小
        
        Returns:
            (hash_id, word_bank, is_from_cache)
        """
        # 1. 计算Hash
        hash_id = self.compute_hash(description)
        
        # 2. 检查缓存
        word_bank = self.load(hash_id)
        if word_bank is not None:
            print(f"命中缓存: {hash_id[:8]}...")
            return hash_id, word_bank, True
        
        # 3. 缓存未命中，调用API生成
        print(f"缓存未命中，调用API生成: {hash_id[:8]}...")
        
        # 延迟导入，避免循环依赖
        import sys
        sys.path.insert(0, '/home/yka-003/workspace/caidao')
        from helper_synonym import 获取匹配词字典
        
        word_bank = 获取匹配词字典(description, 总词数=total_words)
        
        # 4. 保存到缓存
        self.save(hash_id, description, word_bank)
        
        return hash_id, word_bank, False
    
    def clear_cache(self, hash_id: str = None):
        """
        清理缓存
        
        Args:
            hash_id: 如指定则清理单个缓存，否则清理全部
        """
        if hash_id:
            cache_path = self.get_cache_path(hash_id)
            if cache_path.exists():
                cache_path.unlink()
                print(f"已删除缓存: {cache_path}")
        else:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
                print(f"已清空所有缓存: {self.cache_dir}")
    
    def list_cached(self) -> List[dict]:
        """列出所有已缓存的类别"""
        cached = []
        for sub_dir in self.cache_dir.iterdir():
            if sub_dir.is_dir():
                for cache_file in sub_dir.glob("*.json"):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        cached.append({
                            "hash_id": data.get("hash_id", "")[:16] + "...",
                            "描述": data.get("类别描述", "")[:30] + "...",
                            "词数": data.get("统计信息", {}).get("总词数", 0),
                            "生成时间": data.get("生成时间", "")
                        })
                    except:
                        pass
        return cached


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("类别缓存管理器测试")
    print("=" * 60)
    
    manager = CategoryCacheManager(cache_dir="cache")
    
    # 测试Hash计算
    desc = "拼多多电商运营"
    hash_id = CategoryCacheManager.compute_hash(desc)
    print(f"\n类别描述: {desc}")
    print(f"Hash ID: {hash_id}")
    print(f"Hash长度: {len(hash_id)}")
    
    # 测试缓存路径
    cache_path = manager.get_cache_path(hash_id)
    print(f"缓存路径: {cache_path}")
    
    # 列出缓存
    cached = manager.list_cached()
    print(f"\n已有缓存数量: {len(cached)}")
    
    print("\n" + "=" * 60)
    print("测试完成")
