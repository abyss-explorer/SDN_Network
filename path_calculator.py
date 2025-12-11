#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
路径计算模块
实现网络路径计算算法，包括Dijkstra最短路径算法和主机间路径计算
"""

import heapq
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from controller_client import TopologyManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PathCalculator:
    """路径计算器基类"""
    
    def __init__(self, graph: Dict[str, List[Tuple[str, int]]]):
        """
        初始化路径计算器
        
        Args:
            graph: 网络图结构 {device_id: [(neighbor_id, weight), ...]}
        """
        self.graph = graph
    
    def dijkstra(self, start: str, end: str) -> Tuple[List[str], int]:
        """
        Dijkstra最短路径算法
        
        Args:
            start: 起始节点
            end: 目标节点
            
        Returns:
            Tuple[List[str], int]: (路径列表, 总距离)
        """
        if start not in self.graph.keys() or end not in self.graph.keys():
            logger.error(f"节点不存在: start={start}, end={end}")
            logger.debug(f"图中的节点: {list(self.graph.keys())}")
            return [], float('inf')
        
        # 初始化距离和前驱节点
        distances = {node: float('infinity') for node in self.graph}
        distances[start] = 0
        previous_nodes = {node: None for node in self.graph}
        
        # 优先队列存储(距离, 节点)
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_distance, current = heapq.heappop(pq)
            
            if current in visited:
                continue
                
            visited.add(current)
            
            # 如果到达目标节点，提前结束
            if current == end:
                break
            
            # 遍历邻居节点
            for neighbor, weight in self.graph.get(current, []):
                if neighbor in visited:
                    continue
                
                new_distance = current_distance + weight
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous_nodes[neighbor] = current
                    heapq.heappush(pq, (new_distance, neighbor))
        
        # 重构路径
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous_nodes[current]
        
        path.reverse()
        
        if path[0] != start:
            logger.warning(f"从 {start} 到 {end} 没有可达路径")
            return [], float('inf')
        
        logger.info(f"最短路径计算完成: {start} -> {end}, 距离: {distances[end]}")
        return path, distances[end]
    
    def find_all_paths(self, start: str, end: str, max_paths: int = 10) -> List[List[str]]:
        """
        查找所有可能路径（深度优先搜索）
        
        Args:
            start: 起始节点
            end: 目标节点
            max_paths: 最大路径数量
            
        Returns:
            List[List[str]]: 所有路径列表
        """
        if start not in self.graph or end not in self.graph:
            return []
        
        all_paths = []
        
        def dfs(current: str, path: List[str], visited: Set[str]):
            if len(all_paths) >= max_paths:
                return
            
            if current == end:
                all_paths.append(path.copy())
                return
            
            for neighbor, _ in self.graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(neighbor, path, visited)
                    path.pop()
                    visited.remove(neighbor)
        
        visited = {start}
        dfs(start, [start], visited)
        
        logger.info(f"找到 {len(all_paths)} 条路径从 {start} 到 {end}")
        return all_paths
    
    def k_shortest_paths(self, start: str, end: str, k: int = 3) -> List[Tuple[List[str], int]]:
        """
        K最短路径算法（简化版）
        
        Args:
            start: 起始节点
            end: 目标节点
            k: 返回的路径数量
            
        Returns:
            List[Tuple[List[str], int]]: K条最短路径及其距离
        """
        all_paths = self.find_all_paths(start, end, max_paths=k * 2)
        
        # 计算每条路径的距离
        path_distances = []
        for path in all_paths:
            distance = 0
            for i in range(len(path) - 1):
                current = path[i]
                next_node = path[i + 1]
                # 查找边的权重
                for neighbor, weight in self.graph.get(current, []):
                    if neighbor == next_node:
                        distance += weight
                        break
            path_distances.append((path, distance))
        
        # 按距离排序
        path_distances.sort(key=lambda x: x[1])
        
        logger.info(f"K最短路径计算完成，返回前 {min(k, len(path_distances))} 条路径")
        return path_distances[:k]
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        获取图统计信息
        
        Returns:
            Dict[str, Any]: 图统计信息
        """
        total_edges = sum(len(neighbors) for neighbors in self.graph.values())
        
        return {
            'nodes': len(self.graph),
            'edges': total_edges // 2,  # 无向图，每条边被计算两次
            'is_connected': self._is_connected(),
            'average_degree': total_edges / len(self.graph) if self.graph else 0
        }
    
    def _is_connected(self) -> bool:
        """
        检查图是否连通
        
        Returns:
            bool: 图是否连通
        """
        if not self.graph:
            return False
        
        # 从任意节点开始DFS
        start_node = list(self.graph.keys())[0]
        visited = set()
        
        def dfs(node: str):
            visited.add(node)
            for neighbor, _ in self.graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
        
        dfs(start_node)
        
        return len(visited) == len(self.graph)


