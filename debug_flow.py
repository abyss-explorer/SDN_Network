#!/usr/bin/env python3

"""
调试流表规则
"""

import sys
import os
import json
sys.path.insert(0, os.getcwd())

from controller_client import ONOSControllerClient, TopologyManager
from flow_manager import FlowRuleBuilder

def main():
    print("调试流表规则")
    print("=" * 50)
    
    controller = ONOSControllerClient()
    topology_manager = TopologyManager(controller)
    
    if not controller.test_connection():
        print("✗ ONOS控制器连接失败")
        return
    
    print("✓ ONOS控制器连接成功\n")
    
    if not topology_manager.update_topology():
        print("✗ 拓扑更新失败")
        return
    
    print("✓ 拓扑更新成功\n")
    
    # 获取主机信息
    hosts = list(topology_manager.hosts.keys())
    if len(hosts) < 2:
        print("主机数量不足")
        return
    
    src_mac = hosts[0]
    dst_mac = hosts[1]
    device_id = "of:0000000000000002"
    output_port = 3
    
    # 构建流表规则
    builder = FlowRuleBuilder()
    flow_rule = builder.create_host_to_host_flow(device_id, src_mac, dst_mac, output_port)
    
    print("流表规则JSON:")
    print(json.dumps(flow_rule, indent=2))
    
    print(f"\n尝试安装流表...")
    success = controller.install_flow_rule(device_id, flow_rule)
    
    if success:
        print("✓ 流表安装成功")
    else:
        print("✗ 流表安装失败")

if __name__ == "__main__":
    main()
