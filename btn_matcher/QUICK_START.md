# 快速开始指南

## 安装

```bash
# 1. 安装依赖
pip install opencv-python numpy

# 2. 给脚本添加执行权限（Linux/Mac）
chmod +x button_matcher.py
```

## 基本使用

### 第一步：准备模板

创建一个目录存放按钮模板图片：

```
btn_tmpl/
├── login_btn.png
├── submit_btn.png
├── cancel_btn.png
└── settings_btn.png
```

**要求：**
- 图片格式：PNG
- 背景尽量简洁
- 每个按钮单独一张图片

### 第二步：建立特征库

```bash
python button_matcher.py build ./btn_tmpl
```

**输出：**
```
正在处理 4 个模板图片...
✓ 已处理: login_btn.png
✓ 已处理: submit_btn.png
✓ 已处理: cancel_btn.png
✓ 已处理: settings_btn.png

✓ 特征库已保存到: btn_feat.db
✓ 共保存 4 个模板特征
```

### 第三步：检测按钮

```bash
python button_matcher.py detect ./screenshot.png
```

**输出：**
```
正在检测图片: ./screenshot.png

✓ 检测到 2 个按钮（耗时: 0.156秒）:
  1. login_btn - 中心点: (320, 240)
  2. submit_btn - 中心点: (480, 240)

✓ 结果图已保存: ./screenshot_detected.png
```

## 高级用法

### 指定自定义特征库名

```bash
# 建库时指定输出文件名
python button_matcher.py build ./templates -o my_app.db

# 检测时使用指定的特征库
python button_matcher.py detect ./screen.png -d my_app.db
```

### 查看帮助

```bash
python button_matcher.py --help
python button_matcher.py build --help
python button_matcher.py detect --help
```

## 完整命令格式

```
# 建库
python button_matcher.py build <输入目录> [-o <输出文件>]

# 检测
python button_matcher.py detect <图片路径> [-d <特征库文件>]
```

## 常见问题

### Q: 检测不到按钮怎么办？

A: 尝试以下方法：
1. 确保截图清晰，分辨率不要太低
2. 检查模板图片质量
3. 降低匹配阈值（修改代码中的 `len(good) < 8` 为更小的值）

### Q: 检测速度慢？

A: 
1. 减少模板数量
2. 降低特征点数（修改 `nfeatures=800`）
3. 缩小检测图片尺寸

### Q: 误检测太多？

A:
1. 提高匹配阈值（修改 `len(good) < 8` 为更大的值）
2. 增加RANSAC阈值
3. 使用更独特的模板图片

## 测试脚本

运行测试脚本验证环境：

```bash
python test_matcher.py
```

这个脚本会：
1. 创建测试模板和截图
2. 测试建库功能
3. 测试检测功能
4. 自动清理（可选）

## 文件说明

```
button_matcher.py      # 主程序
README.md              # 完整文档
QUICK_START.md         # 本文件
test_matcher.py        # 测试脚本
btn_feat.db            # 特征库文件（自动生成）
*detected.png          # 检测结果图（自动生成）
```

## 示例工作流

```bash
# 1. 准备模板
cp my_buttons/*.png btn_tmpl/

# 2. 建库
python button_matcher.py build btn_tmpl

# 3. 截图并检测
# （截取屏幕，保存为 screen.png）
python button_matcher.py detect screen.png

# 4. 查看结果
eog screen_detected.png  # Linux
open screen_detected.png # Mac
```

## 联系与支持

如有问题，请查看：
- `README.md` - 完整文档
- `python button_matcher.py --help` - 命令帮助
- 测试脚本 `test_matcher.py`
