#!/usr/bin/env python3

"""
调试图结构的脚本
"""

from test_utils import SDNTestUtils

def main():
    print("调试图结构")
    print("=" * 50)
    
    test_utils = SDNTestUtils()
    if not test_utils.initialize_components():
        return
    
    # 显示图结构
    print("图结构详情:")
    print(f"节点数量: {len(test_utils.topology_manager.graph)}")
    print(f"\n节点列表:")
    for node in test_utils.topology_manager.graph.keys():
        print(f"  {node}")
    
    print(f"\n邻接关系:")
    for node, neighbors in test_utils.topology_manager.graph.items():
        print(f"  {node}:")
        if neighbors:
            for neighbor, weight in neighbors:
                print(f"    -> {neighbor} (权重: {weight})")
        else:
            print(f"    (无邻居)")
    
    print(f"\n链路信息:")
    for link in test_utils.topology_manager.links:
        src = f"{link['src']['device']}:{link['src']['port']}"
        dst = f"{link['dst']['device']}:{link['dst']['port']}"
        print(f"  {src} -> {dst}")
        dst = f"{link['dst']['device']}:{link['dst']['port']}"
        print(f"  {src} -> {dst}")

if __name__ == "__main__":
    main()
