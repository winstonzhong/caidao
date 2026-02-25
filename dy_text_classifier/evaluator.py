# encoding: utf-8
"""
评估工具模块

用于分类结果的分析和调试
"""

from typing import List, Dict, Optional
from text_classifier import TextClassifier


class Evaluator:
    """分类器评估工具"""
    
    @staticmethod
    def analyze_results(results: List[Dict]) -> Dict:
        """
        分析分类结果
        
        Args:
            results: 分类结果列表，每项包含'相似度'key
        
        Returns:
            统计信息字典
        """
        if not results:
            return {
                "样本数": 0,
                "平均相似度": 0.0,
                "最高相似度": 0.0,
                "最低相似度": 0.0,
                "高相似度样本(>0.7)": 0,
                "中相似度样本(0.3-0.7)": 0,
                "低相似度样本(<0.3)": 0
            }
        
        similarities = [r.get('相似度', 0) for r in results]
        
        return {
            "样本数": len(results),
            "平均相似度": round(sum(similarities) / len(similarities), 4),
            "最高相似度": round(max(similarities), 4),
            "最低相似度": round(min(similarities), 4),
            "高相似度样本(>0.7)": len([s for s in similarities if s > 0.7]),
            "中相似度样本(0.3-0.7)": len([s for s in similarities if 0.3 <= s <= 0.7]),
            "低相似度样本(<0.3)": len([s for s in similarities if s < 0.3])
        }
    
    @staticmethod
    def debug_match(
        word_bank: Dict[str, float], 
        text: str, 
        classifier: Optional[TextClassifier] = None,
        category_desc: str = "",
        hash_id: str = "debug"
    ):
        """
        调试单条文本的匹配过程
        
        Args:
            word_bank: 词库
            text: 待匹配文本
            classifier: 分类器实例（如为None则创建新实例）
            category_desc: 类别描述
            hash_id: Hash ID
        """
        if classifier is None:
            classifier = TextClassifier()
        
        print(f"\n{'='*60}")
        print(f"调试信息")
        print(f"{'='*60}")
        print(f"类别: {category_desc or '未指定'}")
        print(f"文案: {text}")
        print(f"\n词库内容:")
        for word, weight in sorted(word_bank.items(), key=lambda x: x[1], reverse=True):
            print(f"  - '{word}': {weight}")
        
        result = classifier.classify(
            hash_id=hash_id,
            word_bank=word_bank,
            text=text,
            category_desc=category_desc
        )
        
        print(f"\n{'-'*60}")
        print(f"匹配结果:")
        print(f"  相似度: {result.similarity:.4f}")
        print(f"  匹配词数: {len(result.matched_words)}")
        
        if result.matched_words:
            print(f"\n  匹配详情:")
            for word, location in result.matched_words:
                weight = word_bank.get(word, 0)
                print(f"    - '{word}' (权重:{weight}) @ {location}")
        else:
            print(f"\n  无匹配词")
        
        print(f"{'='*60}\n")
    
    @staticmethod
    def compare_thresholds(
        word_bank: Dict[str, float],
        texts: List[str],
        thresholds: List[float] = None
    ) -> Dict[float, int]:
        """
        比较不同阈值下的命中数量
        
        Args:
            word_bank: 词库
            texts: 文本列表
            thresholds: 阈值列表，默认为[0.1, 0.3, 0.5, 0.7, 0.9]
        
        Returns:
            阈值 -> 命中数量的映射
        """
        if thresholds is None:
            thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        classifier = TextClassifier()
        results = {}
        
        for threshold in thresholds:
            count = 0
            for text in texts:
                result = classifier.classify(
                    hash_id="compare",
                    word_bank=word_bank,
                    text=text
                )
                if result.similarity >= threshold:
                    count += 1
            results[threshold] = count
        
        return results
    
    @staticmethod
    def generate_report(
        results: List[Dict],
        output_file: str = None
    ) -> str:
        """
        生成评估报告
        
        Args:
            results: 分类结果列表
            output_file: 输出文件路径（如指定则保存到文件）
        
        Returns:
            报告文本
        """
        stats = Evaluator.analyze_results(results)
        
        lines = []
        lines.append("=" * 60)
        lines.append("文本分类评估报告")
        lines.append("=" * 60)
        lines.append("")
        lines.append("【统计概览】")
        for key, value in stats.items():
            lines.append(f"  {key}: {value}")
        
        if results:
            lines.append("")
            lines.append("【Top 10 高相似度样本】")
            for i, item in enumerate(results[:10], 1):
                文案 = item.get('文案', '')[:50] + "..." if len(item.get('文案', '')) > 50 else item.get('文案', '')
                lines.append(f"  {i}. [{item.get('相似度', 0):.4f}] {文案}")
        
        lines.append("")
        lines.append("=" * 60)
        
        report = "\n".join(lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"报告已保存: {output_file}")
        
        return report


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("评估工具测试")
    print("=" * 60)
    
    # 测试分析结果
    test_results = [
        {'相似度': 0.85, '文案': '拼多多运营技巧'},
        {'相似度': 0.72, '文案': '店铺发货指南'},
        {'相似度': 0.45, '文案': '电商平台对比'},
        {'相似度': 0.30, '文案': '网络营销方法'},
        {'相似度': 0.15, '文案': ' unrelated text'},
    ]
    
    print("\n测试统计:")
    stats = Evaluator.analyze_results(test_results)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 测试调试输出
    print("\n测试调试匹配:")
    word_bank = {"拼多多": 1.0, "运营": 1.0, "PDD": 0.6}
    text = "#拼多多运营 能发货的抓紧时间去报名活动！"
    Evaluator.debug_match(word_bank, text, category_desc="拼多多电商")
    
    # 测试阈值比较
    print("\n测试阈值比较:")
    texts = [
        "拼多多运营技巧",
        "淘宝店铺管理",
        "PDD发货指南",
        "电商运营心得",
        " unrelated"
    ]
    threshold_results = Evaluator.compare_thresholds(word_bank, texts)
    for threshold, count in threshold_results.items():
        print(f"  阈值 {threshold}: 命中 {count} 条")
    
    # 测试报告生成
    print("\n测试报告生成:")
    report = Evaluator.generate_report(test_results)
    print(report)
    
    print("=" * 60)
    print("测试完成")
