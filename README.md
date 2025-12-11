# SDN网络通信系统

基于SDN（软件定义网络）架构的网络通信系统，使用ONOS控制器、Mininet仿真环境和Python开发语言。

## 功能特性

- 集中控制的网络管理
- 动态路径计算（Dijkstra算法）
- 智能流表管理
- 实时拓扑发现
- 故障自动恢复
- 命令行管理界面

## 系统要求

### 硬件要求
- CPU: 4核以上
- 内存: 8GB以上
- 存储: 20GB以上可用空间

### 软件要求
- 操作系统: Ubuntu 18.04+ 或 CentOS 7+
- Docker: 19.03+
- Python: 3.7+
- Mininet: 2.3.0+
- Open vSwitch: 2.17.0+

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd SDN_network

# 安装Python依赖
pip3 install -r requirements.txt

# 设置脚本权限
chmod +x run.sh
```

### 2. 启动系统

#### 方式一：使用启动脚本（推荐）

```bash
# 启动完整系统（ONOS + SDN应用）
./run.sh

# 或者分步启动
./run.sh start-onos    # 启动ONOS控制器
./run.sh start-app     # 启动SDN应用
```

#### 方式二：手动启动

```bash
# 1. 启动ONOS控制器
docker-compose up -d

# 2. 等待ONOS启动完成（约30秒）
curl -u onos:rocks http://localhost:8181/onos/v1/devices

# 3. 启动SDN应用
python3 main_app.py --with-mininet
```

### 3. 验证系统

在Mininet CLI中测试连通性：

```bash
mininet> h1 ping h2 -c 3
mininet> h1 ping h8 -c 3
mininet> h3 ping h7 -c 3
```

## 使用指南

### 启动脚本选项

```bash
./run.sh [选项]

选项:
  start-onos      启动ONOS控制器
  stop-onos       停止ONOS控制器
  status          检查ONOS状态
  start-app       启动SDN应用（包含Mininet）
  start-mininet   仅启动Mininet拓扑
  test            测试项目模块
  cleanup         清理环境
  install-deps    安装Python依赖
  help            显示帮助信息
```

### SDN应用CLI命令

启动SDN应用后，可以使用以下命令：

```bash
sdn> status          # 显示网络状态
sdn> topology        # 显示拓扑信息
sdn> hosts           # 显示主机列表
sdn> flows           # 显示流表统计
sdn> path <src> <dst> # 计算主机间路径
sdn> enable <src> <dst> # 启用主机间通信
sdn> enable-all      # 启用所有主机通信
sdn> ping <src> <dst> # 测试主机连通性
sdn> help            # 显示帮助信息
sdn> quit            # 退出程序
```

### Mininet拓扑选项

```bash
# 启动不同的拓扑
python3 topology.py --topo linear --switches 4 --hosts-per-switch 2
python3 topology.py --topo tree --depth 2 --fanout 2
python3 topology.py --topo custom
```

## 项目结构

```
SDN_network/
├── controller_client.py    # ONOS控制器客户端
├── path_calculator.py      # 路径计算模块
├── flow_manager.py         # 流表管理模块
├── main_app.py            # 主应用程序
├── topology.py            # Mininet拓扑配置
├── requirements.txt       # Python依赖
├── run.sh                 # 启动脚本
├── docker-compose.yml     # Docker配置
├── IFLOW.md              # 项目上下文文件
├── reqiurement.md        # 需求文档
└── README.md             # 项目说明
```

## 核心模块说明

### controller_client.py
- `ONOSControllerClient`: 与ONOS控制器REST API通信
- `TopologyManager`: 管理网络拓扑信息

### path_calculator.py
- `PathCalculator`: 实现Dijkstra最短路径算法
- `HostPathCalculator`: 计算主机间路径

### flow_manager.py
- `FlowRuleBuilder`: 构建OpenFlow流表规则
- `FlowManager`: 管理流表安装和维护
- `NetworkCommunicator`: 协调网络通信

### main_app.py
- `SDNControllerApp`: 主应用程序，集成所有组件
- `MininetTopology`: Mininet拓扑管理

## 配置说明

### ONOS控制器配置
- URL: http://localhost:8181
- 用户名: onos
- 密码: rocks
- OpenFlow版本: 1.3

### 网络拓扑配置
- 默认拓扑: 4个交换机的线性拓扑
- 每个交换机连接2个主机
- 支持自定义拓扑结构

## 故障排除

### 常见问题

1. **ONOS启动失败**
   ```bash
   # 检查Docker状态
   docker ps
   
   # 查看ONOS日志
   docker logs onos
   ```

2. **Python模块导入错误**
   ```bash
   # 检查Python路径
   python3 -c "import sys; print(sys.path)"
   
   # 安装缺失的依赖
   pip3 install -r requirements.txt
   ```

3. **Mininet权限问题**
   ```bash
   # 确保有sudo权限
   sudo python3 topology.py
   ```

4. **网络连通性问题**
   ```bash
   # 检查ONOS设备状态
   curl -u onos:rocks http://localhost:8181/onos/v1/devices
   
   # 检查流表规则
   curl -u onos:rocks http://localhost:8181/onos/v1/flows/of:0000000000000001
   ```

### 日志查看

```bash
# 查看应用日志
tail -f sdn_network.log

# 查看ONOS日志
docker logs -f onos
```

## 开发指南

### 添加新的拓扑类型

1. 在`topology.py`中创建新的拓扑类
2. 继承`Topo`基类
3. 实现`__init__`方法
4. 在`main()`函数中添加选项

### 扩展流表规则

1. 在`flow_manager.py`中的`FlowRuleBuilder`类添加新方法
2. 定义匹配条件和动作
3. 在`FlowManager`中调用新方法

### 添加新的路径算法

1. 在`path_calculator.py`中的`PathCalculator`类添加新算法
2. 实现算法逻辑
3. 在`HostPathCalculator`中调用新算法

## 性能指标

- 路径计算延迟: < 100ms
- 流表安装时间: < 50ms
- 网络规模支持: 至少100台主机
- 控制器处理能力: > 1000流表/秒

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

如有问题或建议，请提交Issue或联系项目维护者。