#!/usr/bin/env python3
"""
MSYS2-Helper 授权系统测试脚本
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入主程序
try:
    from install_msys2 import get_machine_code, validate_license
    print("✓ 成功导入主程序模块")
except ImportError as e:
    print(f"✗ 导入主程序模块失败: {e}")
    sys.exit(1)

def test_machine_code():
    """测试机器码生成"""
    print("\n" + "="*50)
    print("测试机器码生成功能")
    print("="*50)
    
    try:
        machine_code = get_machine_code()
        print(f"生成的机器码: {machine_code}")
        print(f"机器码长度: {len(machine_code)}")
        
        # 测试一致性
        code2 = get_machine_code()
        if machine_code == code2:
            print("✓ 机器码生成一致")
        else:
            print("✗ 机器码生成不一致")
            
    except Exception as e:
        print(f"✗ 机器码生成失败: {e}")

def test_license_validation():
    """测试授权码验证"""
    print("\n" + "="*50)
    print("测试授权码验证功能")
    print("="*50)
    
    # 测试空授权码
    try:
        success, message = validate_license("")
        print(f"空授权码测试: {success}, {message}")
    except Exception as e:
        print(f"空授权码测试失败: {e}")
    
    # 测试无效授权码
    try:
        success, message = validate_license("INVALID-CODE-123")
        print(f"无效授权码测试: {success}, {message}")
    except Exception as e:
        print(f"无效授权码测试失败: {e}")

def main():
    """主函数"""
    print("MSYS2-Helper 授权系统测试")
    print("="*50)
    
    # 检查配置文件
    if os.path.exists('auth_config.py'):
        print("✓ 找到配置文件 auth_config.py")
        try:
            import auth_config
            print(f"  API地址: {auth_config.API_BASE_URL}{auth_config.VALIDATE_ENDPOINT}")
            print(f"  最大尝试次数: {auth_config.MAX_ATTEMPTS}")
            print(f"  请求超时: {auth_config.TIMEOUT}秒")
        except Exception as e:
            print(f"  配置文件读取失败: {e}")
    else:
        print("! 未找到配置文件，将使用默认配置")
        print("  API地址: http://localhost:5000/api/validate")
        print("  最大尝试次数: 3")
        print("  请求超时: 10秒")
    
    # 测试机器码生成
    test_machine_code()
    
    # 测试授权码验证
    test_license_validation()
    
    print("\n" + "="*50)
    print("测试完成")
    print("="*50)
    
    # 询问是否启动主程序
    try:
        choice = input("\n是否启动主程序进行完整测试? (y/n): ").strip().lower()
        if choice == 'y':
            print("启动主程序...")
            from install_msys2 import create_gui
            create_gui()
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"启动主程序失败: {e}")

if __name__ == "__main__":
    main()
