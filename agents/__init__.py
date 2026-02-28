from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import json

from utils.llm_client import llm_client


class BaseAgent(ABC):
    def __init__(self, name: str, role: str, description: str = ""):
        self.name = name
        self.role = role
        self.description = description
        self.memory: List[Dict[str, Any]] = []
        self.status = "idle"
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def add_memory(self, data: Dict[str, Any]) -> None:
        self.memory.append({
            "timestamp": self._get_timestamp(),
            "data": data
        })
    
    def get_memory(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.memory[-limit:]
    
    def clear_memory(self) -> None:
        self.memory = []
    
    def set_status(self, status: str) -> None:
        self.status = status
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "status": self.status,
            "memory_count": len(self.memory)
        }


class AgentOrchestrator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.workflow_history: List[Dict[str, Any]] = []
    
    def register_agent(self, agent: BaseAgent) -> None:
        self.agents[agent.name] = agent
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self.agents.get(name)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        return [agent.get_info() for agent in self.agents.values()]
    
    def execute_workflow(self, 
                         workflow: List[Dict[str, Any]],
                         context: Dict[str, Any] = None) -> Dict[str, Any]:
        results = {}
        current_context = context or {}
        
        for step in workflow:
            agent_name = step.get("agent")
            action = step.get("action")
            input_mapping = step.get("input_mapping", {})
            output_key = step.get("output_key", agent_name)
            
            agent = self.get_agent(agent_name)
            if not agent:
                results[output_key] = {"error": f"Agent not found: {agent_name}"}
                continue
            
            input_data = self._prepare_input(input_mapping, current_context, results)
            input_data["action"] = action
            
            agent.set_status("running")
            try:
                result = agent.execute(input_data)
                agent.set_status("completed")
            except Exception as e:
                result = {"error": str(e)}
                agent.set_status("error")
            
            results[output_key] = result
            current_context[output_key] = result
            
            self.workflow_history.append({
                "agent": agent_name,
                "action": action,
                "status": agent.status,
                "timestamp": agent._get_timestamp()
            })
        
        return {
            "results": results,
            "context": current_context,
            "workflow_history": self.workflow_history
        }
    
    def _prepare_input(self, 
                       mapping: Dict[str, str], 
                       context: Dict[str, Any],
                       results: Dict[str, Any]) -> Dict[str, Any]:
        input_data = {}
        
        for key, source in mapping.items():
            if "." in source:
                parts = source.split(".")
                value = context.get(parts[0], {})
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        value = None
                        break
                input_data[key] = value
            else:
                input_data[key] = context.get(source) or results.get(source)
        
        return input_data


