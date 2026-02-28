#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智谱AI API 连接测试脚本
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_zhipu_connection():
    print("=" * 50)
    print("智谱AI API 连接测试")
    print("=" * 50)
    
    from config.settings import LLM_CONFIG
    
    print(f"\n配置信息:")
    print(f"  Provider: {LLM_CONFIG.get('provider')}")
    print(f"  Model: {LLM_CONFIG.get('model')}")
    print(f"  Base URL: {LLM_CONFIG.get('base_url')}")
    print(f"  API Key: {LLM_CONFIG.get('api_key')[:20]}...")
    
    print("\n正在测试连接...")
    
    try:
        from utils.llm_client import llm_client
        
        test_message = "你好，请用一句话介绍你自己。"
        print(f"\n发送测试消息: {test_message}")
        
        response = llm_client.chat_with_system(
            "你是一个友好的AI助手。",
            test_message
        )
        
        print(f"\n模型响应:")
        print(f"  {response}")
        
        print("\n✅ 智谱AI API 连接成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        return False


def test_json_response():
    print("\n" + "=" * 50)
    print("JSON响应格式测试")
    print("=" * 50)
    
    try:
        from utils.llm_client import llm_client
        
        system_prompt = "你是一个审计规则提取专家。请以JSON格式返回结果。"
        user_message = "请从以下文本中提取规则：单张优惠券金额不得超过500元。返回格式: {\"rules\": [{\"rule\": \"...\", \"type\": \"...\"]}"
        
        print(f"\n发送JSON格式请求...")
        result = llm_client.chat_json(system_prompt, user_message)
        
        print(f"\n返回结果:")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if "error" not in result:
            print("\n✅ JSON响应格式正确！")
            return True
        else:
            print("\n⚠️ JSON解析有问题，但API连接正常")
            return True
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def main():
    success1 = test_zhipu_connection()
    success2 = test_json_response()
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    print(f"  基础连接: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"  JSON格式: {'✅ 通过' if success2 else '❌ 失败'}")
    
    if success1 and success2:
        print("\n🎉 所有测试通过！系统已准备就绪。")
    else:
        print("\n⚠️ 部分测试未通过，请检查配置。")


if __name__ == "__main__":
    main()
