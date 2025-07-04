#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试 - 验证修复后的代码
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """测试导入"""
    try:
        from install_msys2 import get_machine_code, validate_license, reset_vscode, confirm_vscode_reset
        print("✓ 所有函数导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_machine_code():
    """测试机器码"""
    try:
        from install_msys2 import get_machine_code
        machine_code = get_machine_code()
        print(f"✓ 机器码生成成功: {machine_code[:16]}...")
        return True
    except Exception as e:
        print(f"✗ 机器码生成失败: {e}")
        return False

def test_vscode_paths():
    """测试VS Code路径"""
    try:
        import os
        vscode_config = os.path.expanduser(r'~\AppData\Roaming\Code')
        vscode_extensions = os.path.expanduser(r'~\.vscode')
        
        print(f"VS Code配置路径: {vscode_config}")
        print(f"  存在: {'✓' if os.path.exists(vscode_config) else '✗'}")
        
        print(f"VS Code扩展路径: {vscode_extensions}")
        print(f"  存在: {'✓' if os.path.exists(vscode_extensions) else '✗'}")
        
        return True
    except Exception as e:
        print(f"✗ 路径检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("测试修复后的代码")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_import),
        ("机器码测试", test_machine_code),
        ("VS Code路径测试", test_vscode_paths)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n{name}:")
        if test_func():
            passed += 1
        else:
            print(f"  {name} 失败")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 50)
    
    if passed == total:
        print("✓ 所有测试通过！代码修复成功")
    else:
        print("✗ 部分测试失败，请检查代码")

if __name__ == "__main__":
    main()
