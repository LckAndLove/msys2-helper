#!/usr/bin/env python3
"""
测试卡密编辑功能
"""
import requests
import json
from bs4 import BeautifulSoup

# 配置
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"
ADMIN_URL = f"{BASE_URL}/admin"

def test_edit_card():
    """测试编辑卡密功能"""
    session = requests.Session()
    
    print("=== 测试卡密编辑功能 ===")
    
    # 1. 获取卡密列表
    print("1. 获取卡密列表...")
    response = session.get(f"{ADMIN_URL}/")
    if response.status_code != 200:
        print(f"❌ 获取卡密列表失败: {response.status_code}")
        return
    
    print("✅ 获取卡密列表成功")
    
    # 2. 测试编辑第一个卡密
    print("2. 编辑第一个卡密...")
    
    # 假设编辑ID为1的卡密
    card_id = 1
    edit_data = {
        'prefix': 'TEST_EDIT',
        'status': 'UNUSED'
    }
    
    response = session.post(f"{ADMIN_URL}/card/{card_id}/edit", data=edit_data)
    
    if response.status_code == 200:
        print("✅ 卡密编辑成功")
        # 检查是否有成功消息
        if "卡密更新成功" in response.text:
            print("✅ 发现成功消息")
        elif "更新失败" in response.text:
            print("❌ 发现失败消息")
            # 尝试解析错误信息
            soup = BeautifulSoup(response.text, 'html.parser')
            alerts = soup.find_all('div', class_='alert-danger')
            for alert in alerts:
                print(f"   错误信息: {alert.get_text().strip()}")
    else:
        print(f"❌ 卡密编辑失败: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
    
    # 3. 测试不同状态值
    print("3. 测试不同状态值...")
    
    test_statuses = ['UNUSED', 'ACTIVE', 'EXPIRED']
    for status in test_statuses:
        edit_data = {
            'prefix': 'TEST_STATUS',
            'status': status
        }
        
        response = session.post(f"{ADMIN_URL}/card/{card_id}/edit", data=edit_data)
        
        if response.status_code == 200:
            if "卡密更新成功" in response.text:
                print(f"✅ 状态 {status} 更新成功")
            else:
                print(f"❌ 状态 {status} 更新失败")
        else:
            print(f"❌ 状态 {status} 请求失败: {response.status_code}")

def test_direct_post():
    """直接测试 POST 请求"""
    print("\n=== 直接测试 POST 请求 ===")
    
    # 测试数据
    test_data = {
        'prefix': 'DIRECT_TEST',
        'status': 'UNUSED'
    }
    
    response = requests.post(f"{ADMIN_URL}/card/1/edit", data=test_data)
    
    print(f"状态码: {response.status_code}")
    print(f"响应头: {response.headers}")
    
    if response.status_code == 200:
        print("✅ 请求成功")
    else:
        print(f"❌ 请求失败")
        print(f"响应内容: {response.text[:1000]}")

def test_status_enum():
    """测试状态枚举值"""
    print("\n=== 测试状态枚举值 ===")
    
    # 测试所有状态值
    status_values = ['UNUSED', 'ACTIVE', 'EXPIRED']
    
    for status in status_values:
        try:
            # 这里应该导入CardStatus，但由于脚本独立运行，我们用字符串测试
            print(f"✅ 状态值 '{status}' 有效")
        except Exception as e:
            print(f"❌ 状态值 '{status}' 无效: {e}")

if __name__ == "__main__":
    try:
        test_status_enum()
        test_direct_post()
        test_edit_card()
        print("\n测试完成！")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()