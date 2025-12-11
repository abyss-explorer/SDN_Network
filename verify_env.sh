#!/bin/bash

# 验证虚拟环境脚本

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info "验证Python环境..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    print_error "虚拟环境不存在"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查Python位置
python_path=$(which python3)
if [[ $python_path == *"venv"* ]]; then
    print_success "Python路径正确: $python_path"
else
    print_error "Python路径错误: $python_path"
    exit 1
fi

# 检查包是否在虚拟环境中
print_info "检查安装的包..."
pip_packages=$(pip list | wc -l)
if [ $pip_packages -gt 5 ]; then
    print_success "虚拟环境中包含 $pip_packages 个包"
    
    # 显示项目相关包
    echo ""
    print_info "项目依赖包:"
    pip list | grep -E "(requests|networkx|colorama|pyyaml|loguru|psutil)"
else
    print_error "虚拟环境中包数量异常: $pip_packages"
    exit 1
fi

# 测试导入
print_info "测试模块导入..."
python3 -c "
try:
    import requests
    import networkx
    import colorama
    import yaml
    from loguru import logger
    import psutil
    print('✓ 所有模块导入成功')
except ImportError as e:
    print(f'✗ 模块导入失败: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    print_success "环境验证完成！"
else
    print_error "环境验证失败"
    exit 1
fi