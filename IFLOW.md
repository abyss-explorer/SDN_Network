# SDN网络通信系统 - iFlow 上下文文件

## 项目概述

这是一个基于SDN（软件定义网络）架构的网络通信系统项目，使用ONOS 2.7.0控制器、Mininet仿真环境和Python 3开发语言。项目实现了SDN控制器对网络的集中控制，通过Dijkstra路径计算算法确保任意两点间通信，并实现了动态流表管理机制。

**项目状态**：✅ 核心功能已完成并测试通过
- 路径计算功能正常
- 流表安装功能正常
- 主机间通信功能正常

## 技术栈

- **控制器**: ONOS 2.7.0 (Open Network Operating System)
- **数据平面仿真**: Mininet 2.3.0+
- **开发语言**: Python 3.7+
- **通信协议**: OpenFlow 1.3
- **核心依赖**: requests, networkx, psutil, colorama, pyyaml, loguru

## 系统架构

项目采用三层架构：

```
┌─────────────────────────────────────────┐
│      Python应用程序层 (SDN App)          │
│  ┌──────────────┐  ┌─────────────────┐  │
│  │ NetworkCom-  │  │ PathCalculator  │  │
│  │ municator    │  │ (Dijkstra)      │  │
│  └──────────────┘  └─────────────────┘  │
│  ┌──────────────┐  ┌─────────────────┐  │
│  │ FlowManager  │  │ TopologyManager │  │
│  └──────────────┘  └─────────────────┘  │
│  ┌──────────────┐                      │
│  │ IntentMana-  │                      │
│  │ ger         │                      │
│  └──────────────┘                      │
│  ┌──────────────┐                      │
│  │ 监控与拓扑    │                      │
│  │ 变化处理      │                      │
│  └──────────────┘                      │
└─────────────────────────────────────────┘
                    ↕ REST API
┌─────────────────────────────────────────┐
│        ONOS控制器层 (2.7.0)              │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ 拓扑发现 │ │ 路由服务 │ │ 流表管理│ │
│  └──────────┘ └──────────┘ └─────────┘ │
│              ┌─────────────────┐       │
│              │ Intent管理      │       │
│              └─────────────────┘       │
└─────────────────────────────────────────┘
                    ↕ OpenFlow 1.3
┌─────────────────────────────────────────┐
│         网络数据平面 (Mininet)           │
│  ┌─────┐    ┌─────┐    ┌─────┐         │
│  │ s1  │────│ s2  │────│ s3  │         │
│  └─────┘    └─────┘    └─────┘         │
│  h1  h2     h3  h4     h5  h6          │
└─────────────────────────────────────────┘
```

## 核心模块结构

### 1. 控制器客户端模块 (controller_client.py)

#### ONOSControllerClient类
与ONOS控制器进行REST API通信，处理所有HTTP请求。

**关键方法**：
- `test_connection()`: 测试控制器连接
- `get_topology()`: 获取完整网络拓扑
- `get_devices()`: 获取交换机设备信息
- `get_hosts()`: 获取主机信息
- `get_links()`: 获取链路信息
- `install_flow_rule(device_id, flow_rule)`: 安装流表规则

**重要实现细节**：
- 使用`requests.Session`管理认证
- 不设置默认headers，避免415错误
- 主机位置从`locations`数组获取（非`location`对象）

#### TopologyManager类
管理网络拓扑信息，构建图结构用于路径计算。

**关键方法**：
- `update_topology()`: 更新拓扑信息并重建图
- `_build_graph()`: 构建用于路径计算的图结构
- `get_host_location(mac)`: 获取主机位置
- `get_device_by_host(mac)`: 获取主机连接的交换机

**图结构格式**：
```python
graph = {
    'of:0000000000000001': [('of:0000000000000002', 1)],
    'of:0000000000000002': [('of:0000000000000001', 1)]
}
```

### 2. 路径计算模块 (path_calculator.py)

#### PathCalculator类
实现Dijkstra最短路径算法和K最短路径算法。

**关键方法**：
- `dijkstra(start, end)`: 计算最短路径
- `find_all_paths(start, end)`: 查找所有可能路径
- `k_shortest_paths(start, end, k)`: K最短路径算法
- `get_graph_stats()`: 获取图统计信息

