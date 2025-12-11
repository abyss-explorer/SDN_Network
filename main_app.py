#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SDN网络通信系统主应用程序
集成所有组件，提供完整的网络管理功能
"""

import os
import sys
import time
import signal
import logging
import argparse
from typing import Dict, List, Optional, Any
from threading import Thread, Event

# 导入项目模块
from controller_client import ONOSControllerClient, TopologyManager
from path_calculator import HostPathCalculator
from flow_manager import NetworkCommunicator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sdn_network.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MininetTopology:
    """Mininet拓扑管理器"""
    
    def __init__(self):
        """初始化Mininet拓扑管理器"""
        self.topology_script = None
        self.mininet_process = None
    
    def create_linear_topology(self, num_switches: int = 4, hosts_per_switch: int = 2) -> str:
        """
        创建线性拓扑的Python脚本
        
        Args:
            num_switches: 交换机数量
            hosts_per_switch: 每个交换机连接的主机数量
            
        Returns:
            str: 拓扑脚本路径
        """
        script_content = '''#!/usr/bin/env python3
"""
线性拓扑配置脚本
创建 ''' + str(num_switches) + ''' 个交换机的线性拓扑，每个交换机连接 ''' + str(hosts_per_switch) + ''' 个主机
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.topo import Topo
import sys
import time

class LinearTopology(Topo):
    """线性拓扑类"""
    
    def __init__(self, num_switches=4, hosts_per_switch=2):
        """初始化线性拓扑"""
        Topo.__init__(self)
        
        # 创建交换机
        switches = []
        for i in range(num_switches):
            switch = self.addSwitch('s' + str(i+1))
            switches.append(switch)
        
        # 创建主机并连接到交换机
        host_count = 0
        for i, switch in enumerate(switches):
            for j in range(hosts_per_switch):
                host_count += 1
                host = self.addHost('h' + str(host_count))
                self.addLink(host, switch)
        
        # 连接交换机（线性连接）
        for i in range(num_switches - 1):
            self.addLink(switches[i], switches[i+1])

