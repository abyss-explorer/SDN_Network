#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Intent管理模块
负责在ONOS中创建和管理Intent，用于在UI中突显监控路径
"""

import logging
from typing import Dict, List, Optional, Any
from requests.exceptions import RequestException
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentManager:
    """ONOS Intent管理器"""
    
    def __init__(self, base_url: str, auth: tuple):
        """
        初始化Intent管理器
        
        Args:
            base_url: ONOS控制器基础URL
            auth: (username, password) 认证元组
        """
        self.base_url = base_url
        self.auth = auth
        self.session = requests.Session()
        self.session.auth = auth
        self.headers = {"Content-Type": "application/json"}
    
    def create_host_intent(self, src_mac: str, dst_mac: str) -> bool:
        """
        创建主机间Intent（在ONOS UI中显示为突显的线路）
        
        Args:
            src_mac: 源主机MAC
            dst_mac: 目的主机MAC
            
        Returns:
            bool: 创建是否成功
        """
        try:
            url = f"{self.base_url}/onos/v1/intents"
            
            # 构建Host Intent JSON
            intent_data = {
                "type": "HostToHostIntent",
                "appId": "org.onosproject.core",
                "one": f"{src_mac}/None",
                "two": f"{dst_mac}/None",
                "priority": 100
            }
            
            response = self.session.post(url, json=intent_data, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            logger.info(f"创建Host Intent成功: {src_mac} -> {dst_mac}")
            return True
            
        except RequestException as e:
            logger.error(f"创建Host Intent失败 {src_mac} -> {dst_mac}: {e}")
            return False
    
    def delete_host_intent(self, src_mac: str, dst_mac: str) -> bool:
        """
        删除主机间Intent
        
        Args:
            src_mac: 源主机MAC
            dst_mac: 目的主机MAC
            
        Returns:
            bool: 删除是否成功
        """
        try:
            intents = self.get_intents()
            
            for intent in intents:
                intent_type = intent.get('type', '')
                one = intent.get('one', '')
                two = intent.get('two', '')
                
                # 匹配双向的Host Intent
                if (intent_type == 'HostToHostIntent' and
                    ((one.startswith(src_mac) and two.startswith(dst_mac)) or
                     (one.startswith(dst_mac) and two.startswith(src_mac)))):
                    
                    intent_id = intent.get('id')
                    url = f"{self.base_url}/onos/v1/intents/{intent_id}"
                    
                    response = self.session.delete(url, headers={"Accept": "application/json"}, timeout=10)
                    response.raise_for_status()
                    
                    logger.info(f"删除Host Intent成功: {src_mac} -> {dst_mac}")
                    return True
            
            logger.warning(f"未找到对应的Host Intent: {src_mac} -> {dst_mac}")
            return False
            
        except RequestException as e:
            logger.error(f"删除Host Intent失败 {src_mac} -> {dst_mac}: {e}")
            return False
    
    def get_intents(self) -> List[Dict]:
        """
        获取所有Intent
        
        Returns:
            List[Dict]: Intent列表
        """
        try:
            url = f"{self.base_url}/onos/v1/intents"
            headers = {"Accept": "application/json"}
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            intents_data = response.json()
            return intents_data.get('intents', [])
            
        except RequestException as e:
            logger.error(f"获取Intent列表失败: {e}")
            return []
    
    def get_host_intents(self) -> List[Dict]:
        """
        获取所有Host Intent
        
        Returns:
            List[Dict]: Host Intent列表
        """
        try:
            all_intents = self.get_intents()
            host_intents = [intent for intent in all_intents if intent.get('type') == 'HostToHostIntent']
            return host_intents
            
        except Exception as e:
            logger.error(f"获取Host Intent列表失败: {e}")
            return []
    
    def delete_all_host_intents(self) -> int:
        """
        删除所有Host Intent
        
        Returns:
            int: 删除的Intent数量
        """
        try:
            host_intents = self.get_host_intents()
            deleted_count = 0
            
            for intent in host_intents:
                intent_id = intent.get('id')
                url = f"{self.base_url}/onos/v1/intents/{intent_id}"
                
                try:
                    response = self.session.delete(url, headers={"Accept": "application/json"}, timeout=10)
                    response.raise_for_status()
                    deleted_count += 1
                except RequestException as e:
                    logger.warning(f"删除Intent {intent_id} 失败: {e}")
            
            logger.info(f"删除 {deleted_count} 个Host Intent")
            return deleted_count
            
        except Exception as e:
            logger.error(f"删除所有Host Intent失败: {e}")
            return 0
