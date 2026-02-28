from typing import Dict, List, Any, Optional
import json
import re


class ReasoningEngine:
    def __init__(self):
        pass

    def reason(self, 
               policy_rule: Dict[str, Any], 
               config_data: Dict[str, Any]) -> Dict[str, Any]:
        conclusion = self._quick_reason(policy_rule, config_data)
        
        return {
            "policy_rule": policy_rule,
            "config_data": config_data,
            "reasoning_steps": [{"step": "快速推理", "status": "completed"}],
            "conclusion": conclusion
        }
    
    def _quick_reason(self, rule: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        rule_text = rule.get("source_text", rule.get("content", ""))
        rule_type = rule.get("rule_type", "")
        
        rule_value = self._extract_numeric_value(rule_text)
        config_value = self._extract_config_value(config, rule_text)
        operator = self._extract_operator(rule_text)
        
        is_violation = False
        risk_level = "低"
        description = ""
        
        if rule_value is not None and config_value is not None:
            if operator == "<=" and config_value > rule_value:
                is_violation = True
                risk_level = "高" if (config_value - rule_value) / rule_value > 0.2 else "中"
                description = f"配置值 {config_value} 超过规则上限 {rule_value}"
            elif operator == ">=" and config_value < rule_value:
                is_violation = True
                risk_level = "高" if (rule_value - config_value) / rule_value > 0.2 else "中"
                description = f"配置值 {config_value} 低于规则下限 {rule_value}"
            elif operator == "==" and config_value != rule_value:
                is_violation = True
                risk_level = "中"
                description = f"配置值 {config_value} 不等于规则要求 {rule_value}"
        
        if "仅限" in rule_text or "禁止" in rule_text:
            scope_violation = self._check_scope_violation(rule_text, config)
            if scope_violation:
                is_violation = True
                risk_level = "中"
                description = scope_violation
        
        return {
            "is_violation": "是" if is_violation else "否",
            "violation_type": rule_type if is_violation else "无违规",
            "risk_level": risk_level,
            "description": description if is_violation else "配置符合规则要求",
            "evidence": rule_text,
            "confidence": 0.9 if is_violation else 1.0
        }
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        if not text:
            return None
        
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:万)?(?:元|%)?',
            r'(\d+(?:\.\d+)?)\s*万',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(text))
            if match:
                value = float(match.group(1))
                if '万' in str(text):
                    value *= 10000
                return value
        return None
    
    def _extract_config_value(self, config: Dict[str, Any], rule_text: str) -> Optional[float]:
        if not config:
            return None
        
        keywords = {
            "金额": ["金额", "amount", "max_amount", "price"],
            "预算": ["预算", "budget", "total_budget"],
            "次数": ["次数", "limit", "monthly_limit"],
            "天数": ["天数", "days", "validity_days"],
        }
        
        for category, keys in keywords.items():
            if category in rule_text:
                for key in keys:
                    if key in config:
                        val = config[key]
                        if isinstance(val, (int, float)):
                            return float(val)
                    for k, v in config.items():
                        if isinstance(v, dict) and key in v:
                            val = v[key]
                            if isinstance(val, (int, float)):
                                return float(val)
        
        for key, value in config.items():
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, (int, float)):
                        return float(v)
        
        return None
    
    def _extract_operator(self, text: str) -> str:
        if any(kw in text for kw in ["不超过", "不大于", "上限", "最高", "不得超过"]):
            return "<="
        elif any(kw in text for kw in ["不低于", "不小于", "下限", "最低", "不得少于"]):
            return ">="
        elif any(kw in text for kw in ["等于", "为", "是"]):
            return "=="
        else:
            return "<="
    
    def _check_scope_violation(self, rule_text: str, config: Dict[str, Any]) -> str:
        if "新注册用户" in rule_text or "新用户" in rule_text:
            target = config.get("target_users", config.get("发放对象", ""))
            if target and "新" not in str(target):
                return f"发放对象 '{target}' 不符合规则要求 '新注册用户'"
        
        if "线上" in rule_text and "仅限" in rule_text:
            scope = config.get("scope", config.get("活动渠道", []))
            if scope and "线下" in str(scope):
                return f"活动范围包含线下渠道，不符合规则要求 '仅限线上'"
        
        return ""
    
    def batch_reason(self, 
                     rules: List[Dict[str, Any]], 
                     configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        
        for rule in rules:
            for config in configs:
                result = self.reason(rule, config)
                results.append(result)
        
        return results


reasoning_engine = ReasoningEngine()