def create_network():
    """创建并启动网络"""
    info("*** 创建线性拓扑
")
    topo = LinearTopology(num_switches=''' + str(num_switches) + ''', hosts_per_switch=''' + str(hosts_per_switch) + ''')
    
    info("*** 创建网络
")
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6653),
        link=TCLink,
        waitConnected=True
    )
    
    info("*** 启动网络
")
    net.start()
    
    # 等待交换机连接到控制器
    info("*** 等待交换机连接到控制器
")
    time.sleep(5)
    
    # 为每个主机配置IP地址
    host_count = 0
    for i in range(''' + str(num_switches) + '''):
        for j in range(''' + str(hosts_per_switch) + '''):
            host_count += 1
            host = net.get('h' + str(host_count))
            # 配置IP地址，使用10.0.i.j/24格式
            host.setIP('10.0.' + str(i) + '.' + str(j+1) + '/24')
    
    info("*** 网络配置完成
")
    info("*** 主机IP地址配置:
")
    host_count = 0
    for i in range(''' + str(num_switches) + '''):
        for j in range(''' + str(hosts_per_switch) + '''):
            host_count += 1
            host = net.get('h' + str(host_count))
            info("h" + str(host_count) + ": " + host.IP() + "\n")
    
    # 测试基本连通性
    info("\n*** 测试基本连通性\n")
    net.pingAll()
    
    # 启动CLI
    info("\n*** 启动Mininet CLI\n")
    info("可用命令:\n")
    info("  h1 ping h2        # 测试主机间连通性\n")
    info("  h1 ping h8        # 测试远端主机连通性\n")
    info("  h1 iperf h2       # 测试带宽\n")
    info("  exit              # 退出CLI\n")
    info("\n")
    
    try:
        CLI(net)
    except KeyboardInterrupt:
        info("\n*** 键盘中断\n")
    finally:
        info("*** 停止网络\n")
        net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_network()
'''
        
        script_path = '/tmp/linear_topology.py'
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # 设置执行权限
        os.chmod(script_path, 0o755)
        
        logger.info(f"线性拓扑脚本已创建: {script_path}")
        return script_path
    
    def start_mininet(self, topology_script: str) -> bool:
        """
        启动Mininet仿真
        
        Args:
            topology_script: 拓扑脚本路径
            
        Returns:
            bool: 启动是否成功
        """
        try:
            import subprocess
            
            logger.info("启动Mininet仿真环境")
            
            # 使用subprocess启动Mininet
            self.mininet_process = subprocess.Popen(
                ['sudo', 'python3', topology_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待一段时间确保Mininet启动
            time.sleep(10)
            
            if self.mininet_process.poll() is None:
                logger.info("Mininet仿真环境启动成功")
                return True
            else:
                stdout, stderr = self.mininet_process.communicate()
                logger.error(f"Mininet启动失败: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"启动Mininet失败: {e}")
            return False
    
    def stop_mininet(self):
        """停止Mininet仿真"""
        if self.mininet_process:
            try:
                self.mininet_process.terminate()
                self.mininet_process.wait(timeout=5)
                logger.info("Mininet仿真环境已停止")
            except Exception as e:
                logger.error(f"停止Mininet失败: {e}")
                self.mininet_process.kill()


class SDNControllerApp:
    """SDN控制器应用程序"""
    
    def __init__(self, onos_url: str = "http://localhost:8181",
                 onos_user: str = "onos", onos_pass: str = "rocks"):
        """
        初始化SDN控制器应用
        
        Args:
            onos_url: ONOS控制器URL
            onos_user: ONOS用户名
            onos_pass: ONOS密码
        """
        self.onos_url = onos_url
        self.onos_user = onos_user
        self.onos_pass = onos_pass
        
        # 初始化组件
        self.controller_client = None
        self.topology_manager = None
        self.path_calculator = None
        self.network_communicator = None
        self.mininet_topology = MininetTopology()
        
        # 控制标志
        self.running = False
        self.shutdown_event = Event()
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"接收到信号 {signum}，准备关闭应用...")
        self.shutdown()
    
    def initialize_components(self) -> bool:
        """
        初始化所有组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("初始化SDN控制器应用组件")
            
            # 初始化控制器客户端
            self.controller_client = ONOSControllerClient(
                self.onos_url, self.onos_user, self.onos_pass
            )
            
            # 测试控制器连接
            if not self.controller_client.test_connection():
                logger.error("ONOS控制器连接失败")
                return False
            
            # 初始化拓扑管理器
            self.topology_manager = TopologyManager(self.controller_client)
            
            # 初始化路径计算器
            self.path_calculator = HostPathCalculator(self.topology_manager)
            
            # 初始化网络通信器
            self.network_communicator = NetworkCommunicator(
                self.controller_client, self.topology_manager
            )
            
            logger.info("所有组件初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            return False
    
    def setup_network_communication(self) -> bool:
        """
        设置网络通信
        
        Returns:
            bool: 设置是否成功
        """
        try:
            logger.info("设置网络通信")
            
            # 更新拓扑信息
            if not self.topology_manager.update_topology():
                logger.error("拓扑更新失败")
                return False
            
            # 启用所有主机间通信
            if not self.network_communicator.enable_all_host_communication():
                logger.error("启用主机通信失败")
                return False
            
            logger.info("网络通信设置完成")
            return True
            
        except Exception as e:
            logger.error(f"网络通信设置失败: {e}")
            return False
    
    def run_mininet_simulation(self, num_switches: int = 4, 
                             hosts_per_switch: int = 2) -> bool:
        """
        运行Mininet仿真
        
        Args:
            num_switches: 交换机数量
            hosts_per_switch: 每个交换机的主机数量
            
        Returns:
            bool: 运行是否成功
        """
        try:
            logger.info("启动Mininet仿真")
            
            # 直接使用topology.py文件
            import subprocess
            
            logger.info("启动Mininet仿真环境")
            
            # 使用subprocess启动Mininet
            self.mininet_process = subprocess.Popen(
                ['python3', 'topology.py', '--topo', 'linear', 
                 '--switches', str(num_switches), '--hosts-per-switch', str(hosts_per_switch)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待一段时间确保Mininet启动
            time.sleep(15)
            
            if self.mininet_process.poll() is None:
                logger.info("Mininet仿真环境启动成功")
                return True
            else:
                stdout, stderr = self.mininet_process.communicate()
                logger.error(f"Mininet启动失败: {stderr}")
                return False
            
        except Exception as e:
            logger.error(f"Mininet仿真运行失败: {e}")
            return False
    
    def start_cli(self):
        """启动命令行接口"""
        print("\n" + "="*60)
        print("SDN网络通信系统 - 命令行接口")
        print("="*60)
        print("可用命令:")
        print("  status          - 显示网络状态")
        print("  topology        - 显示拓扑信息")
        print("  hosts           - 显示主机列表")
        print("  flows           - 显示流表统计")
        print("  path <src> <dst> - 计算主机间路径")
        print("  enable <src> <dst> - 启用主机间通信")
        print("  enable-all      - 启用所有主机通信")
        print("  ping <src> <dst> - 测试主机连通性")
        print("  start-mininet   - 启动Mininet拓扑 (需要sudo权限)")
        print("  help            - 显示帮助信息")
        print("  quit/exit       - 退出程序")
        print("="*60)
        print("提示: 使用 'start-mininet' 启动网络拓扑，然后可以使用其他命令")
        print("="*60)
        
        while self.running and not self.shutdown_event.is_set():
            try:
                command = input("\nsdn> ").strip().split()
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd in ['quit', 'exit']:
                    break
                elif cmd == 'status':
                    self._show_status()
                elif cmd == 'topology':
                    self._show_topology()
                elif cmd == 'hosts':
                    self._show_hosts()
                elif cmd == 'flows':
                    self._show_flows()
                elif cmd == 'path':
                    self._calculate_path(command[1:])
                elif cmd == 'enable':
                    self._enable_host_communication(command[1:])
                elif cmd == 'enable-all':
                    self._enable_all_communication()
                elif cmd == 'ping':
                    self._test_connectivity(command[1:])
                elif cmd == 'start-mininet':
                    self._start_mininet_interactive()
                elif cmd == 'help':
                    self._show_help()
                else:
                    print(f"未知命令: {cmd}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"命令执行错误: {e}")
    
    def _show_status(self):
        """显示网络状态"""
        try:
            status = self.network_communicator.get_network_status()
            print("\n网络状态:")
            print(f"  状态: {status.get('status', 'unknown')}")
            print(f"  设备数量: {status['topology']['devices']}")
            print(f"  主机数量: {status['topology']['hosts']}")
            print(f"  链路数量: {status['topology']['links']}")
            print(f"  活跃设备: {status['topology']['active_devices']}")
            print(f"  流表总数: {status['flows']['total_flows']}")
            print(f"  已安装流表: {status['flows']['installed_flows']}")
            
            connectivity = status.get('connectivity', {})
            print(f"  连通主机: {connectivity.get('connected_hosts', 0)}")
            print(f"  连通率: {connectivity.get('connectivity_rate', 0):.2%}")
            
        except Exception as e:
            print(f"获取状态失败: {e}")
    
    def _show_topology(self):
        """显示拓扑信息"""
        try:
            self.topology_manager.update_topology()
            
            print("\n设备列表:")
            for device_id, device_info in self.topology_manager.devices.items():
                status = "活跃" if device_info['available'] else "非活跃"
                print(f"  {device_id}: {device_info['type']} - {status}")
            
            print("\n链路列表:")
            for link in self.topology_manager.links:
                src = f"{link['src']['device']}:{link['src']['port']}"
                dst = f"{link['dst']['device']}:{link['dst']['port']}"
                print(f"  {src} -> {dst}")
                
        except Exception as e:
            print(f"获取拓扑信息失败: {e}")
    
    def _show_hosts(self):
        """显示主机列表"""
        try:
            self.topology_manager.update_topology()
            
            print("\n主机列表:")
            for mac, host_info in self.topology_manager.hosts.items():
                device = host_info['location']['device']
                port = host_info['location']['port']
                ips = ', '.join(host_info['ipAddresses']) if host_info['ipAddresses'] else 'N/A'
                print(f"  {mac}")
                print(f"    IP: {ips}")
                print(f"    位置: {device}:{port}")
                
        except Exception as e:
            print(f"获取主机信息失败: {e}")
    
    def _show_flows(self):
        """显示流表统计"""
        try:
            stats = self.network_communicator.flow_manager.get_flow_statistics()
            
            print("\n流表统计:")
            print(f"  总流表数: {stats['total_flows']}")
            print(f"  已安装流表: {stats['installed_flows']}")
            
            print("\n各设备流表数:")
            for device_id, flow_count in stats['device_flows'].items():
                print(f"  {device_id}: {flow_count}")
                
        except Exception as e:
            print(f"获取流表统计失败: {e}")
    
    def _calculate_path(self, args):
        """计算主机间路径"""
        if len(args) < 2:
            print("用法: path <src_mac> <dst_mac>")
            return
        
        try:
            src_mac, dst_mac = args[0], args[1]
            route_info = self.path_calculator.get_optimal_route(src_mac, dst_mac)
            
            if route_info['success']:
                print(f"\n路径信息 ({src_mac} -> {dst_mac}):")
                print(f"  路径: {' -> '.join(route_info['path'])}")
                print(f"  跳数: {route_info['hop_count']}")
                print(f"  距离: {route_info['distance']}")
                print(f"  质量: {route_info['path_quality']}")
                
                if route_info['alternative_paths']:
                    print("\n备选路径:")
                    for i, alt_path in enumerate(route_info['alternative_paths'], 1):
                        print(f"  {i}. {' -> '.join(alt_path['path'])} (跳数: {alt_path['hop_count']}, 质量: {alt_path['quality']})")
            else:
                print(f"路径计算失败: {route_info['message']}")
                
        except Exception as e:
            print(f"路径计算错误: {e}")
    
    def _enable_host_communication(self, args):
        """启用主机间通信"""
        if len(args) < 2:
            print("用法: enable <src_mac> <dst_mac>")
            return
        
        try:
            src_mac, dst_mac = args[0], args[1]
            success = self.network_communicator.enable_host_communication(src_mac, dst_mac)
            
            if success:
                print(f"主机 {src_mac} 和 {dst_mac} 间通信已启用")
            else:
                print("启用通信失败")
                
        except Exception as e:
            print(f"启用通信错误: {e}")
    
    def _enable_all_communication(self):
        """启用所有主机通信"""
        try:
            success = self.network_communicator.enable_all_host_communication()
            
            if success:
                print("所有主机间通信已启用")
            else:
                print("启用所有主机通信失败")
                
        except Exception as e:
            print(f"启用通信错误: {e}")
    
    def _test_connectivity(self, args):
        """测试主机连通性"""
        if len(args) < 2:
            print("用法: ping <src_mac> <dst_mac>")
            return
        
        try:
            src_mac, dst_mac = args[0], args[1]
            route_info = self.path_calculator.get_host_to_host_path(src_mac, dst_mac)
            
            if route_info['success']:
                print(f"主机 {src_mac} 和 {dst_mac} 间连通性: 正常")
                print(f"路径: {' -> '.join(route_info['path'])}")
            else:
                print(f"主机 {src_mac} 和 {dst_mac} 间连通性: 异常")
                print(f"原因: {route_info['message']}")
                
        except Exception as e:
            print(f"连通性测试错误: {e}")
    
    def _start_mininet_interactive(self):
        """交互式启动Mininet"""
        print("\n启动Mininet拓扑...")
        print("请在另一个终端中运行以下命令:")
        print(f"cd {os.getcwd()}")
        print("sudo python3 topology.py --topo linear --switches 4 --hosts-per-switch 2")
        print("\n或者使用:")
        print("sudo python3 topology.py --topo custom")
        print("\n启动Mininet后，按回车键继续...")
        input()
        
        # 等待一段时间让网络稳定
        print("等待网络稳定...")
        time.sleep(10)
        
        # 更新拓扑
        if self.topology_manager.update_topology():
            print("拓扑更新成功")
        else:
            print("拓扑更新失败")
    
    def _show_help(self):
        """显示帮助信息"""
        print("\n可用命令:")
        print("  status          - 显示网络状态")
        print("  topology        - 显示拓扑信息")
        print("  hosts           - 显示主机列表")
        print("  flows           - 显示流表统计")
        print("  path <src> <dst> - 计算主机间路径")
        print("  enable <src> <dst> - 启用主机间通信")
        print("  enable-all      - 启用所有主机通信")
        print("  ping <src> <dst> - 测试主机连通性")
        print("  start-mininet   - 启动Mininet拓扑 (需要sudo权限)")
        print("  help            - 显示帮助信息")
        print("  quit/exit       - 退出程序")
    
    def run(self, with_mininet: bool = False, num_switches: int = 4, 
            hosts_per_switch: int = 2):
        """
        运行主应用程序
        
        Args:
            with_mininet: 是否启动Mininet仿真
            num_switches: 交换机数量
            hosts_per_switch: 每个交换机的主机数量
        """
        try:
            self.running = True
            logger.info("启动SDN网络通信系统")
            
            # 初始化组件
            if not self.initialize_components():
                logger.error("组件初始化失败，退出程序")
                return
            
            # 启动Mininet仿真（如果需要）
            if with_mininet:
                if not self.run_mininet_simulation(num_switches, hosts_per_switch):
                    logger.error("Mininet仿真启动失败")
                    return
            
            # 设置网络通信
            if not self.setup_network_communication():
                logger.error("网络通信设置失败")
                return
            
            # 启动CLI
            self.start_cli()
            
        except Exception as e:
            logger.error(f"程序运行错误: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """关闭应用程序"""
        logger.info("关闭SDN网络通信系统")
        self.running = False
        self.shutdown_event.set()
        
        # 停止Mininet
        if self.mininet_topology:
            self.mininet_topology.stop_mininet()
        
        logger.info("应用程序已关闭")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SDN网络通信系统')
    parser.add_argument('--onos-url', default='http://localhost:8181',
                       help='ONOS控制器URL')
    parser.add_argument('--onos-user', default='onos',
                       help='ONOS用户名')
    parser.add_argument('--onos-pass', default='rocks',
                       help='ONOS密码')
    parser.add_argument('--with-mininet', action='store_true',
                       help='启动Mininet仿真')
    parser.add_argument('--switches', type=int, default=4,
                       help='交换机数量')
    parser.add_argument('--hosts-per-switch', type=int, default=2,
                       help='每个交换机的主机数量')
    
    args = parser.parse_args()
    
    # 创建并运行应用
    app = SDNControllerApp(
        args.onos_url, args.onos_user, args.onos_pass
    )
    
    app.run(
        with_mininet=args.with_mininet,
        num_switches=args.switches,
        hosts_per_switch=args.hosts_per_switch
    )


if __name__ == '__main__':
    main()