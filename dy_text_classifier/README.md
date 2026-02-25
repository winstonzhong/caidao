# 抖音视频文案文本分类器

基于关键词匹配的轻量级文本分类解决方案，支持LLM自动生成同义词库和智能缓存。

## 特性

- 🚀 **极速响应**：缓存命中时 < 10ms
- 💾 **智能缓存**：相同类别描述自动复用，避免重复API调用
- 📦 **体积极小**：核心代码 < 100KB，满足 < 10MB 严格要求
- 🔧 **零训练成本**：无需准备训练数据，即开即用
- 💡 **可解释性强**：匹配结果清晰展示命中了哪些关键词
- 🎯 **动态可变**：支持任意类别，输入描述即可生成分类器

## 快速开始

### 1. 最简使用（推荐）

```python
from dy_text_classifier import 文本匹配, 获取相似度

# JSON数据（来自XML解析结果）
data = {
    "作者": "@老陶电商",
    "文案": "#老陶电商 #拼多多运营 能发货的抓紧时间去报名活动和打开直通车！",
    "音乐": "@老陶电商创作的原声"
}

# 直接判断匹配
is_match = 文本匹配("拼多多电商运营", data)
print(f"是否匹配: {is_match}")  # True

# 获取相似度分数
similarity = 获取相似度("拼多多电商运营", data)
print(f"相似度: {similarity}")  # 1.0
```

### 2. 使用 SimpleMatcher 类

```python
from dy_text_classifier import SimpleMatcher

matcher = SimpleMatcher()

# 单个匹配
data = {"作者": "@老陶电商", "文案": "#拼多多运营 发货！"}
is_match = matcher.文本匹配("拼多多电商运营", data, 阈值=0.3)

# 批量匹配
data_list = [data1, data2, data3]
matches = matcher.批量匹配("拼多多电商运营", data_list, 阈值=0.3)
# 返回匹配的数据列表（包含相似度）

# 获取相似度（不判断阈值）
similarity = matcher.获取相似度("拼多多电商运营", data)

# 设置全局默认阈值（可通过学习大量数据后优化）
matcher.设置默认阈值(0.35)
```

### 3. 高级使用（完整控制）

```python
from dy_text_classifier import CategoryCacheManager, TextClassifier

# 初始化缓存管理器
cache_manager = CategoryCacheManager(cache_dir="cache")

# 定义类别描述
category_desc = "拼多多电商平台运营相关"

# 获取或创建词库（自动处理缓存）
hash_id, word_bank, is_from_cache = cache_manager.get_or_create(
    description=category_desc,
    total_words=20
)

# 初始化分类器
classifier = TextClassifier(hashtag_weight=1.5)

# 单条分类
text = "#拼多多运营 能发货的抓紧时间去报名活动！"
result = classifier.classify(
    hash_id=hash_id,
    word_bank=word_bank,
    text=text,
    category_desc=category_desc,
    is_from_cache=is_from_cache
)

print(f"相似度: {result.similarity}")
print(f"匹配词: {result.matched_words}")
```

### 2. 批量处理

```python
from dy_text_classifier import BatchProcessor

processor = BatchProcessor(classifier)

results = processor.process_directory(
    hash_id=hash_id,
    word_bank=word_bank,
    category_desc=category_desc,
    xmls_dir="/path/to/json/files",
    threshold=0.3
)

# 查看结果
for item in results[:5]:
    print(f"[{item['相似度']:.2f}] {item['文案'][:50]}...")
```

### 3. 运行示例

```bash
cd dy_text_classifier
python3 main.py
```

## 项目结构

```
dy_text_classifier/
├── __init__.py                   # 包初始化
├── category_cache_manager.py     # 词库缓存管理（含Hash计算）
├── text_classifier.py            # 分类器核心
├── batch_processor.py            # 批量处理
├── evaluator.py                  # 评估工具
├── main.py                       # 主入口示例
├── cache/                        # 缓存目录（运行时生成）
│   └── fba4b13c/                 # Hash前8位作为子目录
│       └── word_bank.json        # 词库缓存文件
└── tests/
    └── test_classifier.py        # 单元测试
```

## 核心类说明

### CategoryCacheManager

管理类别词库的生成和缓存。

```python
manager = CategoryCacheManager(cache_dir="cache")

# 计算Hash
hash_id = CategoryCacheManager.compute_hash("拼多多电商")

# 获取或创建词库
hash_id, word_bank, is_from_cache = manager.get_or_create(
    description="拼多多电商运营",
    total_words=20
)

# 管理缓存
manager.clear_cache()  # 清空所有缓存
manager.list_cached()  # 列出所有已缓存
```

