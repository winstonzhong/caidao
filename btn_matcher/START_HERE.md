# 🎯 从这里开始

## 快速上手指南

### 1️⃣ 安装依赖（只需一次）

```bash
pip install opencv-python numpy
```

### 2️⃣ 运行演示（推荐）

```bash
./demo.sh
```

或手动测试：

```bash
python test_matcher.py
```

### 3️⃣ 实际使用

#### 建立特征库
```bash
python button_matcher.py build ./你的模板目录
```

#### 检测按钮
```bash
python button_matcher.py detect ./你的截图.png
```

## 📚 文档导航

| 文件 | 内容 |
|------|------|
| **START_HERE.md** | 你现在看的这个文件 |
| **QUICK_START.md** | 快速开始指南 |
| **README.md** | 完整的技术文档 |
| **PROJECT_SUMMARY.md** | 项目总结 |

## 🚀 核心命令

```bash
# 建库
python button_matcher.py build <目录路径> [-o <输出文件>]

# 检测
python button_matcher.py detect <图片路径> [-d <特征库文件>]

# 查看帮助
python button_matcher.py --help
```

## 💡 提示

1. **模板准备**
   - 每个按钮保存为单独的PNG文件
   - 背景尽量简洁
   - 文件名就是按钮名称

2. **截图技巧**
   - 保持清晰，分辨率不要太低
   - 尽量保持按钮完整可见

3. **结果查看**
   - 检测完成后会生成带框的结果图
   - 文件名后缀为 `_detected`

## ❓ 遇到问题？

1. 查看 `QUICK_START.md` 的常见问题部分
2. 运行测试脚本检查环境
3. 查看完整文档 `README.md`

## ✅ 确认清单

使用前请确认：
- [ ] Python 3.x 已安装
- [ ] OpenCV 和 NumPy 已安装
- [ ] 模板图片已准备好（PNG格式）
- [ ] 待检测图片已准备好

## 🎉 开始使用

现在你可以开始使用了！记住两个核心命令：

```bash
# 1. 建库（只需一次）
python button_matcher.py build ./btn_tmpl

# 2. 检测（每次新截图）
python button_matcher.py detect ./screenshot.png
```

祝使用愉快！🚀
