#!/usr/bin/env python3

"""
简化的SDN状态测试脚本
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from controller_client import ONOSControllerClient, TopologyManager
from path_calculator import HostPathCalculator

def main():
    print("SDN网络状态测试")
    print("=" * 50)
    
    # 初始化组件
    controller = ONOSControllerClient()
    topology_manager = TopologyManager(controller)
    path_calculator = HostPathCalculator(topology_manager)
    
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
    
    # 显示统计信息
    stats = topology_manager.get_topology_stats()
    print(f"\n网络统计:")
    print(f"  设备数量: {stats['devices']}")
    print(f"  主机数量: {stats['hosts']}")
    print(f"  链路数量: {stats['links']}")
    print(f"  活跃设备: {stats['active_devices']}")
    
    # 显示设备列表
    print(f"\n设备列表:")
    for device_id, device_info in topology_manager.devices.items():
        status = "活跃" if device_info['available'] else "非活跃"
        print(f"  {device_id}: {device_info['type']} - {status}")
    
    # 显示主机列表
    print(f"\n主机列表:")
    for mac, host_info in topology_manager.hosts.items():
        device = host_info['location']['device']
        port = host_info['location']['port']
        ips = ', '.join(host_info['ipAddresses']) if host_info['ipAddresses'] else 'N/A'
        print(f"  {mac}")
        print(f"    IP: {ips}")
        print(f"    位置: {device}:{port}")
    
    # 显示链路列表
    print(f"\n链路列表:")
    for link in topology_manager.links:
        src = f"{link['src']['device']}:{link['src']['port']}"
        dst = f"{link['dst']['device']}:{link['dst']['port']}"
        print(f"  {src} -> {dst}")
    
    # 测试路径计算
    if len(topology_manager.hosts) >= 2:
        host_macs = list(topology_manager.hosts.keys())
        src_mac, dst_mac = host_macs[0], host_macs[1]
        
        print(f"\n路径计算测试 ({src_mac} -> {dst_mac}):")
        route_info = path_calculator.get_optimal_route(src_mac, dst_mac)
        
        if route_info['success']:
            print(f"  路径: {' -> '.join(route_info['path'])}")
            print(f"  跳数: {route_info['hop_count']}")
            print(f"  距离: {route_info['distance']}")
            print(f"  质量: {route_info['path_quality']}")
        else:
            print(f"  失败: {route_info['message']}")
    
    print(f"\n测试完成！系统运行正常。")

if __name__ == "__main__":
    main()