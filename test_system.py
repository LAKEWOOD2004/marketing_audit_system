#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统测试脚本

用于验证各模块功能是否正常工作
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_document_parser():
    print("\n" + "=" * 50)
    print("测试模块一：文档解析")
    print("=" * 50)
    
    from modules.document_parser import document_parser
    
    policy_file = project_root / "data" / "input" / "sample_policy.json"
    
    if policy_file.exists():
        with open(policy_file, 'r', encoding='utf-8') as f:
            policy_data = json.load(f)
        
        print(f"加载政策数据: {policy_data.get('metadata', {}).get('title', '未知')}")
        print(f"内容段落数: {len(policy_data.get('content', []))}")
        print(f"表格数量: {len(policy_data.get('tables', []))}")
        
        rules = []
        for item in policy_data.get('content', []):
            text = item.get('text', '')
            if any(kw in text for kw in ['不得', '禁止', '必须', '不超过', '不得超过']):
                rules.append({
                    "type": "text_rule",
                    "content": text,
                    "section": item.get('section', '')
                })
        
        print(f"提取规则数: {len(rules)}")
        for i, rule in enumerate(rules[:3], 1):
            print(f"  规则{i}: {rule['content'][:50]}...")
        
        return True
    else:
        print(f"测试文件不存在: {policy_file}")
        return False


def test_knowledge_base():
    print("\n" + "=" * 50)
    print("测试模块二：知识库构建")
    print("=" * 50)
    
    from modules.knowledge_base import knowledge_base, rule_extractor
    
    sample_text = """
    单张优惠券金额不得超过500元。
    每位用户每月领取次数不超过3次。
    促销活动总预算不得超过100万元。
    """
    
    print("测试规则提取...")
    rules = rule_extractor.extract_rules(sample_text)
    print(f"提取规则数: {len(rules)}")
    
    for i, rule in enumerate(rules[:3], 1):
        print(f"  规则{i}: {rule.get('rule_type', '未知')} - {rule.get('source_text', '')[:40]}...")
    
    print("\n测试知识库查询...")
    knowledge_base.build_from_documents([{
        "document_type": "policy_document",
        "content": [{"text": "优惠券金额不得超过500元"}],
        "metadata": {"title": "测试政策"}
    }])
    
    stats = knowledge_base.get_statistics()
    print(f"知识库统计: {stats}")
    
    return True


def test_audit_engine():
    print("\n" + "=" * 50)
    print("测试模块三：审计引擎")
    print("=" * 50)
    
    from modules.audit_engine import comparator, reasoning_engine
    
    sample_rule = {
        "rule_type": "上限约束",
        "constraint_field": "优惠券金额",
        "constraint_value": "500元",
        "source_text": "单张优惠券金额不得超过500元"
    }
    
    sample_config = {
        "优惠券金额": 600,
        "发放对象": "全部用户",
        "有效期": 60
    }
    
    print("测试数值比对...")
    comparison = comparator.compare(sample_rule, sample_config)
    print(f"比对结果: {comparison}")
    
    print("\n测试语义比对...")
    numeric_comparison = comparison.get('comparisons', [])
    if numeric_comparison:
        for c in numeric_comparison:
            print(f"  类型: {c.get('type')}, 匹配: {c.get('is_match')}")
    
    return True


def test_report_generator():
    print("\n" + "=" * 50)
    print("测试模块四：报告生成")
    print("=" * 50)
    
    from modules.report_generator import report_generator
    
    sample_violations = [
        {
            "violation_id": "VIO_001",
            "title": "优惠券金额超限",
            "risk_level": "高",
            "description": "优惠券金额600元超过规定的500元上限",
            "policy_reference": "单张优惠券金额不得超过500元",
            "config_value": {"优惠券金额": 600},
            "confidence": 0.95
        },
        {
            "violation_id": "VIO_002",
            "title": "发放对象范围越界",
            "risk_level": "中",
            "description": "优惠券发放对象为全部用户，超出规定的新用户范围",
            "policy_reference": "优惠券发放对象仅限新注册用户",
            "config_value": {"发放对象": "全部用户"},
            "confidence": 0.85
        }
    ]
    
    print("生成测试报告...")
    report = report_generator.quick_report(sample_violations)
    print(f"报告长度: {len(report)} 字符")
    print("\n报告预览:")
    print(report[:500] + "...")
    
    return True


def test_multi_agent_system():
    print("\n" + "=" * 50)
    print("测试多智能体系统")
    print("=" * 50)
    
    from agents import multi_agent_system
    
    status = multi_agent_system.get_system_status()
    print("系统状态:")
    for agent in status['agents']:
        print(f"  - {agent['name']}: {agent['role']}")
    
    print("\n执行快速审计测试...")
    policy_text = "单张优惠券金额不得超过500元"
    config_data = {"优惠券金额": 600}
    
    result = multi_agent_system.quick_audit(policy_text, config_data)
    print(f"提取规则数: {result['rules_extracted']}")
    print(f"发现违规数: {result['violations_found']}")
    
    return True


def run_all_tests():
    print("\n" + "=" * 60)
    print("营销审计多智能体系统 - 功能测试")
    print("=" * 60)
    
    tests = [
        ("文档解析模块", test_document_parser),
        ("知识库构建模块", test_knowledge_base),
        ("审计引擎模块", test_audit_engine),
        ("报告生成模块", test_report_generator),
        ("多智能体系统", test_multi_agent_system)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "通过" if success else "失败"))
        except Exception as e:
            results.append((name, f"错误: {str(e)[:50]}"))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        print(f"  {name}: {result}")
    
    passed = sum(1 for _, r in results if r == "通过")
    print(f"\n总计: {passed}/{len(results)} 通过")


if __name__ == "__main__":
    run_all_tests()
