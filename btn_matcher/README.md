# Button Matcher - 按钮匹配工具

增强版的按钮匹配工具，支持批量处理、智能过滤和高性能匹配。

## 功能特性

### 核心功能
- **批量匹配**: 支持多个masks同时匹配
- **智能过滤**: 宽高比和尺寸预过滤，提升效率
- **缩放支持**: 适配不同设备分辨率的APP界面
- **完整流程**: 集成化的批量匹配流程

### 新增函数

#### 1. `find_buttons_all(masks, db, min_match_prob=0.9)`
批量查找所有符合条件的按钮。

```python
masks = [mask1, mask2, mask3]
success, results = find_buttons_all(masks, db, min_match_prob=0.8)
# results包含所有mask的匹配结果
```

#### 2. `过滤宽高比(masks, db, aspect_ratio_tolerance=0.15)`
根据宽高比过滤masks和数据库模板。

- 预计算数据库中所有模板的宽高比
- 批量计算所有masks的宽高比
- 使用numpy数组避免循环，提升效率

```python
filtered_masks, filtered_db, indices = 过滤宽高比(
    masks, db, aspect_ratio_tolerance=0.2
)
```

#### 3. `过滤尺寸(masks, db, x方向缩放率=1, y方向缩放率=1, 容忍阈值=0.2)`
根据尺寸过滤，支持缩放率和容忍阈值。

- 适配不同设备中的APP界面尺寸变化
- 批量计算尺寸差异矩阵
- 支持不同的X/Y方向缩放率

```python
filtered_masks, filtered_db, indices = 过滤尺寸(
    masks, db,
    x方向缩放率=0.8,  # 模拟小屏设备
    y方向缩放率=0.9,
    容忍阈值=0.25
)
```

#### 4. `批量匹配流程(...)`
完整的批量匹配流程，集成所有过滤策略。

```python
success, results = 批量匹配流程(
    masks, db,
    min_match_prob=0.8,
    使用宽高比过滤=True,
    使用尺寸过滤=True,
    aspect_ratio_tolerance=0.15,
    x方向缩放率=1.0,
    y方向缩放率=1.0,
    尺寸容忍阈值=0.2
)
```

### 辅助函数

#### 数据管理
- `保存匹配结果(results, output_file)`: 保存结果为JSON格式
- `加载匹配结果(input_file)`: 从JSON文件加载结果
- `统计数据库信息(db)`: 获取数据库统计信息

#### 宽高比工具
- `计算宽高比数据库(db)`: 预计算所有模板的宽高比

## 性能优势

### 批量计算
所有过滤函数都使用numpy数组进行批量计算，避免Python循环：

```python
# 批量计算所有masks的宽高比
masks_array = np.array([mask.shape for mask in masks])
mask_heights = masks_array[:, 0].astype(float)
mask_widths = masks_array[:, 1].astype(float)
mask_aspect_ratios = mask_widths / mask_heights
```

### 预计算策略
数据库宽高比预先计算，避免重复计算：

```python
aspect_ratios = 计算宽高比数据库(db)
# 后续过滤直接使用预计算结果
```

### 多层次过滤
通过宽高比和尺寸预过滤，显著减少ORB特征匹配的计算量：

```
原始数据 → 宽高比过滤 → 尺寸过滤 → ORB匹配
  100%        50%          30%        30%
```

## 使用示例

### 基本使用

```python
from button_matcher import *

# 1. 构建数据库
build_database('templates/', 'btn_feat.db')

# 2. 加载数据库
success, db = load_database('btn_feat.db')

# 3. 读取测试mask
mask = cv2.imread('test_mask.png', 0)

# 4. 执行匹配
success, matches = find_buttons(mask, db)

# 5. 查看结果
for match in matches:
    if match['match_prob'] > 0.8:
        print(f"匹配到按钮: {match['btn_name']}")
```

### 批量处理

```python
# 批量处理多个masks
masks = [mask1, mask2, mask3, mask4]

# 方法1: 使用find_buttons_all
success, results = find_buttons_all(masks, db, min_match_prob=0.8)

# 方法2: 使用完整流程（推荐）
success, results = 批量匹配流程(
    masks, db,
    min_match_prob=0.8,
    使用宽高比过滤=True,
    使用尺寸过滤=True,
    aspect_ratio_tolerance=0.15,
    尺寸容忍阈值=0.2
)

# 结果按置信度排序
for result in results:
    print(f"Mask {result['mask_idx']}: {result['btn_name']} "
          f"(置信度: {result['match_prob']})")
```

### 适配不同设备

```python
# 手机设备（小屏）
success, results = 批量匹配流程(
    masks, db,
    x方向缩放率=0.7,  # 宽度缩小30%
    y方向缩放率=0.75, # 高度缩小25%
    尺寸容忍阈值=0.3  # 更大的容忍度
)

# 平板设备（大屏）
success, results = 批量匹配流程(
    masks, db,
    x方向缩放率=1.2,  # 宽度放大20%
    y方向缩放率=1.15, # 高度放大15%
    尺寸容忍阈值=0.25
)
```

## API文档

### find_buttons_all
```python
def find_buttons_all(
    masks: List[np.ndarray], 
    db: list, 
    min_match_prob: float = 0.9
) -> Tuple[bool, List[Dict[str, Any]]]
```

批量查找所有符合条件的按钮。

