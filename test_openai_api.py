#!/usr/bin/env python3
"""
测试 OpenAI API 连接
"""

import warnings

# Quiet common environment warning on macOS LibreSSL builds
warnings.filterwarnings('ignore', message=r"urllib3 v2 only supports OpenSSL.*")

import requests
import sys

def test_openai_api(api_key):
    """测试 OpenAI API 是否可用"""
    
    if not api_key:
        print("❌ 错误：未提供 OpenAI API Key")
        return False
    
    print(f"🔍 测试 OpenAI API...")
    print(f"📌 API Key: {api_key[:20]}...{api_key[-10:]}")
    print()
    
    # Test 1: List Models
    print("Test 1️⃣: 获取模型列表...")
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=10
        )
        
        print(f"   HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            print(f"   ✓ 成功！获取到 {len(models)} 个模型")
            print(f"   可用模型示例：")
            for model in models[:5]:
                print(f"     - {model.get('id')}")
            if len(models) > 5:
                print(f"     ... 还有 {len(models) - 5} 个模型")
            return True
        
        elif response.status_code == 401:
            print(f"   ✗ 认证失败 (HTTP 401)")
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                print(f"   错误信息：{error_msg}")
            except:
                print(f"   响应：{response.text[:200]}")
            return False
        
        elif response.status_code == 429:
            print(f"   ✗ 速率限制 (HTTP 429) - API 调用过于频繁")
            return False
        
        else:
            print(f"   ✗ 请求失败")
            print(f"   响应：{response.text[:300]}")
            return False
    
    except requests.exceptions.Timeout:
        print(f"   ✗ 请求超时 (timeout)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ✗ 连接错误：{str(e)[:100]}")
        return False
    except Exception as e:
        print(f"   ✗ 异常错误：{str(e)[:100]}")
        return False

def main():
    """主函数"""
    
    # 从命令行参数获取 API Key
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        # 尝试从环境变量读取
        import os
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        
        if not api_key:
            print("=" * 60)
            print("OpenAI API 连接测试工具")
            print("=" * 60)
            print()
            print("用法：")
            print("  python3 test_openai_api.py <API_KEY>")
            print()
            print("或者设置环境变量：")
            print("  export OPENAI_API_KEY='sk-proj-...'")
            print("  python3 test_openai_api.py")
            print()
            print("=" * 60)
            return False
    
    print("=" * 60)
    print("🧪 OpenAI API 连接测试")
    print("=" * 60)
    print()
    
    result = test_openai_api(api_key)
    
    print()
    print("=" * 60)
    if result:
        print("✅ OpenAI API 连接成功！")
        print("=" * 60)
        return True
    else:
        print("❌ OpenAI API 连接失败！")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
