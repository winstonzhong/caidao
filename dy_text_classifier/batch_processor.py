# encoding: utf-8
"""
批量处理器模块

用于批量处理JSON文件目录
"""

import json
from pathlib import Path
from typing import List, Dict
from text_classifier import TextClassifier


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, classifier: TextClassifier):
        """
        初始化批量处理器
        
        Args:
            classifier: 文本分类器实例
        """
        self.classifier = classifier
    
    def process_directory(
        self, 
        hash_id: str,
        word_bank: Dict[str, float],
        category_desc: str,
        xmls_dir: str,
        threshold: float = 0.3,
        is_from_cache: bool = False
    ) -> List[Dict]:
        """
        批量处理目录下的所有JSON文件
        
        Args:
            hash_id: 类别Hash ID
            word_bank: 词库
            category_desc: 类别描述
            xmls_dir: JSON文件目录
            threshold: 相似度阈值，低于此值的会被过滤
            is_from_cache: 词库是否来自缓存
        
        Returns:
            处理结果列表，按相似度降序排列
        """
        results = []
        xmls_path = Path(xmls_dir)
        
        if not xmls_path.exists():
            print(f"目录不存在: {xmls_dir}")
            return results
        
        json_files = list(xmls_path.glob("*.json"))
        print(f"找到 {len(json_files)} 个JSON文件")
        
        for i, json_file in enumerate(json_files, 1):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 分类
                match_result = self.classifier.classify(
                    hash_id=hash_id,
                    word_bank=word_bank,
                    text=data.get('文案', ''),
                    category_desc=category_desc,
                    is_from_cache=is_from_cache
                )
                
                if match_result.similarity >= threshold:
                    results.append({
                        '文件名': json_file.name,
                        '作者': data.get('作者', ''),
                        '文案': data.get('文案', ''),
                        '相似度': match_result.similarity,
                        '匹配词': [w for w, _ in match_result.matched_words],
                        'hash_id': hash_id[:8]
                    })
                
                # 每处理10个文件打印进度
                if i % 10 == 0:
                    print(f"已处理: {i}/{len(json_files)}")
                    
            except Exception as e:
                print(f"处理文件 {json_file.name} 失败: {e}")
                continue
        
        # 按相似度排序
        results.sort(key=lambda x: x['相似度'], reverse=True)
        
        print(f"处理完成，命中 {len(results)} 条（阈值: {threshold}）")
        return results
    
    def process_list(
        self,
        hash_id: str,
        word_bank: Dict[str, float],
        category_desc: str,
        items: List[Dict],
        threshold: float = 0.3,
        is_from_cache: bool = False
    ) -> List[Dict]:
        """
        批量处理列表数据
        
        Args:
            hash_id: 类别Hash ID
            word_bank: 词库
            category_desc: 类别描述
            items: 数据列表，每项包含'文案'key
            threshold: 相似度阈值
            is_from_cache: 词库是否来自缓存
        
        Returns:
            处理结果列表
        """
        results = []
        
        for item in items:
            try:
                text = item.get('文案', '')
                
                match_result = self.classifier.classify(
                    hash_id=hash_id,
                    word_bank=word_bank,
                    text=text,
                    category_desc=category_desc,
                    is_from_cache=is_from_cache
                )
                
                if match_result.similarity >= threshold:
                    result_item = item.copy()
                    result_item['相似度'] = match_result.similarity
                    result_item['匹配词'] = [w for w, _ in match_result.matched_words]
                    results.append(result_item)
                    
            except Exception as e:
                print(f"处理条目失败: {e}")
                continue
        
        # 按相似度排序
        results.sort(key=lambda x: x['相似度'], reverse=True)
        
        return results


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("批量处理器测试")
    print("=" * 60)
    
    from text_classifier import TextClassifier
    
    classifier = TextClassifier(hashtag_weight=1.5)
    processor = BatchProcessor(classifier)
    
    # 测试词库
    word_bank = {
        "拼多多": 1.0,
        "运营": 1.0,
        "PDD": 0.6,
        "拼夕夕": 0.6,
    }
    
    # 测试列表数据
    test_items = [
        {'文案': '#拼多多运营 能发货的抓紧时间去报名活动！', '作者': '@老陶电商'},
        {'文案': '今天教大家如何做好淘宝店铺', '作者': '@电商导师'},
        {'文案': '拼夕夕上面的东西真便宜', '作者': '@省钱达人'},
        {'文案': '这是一个无关的文案', '作者': '@路人甲'},
    ]
    
    print("\n测试列表处理:")
    results = processor.process_list(
        hash_id="test_hash_123",
        word_bank=word_bank,
        category_desc="拼多多电商",
        items=test_items,
        threshold=0.3
    )
    
    print(f"\n命中 {len(results)} 条:")
    for item in results:
        print(f"  [{item['相似度']:.2f}] {item['文案'][:30]}...")
    
    print("\n" + "=" * 60)
    print("测试完成")