**参数:**
- `masks`: 待匹配的灰度图列表
- `db`: 加载后的特征库
- `min_match_prob`: 最小匹配置信度阈值（默认0.9）

**返回:**
- `success`: 执行是否成功
- `results`: 所有匹配结果列表，包含：
  - `mask_idx`: mask索引
  - `btn_name`: 按钮名称
  - `match_prob`: 匹配置信度
  - `match_count`: 有效匹配对数量
  - `total_features`: 模板总特征数

### 过滤宽高比
```python
def 过滤宽高比(
    masks: List[np.ndarray], 
    db: list, 
    aspect_ratio_tolerance: float = 0.15
) -> Tuple[List[np.ndarray], List[Tuple], List[int]]
```

根据宽高比过滤masks和数据库。

**参数:**
- `masks`: 待匹配的灰度图列表
- `db`: 加载后的特征库
- `aspect_ratio_tolerance`: 宽高比容忍阈值（默认0.15）

**返回:**
- `filtered_masks`: 过滤后的masks列表
- `filtered_db`: 过滤后的数据库
- `mask_indices`: 保留的mask原始索引

### 过滤尺寸
```python
def 过滤尺寸(
    masks: List[np.ndarray], 
    db: list, 
    x方向缩放率: float = 1, 
    y方向缩放率: float = 1, 
    容忍阈值: float = 0.2
) -> Tuple[List[np.ndarray], List[Tuple], List[int]]
```

根据尺寸过滤，支持缩放。

**参数:**
- `masks`: 待匹配的灰度图列表
- `db`: 加载后的特征库
- `x方向缩放率`: X方向缩放系数（默认1）
- `y方向缩放率`: Y方向缩放系数（默认1）
- `容忍阈值`: 尺寸差异容忍阈值（默认0.2）

**返回:**
- `filtered_masks`: 过滤后的masks列表
- `filtered_db`: 过滤后的数据库
- `mask_indices`: 保留的mask原始索引

## 工程化特性

### 类型注解
所有函数都包含完整的类型提示：

```python
from typing import List, Tuple, Dict, Any

def find_buttons_all(
    masks: List[np.ndarray], 
    db: list, 
    min_match_prob: float = 0.9
) -> Tuple[bool, List[Dict[str, Any]]]:
```

### 文档字符串
每个函数都包含详细的docstring：

- 功能描述
- 参数说明
- 返回值说明
- 使用示例（doctest格式）

### 错误处理
完善的输入校验和异常处理：

```python
if not masks or not isinstance(masks, list):
    print("错误：输入的masks列表为空或无效")
    return False, []
```

### 日志输出
清晰的操作日志，便于调试：

```
✓ 宽高比过滤完成：保留 5/20 个masks，3/4 个模板
✓ 尺寸过滤完成：保留 15/20 个masks，3/4 个模板
✓ 交叉验证匹配完成：共找到 4 个有效按钮
```

## 性能基准

测试环境：Intel i7, 16GB RAM

| 操作 | 数量 | 时间 |
|------|------|------|
| 宽高比过滤 | 20个masks | 0.27ms |
| 尺寸过滤 | 20个masks | 0.14ms |
| ORB匹配 | 1个mask | 0.89ms |
| 完整流程 | 20个masks | ~20ms |

## 测试

### 单元测试
使用Python的doctest模块，包含37个测试用例：

```bash
python button_matcher.py --test
```

### 集成测试
完整流程验证：

```python
# 创建测试数据
masks = [create_test_mask() for _ in range(10)]
db = load_test_database()

# 执行完整流程
success, results = 批量匹配流程(masks, db)
```

### 性能测试
大规模数据验证：

```python
# 测试100个masks的批量处理
large_masks = [create_random_mask() for _ in range(100)]
measure_performance(large_masks, db)
```

## 依赖

- Python 3.8+
- OpenCV (cv2) >= 4.0
- NumPy >= 1.18

## 安装

```bash
# 安装依赖
pip install opencv-python numpy

# 使用
python button_matcher.py --build-db --input-dir templates/
```

## 命令行接口

```bash
# 构建数据库
python button_matcher.py --build-db --input-dir templates/ --db-file btn_feat.db

# 测试匹配
python button_matcher.py --test-mask test.png --db-file btn_feat.db --min-prob 0.8
```

## 最佳实践

### 1. 数据库构建
- 使用高质量、清晰的模板图片
- 包含不同尺寸的同一按钮
- 定期更新数据库

### 2. 过滤参数
- 宽高比容忍阈值：0.1-0.2
- 尺寸容忍阈值：0.2-0.3
- 最小匹配置信度：0.8-0.9

### 3. 性能优化
- 先使用过滤减少数据量
- 批量处理优于单个处理
- 合理设置ORB参数

### 4. 设备适配
- 收集不同设备的缩放率数据
- 建立设备-缩放率映射表
- 动态调整容忍阈值

## 更新日志

### v2.0.0
- 新增 `find_buttons_all` 批量匹配函数
- 新增 `过滤宽高比` 智能过滤函数
- 新增 `过滤尺寸` 缩放适配函数
- 新增 `批量匹配流程` 完整流程函数
- 新增数据保存/加载功能
- 新增数据库统计功能
- 完整的类型注解
- 详细的API文档
- 37个单元测试用例

## 许可证

MIT License
