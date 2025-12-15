#!/bin/bash

# SDN网络通信系统启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装 $1"
        return 1
    fi
    return 0
}

# 检查Docker是否运行
check_docker() {
    if ! docker info &> /dev/null; then
        print_error "Docker 未运行，请启动Docker服务"
        return 1
    fi
    return 0
}

# 检查Python依赖
check_python_deps() {
    print_info "检查Python依赖..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt 文件不存在"
        return 1
    fi
    
    # 检查pip是否可用
    if ! check_command pip3; then
        return 1
    fi
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        print_info "创建Python虚拟环境..."
        python3 -m venv venv --copies
        if [ $? -ne 0 ]; then
            print_error "虚拟环境创建失败"
            return 1
        fi
    fi
    
    # 激活虚拟环境
    print_info "激活虚拟环境..."
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    print_info "安装Python依赖..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "Python依赖安装完成"
        return 0
    else
        print_error "Python依赖安装失败"
        return 1
    fi
}

# 检查ONOS控制器状态
check_onos_status() {
    print_info "检查ONOS控制器状态..."
    
    if curl -s -u onos:rocks http://localhost:8181/onos/v1/devices &> /dev/null; then
        print_success "ONOS控制器运行正常"
        
        # 显示设备信息
        echo "设备信息:"
        curl -s -u onos:rocks http://localhost:8181/onos/v1/devices | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    devices = data.get('devices', [])
    if devices:
        for device in devices:
            print(f\"  {device['id']}: {device['type']} - {'活跃' if device['available'] else '非活跃'}\")
    else:
        print(\"  无设备连接\")
except:
    print(\"  无法解析设备信息\")
"
        
        return 0
    else
        print_error "ONOS控制器未响应"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "SDN网络通信系统启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  status          检查ONOS状态"
    echo "  start-app       启动SDN应用（包含Mininet）"
    echo "  start-mininet   仅启动Mininet拓扑"
    echo "  test            测试项目模块"
    echo "  cleanup         清理环境"
    echo "  install-deps    安装Python依赖"
    echo "  help            显示此帮助信息"
    echo ""
    echo "注意: ONOS控制器应该在后台运行，本脚本不管理ONOS的启动和停止"
    echo ""
    echo "示例:"
    echo "  $0 status        # 检查ONOS状态"
    echo "  $0 start-app     # 启动SDN应用"
    echo "  $0 cleanup        # 清理环境"
}

# 启动SDN应用
start_sdn_app() {
    print_info "启动SDN网络通信系统..."
    
    # 检查Python文件是否存在
    if [ ! -f "main_app.py" ]; then
        print_error "main_app.py 文件不存在"
        return 1
    fi
    
    # 激活虚拟环境
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # 启动应用
    python main_app.py --with-mininet --switches 4 --hosts-per-switch 2
}

# 仅启动Mininet拓扑
start_mininet_only() {
    print_info "启动Mininet拓扑..."
    
    if [ ! -f "topology.py" ]; then
        print_error "topology.py 文件不存在"
        return 1
    fi
    
    # 激活虚拟环境
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # 启动Mininet拓扑
    python topology.py --topo linear --switches 4 --hosts-per-switch 2
}

# 测试模块
test_modules() {
    print_info "测试项目模块..."
    
    # 激活虚拟环境
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # 测试控制器客户端
    print_info "测试控制器客户端..."
    python controller_client.py
    
    # 测试路径计算
    print_info "测试路径计算模块..."
    python path_calculator.py
    
    # 测试流表管理
    print_info "测试流表管理模块..."
    python flow_manager.py
    
    print_success "模块测试完成"
}

# 清理环境
cleanup() {
    print_info "清理环境..."
    
    # 清理虚拟环境
    if [ -d "venv" ]; then
        print_info "删除Python虚拟环境..."
        rm -rf venv
    fi
    
    # 清理临时文件
    rm -f /tmp/linear_topology.py
    
    print_success "环境清理完成"
}


# 主函数
main() {
    case "$1" in
        "status")
            check_onos_status
            ;;
        "start-app")
            check_onos_status || exit 1
            check_python_deps || exit 1
            start_sdn_app
            ;;
        "start-mininet")
            check_python_deps || exit 1
            start_mininet_only
            ;;
        "test")
            test_modules
            ;;
        "cleanup")
            cleanup
            ;;
        "install-deps")
            check_python_deps
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        "")
            print_info "启动SDN网络通信系统..."
            check_onos_status || exit 1
            check_python_deps || exit 1
            start_sdn_app
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 捕获中断信号
trap cleanup EXIT

# 执行主函数
main "$@"