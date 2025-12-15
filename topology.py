#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mininet拓扑配置文件
创建可配置的网络拓扑，支持不同的拓扑结构和参数
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink, Intf
from mininet.log import setLogLevel, info
from mininet.topo import Topo
from mininet.util import custom, quietRun
import time
import argparse
import sys


class LinearTopology(Topo):
    """线性拓扑类"""
    
    def __init__(self, num_switches=4, hosts_per_switch=2, **params):
        """
        初始化线性拓扑
        
        Args:
            num_switches: 交换机数量
            hosts_per_switch: 每个交换机连接的主机数量
        """
        Topo.__init__(self, **params)
        
        # 创建交换机
        switches = []
        for i in range(num_switches):
            switch = self.addSwitch(f's{i+1}', cls=OVSSwitch, protocols='OpenFlow13')
            switches.append(switch)
        
        # 创建主机并连接到交换机
        host_count = 0
        for i, switch in enumerate(switches):
            for j in range(hosts_per_switch):
                host_count += 1
                host = self.addHost(f'h{host_count}')
                self.addLink(host, switch, bw=10)  # 10 Mbps带宽
        
        # 连接交换机（线性连接）
        for i in range(num_switches - 1):
            self.addLink(switches[i], switches[i+1], bw=20)  # 20 Mbps带宽


class TreeTopology(Topo):
    def __init__(self, depth=2, fanout=2, **params):
        super().__init__(**params)
        self.switch_counter = 1  # s1 is root
        self.host_counter = 0
        
        root = self.addSwitch('s1', cls=OVSSwitch, protocols='OpenFlow13')
        self._create_tree_level(root, 1, depth, fanout)
    
    def _create_tree_level(self, parent, level, max_depth, fanout):
        if level >= max_depth:
            return
        
        for i in range(fanout):
            self.switch_counter += 1
            child = self.addSwitch(f's{self.switch_counter}', cls=OVSSwitch, protocols='OpenFlow13')
            self.addLink(parent, child, bw=20)
            
            if level == max_depth - 1:
                for j in range(2):
                    self.host_counter += 1
                    host = self.addHost(f'h{self.host_counter}')
                    self.addLink(host, child, bw=10)
            
            self._create_tree_level(child, level + 1, max_depth, fanout)


class CustomTopology(Topo):
    """自定义拓扑类"""
    
    def __init__(self, topology_config=None, **params):
        """
        初始化自定义拓扑
        
        Args:
            topology_config: 拓扑配置字典
        """
        Topo.__init__(self, **params)
        
        switches = {}
        hosts = {}
        
        # 如果没有提供配置，使用默认配置
        if topology_config is None:
            topology_config = {
                'switches': ['s1', 's2', 's3', 's4'],
                'hosts': [
                    {'id': 'h1', 'switch': 's1', 'bw': 10},
                    {'id': 'h2', 'switch': 's1', 'bw': 10},
                    {'id': 'h3', 'switch': 's2', 'bw': 10},
                    {'id': 'h4', 'switch': 's2', 'bw': 10},
                    {'id': 'h5', 'switch': 's3', 'bw': 10},
                    {'id': 'h6', 'switch': 's3', 'bw': 10},
                    {'id': 'h7', 'switch': 's4', 'bw': 10},
                    {'id': 'h8', 'switch': 's4', 'bw': 10}
                ],
                'links': [
                    {'src': 's1', 'dst': 's2', 'bw': 20},
                    {'src': 's2', 'dst': 's3', 'bw': 20},
                    {'src': 's3', 'dst': 's4', 'bw': 20},
                    {'src': 's1', 'dst': 's3', 'bw': 15},
                    {'src': 's2', 'dst': 's4', 'bw': 15}
                ]
            }
        
        links = topology_config.get('links', [])
        
        # 创建交换机
        for switch_id in topology_config.get('switches', []):
            switch = self.addSwitch(switch_id, cls=OVSSwitch, protocols='OpenFlow13')
            switches[switch_id] = switch
        
        # 创建主机
        for host_config in topology_config.get('hosts', []):
            host_id = host_config['id']
            host = self.addHost(host_id)
            hosts[host_id] = host
            
            # 连接主机到交换机
            switch_id = host_config['switch']
            port = host_config.get('port', 1)
            self.addLink(host, switches[switch_id], bw=host_config.get('bw', 10))
        
        # 创建交换机间链路
        for link in links:
            src_switch = link['src']
            dst_switch = link['dst']
            bw = link.get('bw', 20)
            self.addLink(switches[src_switch], switches[dst_switch], bw=bw)


