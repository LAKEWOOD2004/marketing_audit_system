#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
营销审计多智能体系统 - 主程序入口

本系统实现企业营销审计的自动化流程，包括：
1. 异构文档解析（docx/xlsx）
2. 审计知识库构建（RAG）
3. 智能审计推理（多智能体协作）
4. 审计报告生成

使用方法：
    python main.py --policy <政策文件路径> --config <配置文件路径>
    python main.py --demo  # 运行演示模式
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import INPUT_DIR, OUTPUT_DIR, LLM_CONFIG
from agents import multi_agent_system
from modules.document_parser import document_parser
from modules.knowledge_base import knowledge_base
from modules.audit_engine import audit_engine
from modules.report_generator import report_generator


def setup_environment():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("营销审计多智能体系统")
    print("=" * 60)
    print(f"输入目录: {INPUT_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"LLM配置: {LLM_CONFIG.get('provider', 'openai')} / {LLM_CONFIG.get('model', 'gpt-4')}")
    print("=" * 60)


def run_demo():
    print("\n【演示模式】运行示例审计流程...\n")
    
    demo_policy = """
    营销活动管理规定
    
    一、优惠券发放规则
    1. 单张优惠券金额不得超过500元
    2. 优惠券发放对象仅限新注册用户
    3. 每位用户每月领取次数不超过3次
    4. 优惠券有效期不得少于7天，不得超过30天
    
    二、促销活动限制
    1. 单次促销活动总预算不得超过100万元
    2. 促销范围仅限线上渠道
    3. 禁止与其它优惠活动叠加使用
    
    三、用户权益保护
    1. 活动规则必须明确告知用户
    2. 不得设置隐性消费门槛
    3. 退款时优惠券应当返还
    """
    
    demo_config = {
        "activity_id": "PROMO_2024_001",
        "activity_name": "春节促销活动",
        "coupon_config": {
            "max_amount": 600,
            "target_users": "全部用户",
            "monthly_limit": 5,
            "validity_days": 60
        },
        "budget": {
            "total_budget": 1500000,
            "used_budget": 800000
        },
        "scope": ["线上", "线下门店"],
        "stackable": True
    }
    
    print("【政策规则】")
    print(demo_policy[:200] + "...\n")
    
    print("【业务配置】")
    print(json.dumps(demo_config, ensure_ascii=False, indent=2))
    print()
    
    print("正在执行审计推理...\n")
    
    result = multi_agent_system.quick_audit(demo_policy, demo_config)
    
    print("【审计结果】")
    print(f"提取规则数: {result['rules_extracted']}")
    print(f"发现违规数: {result['violations_found']}")
    print()
    
    if result['violations']:
        print("【违规详情】")
        for i, v in enumerate(result['violations'], 1):
            rule = v.get('rule', {})
            reasoning = v.get('reasoning', {})
            conclusion = reasoning.get('conclusion', {})
            
            print(f"\n违规项 {i}:")
            print(f"  规则类型: {rule.get('rule_type', '未知')}")
            print(f"  风险等级: {conclusion.get('risk_level', '中')}")
            print(f"  违规描述: {conclusion.get('description', '暂无描述')}")
            print(f"  政策依据: {rule.get('source_text', '')[:100]}...")
    else:
        print("未发现违规问题，配置符合政策要求。")
    
    audit_result = {
        "violations": [
            {
                "violation_id": f"VIO_{i+1}",
                "title": v.get('rule', {}).get('rule_type', '未知违规'),
                "risk_level": v.get('reasoning', {}).get('conclusion', {}).get('risk_level', '中'),
                "description": v.get('reasoning', {}).get('conclusion', {}).get('description', ''),
                "policy_reference": v.get('rule', {}).get('source_text', ''),
                "config_value": demo_config,
                "confidence": v.get('reasoning', {}).get('conclusion', {}).get('confidence', 0.8)
            }
            for i, v in enumerate(result['violations'])
        ],
        "metadata": {
            "audit_time": datetime.now().isoformat(),
            "policy_source": "demo_policy",
            "config_source": "demo_config"
        }
    }
    
    outputs = report_generator.save_all_outputs(audit_result)
    
    print("\n【报告已生成】")
    for name, path in outputs.items():
        print(f"  {name}: {path}")
    
    return result


def run_audit(policy_files: list, config_files: list):
    print(f"\n开始审计流程...")
    print(f"政策文件: {policy_files}")
    print(f"配置文件: {config_files}")
    print()
    
    for f in policy_files + config_files:
        if not os.path.exists(f):
            print(f"错误: 文件不存在 - {f}")
            return None
    
    result = multi_agent_system.run_audit(policy_files, config_files)
    
    print("\n【审计完成】")
    
    audit_result = result.get('results', {}).get('audit_result', {})
    violations = audit_result.get('violations', [])
    
    print(f"总检查项: {audit_result.get('total_checks', 0)}")
    print(f"发现违规: {len(violations)}")
    
    if violations:
        print("\n【违规概览】")
        for v in violations[:5]:
            print(f"  - [{v.get('risk_level', '中')}] {v.get('title', '')}")
        if len(violations) > 5:
            print(f"  ... 还有 {len(violations) - 5} 项违规")
    
    report_result = result.get('results', {}).get('report', {})
    if report_result.get('output_files'):
        print("\n【报告文件】")
        for name, path in report_result['output_files'].items():
            print(f"  {name}: {path}")
    
    return result


def parse_single_document(file_path: str):
    print(f"\n解析文档: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return None
    
    result = document_parser.parse(file_path)
    
    print("\n【解析结果】")
    print(f"文档类型: {result.get('document_type', '未知')}")
    
    if result.get('metadata'):
        print(f"元数据: {json.dumps(result['metadata'], ensure_ascii=False)}")
    
    if result.get('structure'):
        print(f"\n文档结构:")
        for section in result['structure'].get('sections', [])[:5]:
            print(f"  {'  ' * (section.get('level', 1) - 1)}{section.get('title', '')}")
    
    if result.get('tables'):
        print(f"\n表格数量: {len(result['tables'])}")
    
    rules = document_parser.extract_policy_rules(result)
    if rules:
        print(f"\n提取规则数: {len(rules)}")
        for rule in rules[:3]:
            print(f"  - [{rule.get('type', '未知')}] {rule.get('content', '')[:50]}...")
    
    return result


def query_knowledge(question: str):
    print(f"\n知识库查询: {question}")
    
    result = knowledge_base.query(question)
    
    print("\n【查询结果】")
    print(f"回答: {result.get('answer', '暂无回答')}")
    
    if result.get('context'):
        print(f"\n参考文档:")
        for i, ctx in enumerate(result['context'][:3], 1):
            print(f"  [{i}] {ctx.get('content', '')[:100]}...")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="营销审计多智能体系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --demo                    # 运行演示模式
  python main.py --policy policy.docx --config config.xlsx  # 执行审计
  python main.py --parse document.docx     # 解析单个文档
  python main.py --query "优惠券金额限制"   # 知识库查询
        """
    )
    
    parser.add_argument('--demo', action='store_true', help='运行演示模式')
    parser.add_argument('--policy', nargs='+', help='政策文件路径')
    parser.add_argument('--config', nargs='+', help='配置文件路径')
    parser.add_argument('--parse', type=str, help='解析单个文档')
    parser.add_argument('--query', type=str, help='知识库查询')
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    
    args = parser.parse_args()
    
    setup_environment()
    
    if args.demo:
        return run_demo()
    
    if args.policy and args.config:
        return run_audit(args.policy, args.config)
    
    if args.parse:
        return parse_single_document(args.parse)
    
    if args.query:
        return query_knowledge(args.query)
    
    if args.status:
        status = multi_agent_system.get_system_status()
        print("\n【系统状态】")
        for agent in status['agents']:
            print(f"  {agent['name']}: {agent['status']} (memory: {agent['memory_count']})")
        return status
    
    parser.print_help()
    return None


if __name__ == "__main__":
    main()
