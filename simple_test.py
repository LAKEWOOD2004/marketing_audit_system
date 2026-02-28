# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'c:\Users\LAKEWOOD\Desktop\毕业设计\marketing_audit_system')

from openai import OpenAI

api_key = "9d16cdbfdbd8422ba8dd142aae4e9107.SeYx3XbdzNpUZqov"
base_url = "https://open.bigmodel.cn/api/paas/v4"

print("=" * 50)
print("Zhipu AI API Connection Test")
print("=" * 50)
print(f"API Key: {api_key[:20]}...")
print(f"Base URL: {base_url}")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

print("\nTesting connection...")

try:
    response = client.chat.completions.create(
        model="glm-4",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "Hello, please introduce yourself in one sentence."}
        ],
        temperature=0.7
    )
    
    print("\nModel Response:")
    print(response.choices[0].message.content)
    print("\n" + "=" * 50)
    print("API Connection Successful!")
    print("=" * 50)
    
except Exception as e:
    print(f"\nError: {e}")
    print("\n" + "=" * 50)
    print("API Connection Failed!")
    print("=" * 50)
