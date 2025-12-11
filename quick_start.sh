#!/bin/bash

# SDN网络通信系统快速启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查ONOS是否运行
print_info "检查ONOS控制器状态..."
if curl -s -u onos:rocks http://localhost:8181/onos/v1/devices &> /dev/null; then
    print_success "ONOS控制器运行正常"
else
    print_error "ONOS控制器未响应，请确保ONOS正在运行"
    exit 1
fi

# 创建虚拟环境并安装最小依赖
print_info "设置Python环境..."

# 检查python3-venv是否可用
if ! python3 -c "import venv" 2>/dev/null; then
    print_error "python3-venv未安装"
    print_info "请运行以下命令安装："
    print_info "  sudo apt update && sudo apt install python3-venv"
    exit 1
fi

if [ ! -d "venv" ]; then
    print_info "创建Python虚拟环境..."
    python3 -m venv venv --copies
    if [ $? -ne 0 ]; then
        print_error "虚拟环境创建失败"
        exit 1
    fi
    
    print_info "激活虚拟环境并安装依赖..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install requests networkx colorama pyyaml loguru psutil
else
    print_info "激活虚拟环境..."
    source venv/bin/activate
fi

if [ $? -eq 0 ]; then
    print_success "Python环境设置完成"
else
    print_error "Python环境设置失败"
    exit 1
fi

print_success "系统准备完成！"
print_info "现在可以运行以下命令启动SDN应用："
print_info "  python main_app.py --with-mininet"
print_info ""
print_info "或者只启动Mininet拓扑："
print_info "  python topology.py --topo linear --switches 4 --hosts-per-switch 2"