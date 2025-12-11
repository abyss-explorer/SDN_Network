#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
流表管理模块
负责构建和管理OpenFlow流表规则，实现网络数据包转发
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from controller_client import ONOSControllerClient, TopologyManager
from path_calculator import HostPathCalculator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlowRuleBuilder:
    """流表规则构建器"""
    
    def __init__(self):
        """初始化流表规则构建器"""
        self.next_priority = 40000  # 默认优先级起始值
    
    def create_basic_flow_rule(self, device_id: str, match_criteria: Dict[str, Any], 
                             output_port: int, priority: int = None) -> Dict[str, Any]:
        """
        创建基本流表规则
        
        Args:
            device_id: 设备ID
            match_criteria: 匹配条件
            output_port: 输出端口
            priority: 优先级
            
        Returns:
            Dict[str, Any]: 流表规则
        """
        if priority is None:
            priority = self.next_priority
            self.next_priority += 10
        
        # 构建匹配条件
        criteria = []
        for criterion_type, value in match_criteria.items():
            criteria.append({
                "type": criterion_type,
                "mac": value if criterion_type.startswith("ETH") else str(value)
            })
        
        flow_rule = {
            "priority": priority,
            "timeout": 0,
            "isPermanent": True,
            "deviceId": device_id,
            "appId": "org.onosproject.rest",
            "treatment": {
                "instructions": [
                    {
                        "type": "OUTPUT",
                        "port": str(output_port)
                    }
                ]
            },
            "selector": {
                "criteria": criteria
            }
        }
        
        return flow_rule
    
    def create_host_to_host_flow(self, device_id: str, src_mac: str, dst_mac: str, 
                               output_port: int, priority: int = None) -> Dict[str, Any]:
        """
        创建主机到主机的流表规则
        
        Args:
            device_id: 设备ID
            src_mac: 源MAC地址
            dst_mac: 目标MAC地址
            output_port: 输出端口
            priority: 优先级
            
        Returns:
            Dict[str, Any]: 流表规则
        """
        match_criteria = {
            "ETH_SRC": src_mac,
            "ETH_DST": dst_mac
        }
        
        return self.create_basic_flow_rule(device_id, match_criteria, output_port, priority)
    
    def create_broadcast_flow(self, device_id: str, dst_mac: str, output_ports: List[int], 
                            priority: int = None) -> Dict[str, Any]:
        """
        创建广播流表规则
        
        Args:
            device_id: 设备ID
            dst_mac: 目标MAC地址（广播MAC）
            output_ports: 输出端口列表
            priority: 优先级
            
        Returns:
            Dict[str, Any]: 流表规则
        """
        if priority is None:
            priority = self.next_priority
            self.next_priority += 10
        
        # 构建多个输出指令
        instructions = []
        for port in output_ports:
            instructions.append({
                "type": "OUTPUT",
                "port": str(port)
            })
        
        flow_rule = {
            "priority": priority,
            "timeout": 0,
            "isPermanent": True,
            "deviceId": device_id,
            "appId": "org.onosproject.rest",
            "treatment": {
                "instructions": instructions
            },
            "selector": {
                "criteria": [
                    {
                        "type": "ETH_DST",
                        "mac": dst_mac
                    }
                ]
            }
        }
        
        return flow_rule
    
    def create_arp_flow(self, device_id: str, output_ports: List[int], 
                       priority: int = 30000) -> Dict[str, Any]:
        """
        创建ARP处理流表规则
        
        Args:
            device_id: 设备ID
            output_ports: 输出端口列表
            priority: 优先级
            
        Returns:
            Dict[str, Any]: 流表规则
        """
        instructions = []
        for port in output_ports:
            instructions.append({
                "type": "OUTPUT",
                "port": str(port)
            })
        
        flow_rule = {
            "priority": priority,
            "timeout": 0,
            "isPermanent": True,
            "deviceId": device_id,
            "appId": "org.onosproject.rest",
            "treatment": {
                "instructions": instructions
            },
            "selector": {
                "criteria": [
                    {
                        "type": "ETH_TYPE",
                        "ethType": "0x0806"
                    }
                ]
            }
        }
        
        return flow_rule
    
    def create_ip_flow(self, device_id: str, src_ip: str = None, dst_ip: str = None,
                      output_port: int = None, priority: int = None) -> Dict[str, Any]:
        """
        创建IP流表规则
        
        Args:
            device_id: 设备ID
            src_ip: 源IP地址
            dst_ip: 目标IP地址
            output_port: 输出端口
            priority: 优先级
            
        Returns:
            Dict[str, Any]: 流表规则
        """
        if priority is None:
            priority = self.next_priority
            self.next_priority += 10
        
        criteria = [
            {
                "type": "ETH_TYPE",
                "ethType": "0x0800"  # IPv4协议类型
            }
        ]
        
        if src_ip:
            criteria.append({
                "type": "IPV4_SRC",
                "ip": src_ip
            })
        
        if dst_ip:
            criteria.append({
                "type": "IPV4_DST",
                "ip": dst_ip
            })
        
        flow_rule = {
            "priority": priority,
            "timeout": 0,
            "isPermanent": True,
            "deviceId": device_id,
            "appId": "org.onosproject.rest",
            "treatment": {
                "instructions": [
                    {
                        "type": "OUTPUT",
                        "port": str(output_port) if output_port else "CONTROLLER"
                    }
                ]
            },
            "selector": {
                "criteria": criteria
            }
        }
        
        return flow_rule


