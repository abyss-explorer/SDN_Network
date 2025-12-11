#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试ONOS控制器连接
"""

import requests
import sys

def test_onos_connection():
    """测试ONOS连接"""
    base_url = "http://localhost:8181"
    auth = ("onos", "rocks")
    
    print("测试ONOS控制器连接...")
    
    # 测试不同的API端点
    endpoints = [
        "/onos/v1/system",
        "/onos/v1/devices", 
        "/onos/v1/hosts",
        "/onos/v1/links"
    ]
    
    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"\n测试端点: {url}")
        
        try:
            response = requests.get(url, auth=auth, timeout=5)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ 连接成功")
                if endpoint == "/onos/v1/devices":
                    data = response.json()
                    devices = data.get('devices', [])
                    print(f"  设备数量: {len(devices)}")
                    for device in devices:
                        print(f"  - {device.get('id')}: {device.get('type')} {'(活跃)' if device.get('available') else '(非活跃)'}")
                elif endpoint == "/onos/v1/hosts":
                    data = response.json()
                    hosts = data.get('hosts', [])
                    print(f"  主机数量: {len(hosts)}")
            else:
                print(f"✗ 连接失败: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("✗ 连接失败: 无法连接到ONOS控制器")
            return False
        except requests.exceptions.Timeout:
            print("✗ 连接失败: 请求超时")
            return False
        except Exception as e:
            print(f"✗ 连接失败: {e}")
            return False
    
    print("\nONOS控制器测试完成")
    return True

if __name__ == "__main__":
    if test_onos_connection():
        print("\n✓ ONOS控制器正常工作")
        sys.exit(0)
    else:
        print("\n✗ ONOS控制器连接失败")
        sys.exit(1)