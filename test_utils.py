#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试工具模块
提供通用的测试初始化和工具函数
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from controller_client import ONOSControllerClient, TopologyManager
from path_calculator import HostPathCalculator
from flow_manager import NetworkCommunicator


class SDNTestUtils:
    """SDN测试工具类"""

    def __init__(self):
        """初始化测试工具"""
        self.controller = None
        self.topology_manager = None
        self.path_calculator = None
        self.communicator = None

    def initialize_components(self) -> bool:
        """
        初始化所有组件

        Returns:
            bool: 初始化是否成功
        """
        try:
            print("初始化SDN组件...")

            # 初始化控制器客户端
            self.controller = ONOSControllerClient()

            # 测试连接
            if not self.controller.test_connection():
                print("✗ ONOS控制器连接失败")
                return False

            print("✓ ONOS控制器连接成功")

            # 初始化拓扑管理器
            self.topology_manager = TopologyManager(self.controller)

            # 更新拓扑
            if not self.topology_manager.update_topology():
                print("✗ 拓扑更新失败")
                return False

            print("✓ 拓扑更新成功")

            # 初始化路径计算器
            self.path_calculator = HostPathCalculator(self.topology_manager)

            # 初始化网络通信器
            self.communicator = NetworkCommunicator(self.controller, self.topology_manager)

            return True

        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            return False

    def print_topology_stats(self):
        """打印拓扑统计信息"""
        if not self.topology_manager:
            return

        stats = self.topology_manager.get_topology_stats()
        print(f"\n网络统计:")
        print(f"  设备数量: {stats['devices']}")
        print(f"  主机数量: {stats['hosts']}")
        print(f"  链路数量: {stats['links']}")
        print(f"  活跃设备: {stats['active_devices']}")

    def print_devices(self):
        """打印设备列表"""
        if not self.topology_manager:
            return

        print(f"\n设备列表:")
        for device_id, device_info in self.topology_manager.devices.items():
            status = "活跃" if device_info['available'] else "非活跃"
            print(f"  {device_id}: {device_info['type']} - {status}")

    def print_hosts(self):
        """打印主机列表"""
        if not self.topology_manager:
            return

        print(f"\n主机列表:")
        for mac, host_info in self.topology_manager.hosts.items():
            device = host_info['location']['device']
            port = host_info['location']['port']
            ips = ', '.join(host_info['ipAddresses']) if host_info['ipAddresses'] else 'N/A'
            print(f"  {mac}")
            print(f"    IP: {ips}")
            print(f"    位置: {device}:{port}")

    def get_host_list(self) -> list:
        """获取主机MAC列表"""
        if not self.topology_manager:
            return []
        return list(self.topology_manager.hosts.keys())</content>
<parameter name="filePath">d:\MyCustomPath\Git\home\SDN_Network\test_utils.py