class FlowManager:
    """流表管理器"""
    
    def __init__(self, controller_client: ONOSControllerClient, 
                 topology_manager: TopologyManager):
        """
        初始化流表管理器
        
        Args:
            controller_client: ONOS控制器客户端
            topology_manager: 拓扑管理器
        """
        self.controller = controller_client
        self.topology_manager = topology_manager
        self.flow_builder = FlowRuleBuilder()
        self.installed_flows = {}  # 记录已安装的流表
        
    def install_host_to_host_flows(self, src_host_mac: str, dst_host_mac: str) -> bool:
        """
        安装主机间通信的双向流表
        
        Args:
            src_host_mac: 源主机MAC地址
            dst_host_mac: 目标主机MAC地址
            
        Returns:
            bool: 安装是否成功
        """
        try:
            # 获取路径信息
            path_calc = HostPathCalculator(self.topology_manager)
            route_info = path_calc.get_host_to_host_path(src_host_mac, dst_host_mac)
            
            if not route_info['success']:
                logger.error(f"无法获取路径信息: {route_info['message']}")
                return False
            
            device_path = route_info['device_path']
            
            # 安装正向流表
            success_forward = self._install_unidirectional_flows(
                src_host_mac, dst_host_mac, device_path
            )
            
            # 安装反向流表
            success_reverse = self._install_unidirectional_flows(
                dst_host_mac, src_host_mac, list(reversed(device_path))
            )
            
            success = success_forward and success_reverse
            if success:
                logger.info(f"主机 {src_host_mac} 和 {dst_host_mac} 间流表安装成功")
            
            return success
            
        except Exception as e:
            logger.error(f"安装主机间流表失败: {e}")
            return False
    
    def _install_unidirectional_flows(self, src_mac: str, dst_mac: str, 
                                    device_path: List[str]) -> bool:
        """
        安装单向流表
        
        Args:
            src_mac: 源MAC地址
            dst_mac: 目标MAC地址
            device_path: 设备路径
            
        Returns:
            bool: 安装是否成功
        """
        try:
            for i in range(len(device_path) - 1):
                current_device = device_path[i]
                next_device = device_path[i + 1]
                
                # 获取输出端口
                output_port = self._get_output_port(current_device, next_device)
                if output_port is None:
                    logger.error(f"无法找到设备 {current_device} 到 {next_device} 的端口")
                    return False
                
                # 创建流表规则
                flow_rule = self.flow_builder.create_host_to_host_flow(
                    current_device, src_mac, dst_mac, output_port
                )
                
                # 安装流表
                if not self.controller.install_flow_rule(current_device, flow_rule):
                    logger.error(f"设备 {current_device} 流表安装失败")
                    return False
                
                # 记录已安装的流表
                flow_key = f"{current_device}_{src_mac}_{dst_mac}"
                self.installed_flows[flow_key] = {
                    'device': current_device,
                    'src_mac': src_mac,
                    'dst_mac': dst_mac,
                    'output_port': output_port
                }
            
            return True
            
        except Exception as e:
            logger.error(f"安装单向流表失败: {e}")
            return False
    
    def _get_output_port(self, src_device: str, dst_device: str) -> Optional[int]:
        """
        获取源设备到目标设备的输出端口
        
        Args:
            src_device: 源设备ID
            dst_device: 目标设备ID
            
        Returns:
            Optional[int]: 输出端口号
        """
        try:
            # 查找链路信息
            for link in self.topology_manager.links:
                if (link['src']['device'] == src_device and 
                    link['dst']['device'] == dst_device):
                    return int(link['src']['port'])
                elif (link['src']['device'] == dst_device and 
                      link['dst']['device'] == src_device):
                    return int(link['dst']['port'])
            
            logger.warning(f"未找到设备 {src_device} 到 {dst_device} 的链路")
            return None
            
        except Exception as e:
            logger.error(f"获取输出端口失败: {e}")
            return None
    
    def install_broadcast_flows(self) -> bool:
        """
        安装广播流表
        
        Returns:
            bool: 安装是否成功
        """
        try:
            broadcast_mac = "ff:ff:ff:ff:ff:ff"
            
            for device_id, device_info in self.topology_manager.devices.items():
                # 获取设备的所有端口（除连接到其他交换机的端口）
                output_ports = self._get_broadcast_ports(device_id)
                
                if output_ports:
                    # 创建广播流表规则
                    flow_rule = self.flow_builder.create_broadcast_flow(
                        device_id, broadcast_mac, output_ports
                    )
                    
                    # 安装流表
                    if not self.controller.install_flow_rule(device_id, flow_rule):
                        logger.error(f"设备 {device_id} 广播流表安装失败")
                        return False
            
            logger.info("广播流表安装完成")
            return True
            
        except Exception as e:
            logger.error(f"安装广播流表失败: {e}")
            return False
    
    def _get_broadcast_ports(self, device_id: str) -> List[int]:
        """
        获取设备的广播端口（连接主机的端口）
        
        Args:
            device_id: 设备ID
            
        Returns:
            List[int]: 广播端口列表
        """
        try:
            host_ports = []
            
            # 查找连接到此设备的主机
            for host_mac, host_info in self.topology_manager.hosts.items():
                if host_info['location']['device'] == device_id:
                    host_ports.append(int(host_info['location']['port']))
            
            return host_ports
            
        except Exception as e:
            logger.error(f"获取广播端口失败: {e}")
            return []
    
    def install_arp_flows(self) -> bool:
        """
        安装ARP处理流表
        
        Returns:
            bool: 安装是否成功
        """
        try:
            for device_id, device_info in self.topology_manager.devices.items():
                # 获取设备的所有端口
                output_ports = self._get_all_device_ports(device_id)
                
                if output_ports:
                    # 创建ARP流表规则
                    flow_rule = self.flow_builder.create_arp_flow(
                        device_id, output_ports
                    )
                    
                    # 安装流表
                    if not self.controller.install_flow_rule(device_id, flow_rule):
                        logger.error(f"设备 {device_id} ARP流表安装失败")
                        return False
            
            logger.info("ARP流表安装完成")
            return True
            
        except Exception as e:
            logger.error(f"安装ARP流表失败: {e}")
            return False
    
    def _get_all_device_ports(self, device_id: str) -> List[int]:
        """
        获取设备的所有端口
        
        Args:
            device_id: 设备ID
            
        Returns:
            List[int]: 端口列表
        """
        try:
            device_info = self.topology_manager.devices.get(device_id, {})
            ports = device_info.get('ports', [])
            
            return [int(port['port']) for port in ports if port.get('enabled', True)]
            
        except Exception as e:
            logger.error(f"获取设备端口失败: {e}")
            return []
    
    def clear_device_flows(self, device_id: str) -> bool:
        """
        清除设备的所有流表
        
        Args:
            device_id: 设备ID
            
        Returns:
            bool: 清除是否成功
        """
        try:
            flow_rules = self.controller.get_flow_rules(device_id)
            
            for flow in flow_rules:
                flow_id = flow.get('id')
                if flow_id:
                    self.controller.delete_flow_rule(device_id, flow_id)
            
            logger.info(f"设备 {device_id} 流表清除完成")
            return True
            
        except Exception as e:
            logger.error(f"清除设备流表失败: {e}")
            return False
    
    def get_flow_statistics(self) -> Dict[str, Any]:
        """
        获取流表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = {
                'total_flows': 0,
                'device_flows': {},
                'installed_flows': len(self.installed_flows)
            }
            
            for device_id in self.topology_manager.devices:
                flows = self.controller.get_flow_rules(device_id)
                stats['device_flows'][device_id] = len(flows)
                stats['total_flows'] += len(flows)
            
            return stats
            
        except Exception as e:
            logger.error(f"获取流表统计失败: {e}")
            return {'total_flows': 0, 'device_flows': {}, 'installed_flows': 0}


class NetworkCommunicator:
    """网络通信器"""
    
    def __init__(self, controller_client: ONOSControllerClient, 
                 topology_manager: TopologyManager):
        """
        初始化网络通信器
        
        Args:
            controller_client: ONOS控制器客户端
            topology_manager: 拓扑管理器
        """
        self.controller = controller_client
        self.topology_manager = topology_manager
        self.flow_manager = FlowManager(controller_client, topology_manager)
    
    def enable_host_communication(self, src_host_mac: str, dst_host_mac: str) -> bool:
        """
        启用两个主机间的通信
        
        Args:
            src_host_mac: 源主机MAC地址
            dst_host_mac: 目标主机MAC地址
            
        Returns:
            bool: 启用是否成功
        """
        try:
            # 更新拓扑信息
            if not self.topology_manager.update_topology():
                logger.error("拓扑更新失败")
                return False
            
            # 安装主机间流表
            success = self.flow_manager.install_host_to_host_flows(src_host_mac, dst_host_mac)
            
            if success:
                logger.info(f"主机 {src_host_mac} 和 {dst_host_mac} 间通信已启用")
            
            return success
            
        except Exception as e:
            logger.error(f"启用主机通信失败: {e}")
            return False
    
    def enable_all_host_communication(self) -> bool:
        """
        启用所有主机间的通信
        
        Returns:
            bool: 启用是否成功
        """
        try:
            # 更新拓扑信息
            if not self.topology_manager.update_topology():
                logger.error("拓扑更新失败")
                return False
            
            # 安装基础流表（ARP和广播）
            if not self.flow_manager.install_arp_flows():
                logger.error("ARP流表安装失败")
                return False
            
            if not self.flow_manager.install_broadcast_flows():
                logger.error("广播流表安装失败")
                return False
            
            # 为所有主机对安装流表
            host_macs = list(self.topology_manager.hosts.keys())
            success_count = 0
            total_pairs = 0
            
            for i, src_mac in enumerate(host_macs):
                for dst_mac in host_macs[i+1:]:
                    total_pairs += 1
                    if self.flow_manager.install_host_to_host_flows(src_mac, dst_mac):
                        success_count += 1
            
            success_rate = success_count / total_pairs if total_pairs > 0 else 0
            logger.info(f"所有主机通信启用完成，成功率: {success_rate:.2%}")
            
            return success_rate > 0.8  # 80%以上成功率认为成功
            
        except Exception as e:
            logger.error(f"启用所有主机通信失败: {e}")
            return False
    
    def get_network_status(self) -> Dict[str, Any]:
        """
        获取网络状态
        
        Returns:
            Dict[str, Any]: 网络状态信息
        """
        try:
            # 更新拓扑
            self.topology_manager.update_topology()
            
            # 获取拓扑统计
            topology_stats = self.topology_manager.get_topology_stats()
            
            # 获取流表统计
            flow_stats = self.flow_manager.get_flow_statistics()
            
            # 检查主机连通性
            connectivity_status = self._check_connectivity()
            
            return {
                'topology': topology_stats,
                'flows': flow_stats,
                'connectivity': connectivity_status,
                'status': 'healthy' if connectivity_status['connected_hosts'] > 0 else 'disconnected'
            }
            
        except Exception as e:
            logger.error(f"获取网络状态失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _check_connectivity(self) -> Dict[str, Any]:
        """
        检查网络连通性
        
        Returns:
            Dict[str, Any]: 连通性信息
        """
        try:
            host_macs = list(self.topology_manager.hosts.keys())
            connected_hosts = 0
            
            if len(host_macs) < 2:
                return {'connected_hosts': 0, 'total_hosts': len(host_macs)}
            
            path_calc = HostPathCalculator(self.topology_manager)
            
            for i, src_mac in enumerate(host_macs):
                for dst_mac in host_macs[i+1:]:
                    route_info = path_calc.get_host_to_host_path(src_mac, dst_mac)
                    if route_info['success']:
                        connected_hosts += 2  # 双向连通
            
            return {
                'connected_hosts': connected_hosts,
                'total_hosts': len(host_macs),
                'connectivity_rate': connected_hosts / (len(host_macs) * (len(host_macs) - 1))
            }
            
        except Exception as e:
            logger.error(f"检查连通性失败: {e}")
            return {'connected_hosts': 0, 'total_hosts': 0}


if __name__ == "__main__":
    # 测试代码
    from controller_client import ONOSControllerClient
    
    # 创建控制器客户端
    client = ONOSControllerClient()
    
    if client.test_connection():
        print("ONOS控制器连接成功")
        
        # 创建拓扑管理器
        topology_manager = TopologyManager(client)
        topology_manager.update_topology()
        
        # 创建网络通信器
        communicator = NetworkCommunicator(client, topology_manager)
        
        # 获取网络状态
        status = communicator.get_network_status()
        print(f"网络状态: {status}")
        
        # 启用所有主机通信
        success = communicator.enable_all_host_communication()
        print(f"启用所有主机通信: {success}")
        
    else:
        print("ONOS控制器连接失败")