class NetworkManager:
    """网络管理器"""
    
    def __init__(self, topo, controller_ip='127.0.0.1', controller_port=6653):
        """
        初始化网络管理器
        
        Args:
            topo: 拓扑对象
            controller_ip: 控制器IP地址
            controller_port: 控制器端口
        """
        self.topo = topo
        self.controller_ip = controller_ip
        self.controller_port = controller_port
        self.net = None
    
    def create_network(self):
        """创建网络"""
        info("*** 创建网络\n")
        
        self.net = Mininet(
            topo=self.topo,
            controller=lambda name: RemoteController(
                name, 
                ip=self.controller_ip, 
                port=self.controller_port
            ),
            link=TCLink,
            switch=custom(OVSSwitch, protocols='OpenFlow13'),
            waitConnected=True
        )
        
        return self.net
    
    def start_network(self):
        """启动网络"""
        if not self.net:
            self.create_network()
        
        info("*** 启动网络\n")
        self.net.start()
        
        # 等待交换机连接到控制器
        info("*** 等待交换机连接到控制器\n")
        time.sleep(10)
        
        # 验证控制器连接
        self._verify_controller_connection()
    
    def _verify_controller_connection(self):
        """验证控制器连接"""
        info("*** 验证控制器连接\n")
        
        for switch in self.net.switches:
            if 'OVSSwitch' in str(type(switch)):
                # 检查交换机是否连接到控制器
                if switch.connected():
                    info(f"交换机 {switch.name} 已连接到控制器\n")
                else:
                    info(f"警告: 交换机 {switch.name} 未连接到控制器\n")
    
    def configure_hosts(self, ip_config=None):
        """配置主机IP地址"""
        info("*** 配置主机IP地址\n")
        
        if not ip_config:
            ip_config = self._generate_default_ip_config()
        
        host_count = 0
        for host in self.net.hosts:
            host_count += 1
            
            if host.name in ip_config:
                ip = ip_config[host.name]
                host.setIP(ip)
                info(f"{host.name}: {ip}\n")
            else:
                # 使用默认IP配置
                subnet = (host_count - 1) // 254 + 1
                host_ip = f"10.0.{subnet}.{(host_count - 1) % 254 + 1}/24"
                host.setIP(host_ip)
                info(f"{host.name}: {host_ip}\n")
    
    def _generate_default_ip_config(self):
        """生成默认IP配置"""
        ip_config = {}
        
        # 为线性拓扑生成IP配置
        if isinstance(self.topo, LinearTopology):
            host_count = 0
            for i, switch in enumerate(self.net.switches):
                for j, host in enumerate(self.net.hosts):
                    if host_count >= 8:  # 限制主机数量
                        break
                    host_count += 1
                    ip = f"10.0.{i}.{j+1}/24"
                    ip_config[host.name] = ip
        
        return ip_config
    
    def test_connectivity(self):
        """测试网络连通性"""
        info("\n*** 测试网络连通性\n")
        
        if self.net:
            result = self.net.pingAll()
            info(f"连通性测试结果: {result}% 成功率\n")
            
            # 测试特定主机对
            hosts = list(self.net.hosts)
            if len(hosts) >= 2:
                h1, h2 = hosts[0], hosts[-1]
                info(f"\n测试 {h1.name} -> {h2.name}:\n")
                result = h1.cmd(f"ping -c 3 {h2.IP()}")
                info(result)
    
    def start_cli(self):
        """启动CLI"""
        info("\n*** 启动Mininet CLI\n")
        info("可用命令:\n")
        info("  h1 ping h2        # 测试主机间连通性\n")
        info("  h1 ping h8        # 测试远端主机连通性\n")
        info("  h1 iperf h2       # 测试带宽\n")
        info("  dpctl dump-flows  # 查看流表\n")
        info("  exit              # 退出CLI\n")
        info("\n")
        
        try:
            CLI(self.net)
        except KeyboardInterrupt:
            info("\n*** 键盘中断\n")
    
    def stop_network(self):
        """停止网络"""
        if self.net:
            info("*** 停止网络\n")
            self.net.stop()