class HostPathCalculator:
    """主机间路径计算器"""
    
    def __init__(self, topology_manager: TopologyManager):
        """
        初始化主机路径计算器
        
        Args:
            topology_manager: 拓扑管理器
        """
        self.topology_manager = topology_manager
    
    def get_host_to_host_path(self, src_host_mac: str, dst_host_mac: str) -> Dict[str, Any]:
        """
        计算主机间的路径
        
        Args:
            src_host_mac: 源主机MAC地址
            dst_host_mac: 目标主机MAC地址
            
        Returns:
            Dict[str, Any]: 路径信息
        """
        route_info = {
            'success': False,
            'message': '',
            'path': [],
            'distance': float('inf'),
            'src_host': None,
            'dst_host': None
        }
        
        # 检查主机是否存在
        if not self.topology_manager.is_host_connected(src_host_mac):
            route_info['message'] = f"源主机 {src_host_mac} 未连接"
            return route_info
        
        if not self.topology_manager.is_host_connected(dst_host_mac):
            route_info['message'] = f"目标主机 {dst_host_mac} 未连接"
            return route_info
        
        # 获取主机连接的设备
        src_device = self.topology_manager.get_device_by_host(src_host_mac)
        dst_device = self.topology_manager.get_device_by_host(dst_host_mac)
        
        if not src_device or not dst_device:
            route_info['message'] = "无法获取主机连接的设备"
            return route_info
        
        # 使用最新的图结构创建路径计算器
        path_calculator = PathCalculator(self.topology_manager.graph)
        
        # 计算设备间路径
        device_path, distance = path_calculator.dijkstra(src_device, dst_device)
        
        if not device_path:
            route_info['message'] = f"从设备 {src_device} 到 {dst_device} 没有可达路径"
            return route_info
        
        # 构建完整路径（包含主机）
        complete_path = [f"host_{src_host_mac}"] + device_path + [f"host_{dst_host_mac}"]
        
        route_info.update({
            'success': True,
            'message': '路径计算成功',
            'path': complete_path,
            'distance': distance,
            'src_host': self.topology_manager.hosts[src_host_mac],
            'dst_host': self.topology_manager.hosts[dst_host_mac],
            'src_device': src_device,
            'dst_device': dst_device,
            'device_path': device_path
        })
        
        logger.info(f"主机间路径计算成功: {src_host_mac} -> {dst_host_mac}")
        return route_info
    
    def get_optimal_route(self, src_host_mac: str, dst_host_mac: str) -> Dict[str, Any]:
        """
        获取最优路由信息
        
        Args:
            src_host_mac: 源主机MAC地址
            dst_host_mac: 目标主机MAC地址
            
        Returns:
            Dict[str, Any]: 最优路由信息
        """
        route_info = self.get_host_to_host_path(src_host_mac, dst_host_mac)
        
        if not route_info['success']:
            return route_info
        
        # 添加额外的路由信息
        route_info.update({
            'hop_count': len(route_info['device_path']) - 1,
            'path_quality': self._evaluate_path_quality(route_info['device_path']),
            'alternative_paths': self._get_alternative_paths(src_host_mac, dst_host_mac)
        })
        
        return route_info
    
    def _evaluate_path_quality(self, device_path: List[str]) -> str:
        """
        评估路径质量
        
        Args:
            device_path: 设备路径列表
            
        Returns:
            str: 路径质量评估
        """
        hop_count = len(device_path) - 1
        
        if hop_count <= 2:
            return "excellent"
        elif hop_count <= 4:
            return "good"
        elif hop_count <= 6:
            return "fair"
        else:
            return "poor"
    
    def _get_alternative_paths(self, src_host_mac: str, dst_host_mac: str, 
                             max_alternatives: int = 2) -> List[Dict[str, Any]]:
        """
        获取备选路径
        
        Args:
            src_host_mac: 源主机MAC地址
            dst_host_mac: 目标主机MAC地址
            max_alternatives: 最大备选路径数量
            
        Returns:
            List[Dict[str, Any]]: 备选路径列表
        """
        src_device = self.topology_manager.get_device_by_host(src_host_mac)
        dst_device = self.topology_manager.get_device_by_host(dst_host_mac)
        
        if not src_device or not dst_device:
            return []
        
        # 使用最新的图结构创建路径计算器
        path_calculator = PathCalculator(self.topology_manager.graph)
        
        k_paths = path_calculator.k_shortest_paths(src_device, dst_device, 
                                                      k=max_alternatives + 1)
        
        # 跳过第一条路径（最优路径）
        alternative_paths = []
        for i, (device_path, distance) in enumerate(k_paths[1:max_alternatives + 1]):
            complete_path = [f"host_{src_host_mac}"] + device_path + [f"host_{dst_host_mac}"]
            
            alternative_paths.append({
                'path': complete_path,
                'device_path': device_path,
                'distance': distance,
                'hop_count': len(device_path) - 1,
                'quality': self._evaluate_path_quality(device_path)
            })
        
        return alternative_paths
    
    def get_all_host_pairs_paths(self) -> Dict[str, Dict[str, Any]]:
        """
        计算所有主机对之间的路径
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有主机对的路径信息
        """
        all_paths = {}
        host_macs = list(self.topology_manager.hosts.keys())
        
        for i, src_mac in enumerate(host_macs):
            for dst_mac in host_macs[i+1:]:
                pair_key = f"{src_mac}->{dst_mac}"
                route_info = self.get_optimal_route(src_mac, dst_mac)
                all_paths[pair_key] = route_info
        
        logger.info(f"计算了 {len(all_paths)} 个主机对的路径")
        return all_paths


if __name__ == "__main__":
    # 测试代码
    from controller_client import ONOSControllerClient
    
    # 创建测试图
    test_graph = {
        's1': [('s2', 1)],
        's2': [('s1', 1), ('s3', 1)],
        's3': [('s2', 1), ('s4', 1)],
        's4': [('s3', 1)]
    }
    
    # 测试路径计算器
    calculator = PathCalculator(test_graph)
    
    # 测试Dijkstra算法
    path, distance = calculator.dijkstra('s1', 's4')
    print(f"最短路径: {path}, 距离: {distance}")
    
    # 测试K最短路径
    k_paths = calculator.k_shortest_paths('s1', 's4', k=3)
    print(f"K最短路径: {k_paths}")
    
    # 测试图统计
    stats = calculator.get_graph_stats()
    print(f"图统计信息: {stats}")