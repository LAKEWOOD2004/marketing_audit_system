from typing import Dict, List, Any, Optional

from .reasoning import ReasoningEngine, reasoning_engine
from .comparator import Comparator, comparator
from .agents import (
    BaseAgent, ParserAgent, KnowledgeAgent, 
    AuditAgent, ReportAgent,
    parser_agent, knowledge_agent, audit_agent, report_agent
)


class AuditEngine:
    def __init__(self):
        self.reasoning_engine = reasoning_engine
        self.comparator = comparator
        self.parser_agent = parser_agent
        self.knowledge_agent = knowledge_agent
        self.audit_agent = audit_agent
        self.report_agent = report_agent
    
    def run_full_audit(self, 
                       policy_files: List[str], 
                       config_files: List[str]) -> Dict[str, Any]:
        parsed_policies = []
        for file_path in policy_files:
            result = self.parser_agent.execute({
                "file_path": file_path,
                "file_type": "policy"
            })
            if result.get("status") == "success":
                parsed_policies.append(result)
        
        parsed_configs = []
        for file_path in config_files:
            result = self.parser_agent.execute({
                "file_path": file_path,
                "file_type": "config"
            })
            if result.get("status") == "success":
                parsed_configs.append(result)
        
        all_rules = []
        for policy in parsed_policies:
            all_rules.extend(policy.get("extracted_rules", []))
        
        all_configs = []
        for config in parsed_configs:
            config_data = config.get("parsed_data", {})
            if "sheets" in config_data:
                for sheet_data in config_data["sheets"].values():
                    all_configs.extend(sheet_data.get("data", []))
        
        self.knowledge_agent.execute({
            "action": "build",
            "documents": [p.get("parsed_data") for p in parsed_policies]
        })
        
        audit_result = self.audit_agent.execute({
            "action": "audit",
            "rules": all_rules,
            "configs": all_configs
        })
        
        report = self.report_agent.execute({
            "action": "generate",
            "violations": audit_result.get("violations", []),
            "metadata": {
                "policy_files": policy_files,
                "config_files": config_files,
                "total_rules": len(all_rules),
                "total_configs": len(all_configs)
            }
        })
        
        return {
            "audit_result": audit_result,
            "report": report,
            "parsed_policies": parsed_policies,
            "parsed_configs": parsed_configs
        }
    
    def quick_check(self, 
                    rule: Dict[str, Any], 
                    config: Dict[str, Any]) -> Dict[str, Any]:
        comparison = self.comparator.compare(rule, config)
        reasoning = self.reasoning_engine.reason(rule, config)
        
        return {
            "comparison": comparison,
            "reasoning": reasoning,
            "is_compliant": comparison.get("overall_match", True) and 
                           reasoning.get("conclusion", {}).get("is_violation") != "是"
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        return {
            "parser_agent": {
                "name": self.parser_agent.name,
                "memory_count": len(self.parser_agent.get_memory())
            },
            "knowledge_agent": {
                "name": self.knowledge_agent.name,
                "memory_count": len(self.knowledge_agent.get_memory())
            },
            "audit_agent": {
                "name": self.audit_agent.name,
                "memory_count": len(self.audit_agent.get_memory())
            },
            "report_agent": {
                "name": self.report_agent.name,
                "memory_count": len(self.report_agent.get_memory())
            }
        }


audit_engine = AuditEngine()