def create_linear_topology(num_switches=4, hosts_per_switch=2):
    """创建线性拓扑"""
    info(f"*** 创建线性拓扑: {num_switches}个交换机，每个交换机{hosts_per_switch}个主机\n")
    topo = LinearTopology(num_switches=num_switches, hosts_per_switch=hosts_per_switch)
    return topo


def create_tree_topology(depth=2, fanout=2):
    """创建树形拓扑"""
    info(f"*** 创建树形拓扑: 深度{depth}，分支因子{fanout}\n")
    topo = TreeTopology(depth=depth, fanout=fanout)
    return topo


def create_custom_topology():
    """创建自定义拓扑"""
    info("*** 创建自定义拓扑\n")
    
    topology_config = {
        'switches': ['s1', 's2', 's3', 's4'],
        'hosts': [
            {'id': 'h1', 'switch': 's1', 'bw': 10},
            {'id': 'h2', 'switch': 's1', 'bw': 10},
            {'id': 'h3', 'switch': 's2', 'bw': 10},
            {'id': 'h4', 'switch': 's2', 'bw': 10},
            {'id': 'h5', 'switch': 's3', 'bw': 10},
            {'id': 'h6', 'switch': 's3', 'bw': 10},
            {'id': 'h7', 'switch': 's4', 'bw': 10},
            {'id': 'h8', 'switch': 's4', 'bw': 10}
        ],
        'links': [
            {'src': 's1', 'dst': 's2', 'bw': 20},
            {'src': 's2', 'dst': 's3', 'bw': 20},
            {'src': 's3', 'dst': 's4', 'bw': 20},
            {'src': 's1', 'dst': 's3', 'bw': 15},  # 添加额外链路
            {'src': 's2', 'dst': 's4', 'bw': 15}   # 添加额外链路
        ]
    }
    
    topo = CustomTopology(topology_config)
    return topo


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Mininet拓扑生成器')
    parser.add_argument('--topo', choices=['linear', 'tree', 'custom'], 
                       default='linear', help='拓扑类型')
    parser.add_argument('--switches', type=int, default=4, 
                       help='交换机数量（线性拓扑）')
    parser.add_argument('--hosts-per-switch', type=int, default=2, 
                       help='每个交换机的主机数量（线性拓扑）')
    parser.add_argument('--depth', type=int, default=2, 
                       help='树的深度（树形拓扑）')
    parser.add_argument('--fanout', type=int, default=2, 
                       help='分支因子（树形拓扑）')
    parser.add_argument('--controller-ip', default='127.0.0.1', 
                       help='控制器IP地址')
    parser.add_argument('--controller-port', type=int, default=6653, 
                       help='控制器端口')
    
    args = parser.parse_args()
    
    # 设置日志级别
    setLogLevel('info')
    
    try:
        # 根据参数创建拓扑
        if args.topo == 'linear':
            topo = create_linear_topology(args.switches, args.hosts_per_switch)
        elif args.topo == 'tree':
            topo = create_tree_topology(args.depth, args.fanout)
        elif args.topo == 'custom':
            topo = create_custom_topology()
        
        # 创建网络管理器
        network_manager = NetworkManager(
            topo, 
            args.controller_ip, 
            args.controller_port
        )
        
        # 启动网络
        network_manager.start_network()
        
        # 配置主机
        network_manager.configure_hosts()
        
        # 测试连通性
        network_manager.test_connectivity()
        
        # 启动CLI
        network_manager.start_cli()
        
    except Exception as e:
        info(f"错误: {e}\n")
        sys.exit(1)
    finally:
        if 'network_manager' in locals():
            network_manager.stop_network()


if __name__ == '__main__':
    main()