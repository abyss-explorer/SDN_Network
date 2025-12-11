#!/usr/bin/env python3

"""
调试图结构的脚本
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from controller_client import ONOSControllerClient, TopologyManager

def main():
    print("调试图结构")
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
    
    # 显示图结构
    print("图结构详情:")
    print(f"节点数量: {len(topology_manager.graph)}")
    print(f"\n节点列表:")
    for node in topology_manager.graph.keys():
        print(f"  {node}")
    
    print(f"\n邻接关系:")
    for node, neighbors in topology_manager.graph.items():
        print(f"  {node}:")
        if neighbors:
            for neighbor, weight in neighbors:
                print(f"    -> {neighbor} (权重: {weight})")
        else:
            print(f"    (无邻居)")
    
    print(f"\n链路信息:")
    for link in topology_manager.links:
        src = f"{link['src']['device']}:{link['src']['port']}"
        dst = f"{link['dst']['device']}:{link['dst']['port']}"
        print(f"  {src} -> {dst}")

if __name__ == "__main__":
    main()
