#!/bin/bash
# 下载 atx-agent 脚本
# 当本地缓存不存在时，运行此脚本下载 atx-agent

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATX_VERSION="0.10.0"

echo "正在下载 atx-agent ${ATX_VERSION}..."

# 下载 arm64 版本
echo "下载 atx-agent_${ATX_VERSION}_linux_arm64.tar.gz..."
curl -L -o "${SCRIPT_DIR}/atx-agent_${ATX_VERSION}_linux_arm64.tar.gz" \
    "https://github.com/openatx/atx-agent/releases/download/${ATX_VERSION}/atx-agent_${ATX_VERSION}_linux_arm64.tar.gz" \
    --max-time 300

# 验证文件
if file "${SCRIPT_DIR}/atx-agent_${ATX_VERSION}_linux_arm64.tar.gz" | grep -q "gzip"; then
    echo "✓ arm64 版本下载成功并验证通过"
else
    echo "✗ arm64 版本文件损坏，请手动下载"
    rm -f "${SCRIPT_DIR}/atx-agent_${ATX_VERSION}_linux_arm64.tar.gz"
    exit 1
fi

# 可选：下载其他架构版本
# echo "下载 atx-agent_${ATX_VERSION}_linux_armv7.tar.gz..."
# curl -L -o "${SCRIPT_DIR}/atx-agent_${ATX_VERSION}_linux_armv7.tar.gz" \
#     "https://github.com/openatx/atx-agent/releases/download/${ATX_VERSION}/atx-agent_${ATX_VERSION}_linux_armv7.tar.gz" \
#     --max-time 300

echo ""
echo "下载完成！文件保存在: ${SCRIPT_DIR}"
ls -lh "${SCRIPT_DIR}/"