### TextClassifier

基于关键词的文本分类器。

```python
classifier = TextClassifier(
    hashtag_weight=1.5,  # hashtag内匹配权重倍数
    max_score=1.0        # 用于归一化的最大分数
)

result = classifier.classify(
    hash_id=hash_id,
    word_bank=word_bank,
    text="待分类文案",
    category_desc="类别描述"
)

# result.similarity: 相似度分数 (0-1)
# result.matched_words: 匹配的词列表 [(词, 位置), ...]
```

### BatchProcessor

批量处理JSON文件。

```python
processor = BatchProcessor(classifier)

results = processor.process_directory(
    hash_id=hash_id,
    word_bank=word_bank,
    category_desc=category_desc,
    xmls_dir="/path/to/json/files",
    threshold=0.3  # 相似度阈值
)
```

### Evaluator

评估工具。

```python
# 分析结果
stats = Evaluator.analyze_results(results)
print(f"样本数: {stats['样本数']}")
print(f"平均相似度: {stats['平均相似度']}")

# 调试单条
Evaluator.debug_match(word_bank, "待测试文案")

# 生成报告
report = Evaluator.generate_report(results, "report.txt")
```

## 缓存机制

### Hash计算

使用MD5计算类别描述的Hash作为唯一标识：

```
"拼多多电商运营" → md5 → "fba4b13cd3803f1725bc6a6a32c388e6"
```

### 缓存目录结构

```
cache/
├── fba4b13c/                 # Hash前8位作为子目录
│   └── word_bank.json        # 词库缓存文件
├── a1b2c3d4/
│   └── word_bank.json
└── ...
```

### 缓存文件格式

```json
{
  "hash_id": "fba4b13cd3803f1725bc6a6a32c388e6",
  "类别描述": "拼多多电商平台运营相关",
  "生成时间": "2026-02-25T15:45:00",
  "词库": {
    "拼多多": 1.0,
    "电商": 1.0,
    "PDD": 0.6,
    "拼夕夕": 0.6
  },
  "统计信息": {
    "核心词数": 2,
    "扩展词数": 2,
    "总词数": 4
  }
}
```

## 阈值设置

默认相似度阈值为 **0.3**（经验值），可通过学习大量数据后优化。

```python
from dy_text_classifier import SimpleMatcher

matcher = SimpleMatcher()

# 使用默认阈值 (0.3)
is_match = matcher.文本匹配("拼多多电商", data)

# 自定义阈值
is_match = matcher.文本匹配("拼多多电商", data, 阈值=0.5)

# 设置全局默认阈值（推荐：通过大量数据学习后设置）
matcher.设置默认阈值(0.35)
```

### 阈值选择建议

| 阈值 | 适用场景 |
|-----|---------|
| 0.2 | 宽松匹配，尽可能多召回 |
| 0.3 | 平衡（默认），适合大多数场景 |
| 0.5 | 严格匹配，要求较高的相关性 |
| 0.7 | 非常严格，只保留高度相关内容 |

## 匹配算法

### 计分规则

1. **核心词匹配**（权重 1.0）：
   - 普通文本：+1.0
   - hashtag内：+1.0 × hashtag_weight

2. **扩展词匹配**（权重 0.6）：
   - 普通文本：+0.6
   - hashtag内：+0.6 × hashtag_weight

3. **归一化**：
   - 最终分数 = min(累计分数 / max_score, 1.0)

### 示例

```python
词库 = {"拼多多": 1.0, "运营": 0.6}
hashtag_weight = 1.5

# 文本A: "#拼多多运营 技巧"
# - "拼多多"在hashtag中: 1.0 × 1.5 = 1.5
# - "运营"已在hashtag中匹配，不再重复计分
# 相似度 = min(1.5 / 1.0, 1.0) = 1.0

# 文本B: "拼多多技巧"
# - "拼多多"在正文中: 1.0
# 相似度 = min(1.0 / 1.0, 1.0) = 1.0
```

## 性能指标

| 指标 | 值 |
|-----|---|
| 首次调用（含API） | < 5s |
| 缓存命中调用 | < 10ms |
| 单条分类 | < 5ms |
| 批量处理（100条） | < 1s |
| 内存占用 | < 50MB |
| 代码体积 | < 100KB |

## 测试

```bash
# 运行单元测试
python3 tests/test_classifier.py
```

## 依赖

- Python 3.8+
- 标准库：hashlib, json, re, pathlib, datetime
- 外部依赖：
  - `helper_synonym.py`（同义词生成，依赖Redis LLM API）
  - `jieba`（可选，中文分词）

## 许可证

MIT