**算法特点**：
- 使用heapq实现优先队列
- 时间复杂度：O((V+E)logV)
- 支持带权图

#### HostPathCalculator类
计算主机间路径，封装PathCalculator。

**关键方法**：
- `get_host_to_host_path(src_mac, dst_mac)`: 计算主机间路径
- `get_optimal_route(src_mac, dst_mac)`: 获取最优路由信息

**重要修复**：动态创建PathCalculator实例，确保使用最新的图结构。

```python
# 修复前（错误）
def __init__(self, topology_manager):
    self.path_calculator = PathCalculator(topology_manager.graph)  # 空图

# 修复后（正确）
def get_host_to_host_path(self, src_mac, dst_mac):
    path_calculator = PathCalculator(self.topology_manager.graph)  # 最新图
    device_path, distance = path_calculator.dijkstra(src_device, dst_device)
```

### 3. 流表管理模块 (flow_manager.py)

#### FlowRuleBuilder类
构建符合ONOS API规范的流表规则。

**关键方法**：
- `create_basic_flow_rule(device_id, match_criteria, output_port)`: 创建基本流表
- `create_host_to_host_flow(device_id, src_mac, dst_mac, output_port)`: 创建主机间流表
- `create_broadcast_flow(device_id, dst_mac, output_ports)`: 创建广播流表
- `create_arp_flow(device_id, output_ports)`: 创建ARP流表

**流表规则格式（ONOS 2.7.0）**：
```python
flow_rule = {
    "priority": 40000,
    "timeout": 0,
    "isPermanent": True,
    "deviceId": "of:0000000000000001",
    "appId": "org.onosproject.rest",  # 必需字段
    "treatment": {
        "instructions": [
            {"type": "OUTPUT", "port": "1"}
        ]
    },
    "selector": {
        "criteria": [
            {"type": "ETH_DST", "mac": "00:00:00:00:00:01"}
        ]
    }
}
```

**重要修复**：
1. 移除外层`"flow"`键
2. 添加必需的`appId`字段
3. 端口号使用字符串格式

#### FlowManager类
管理流表安装和维护。

**关键方法**：
- `install_host_to_host_flows(route_info)`: 安装主机间流表
- `clear_device_flows(device_id)`: 清除设备流表

#### NetworkCommunicator类
协调路径计算和流表管理，实现端到端通信。

**关键方法**：
- `enable_host_communication(src_mac, dst_mac)`: 启用主机间通信
- `enable_all_host_communication()`: 启用所有主机通信

### 4. Intent管理模块 (intent_manager.py)

#### IntentManager类
负责在ONOS中创建和管理Intent，用于在UI中突显监控路径。

**关键方法**：
- `create_host_intent(src_mac, dst_mac)`: 创建主机间Intent（在ONOS UI中显示为突显的线路）
- `delete_host_intent(src_mac, dst_mac)`: 删除主机间Intent
- `get_intents()`: 获取所有Intent
- `get_host_intents()`: 获取所有Host Intent
- `delete_all_host_intents()`: 删除所有Host Intent

**Intent数据格式**：
```python
intent_data = {
    "type": "HostToHostIntent",
    "appId": "org.onosproject.core",
    "one": f"{src_mac}/None",
    "two": f"{dst_mac}/None",
    "priority": 100
}
```

### 5. 主应用程序模块 (main_app.py)

#### SDNControllerApp类
集成所有组件并管理网络生命周期，新增实时监控功能。

**关键方法**：
- `initialize_components()`: 初始化所有组件
- `setup_network_communication()`: 设置网络通信
- `run_mininet_simulation()`: 运行Mininet仿真
- `start_cli()`: 启动命令行接口
- `add_monitored_pair(src_mac, dst_mac)`: 添加监控节点对
- `remove_monitored_pair(src_mac, dst_mac)`: 移除监控节点对
- `start_monitoring()`: 启动监控线程
- `_monitoring_loop()`: 监控循环
- `_handle_topology_change()`: 处理拓扑变化

**监控功能**：
- 实时监控拓扑变化
- 自动检测网络连通性变化
- 拓扑变化时自动重新计算路径并下发流表
- 通过Intent在ONOS UI中突显监控路径

### 6. 拓扑配置模块 (topology.py)

