#!/usr/bin/env python3

"""
SDN网络通信系统集成测试脚本
"""

import subprocess
import time
import sys
import signal
import os

def signal_handler(sig, frame):
    print("\n正在清理...")
    cleanup()
    sys.exit(0)

def cleanup():
    """清理环境"""
    try:
        # 清理Mininet
        subprocess.run(["echo", "vmsink"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["sudo", "-S", "mn", "-c"], input="vmsink\n", text=True)
    except:
        pass

def wait_for_devices(max_wait=30):
    """等待设备连接到ONOS"""
    print("等待设备连接到ONOS...")
    
    import requests
    from requests.auth import HTTPBasicAuth
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                "http://localhost:8181/onos/v1/devices",
                auth=HTTPBasicAuth("onos", "rocks"),
                timeout=5
            )
            if response.status_code == 200:
                devices = response.json().get('devices', [])
                if len(devices) >= 2:
                    print(f"✓ 检测到 {len(devices)} 个设备")
                    return True
        except:
            pass
        
        print(".", end="", flush=True)
        time.sleep(2)
    
    print(f"\n✗ 等待超时，只检测到设备")
    return False

def wait_for_hosts(max_wait=30):
    """等待主机被发现"""
    print("等待主机被发现...")
    
    import requests
    from requests.auth import HTTPBasicAuth
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                "http://localhost:8181/onos/v1/hosts",
                auth=HTTPBasicAuth("onos", "rocks"),
                timeout=5
            )
            if response.status_code == 200:
                hosts = response.json().get('hosts', [])
                if len(hosts) >= 4:
                    print(f"✓ 发现 {len(hosts)} 个主机")
                    return True
        except:
            pass
        
        print(".", end="", flush=True)
        time.sleep(2)
    
    print(f"\n✗ 等待超时，只发现主机")
    return False

def test_sdn_app():
    """测试SDN应用"""
    print("启动SDN控制器应用...")
    
    # 启动SDN应用
    sdn_process = subprocess.Popen(
        [sys.executable, "main_app.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.getcwd()
    )
    
    # 等待应用启动
    time.sleep(5)
    
    # 发送命令
    commands = ["status\n", "topology\n", "hosts\n", "quit\n"]
    input_text = "".join(commands)
    
    try:
        stdout, stderr = sdn_process.communicate(input=input_text, timeout=30)
        print("SDN应用输出:")
        print(stdout)
        if stderr:
            print("错误信息:")
            print(stderr)
        return True
    except subprocess.TimeoutExpired:
        sdn_process.kill()
        print("SDN应用测试超时")
        return False

def main():
    """主测试流程"""
    print("SDN网络通信系统集成测试")
    print("=" * 50)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    # 1. 清理环境
    print("1. 清理环境...")
    cleanup()
    
    # 2. 启动Mininet
    print("\n2. 启动Mininet拓扑...")
    mininet_process = subprocess.Popen(
        ["echo", "vmsink"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    
    mininet_process = subprocess.Popen(
        ["sudo", "-S", "python3", "topology.py", "--topo", "linear", "--switches", "2", "--hosts-per-switch", "2"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 3. 等待设备连接
    if not wait_for_devices():
        print("设备连接失败，终止测试")
        mininet_process.terminate()
        return False
    
    # 4. 等待主机发现
    if not wait_for_hosts():
        print("主机发现失败，继续测试...")
    
    # 5. 测试SDN应用
    print("\n3. 测试SDN应用...")
    if test_sdn_app():
        print("✓ SDN应用测试完成")
    else:
        print("✗ SDN应用测试失败")
    
    # 6. 清理
    print("\n4. 清理环境...")
    mininet_process.terminate()
    try:
        mininet_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        mininet_process.kill()
    
    cleanup()
    
    print("\n测试完成！")
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n测试被中断")
        cleanup()
