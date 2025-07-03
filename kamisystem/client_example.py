#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
卡密授权管理系统客户端示例
演示如何在其他应用中集成卡密验证功能
"""

import requests
import json
import uuid
import platform
import hashlib
from datetime import datetime, timedelta

class KamiClient:
    """卡密验证客户端"""
    
    def __init__(self, api_url="http://localhost:5000/api"):
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'KamiClient/1.0'
        })
    
    def generate_machine_code(self):
        """生成机器码"""
        # 获取系统信息
        system_info = {
            'system': platform.system(),
            'node': platform.node(),
            'processor': platform.processor(),
            'architecture': platform.architecture()[0]
        }
        
        # 生成唯一标识
        info_str = json.dumps(system_info, sort_keys=True)
        machine_code = hashlib.md5(info_str.encode()).hexdigest()
        
        return f"PC-{machine_code[:16].upper()}"
    
    def validate_card(self, card_code, machine_code=None):
        """验证卡密"""
        if not machine_code:
            machine_code = self.generate_machine_code()
        
        data = {
            "code": card_code,
            "machine_code": machine_code
        }
        
        try:
            response = self.session.post(f"{self.api_url}/validate", json=data)
            result = response.json()
            
            if response.status_code == 200 and result.get("status") == "success":
                return {
                    "success": True,
                    "message": result.get("message"),
                    "expire_at": result.get("expire_at"),
                    "remaining_hours": result.get("remaining_hours"),
                    "machine_code": machine_code
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "验证失败"),
                    "error_code": response.status_code
                }
        
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"网络错误: {str(e)}",
                "error_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"未知错误: {str(e)}",
                "error_code": -2
            }
    
    def get_card_status(self, card_code):
        """获取卡密状态"""
        try:
            response = self.session.get(f"{self.api_url}/status/{card_code}")
            result = response.json()
            
            if response.status_code == 200 and result.get("status") == "success":
                return {
                    "success": True,
                    "data": result.get("data")
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "获取状态失败"),
                    "error_code": response.status_code
                }
        
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"网络错误: {str(e)}",
                "error_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"未知错误: {str(e)}",
                "error_code": -2
            }
    
    def check_service_health(self):
        """检查服务健康状态"""
        try:
            response = self.session.get(f"{self.api_url}/health")
            if response.status_code == 200:
                return True
            return False
        except:
            return False

class SimpleApp:
    """简单应用示例"""
    
    def __init__(self):
        self.client = KamiClient()
        self.authorized = False
        self.card_info = None
        self.machine_code = self.client.generate_machine_code()
    
    def show_welcome(self):
        """显示欢迎界面"""
        print("=" * 60)
        print("欢迎使用示例应用")
        print("=" * 60)
        print(f"机器码: {self.machine_code}")
        print()
        
        # 检查服务状态
        if not self.client.check_service_health():
            print("⚠️  警告: 卡密验证服务不可用")
            print("请确保卡密授权管理系统正在运行")
            print()
    
    def request_card_input(self):
        """请求输入卡密"""
        print("请输入您的卡密进行验证:")
        print("(示例卡密: VIP-DEMO123456, PREMIUM-TEST789012, BASIC-SAMPLE345678)")
        print()
        
        card_code = input("卡密: ").strip()
        if not card_code:
            print("❌ 卡密不能为空")
            return False
        
        return card_code
    
    def validate_authorization(self, card_code):
        """验证授权"""
        print(f"正在验证卡密: {card_code}")
        print("请稍候...")
        
        result = self.client.validate_card(card_code, self.machine_code)
        
        if result["success"]:
            print("✅ 验证成功！")
            print(f"消息: {result['message']}")
            if result.get("expire_at"):
                print(f"过期时间: {result['expire_at']}")
            if result.get("remaining_hours"):
                print(f"剩余时间: {result['remaining_hours']} 小时")
            
            self.authorized = True
            self.card_info = result
            return True
        else:
            print("❌ 验证失败")
            print(f"错误: {result['message']}")
            return False
    
    def show_main_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 40)
        print("主菜单")
        print("=" * 40)
        print("1. 查看卡密状态")
        print("2. 重新验证")
        print("3. 模拟功能使用")
        print("4. 退出")
        print()
        
        choice = input("请选择 (1-4): ").strip()
        return choice
    
    def show_card_status(self):
        """显示卡密状态"""
        if not self.card_info:
            print("❌ 没有卡密信息")
            return
        
        # 获取最新状态
        card_code = input("请输入卡密代码: ").strip()
        if not card_code:
            print("❌ 卡密代码不能为空")
            return
        
        result = self.client.get_card_status(card_code)
        
        if result["success"]:
            data = result["data"]
            print("\n📊 卡密状态信息:")
            print(f"  代码: {data.get('full_code')}")
            print(f"  状态: {data.get('status')}")
            print(f"  创建时间: {data.get('created_at')}")
            print(f"  使用时间: {data.get('used_at') or '未使用'}")
            print(f"  过期时间: {data.get('expire_at') or '未设置'}")
            print(f"  机器码: {data.get('machine_code') or '未绑定'}")
            if data.get('remaining_hours'):
                print(f"  剩余时间: {data['remaining_hours']} 小时")
        else:
            print(f"❌ 获取状态失败: {result['message']}")
    
    def simulate_feature_usage(self):
        """模拟功能使用"""
        print("\n🎯 模拟功能使用")
        print("这里是应用的核心功能...")
        print("功能1: 数据处理 ✅")
        print("功能2: 报表生成 ✅")
        print("功能3: 高级分析 ✅")
        print("所有功能正常运行！")
    
    def run(self):
        """运行应用"""
        self.show_welcome()
        
        # 授权验证循环
        while not self.authorized:
            card_code = self.request_card_input()
            if not card_code:
                continue
            
            if self.validate_authorization(card_code):
                break
            
            retry = input("\n是否重试? (y/n): ").strip().lower()
            if retry != 'y':
                print("退出应用")
                return
        
        # 主功能循环
        while True:
            choice = self.show_main_menu()
            
            if choice == '1':
                self.show_card_status()
            elif choice == '2':
                self.authorized = False
                self.card_info = None
                print("重新验证...")
                card_code = self.request_card_input()
                if card_code:
                    self.validate_authorization(card_code)
            elif choice == '3':
                self.simulate_feature_usage()
            elif choice == '4':
                print("感谢使用！")
                break
            else:
                print("❌ 无效选择")
            
            input("\n按回车键继续...")

def main():
    """主函数"""
    try:
        app = SimpleApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序错误: {str(e)}")

if __name__ == "__main__":
    main()