支持多种网络拓扑类型：
- **LinearTopology**: 线性拓扑（默认4交换机）
- **TreeTopology**: 树形拓扑
- **CustomTopology**: 自定义拓扑

## 项目文件结构

```
SDN_network/
├── controller_client.py        # ONOS控制器客户端和拓扑管理
├── path_calculator.py          # Dijkstra路径计算算法
├── flow_manager.py             # 流表规则构建和管理
├── intent_manager.py           # Intent管理模块，用于在ONOS UI中突显路径
├── main_app.py                 # 主应用程序和CLI
├── topology.py                 # Mininet拓扑配置
├── test_utils.py               # 测试工具模块
├── requirements.txt            # Python依赖列表
├── quick_start.sh              # 快速启动脚本
├── run.sh                      # 完整启动脚本
├── verify_env.sh               # 环境验证脚本
│
├── test_onos.py                # ONOS连接测试
├── simple_test.py              # 简化功能测试
├── test_communication.py       # 通信功能测试
├── integration_test.py         # 集成测试
├── debug_flow.py               # 流表调试工具
├── debug_graph.py              # 图结构调试工具
│
├── IFLOW.md                    # 项目上下文文件（本文件）
├── README.md                   # 项目说明文档
├── reqiurements_documents.md   # 需求文档
├── 修复总结.md                  # 问题修复总结
├── sdn_network.log             # 应用日志文件
│
├── venv/                       # Python虚拟环境
└── __pycache__/                # Python缓存文件
```

## 环境要求和设置

### 硬件要求
- CPU: 4核以上
- 内存: 8GB以上
- 存储: 20GB以上可用空间

### 软件要求
- 操作系统: Ubuntu 18.04+ 或 CentOS 7+
- Docker: 19.03+ （用于运行ONOS）
- Python: 3.7+ （推荐3.10）
- Git

### Python依赖
```
requests>=2.28.0      # HTTP请求库
psutil>=5.9.0         # 系统工具
networkx>=2.8.0       # 图处理（路径计算）
colorama>=0.4.4       # CLI颜色输出
pyyaml>=6.0           # 配置文件处理
loguru>=0.6.0         # 日志处理
```

## 快速启动指南

### 方式一：使用快速启动脚本（推荐）

```bash
# 1. 确保ONOS已运行
docker ps | grep onos

# 2. 运行快速启动脚本
./quick_start.sh

# 3. 启动SDN应用
python3 main_app.py --with-mininet
```

### 方式二：手动启动

```bash
# 1. 启动ONOS控制器（如未运行）
docker run -t -d --name onos -p 8181:8181 -p 8101:8101 onosproject/onos:2.7.0

# 2. 等待ONOS启动（约30秒）
curl -u onos:rocks http://localhost:8181/onos/v1/devices

# 3. 创建虚拟环境
python3 -m venv venv --copies
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 启动SDN应用
python3 main_app.py --with-mininet
```

### 方式三：使用完整启动脚本

```bash
# 查看所有选项
./run.sh help

# 启动ONOS
./run.sh start-onos

# 启动SDN应用
./run.sh start-app

# 检查状态
./run.sh status
```

## 测试和验证

### 1. 基础连接测试

```bash
# 测试ONOS连接
python3 test_onos.py

# 预期输出：
# ✓ ONOS控制器连接成功
# ✓ 设备数量: 4
# ✓ 主机数量: 4-8
```

### 2. 简化功能测试

```bash
# 运行简化测试
python3 simple_test.py

# 预期输出：
# ✓ ONOS控制器连接成功
# ✓ 拓扑更新成功
# ✓ 路径计算成功
#   路径: host_MAC1 -> switch1 -> switch2 -> host_MAC2
#   跳数: 1
#   质量: excellent
```

### 3. 通信功能测试

```bash
# 测试主机间通信
python3 test_communication.py

# 预期输出：
# ✓ 通信建立成功!
# INFO: 流表安装成功
```

### 4. 端到端通信测试

在Mininet CLI中执行：
```bash
mininet> h1 ping h2 -c 3
# 预期：0% packet loss

mininet> h1 ping h8 -c 3
# 预期：0% packet loss（如果流表已安装）
```

### 5. 性能测试

```bash
# 带宽测试
mininet> h1 iperf h2 -t 10
```

## 调试工具

### 1. 图结构调试