class MultiAgentSystem:
    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self._setup_agents()
    
    def _setup_agents(self) -> None:
        from modules.document_parser import document_parser
        from modules.knowledge_base import knowledge_base
        from modules.audit_engine import audit_engine
        from modules.report_generator import report_generator
        
        parser_agent = ParserAgent()
        knowledge_agent = KnowledgeAgent()
        audit_agent = AuditAgent()
        report_agent = ReportAgent()
        
        self.orchestrator.register_agent(parser_agent)
        self.orchestrator.register_agent(knowledge_agent)
        self.orchestrator.register_agent(audit_agent)
        self.orchestrator.register_agent(report_agent)
    
    def run_audit(self, 
                  policy_files: List[str], 
                  config_files: List[str]) -> Dict[str, Any]:
        workflow = [
            {
                "agent": "ParserAgent",
                "action": "parse_policies",
                "input_mapping": {
                    "file_paths": "policy_files"
                },
                "output_key": "parsed_policies"
            },
            {
                "agent": "ParserAgent",
                "action": "parse_configs",
                "input_mapping": {
                    "file_paths": "config_files"
                },
                "output_key": "parsed_configs"
            },
            {
                "agent": "KnowledgeAgent",
                "action": "build",
                "input_mapping": {
                    "documents": "parsed_policies"
                },
                "output_key": "knowledge_base"
            },
            {
                "agent": "AuditAgent",
                "action": "audit",
                "input_mapping": {
                    "rules": "parsed_policies.extracted_rules",
                    "configs": "parsed_configs.configs"
                },
                "output_key": "audit_result"
            },
            {
                "agent": "ReportAgent",
                "action": "generate",
                "input_mapping": {
                    "violations": "audit_result.violations"
                },
                "output_key": "report"
            }
        ]
        
        context = {
            "policy_files": policy_files,
            "config_files": config_files
        }
        
        return self.orchestrator.execute_workflow(workflow, context)
    
    def quick_audit(self, 
                    policy_text: str, 
                    config_data: Dict[str, Any]) -> Dict[str, Any]:
        from modules.knowledge_base import rule_extractor
        from modules.audit_engine import reasoning_engine, comparator
        
        rules = rule_extractor.extract_rules(policy_text)
        
        violations = []
        for rule in rules:
            comparison = comparator.compare(rule, config_data)
            reasoning = reasoning_engine.reason(rule, config_data)
            
            if reasoning.get("conclusion", {}).get("is_violation") == "是":
                violations.append({
                    "rule": rule,
                    "comparison": comparison,
                    "reasoning": reasoning
                })
        
        return {
            "rules_extracted": len(rules),
            "violations_found": len(violations),
            "violations": violations
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        return {
            "agents": self.orchestrator.list_agents(),
            "workflow_history_count": len(self.orchestrator.workflow_history)
        }


class ParserAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ParserAgent",
            role="文档解析专家",
            description="负责解析docx、xlsx等异构文档，提取结构化数据"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from modules.document_parser import document_parser
        
        action = input_data.get("action", "parse")
        
        if action == "parse_policies":
            return self._parse_policies(input_data.get("file_paths", []))
        elif action == "parse_configs":
            return self._parse_configs(input_data.get("file_paths", []))
        elif action == "parse":
            return self._parse_single(input_data.get("file_path"))
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _parse_policies(self, file_paths: List[str]) -> Dict[str, Any]:
        from modules.document_parser import document_parser
        
        results = []
        all_rules = []
        
        for file_path in file_paths:
            try:
                parsed = document_parser.parse(file_path)
                rules = document_parser.extract_policy_rules(parsed)
                results.append({
                    "file_path": file_path,
                    "status": "success",
                    "parsed_data": parsed,
                    "extracted_rules": rules
                })
                all_rules.extend(rules)
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "status": "error",
                    "error": str(e)
                })
        
        self.add_memory({"action": "parse_policies", "count": len(file_paths)})
        
        return {
            "status": "success",
            "results": results,
            "extracted_rules": all_rules
        }
    
    def _parse_configs(self, file_paths: List[str]) -> Dict[str, Any]:
        from modules.document_parser import document_parser
        
        results = []
        all_configs = []
        
        for file_path in file_paths:
            try:
                parsed = document_parser.parse(file_path)
                configs = document_parser.extract_business_config(parsed)
                results.append({
                    "file_path": file_path,
                    "status": "success",
                    "parsed_data": parsed,
                    "configs": configs
                })
                all_configs.extend(configs)
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "status": "error",
                    "error": str(e)
                })
        
        self.add_memory({"action": "parse_configs", "count": len(file_paths)})
        
        return {
            "status": "success",
            "results": results,
            "configs": all_configs
        }
    
    def _parse_single(self, file_path: str) -> Dict[str, Any]:
        from modules.document_parser import document_parser
        
        try:
            parsed = document_parser.parse(file_path)
            self.add_memory({"action": "parse_single", "file_path": file_path})
            return {
                "status": "success",
                "parsed_data": parsed
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


class KnowledgeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="KnowledgeAgent",
            role="知识库管理专家",
            description="负责构建和查询审计知识库"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from modules.knowledge_base import knowledge_base
        
        action = input_data.get("action", "query")
        
        if action == "build":
            documents = input_data.get("documents", [])
            if isinstance(documents, dict) and "results" in documents:
                documents = [r.get("parsed_data") for r in documents["results"] if r.get("parsed_data")]
            knowledge_base.build_from_documents(documents)
            self.add_memory({"action": "build", "document_count": len(documents)})
            return {
                "status": "success",
                "statistics": knowledge_base.get_statistics()
            }
        
        elif action == "query":
            query = input_data.get("query", "")
            result = knowledge_base.query(query)
            self.add_memory({"action": "query", "query": query})
            return result
        
        elif action == "get_rules":
            config_data = input_data.get("config_data", {})
            rules = knowledge_base.get_applicable_rules(config_data)
            return {
                "status": "success",
                "rules": rules
            }
        
        else:
            return {"error": f"Unknown action: {action}"}


class AuditAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="AuditAgent",
            role="审计专家",
            description="负责执行审计推理和违规识别"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from modules.audit_engine import audit_engine, reasoning_engine, comparator
        
        action = input_data.get("action", "audit")
        
        if action == "audit":
            rules = input_data.get("rules", [])
            configs = input_data.get("configs", [])
            
            if isinstance(rules, dict) and "extracted_rules" in rules:
                rules = rules["extracted_rules"]
            if isinstance(configs, dict) and "configs" in configs:
                configs = configs["configs"]
            
            return self._perform_audit(rules, configs)
        
        elif action == "quick_check":
            rule = input_data.get("rule", {})
            config = input_data.get("config", {})
            return audit_engine.quick_check(rule, config)
        
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _perform_audit(self, rules: List[Dict], configs: List[Dict]) -> Dict[str, Any]:
        from modules.audit_engine import reasoning_engine
        
        violations = []
        
        for rule in rules:
            for config in configs:
                reasoning = reasoning_engine.reason(rule, config)
                
                if reasoning.get("conclusion", {}).get("is_violation") == "是":
                    violations.append({
                        "violation_id": f"VIO_{len(violations) + 1}",
                        "title": self._generate_title(rule),
                        "risk_level": reasoning["conclusion"].get("risk_level", "中"),
                        "description": reasoning["conclusion"].get("description", ""),
                        "policy_reference": rule.get("source_text", ""),
                        "config_value": config,
                        "reasoning": reasoning,
                        "confidence": reasoning["conclusion"].get("confidence", 0)
                    })
        
        self.add_memory({
            "action": "audit",
            "rules_count": len(rules),
            "configs_count": len(configs),
            "violations_found": len(violations)
        })
        
        return {
            "status": "success",
            "total_checks": len(rules) * len(configs) if rules and configs else 0,
            "violations": violations
        }
    
    def _generate_title(self, rule: Dict) -> str:
        rule_type = rule.get("rule_type", "")
        constraint_field = rule.get("constraint_field", "")
        
        if "金额" in rule_type or "上限" in rule_type:
            return f"金额超限违规 - {constraint_field}"
        elif "范围" in rule_type:
            return f"范围越界违规 - {constraint_field}"
        else:
            return f"配置违规 - {constraint_field}"


class ReportAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ReportAgent",
            role="报告生成专家",
            description="负责汇总审计结果并生成报告"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from modules.report_generator import report_generator
        
        action = input_data.get("action", "generate")
        
        if action == "generate":
            violations = input_data.get("violations", [])
            if isinstance(violations, dict) and "violations" in violations:
                violations = violations["violations"]
            
            audit_result = {
                "violations": violations,
                "metadata": input_data.get("metadata", {})
            }
            
            report = report_generator.generate_report(audit_result)
            outputs = report_generator.save_all_outputs(audit_result)
            
            self.add_memory({
                "action": "generate",
                "violations_count": len(violations),
                "outputs": [str(p) for p in outputs.values()]
            })
            
            return {
                "status": "success",
                "report": report,
                "output_files": {k: str(v) for k, v in outputs.items()}
            }
        
        elif action == "quick_report":
            violations = input_data.get("violations", [])
            report_text = report_generator.quick_report(violations)
            return {
                "status": "success",
                "report_text": report_text
            }
        
        else:
            return {"error": f"Unknown action: {action}"}


multi_agent_system = MultiAgentSystem()
