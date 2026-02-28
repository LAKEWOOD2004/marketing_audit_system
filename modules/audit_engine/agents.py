from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
import json

from .reasoning import ReasoningEngine, reasoning_engine
from .comparator import Comparator, comparator
from utils.llm_client import llm_client


class BaseAgent(ABC):
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.memory = []
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def add_to_memory(self, data: Dict[str, Any]) -> None:
        self.memory.append(data)
    
    def get_memory(self) -> List[Dict[str, Any]]:
        return self.memory
    
    def clear_memory(self) -> None:
        self.memory = []


class ParserAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ParserAgent",
            role="文档解析专家，负责将异构文档转换为标准化格式"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from modules.document_parser import document_parser
        
        file_path = input_data.get("file_path")
        file_type = input_data.get("file_type", "auto")
        
        try:
            parsed_data = document_parser.parse(file_path)
            
            if file_path.endswith(('.docx', '.doc')):
                rules = document_parser.extract_policy_rules(parsed_data)
            else:
                rules = []
            
            result = {
                "status": "success",
                "parsed_data": parsed_data,
                "extracted_rules": rules,
                "file_path": file_path
            }
            
            self.add_to_memory(result)
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                "file_path": file_path
            }


class KnowledgeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="KnowledgeAgent",
            role="知识库管理专家，负责构建和查询审计知识库"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from modules.knowledge_base import knowledge_base
        
        action = input_data.get("action", "query")
        
        if action == "build":
            documents = input_data.get("documents", [])
            knowledge_base.build_from_documents(documents)
            return {
                "status": "success",
                "action": "build",
                "statistics": knowledge_base.get_statistics()
            }
        
        elif action == "query":
            query = input_data.get("query", "")
            n_context = input_data.get("n_context", 3)
            result = knowledge_base.query(query, n_context)
            self.add_to_memory(result)
            return result
        
        elif action == "get_rules":
            config_data = input_data.get("config_data", {})
            rules = knowledge_base.get_applicable_rules(config_data)
            return {
                "status": "success",
                "applicable_rules": rules
            }
        
        else:
            return {
                "status": "error",
                "error_message": f"Unknown action: {action}"
            }


class AuditAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="AuditAgent",
            role="审计专家，负责执行审计推理和违规识别"
        )
        self.reasoning_engine = reasoning_engine
        self.comparator = comparator
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "audit")
        
        if action == "audit":
            return self._perform_audit(input_data)
        elif action == "compare":
            return self._perform_comparison(input_data)
        elif action == "reason":
            return self._perform_reasoning(input_data)
        else:
            return {
                "status": "error",
                "error_message": f"Unknown action: {action}"
            }
    
    def _perform_audit(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        rules = input_data.get("rules", [])
        configs = input_data.get("configs", [])
        
        violations = []
        
        for rule in rules:
            for config in configs:
                reasoning_result = self.reasoning_engine.reason(rule, config)
                
                if reasoning_result.get("conclusion", {}).get("is_violation") == "是":
                    violation = self._create_violation_record(rule, config, reasoning_result)
                    violations.append(violation)
        
        result = {
            "status": "success",
            "total_checks": len(rules) * len(configs),
            "violations_found": len(violations),
            "violations": violations
        }
        
        self.add_to_memory(result)
        return result
    
    def _perform_comparison(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        rule = input_data.get("rule", {})
        config = input_data.get("config", {})
        
        comparison = self.comparator.compare(rule, config)
        
        return {
            "status": "success",
            "comparison": comparison
        }
    
    def _perform_reasoning(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        rule = input_data.get("rule", {})
        config = input_data.get("config", {})
        
        reasoning = self.reasoning_engine.reason(rule, config)
        
        return {
            "status": "success",
            "reasoning": reasoning
        }
    
    def _create_violation_record(self, 
                                  rule: Dict[str, Any], 
                                  config: Dict[str, Any],
                                  reasoning: Dict[str, Any]) -> Dict[str, Any]:
        conclusion = reasoning.get("conclusion", {})
        
        return {
            "violation_id": f"VIO_{len(self.memory) + 1}",
            "title": self._generate_violation_title(rule, config),
            "risk_level": conclusion.get("risk_level", "中"),
            "description": conclusion.get("description", ""),
            "policy_reference": rule.get("source_text", ""),
            "config_value": config,
            "reasoning_steps": reasoning.get("reasoning_steps", []),
            "confidence": conclusion.get("confidence", 0.0)
        }
    
    def _generate_violation_title(self, rule: Dict[str, Any], config: Dict[str, Any]) -> str:
        rule_type = rule.get("rule_type", "")
        constraint_field = rule.get("constraint_field", "")
        
        if "金额" in rule_type or "上限" in rule_type:
            return f"金额超限违规 - {constraint_field}"
        elif "范围" in rule_type:
            return f"范围越界违规 - {constraint_field}"
        elif "条件" in rule_type:
            return f"条件不符违规 - {constraint_field}"
        else:
            return f"配置违规 - {constraint_field}"


class ReportAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ReportAgent",
            role="报告生成专家，负责汇总审计结果并生成报告"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "generate")
        
        if action == "generate":
            return self._generate_report(input_data)
        elif action == "summarize":
            return self._summarize_violations(input_data)
        else:
            return {
                "status": "error",
                "error_message": f"Unknown action: {action}"
            }
    
    def _generate_report(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        violations = input_data.get("violations", [])
        audit_metadata = input_data.get("metadata", {})
        
        summary = self._create_summary(violations)
        categorized = self._categorize_violations(violations)
        recommendations = self._generate_recommendations(violations)
        
        report = {
            "status": "success",
            "report_type": "audit_report",
            "metadata": audit_metadata,
            "summary": summary,
            "violations_by_category": categorized,
            "recommendations": recommendations,
            "detailed_violations": violations
        }
        
        self.add_to_memory(report)
        return report
    
    def _summarize_violations(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        violations = input_data.get("violations", [])
        
        summary = {
            "total_violations": len(violations),
            "by_risk_level": {
                "高": len([v for v in violations if v.get("risk_level") == "高"]),
                "中": len([v for v in violations if v.get("risk_level") == "中"]),
                "低": len([v for v in violations if v.get("risk_level") == "低"])
            },
            "top_violations": sorted(violations, key=lambda x: x.get("confidence", 0), reverse=True)[:5]
        }
        
        return {
            "status": "success",
            "summary": summary
        }
    
    def _create_summary(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not violations:
            return {
                "total": 0,
                "message": "本次审计未发现违规问题"
            }
        
        high_risk = [v for v in violations if v.get("risk_level") == "高"]
        medium_risk = [v for v in violations if v.get("risk_level") == "中"]
        low_risk = [v for v in violations if v.get("risk_level") == "低"]
        
        return {
            "total": len(violations),
            "high_risk_count": len(high_risk),
            "medium_risk_count": len(medium_risk),
            "low_risk_count": len(low_risk),
            "message": f"本次审计共发现 {len(violations)} 个违规问题，其中高风险 {len(high_risk)} 个，中风险 {len(medium_risk)} 个，低风险 {len(low_risk)} 个"
        }
    
    def _categorize_violations(self, violations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        categories = {
            "金额超限": [],
            "范围越界": [],
            "条件不符": [],
            "逻辑冲突": [],
            "其他": []
        }
        
        for violation in violations:
            title = violation.get("title", "")
            if "金额" in title or "超限" in title:
                categories["金额超限"].append(violation)
            elif "范围" in title or "越界" in title:
                categories["范围越界"].append(violation)
            elif "条件" in title:
                categories["条件不符"].append(violation)
            elif "逻辑" in title or "冲突" in title:
                categories["逻辑冲突"].append(violation)
            else:
                categories["其他"].append(violation)
        
        return {k: v for k, v in categories.items() if v}
    
    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        if not violations:
            return ["当前配置符合政策要求，建议继续保持"]
        
        recommendations = []
        
        high_risk_count = len([v for v in violations if v.get("risk_level") == "高"])
        if high_risk_count > 0:
            recommendations.append(f"【紧急】发现 {high_risk_count} 个高风险违规，建议立即整改")
        
        categories = self._categorize_violations(violations)
        for category, items in categories.items():
            if items:
                recommendations.append(f"建议检查 {category} 相关配置，共 {len(items)} 处问题")
        
        recommendations.append("建议建立定期审计机制，确保配置持续合规")
        
        return recommendations


parser_agent = ParserAgent()
knowledge_agent = KnowledgeAgent()
audit_agent = AuditAgent()
report_agent = ReportAgent()