```bash
python3 debug_graph.py

# 输出：
# - 节点列表
# - 邻接关系
# - 链路信息
```

### 2. 流表调试

```bash
python3 debug_flow.py

# 输出：
# - 流表规则JSON
# - 安装结果
```

### 3. 查看ONOS状态

```bash
# 设备信息
curl -u onos:rocks http://localhost:8181/onos/v1/devices | python3 -m json.tool

# 主机信息
curl -u onos:rocks http://localhost:8181/onos/v1/hosts | python3 -m json.tool

# 链路信息
curl -u onos:rocks http://localhost:8181/onos/v1/links | python3 -m json.tool

# 流表信息
curl -u onos:rocks http://localhost:8181/onos/v1/flows/of:0000000000000001 | python3 -m json.tool

# Intent信息
curl -u onos:rocks http://localhost:8181/onos/v1/intents | python3 -m json.tool
```

## 命令行接口功能

### SDN应用CLI命令

启动SDN应用后，可以使用以下命令：

```bash
sdn> status                    # 显示网络状态
sdn> topology                  # 显示拓扑信息
sdn> hosts                     # 显示主机列表
sdn> flows                     # 显示流表统计
sdn> path <src> <dst>          # 计算主机间路径
sdn> enable <src> <dst>        # 启用主机间通信
sdn> enable-all                # 启用所有主机通信
sdn> ping <src> <dst>          # 测试主机连通性
sdn> monitor <src> <dst>       # 添加监控节点对
sdn> unmonitor <src> <dst>     # 移除监控节点对
sdn> show-monitors             # 显示监控的节点对
sdn> start-monitoring          # 启动监控
sdn> stop-monitoring           # 停止监控
sdn> start-mininet             # 启动Mininet拓扑 (需要sudo权限)
sdn> help                      # 显示帮助信息
sdn> quit/exit                 # 退出程序
```

**监控功能**：
- `monitor`命令：添加要监控的节点对，会在ONOS UI中突显路径
- `unmonitor`命令：移除监控的节点对
- `start-monitoring`命令：启动网络监控，实时检测拓扑变化
- `stop-monitoring`命令：停止网络监控
- `show-monitors`命令：显示当前监控的节点对

## 开发约定和最佳实践

### 代码风格
- 使用Python 3.7+语法特性
- 遵循PEP 8代码风格指南
- 使用类型提示增强代码可读性
- 采用模块化设计原则
- 添加详细的docstring文档

### 错误处理
- 实现完整的异常处理机制
- 提供详细的错误日志记录
- 确保网络连接失败时的优雅降级
- 使用logging模块记录调试信息

### API设计原则
- REST API调用使用统一的错误处理
- 实现重试机制处理网络不稳定
- 提供清晰的API响应格式
- 避免在GET请求中设置Content-Type头

### 关键技术要点

#### 1. Python对象引用问题
当传递可变对象（如字典）时，传递的是引用而非副本。需要确保使用最新状态：

```python
# 错误：初始化时图为空
self.path_calculator = PathCalculator(topology_manager.graph)

# 正确：每次使用时创建新实例
path_calculator = PathCalculator(self.topology_manager.graph)
```

#### 2. ONOS API格式要求
- 流表规则不需要外层`"flow"`包装
- 必须包含`appId`字段
- 端口号使用字符串格式
- GET请求不要设置Content-Type头

#### 3. 虚拟环境隔离
使用`--copies`参数创建完全隔离的虚拟环境：

```bash
python3 -m venv venv --copies
```

## 关键API端点

