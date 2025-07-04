#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证改进后的功能
"""
import sys
import os
import json
import urllib.request
import urllib.error

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from install_msys2 import get_machine_code, validate_license
from auth_config import AUTH_API_URL

def test_machine_code():
    """测试机器码生成"""
    print("=" * 50)
    print("测试机器码生成功能")
    print("=" * 50)
    
    try:
        machine_code = get_machine_code()
        print(f"✓ 机器码生成成功: {machine_code}")
        print(f"✓ 机器码长度: {len(machine_code)} 字符")
        return True
    except Exception as e:
        print(f"✗ 机器码生成失败: {e}")
        return False

def test_api_connection():
    """测试API连接"""
    print("\n" + "=" * 50)
    print("测试API连接")
    print("=" * 50)
    
    try:
        # 测试健康检查接口
        health_url = AUTH_API_URL.replace('/api/validate', '/api/health')
        print(f"测试健康检查: {health_url}")
        
        request = urllib.request.Request(health_url)
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✓ API服务器响应: {result}")
            return True
    except Exception as e:
        print(f"✗ API连接失败: {e}")
        return False

def test_invalid_license():
    """测试无效卡密"""
    print("\n" + "=" * 50)
    print("测试无效卡密验证")
    print("=" * 50)
    
    test_codes = [
        "INVALID-CODE-123",
        "EXPIRED-CODE-456", 
        "USED-CODE-789",
        ""
    ]
    
    for code in test_codes:
        print(f"测试卡密: '{code}'")
        success, message = validate_license(code)
        
        if success:
            print(f"  ✗ 预期失败但成功了: {message}")
        else:
            print(f"  ✓ 正确失败: {message}")
        print()

def test_vs_code_paths():
    """测试VS Code路径检测"""
    print("\n" + "=" * 50)
    print("测试VS Code路径检测")
    print("=" * 50)
    
    import os
    
    # 检查VS Code配置路径
    vscode_config = os.path.expanduser(r'~\AppData\Roaming\Code')
    vscode_extensions = os.path.expanduser(r'~\.vscode')
    
    print(f"VS Code配置路径: {vscode_config}")
    print(f"  存在: {'✓' if os.path.exists(vscode_config) else '✗'}")
    
    print(f"VS Code扩展路径: {vscode_extensions}")
    print(f"  存在: {'✓' if os.path.exists(vscode_extensions) else '✗'}")
    
    # 检查备份目录创建
    backup_dir = os.path.join(os.path.expanduser('~'), 'VSCode_Backup_Test')
    try:
        os.makedirs(backup_dir, exist_ok=True)
        print(f"✓ 备份目录创建成功: {backup_dir}")
        os.rmdir(backup_dir)  # 清理测试目录
    except Exception as e:
        print(f"✗ 备份目录创建失败: {e}")

def main():
    """主测试函数"""
    print("开始测试改进后的功能...")
    print(f"API地址: {AUTH_API_URL}")
    
    # 运行所有测试
    test_machine_code()
    test_api_connection()
    test_invalid_license()
    test_vs_code_paths()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()
