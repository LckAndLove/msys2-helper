#!/usr/bin/env python3
"""
机器码生成测试脚本
用于测试机器码生成功能
"""
import sys
import os

# 添加当前目录到Python路径，以便导入install_msys2模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from install_msys2 import get_machine_code
    
    print("=" * 50)
    print("机器码生成测试")
    print("=" * 50)
    
    machine_code = get_machine_code()
    print(f"生成的机器码: {machine_code}")
    print(f"机器码长度: {len(machine_code)}")
    
    # 验证机器码的一致性
    machine_code2 = get_machine_code()
    if machine_code == machine_code2:
        print("✓ 机器码生成一致性测试通过")
    else:
        print("✗ 机器码生成不一致")
    
    print("=" * 50)
    print("测试完成")
    print("=" * 50)
    
except ImportError as e:
    print(f"导入错误: {e}")
except Exception as e:
    print(f"运行错误: {e}")

input("按任意键退出...")