### ONOS控制器REST API
- **基础URL**: `http://localhost:8181`
- **认证**: Basic Auth (onos:rocks)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/onos/v1/devices` | GET | 获取所有设备信息 |
| `/onos/v1/hosts` | GET | 获取所有主机信息 |
| `/onos/v1/links` | GET | 获取所有链路信息 |
| `/onos/v1/flows/{deviceId}` | GET | 获取设备流表 |
| `/onos/v1/flows/{deviceId}` | POST | 安装流表规则 |
| `/onos/v1/flows/{deviceId}/{flowId}` | DELETE | 删除流表规则 |

### 认证信息
- 用户名: `onos`
- 密码: `rocks`

## 性能指标

实际测试结果：
- ✅ 路径计算延迟: < 50ms
- ✅ 流表安装时间: < 30ms
- ✅ 网络规模支持: 已测试4交换机8主机
- ⏳ 控制器处理能力: > 1000流表/秒（理论值）
- ⏳ 并发连接数: 至少50台交换机（理论值）

## 故障排除

### 常见问题及解决方案

#### 1. 路径计算失败
**症状**：`ERROR: 节点不存在`

**原因**：PathCalculator使用了空图或旧图

**解决**：确保动态创建PathCalculator实例
```python
path_calculator = PathCalculator(self.topology_manager.graph)
```

#### 2. 流表安装失败（400错误）
**症状**：`400 Client Error: Bad Request`

**原因**：流表规则格式不正确

**解决**：
- 移除外层`"flow"`键
- 添加`appId`字段
- 确保端口号为字符串

#### 3. ONOS连接失败（415错误）
**症状**：`415 Unsupported Media Type`

**原因**：GET请求不应包含Content-Type头

**解决**：使用session.auth而非headers
```python
self.session.auth = (username, password)
response = self.session.get(url)  # 不设置headers
```

#### 4. 主机位置解析错误
**症状**：`无法获取主机连接的设备`

**原因**：ONOS API返回`locations`数组而非`location`对象

**解决**：
```python
locations = host.get('locations', [])
location = locations[0] if locations else {}
```

#### 5. 虚拟环境污染全局
**症状**：包安装到全局Python环境

**解决**：使用`--copies`参数
```bash
python3 -m venv venv --copies
```

### 调试命令

```bash
# 检查ONOS容器状态
docker ps | grep onos
docker logs onos

# 检查ONOS应用状态
ssh -p 8101 onos@localhost  # 密码: rocks
onos> apps -s -a

# 检查网络连通性
ping localhost -c 3
telnet localhost 8181

# 查看应用日志
tail -f sdn_network.log

# 检查Python进程
ps aux | grep python
```

## 已知问题和限制

1. **网络规模**：当前仅测试了小规模网络（4交换机8主机）
2. **拓扑动态性**：支持运行时拓扑变化的自动适应（通过监控功能）
3. **故障恢复**：实现了链路故障的部分自动恢复机制（通过拓扑变化处理）
4. **负载均衡**：未实现多路径负载均衡
5. **QoS支持**：未实现服务质量保证机制
6. **Intent管理**：Intent用于UI突显，但未用于实际流量控制

## 扩展性考虑

### 添加新的拓扑类型
1. 在`topology.py`中创建新的拓扑类
2. 继承`Topo`基类
3. 实现`__init__`方法
4. 在`main()`函数中添加选项

### 扩展流表规则
1. 在`FlowRuleBuilder`类添加新方法
2. 定义匹配条件和动作
3. 在`FlowManager`中调用新方法

### 添加新的路径算法
1. 在`PathCalculator`类添加新算法
2. 实现算法逻辑
3. 在`HostPathCalculator`中调用

## 安全要求

- ✅ 实现控制器身份验证（Basic Auth）
- ⏳ 支持交换机证书验证
- ⏳ 防止恶意流表注入
- ⏳ 网络访问控制

## 项目里程碑

- [x] 2025-12-11: 完成核心功能开发
- [x] 2025-12-11: 修复路径计算问题
- [x] 2025-12-11: 修复流表安装问题
- [x] 2025-12-11: 完成基础测试
- [x] 2025-12-16: 添加Intent管理功能，支持在ONOS UI中突显路径
- [x] 2025-12-16: 添加实时监控和拓扑变化处理功能
- [ ] 待定: 实现故障恢复机制
- [ ] 待定: 实现负载均衡
- [ ] 待定: 性能优化和压力测试

## 参考资源

- [ONOS官方文档](https://wiki.onosproject.org/)
- [OpenFlow 1.3规范](https://www.opennetworking.org/software-defined-standards/specifications/)
- [Mininet文档](http://mininet.org/)
- [Python NetworkX文档](https://networkx.org/)

## 维护者信息

项目当前状态：**开发完成，测试通过**

如有问题或建议，请查看`修复总结.md`或提交Issue。

---

*最后更新：2025-12-11*  
*版本：1.0.0*  
*此文件提供了SDN网络通信系统的完整上下文信息，包括架构设计、实现细节、调试经验和最佳实践。*