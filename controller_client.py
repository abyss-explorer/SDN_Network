#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ONOS控制器客户端模块
负责与ONOS控制器进行REST API通信，获取网络拓扑信息
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from requests.exceptions import RequestException, ConnectionError, Timeout

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ONOSControllerClient:
    """ONOS控制器REST API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8181", 
                 username: str = "onos", password: str = "rocks"):
        """
        初始化ONOS控制器客户端
        
        Args:
            base_url: ONOS控制器基础URL
            username: 用户名
            password: 密码
        """
        self.base_url = base_url
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        
    def test_connection(self) -> bool:
        """
        测试与ONOS控制器的连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 首先尝试获取系统信息
            url = f"{self.base_url}/onos/v1/system"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            logger.info("ONOS控制器连接成功")
            return True
        except (ConnectionError, Timeout) as e:
            logger.error(f"连接ONOS控制器失败: {e}")
            return False
        except RequestException as e:
            logger.error(f"ONOS控制器请求异常: {e}")
            return False
    
    def get_topology(self) -> Dict[str, Any]:
        """
        获取网络拓扑信息
        
        Returns:
            Dict: 包含设备、主机、链路信息的拓扑数据
        """
        topology = {
            'devices': {},
            'hosts': {},
            'links': []
        }
        
        try:
            # 获取设备信息
            devices = self.get_devices()
            topology['devices'] = devices
            
            # 获取主机信息
            hosts = self.get_hosts()
            topology['hosts'] = hosts
            
            # 获取链路信息
            links = self.get_links()
            topology['links'] = links
            
            logger.info("拓扑信息获取成功")
            return topology
            
        except RequestException as e:
            logger.error(f"获取拓扑信息失败: {e}")
            return topology
    
    def get_devices(self) -> Dict[str, Dict]:
        """
        获取网络设备信息
        
        Returns:
            Dict: 设备信息字典
        """
        try:
            url = f"{self.base_url}/onos/v1/devices"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            devices_data = response.json()
            devices = {}
            
            for device in devices_data.get('devices', []):
                device_id = device.get('id')
                devices[device_id] = {
                    'id': device_id,
                    'type': device.get('type', 'SWITCH'),
                    'available': device.get('available', False),
                    'adminState': device.get('adminState', 'DISABLED'),
                    'operationalState': device.get('operationalState', 'INACTIVE'),
                    'ports': device.get('ports', [])
                }
            
            logger.info(f"获取到 {len(devices)} 个设备")
            return devices
            
        except RequestException as e:
            logger.error(f"获取设备信息失败: {e}")
            return {}
    
    def get_hosts(self) -> Dict[str, Dict]:
        """
        获取主机信息
        
        Returns:
            Dict: 主机信息字典
        """
        try:
            url = f"{self.base_url}/onos/v1/hosts"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            hosts_data = response.json()
            hosts = {}
            
            for host in hosts_data.get('hosts', []):
                mac = host.get('mac')
                # 获取第一个位置（主机可能连接到多个位置）
                locations = host.get('locations', [])
                location = locations[0] if locations else {}
                
                hosts[mac] = {
                    'mac': mac,
                    'ipAddresses': host.get('ipAddresses', []),
                    'location': {
                        'device': location.get('elementId'),
                        'port': location.get('port')
                    },
                    'vlan': host.get('vlan', 'unknown')
                }
            
            logger.info(f"获取到 {len(hosts)} 个主机")
            return hosts
            
        except RequestException as e:
            logger.error(f"获取主机信息失败: {e}")
            return {}
    
    def get_links(self) -> List[Dict]:
        """
        获取链路信息
        
        Returns:
            List[Dict]: 链路信息列表
        """
        try:
            url = f"{self.base_url}/onos/v1/links"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            links_data = response.json()
            links = []
            
            for link in links_data.get('links', []):
                links.append({
                    'src': {
                        'device': link.get('src', {}).get('device'),
                        'port': link.get('src', {}).get('port')
                    },
                    'dst': {
                        'device': link.get('dst', {}).get('device'),
                        'port': link.get('dst', {}).get('port')
                    },
                    'type': link.get('type', 'DIRECT'),
                    'state': link.get('state', 'ACTIVE')
                })
            
            logger.info(f"获取到 {len(links)} 条链路")
            return links
            
        except RequestException as e:
            logger.error(f"获取链路信息失败: {e}")
            return []
    
    def install_flow_rule(self, device_id: str, flow_rule: Dict[str, Any]) -> bool:
        """
        安装流表规则
        
        Args:
            device_id: 设备ID
            flow_rule: 流表规则
            
        Returns:
            bool: 安装是否成功
        """
        try:
            url = f"{self.base_url}/onos/v1/flows/{device_id}"
            response = self.session.post(url, json=flow_rule, timeout=10)
            response.raise_for_status()
            
            logger.info(f"设备 {device_id} 流表安装成功")
            return True
            
        except RequestException as e:
            logger.error(f"设备 {device_id} 流表安装失败: {e}")
            return False
    
    def get_flow_rules(self, device_id: str) -> List[Dict]:
        """
        获取设备的流表规则
        
        Args:
            device_id: 设备ID
            
        Returns:
            List[Dict]: 流表规则列表
        """
        try:
            url = f"{self.base_url}/onos/v1/flows/{device_id}"
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            flows_data = response.json()
            return flows_data.get('flows', [])
            
        except RequestException as e:
            logger.error(f"获取设备 {device_id} 流表失败: {e}")
            return []
    
    def delete_flow_rule(self, device_id: str, flow_id: str) -> bool:
        """
        删除流表规则
        
        Args:
            device_id: 设备ID
            flow_id: 流表ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            url = f"{self.base_url}/onos/v1/flows/{device_id}/{flow_id}"
            response = self.session.delete(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            logger.info(f"设备 {device_id} 流表 {flow_id} 删除成功")
            return True
            
        except RequestException as e:
            logger.error(f"设备 {device_id} 流表 {flow_id} 删除失败: {e}")
            return False


class TopologyManager:
    """网络拓扑管理器"""
    
    def __init__(self, controller_client: ONOSControllerClient):
        """
        初始化拓扑管理器
        
        Args:
            controller_client: ONOS控制器客户端
        """
        self.controller = controller_client
        self.devices = {}
        self.hosts = {}
        self.links = []
        self.graph = {}
        
    def update_topology(self) -> bool:
        """
        更新拓扑信息
        
        Returns:
            bool: 更新是否成功
        """
        try:
            topology = self.controller.get_topology()
            self.devices = topology['devices']
            self.hosts = topology['hosts']
            self.links = topology['links']
            
            # 构建图结构
            self._build_graph()
            
            logger.info("拓扑更新成功")
            return True
            
        except Exception as e:
            logger.error(f"拓扑更新失败: {e}")
            return False
    
    def _build_graph(self):
        """构建用于路径计算的图结构"""
        self.graph = {}
        
        # 初始化所有设备节点
        for device_id in self.devices:
            self.graph[device_id] = []
        
        # 添加链路连接（ONOS API已返回双向链路，无需重复添加）
        for link in self.links:
            src_device = link['src']['device']
            dst_device = link['dst']['device']
            
            if src_device in self.graph and dst_device in self.graph:
                # 只添加单向连接，权重为1
                self.graph[src_device].append((dst_device, 1))
                logger.debug(f"添加边: {src_device} -> {dst_device}")
        
        # 统计边数
        total_edges = sum(len(neighbors) for neighbors in self.graph.values())
        logger.info(f"图结构构建完成，包含 {len(self.graph)} 个节点，{total_edges} 条边")
        
        # 调试输出
        for node, neighbors in self.graph.items():
            if neighbors:
                logger.debug(f"节点 {node}: {len(neighbors)} 个邻居")
    
    def get_host_location(self, host_mac: str) -> Optional[Dict[str, str]]:
        """
        获取主机位置信息
        
        Args:
            host_mac: 主机MAC地址
            
        Returns:
            Optional[Dict]: 主机位置信息
        """
        if host_mac in self.hosts:
            return self.hosts[host_mac]['location']
        return None
    
    def get_device_by_host(self, host_mac: str) -> Optional[str]:
        """
        根据主机MAC获取连接的设备ID
        
        Args:
            host_mac: 主机MAC地址
            
        Returns:
            Optional[str]: 设备ID
        """
        location = self.get_host_location(host_mac)
        if location:
            return location['device']
        return None
    
    def is_host_connected(self, host_mac: str) -> bool:
        """
        检查主机是否已连接
        
        Args:
            host_mac: 主机MAC地址
            
        Returns:
            bool: 是否已连接
        """
        return host_mac in self.hosts
    
    def get_topology_stats(self) -> Dict[str, int]:
        """
        获取拓扑统计信息
        
        Returns:
            Dict[str, int]: 统计信息
        """
        return {
            'devices': len(self.devices),
            'hosts': len(self.hosts),
            'links': len(self.links),
            'active_devices': sum(1 for d in self.devices.values() if d['available'])
        }


if __name__ == "__main__":
    # 测试代码
    client = ONOSControllerClient()
    
    if client.test_connection():
        print("ONOS控制器连接成功")
        
        topology_manager = TopologyManager(client)
        if topology_manager.update_topology():
            stats = topology_manager.get_topology_stats()
            print(f"拓扑统计: {stats}")
        else:
            print("拓扑更新失败")
    else:
        print("ONOS控制器连接失败")