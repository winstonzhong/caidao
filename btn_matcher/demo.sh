#!/bin/bash

# 按钮检测工具 - 使用示例脚本

echo "=========================================="
echo "按钮检测工具 - 使用示例"
echo "=========================================="
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 检查依赖是否安装
echo "检查依赖..."
python3 -c "import cv2; import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "错误: 缺少依赖，请先安装："
    echo "  pip install opencv-python numpy"
    exit 1
fi
echo "✓ 依赖检查通过"
echo

# 创建示例目录和文件
echo "创建示例数据..."
mkdir -p example/{templates,screenshots}

# 创建示例模板（使用Python）
python3 << 'EOF'
import cv2
import numpy as np
import os

# 创建模板目录
os.makedirs('example/templates', exist_ok=True)

# 创建几个示例按钮模板
templates = [
    ('login_btn', (0, 100, 200)),      # 蓝色按钮
    ('submit_btn', (0, 200, 100)),     # 绿色按钮
    ('cancel_btn', (200, 100, 0)),     # 紫色按钮
]

for name, color in templates:
    img = np.zeros((50, 120, 3), dtype=np.uint8)
    cv2.rectangle(img, (5, 5), (115, 45), color, -1)
    cv2.putText(img, name.split('_')[0].upper(), (15, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.imwrite(f'example/templates/{name}.png', img)
    print(f"✓ 创建模板: example/templates/{name}.png")

# 创建示例截图
screenshot = np.zeros((600, 800, 3), dtype=np.uint8)
screenshot[:] = (40, 40, 40)  # 深灰色背景

# 添加按钮到截图
buttons = [
    ('login_btn', (100, 200), (220, 250), (0, 100, 200)),
    ('submit_btn', (350, 200), (470, 250), (0, 200, 100)),
    ('cancel_btn', (600, 200), (720, 250), (200, 100, 0)),
]

for name, pt1, pt2, color in buttons:
    cv2.rectangle(screenshot, pt1, pt2, color, -1)
    cv2.putText(screenshot, name.split('_')[0].upper(), 
                (pt1[0] + 20, pt1[1] + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

cv2.imwrite('example/screenshots/sample_screen.png', screenshot)
print(f"✓ 创建截图: example/screenshots/sample_screen.png")

print()
EOF

# 显示示例数据
echo "示例数据已创建："
echo "  模板目录: example/templates/"
echo "  截图文件: example/screenshots/sample_screen.png"
echo

# 运行建库命令
echo "=========================================="
echo "步骤1: 建立特征库"
echo "=========================================="
echo "命令: python3 button_matcher.py build example/templates"
echo
python3 button_matcher.py build example/templates
echo

# 运行检测命令
echo "=========================================="
echo "步骤2: 检测按钮"
echo "=========================================="
echo "命令: python3 button_matcher.py detect example/screenshots/sample_screen.png"
echo
python3 button_matcher.py detect example/screenshots/sample_screen.png
echo

# 显示结果
echo "=========================================="
echo "完成!"
echo "=========================================="
echo
echo "生成的文件："
echo "  ✓ 特征库: btn_feat.db"
echo "  ✓ 检测结果: example/screenshots/sample_screen_detected.png"
echo
echo "可以使用以下命令查看结果图："
if command -v eog &> /dev/null; then
    echo "  eog example/screenshots/sample_screen_detected.png"
elif command -v open &> /dev/null; then
    echo "  open example/screenshots/sample_screen_detected.png"
elif command -v xdg-open &> /dev/null; then
    echo "  xdg-open example/screenshots/sample_screen_detected.png"
else
    echo "  请手动打开: example/screenshots/sample_screen_detected.png"
fi
echo
echo "=========================================="
