#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
卡密授权管理系统 API 测试脚本
"""

import requests
import json
import time
import uuid
from datetime import datetime

class KamiSystemTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, test_name, success, message=""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {message}")
    
    def test_health_check(self):
        """测试健康检查"""
        try:
            response = self.session.get(f"{self.api_url}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log_test("健康检查", True, "服务运行正常")
                    return True
                else:
                    self.log_test("健康检查", False, "服务状态异常")
                    return False
            else:
                self.log_test("健康检查", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("健康检查", False, f"连接失败: {str(e)}")
            return False
    
    def test_validate_nonexistent_card(self):
        """测试不存在的卡密"""
        try:
            data = {
                "code": "NONEXISTENT-123456",
                "machine_code": "TEST-MACHINE-001"
            }
            response = self.session.post(f"{self.api_url}/validate", json=data)
            
            if response.status_code == 404:
                result = response.json()
                if result.get("status") == "error" and "不存在" in result.get("message", ""):
                    self.log_test("不存在卡密验证", True, "正确返回404错误")
                    return True
            
            self.log_test("不存在卡密验证", False, f"返回状态码: {response.status_code}")
            return False
        except Exception as e:
            self.log_test("不存在卡密验证", False, f"请求失败: {str(e)}")
            return False
    
    def test_validate_demo_card(self):
        """测试示例卡密首次激活"""
        try:
            machine_code = f"TEST-MACHINE-{uuid.uuid4().hex[:8]}"
            data = {
                "code": "VIP-DEMO123456",
                "machine_code": machine_code
            }
            response = self.session.post(f"{self.api_url}/validate", json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    self.log_test("示例卡密首次激活", True, "激活成功")
                    return True, machine_code
                else:
                    self.log_test("示例卡密首次激活", False, result.get("message", "未知错误"))
                    return False, None
            else:
                self.log_test("示例卡密首次激活", False, f"HTTP {response.status_code}")
                return False, None
        except Exception as e:
            self.log_test("示例卡密首次激活", False, f"请求失败: {str(e)}")
            return False, None
    
    def test_validate_activated_card(self, machine_code):
        """测试已激活卡密的验证"""
        try:
            data = {
                "code": "VIP-DEMO123456",
                "machine_code": machine_code
            }
            response = self.session.post(f"{self.api_url}/validate", json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    remaining_hours = result.get("remaining_hours", 0)
                    self.log_test("已激活卡密验证", True, f"验证成功，剩余时间: {remaining_hours}小时")
                    return True
                else:
                    self.log_test("已激活卡密验证", False, result.get("message", "未知错误"))
                    return False
            else:
                self.log_test("已激活卡密验证", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("已激活卡密验证", False, f"请求失败: {str(e)}")
            return False
    
    def test_validate_wrong_machine_code(self):
        """测试错误的机器码"""
        try:
            data = {
                "code": "VIP-DEMO123456",
                "machine_code": "WRONG-MACHINE-CODE"
            }
            response = self.session.post(f"{self.api_url}/validate", json=data)
            
            if response.status_code == 403:
                result = response.json()
                if "机器码不匹配" in result.get("message", ""):
                    self.log_test("错误机器码验证", True, "正确拒绝了错误的机器码")
                    return True
            
            self.log_test("错误机器码验证", False, f"返回状态码: {response.status_code}")
            return False
        except Exception as e:
            self.log_test("错误机器码验证", False, f"请求失败: {str(e)}")
            return False
    
    def test_get_card_status(self):
        """测试获取卡密状态"""
        try:
            response = self.session.get(f"{self.api_url}/status/VIP-DEMO123456")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    card_data = result.get("data", {})
                    status = card_data.get("status")
                    self.log_test("获取卡密状态", True, f"状态: {status}")
                    return True
                else:
                    self.log_test("获取卡密状态", False, result.get("message", "未知错误"))
                    return False
            else:
                self.log_test("获取卡密状态", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("获取卡密状态", False, f"请求失败: {str(e)}")
            return False
    
    def test_invalid_request_format(self):
        """测试无效的请求格式"""
        try:
            # 测试空的JSON
            response = self.session.post(f"{self.api_url}/validate", json={})
            if response.status_code == 400:
                self.log_test("无效请求格式", True, "正确处理了无效请求")
                return True
            
            self.log_test("无效请求格式", False, f"返回状态码: {response.status_code}")
            return False
        except Exception as e:
            self.log_test("无效请求格式", False, f"请求失败: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("卡密授权管理系统 API 测试")
        print("=" * 60)
        print()
        
        # 健康检查
        if not self.test_health_check():
            print("服务不可用，停止测试")
            return False
        
        print()
        
        # 基础功能测试
        self.test_validate_nonexistent_card()
        self.test_invalid_request_format()
        
        # 示例卡密测试
        success, machine_code = self.test_validate_demo_card()
        if success and machine_code:
            time.sleep(1)  # 等待1秒
            self.test_validate_activated_card(machine_code)
            self.test_validate_wrong_machine_code()
        
        # 状态查询测试
        self.test_get_card_status()
        
        print()
        print("=" * 60)
        print("测试报告")
        print("=" * 60)
        
        success_count = sum(1 for r in self.test_results if r["success"])
        total_count = len(self.test_results)
        
        print(f"总测试数: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")
        print(f"成功率: {success_count / total_count * 100:.1f}%")
        
        print()
        print("详细结果:")
        for result in self.test_results:
            status = "✓" if result["success"] else "✗"
            print(f"  {status} {result['test']}: {result['message']}")
        
        return success_count == total_count

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="卡密授权管理系统 API 测试")
    parser.add_argument("--url", default="http://localhost:5000", help="服务地址")
    parser.add_argument("--output", help="输出测试报告到文件")
    
    args = parser.parse_args()
    
    tester = KamiSystemTester(args.url)
    success = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(tester.test_results, f, ensure_ascii=False, indent=2)
        print(f"\n测试报告已保存到: {args.output}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
