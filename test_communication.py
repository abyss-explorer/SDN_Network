#!/usr/bin/env python3

"""
测试网络通信功能
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from controller_client import ONOSControllerClient, TopologyManager
from path_calculator import HostPathCalculator
from flow_manager import NetworkCommunicator

def main():
    print("SDN网络通信测试")
    print("=" * 50)
    
    # 初始化组件
    controller = ONOSControllerClient()
    topology_manager = TopologyManager(controller)
    communicator = NetworkCommunicator(controller, topology_manager)
    
    # 测试连接
    if not controller.test_connection():
        print("✗ ONOS控制器连接失败")
        return
    
    print("✓ ONOS控制器连接成功")
    
    # 更新拓扑
    if not topology_manager.update_topology():
        print("✗ 拓扑更新失败")
        return
    
    print("✓ 拓扑更新成功")
    
    # 获取主机列表
    hosts = list(topology_manager.hosts.keys())
    if len(hosts) < 2:
        print(f"✗ 主机数量不足，需要至少2个主机，当前有{len(hosts)}个")
        return
    
    print(f"✓ 检测到 {len(hosts)} 个主机")
    
    # 测试主机间通信
    src_mac = hosts[0]
    dst_mac = hosts[1]
    
    src_ip = topology_manager.hosts[src_mac]['ipAddresses'][0] if topology_manager.hosts[src_mac]['ipAddresses'] else 'N/A'
    dst_ip = topology_manager.hosts[dst_mac]['ipAddresses'][0] if topology_manager.hosts[dst_mac]['ipAddresses'] else 'N/A'
    
    print(f"\n测试通信:")
    print(f"  源主机: {src_mac} ({src_ip})")
    print(f"  目标主机: {dst_mac} ({dst_ip})")
    
    # 建立通信
    success = communicator.enable_host_communication(src_mac, dst_mac)
    
    if success:
        print(f"\n✓ 通信建立成功!")
    else:
        print(f"\n✗ 通信建立失败")
    
    print(f"\n测试完成！")

if __name__ == "__main__":
    main()
