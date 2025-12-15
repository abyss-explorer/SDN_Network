#!/usr/bin/env python3

"""
简化的SDN状态测试脚本
"""

from test_utils import SDNTestUtils

def main():
    print("SDN网络状态测试")
    print("=" * 50)
    
    # 初始化组件
    test_utils = SDNTestUtils()
    if not test_utils.initialize_components():
        return
    
    # 显示统计信息
    test_utils.print_topology_stats()
    
    # 显示设备列表
    test_utils.print_devices()
    
    # 显示主机列表
    test_utils.print_hosts()
    
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