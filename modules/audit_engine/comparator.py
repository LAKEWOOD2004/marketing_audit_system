from typing import Dict, List, Any, Optional, Tuple
import re
from difflib import SequenceMatcher


class Comparator:
    def __init__(self):
        self.field_mappings = {
            "金额": ["金额", "amount", "price", "费用", "预算"],
            "比例": ["比例", "ratio", "percent", "折扣", "discount"],
            "范围": ["范围", "scope", "range", "对象", "target"],
            "时间": ["时间", "time", "date", "期限", "period"],
            "数量": ["数量", "count", "quantity", "次数", "limit"]
        }
    
    def compare(self, 
                rule: Dict[str, Any], 
                config: Dict[str, Any]) -> Dict[str, Any]:
        comparisons = []
        
        rule_type = rule.get("rule_type", "")
        
        if "金额" in rule_type or "上限" in rule_type or "下限" in rule_type:
            comparison = self._compare_numeric(rule, config)
            comparisons.append(comparison)
        
        if "范围" in rule_type or "对象" in rule_type or "限制" in rule_type:
            comparison = self._compare_scope(rule, config)
            comparisons.append(comparison)
        
        if "条件" in rule_type or "约束" in rule_type:
            comparison = self._compare_conditions(rule, config)
            comparisons.append(comparison)
        
        return {
            "rule": rule,
            "config": config,
            "comparisons": comparisons,
            "overall_match": self._calculate_overall_match(comparisons)
        }
    
    def _compare_numeric(self, rule: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        constraint_value = rule.get("constraint_value", "")
        if isinstance(constraint_value, list):
            constraint_value = " ".join(str(v) for v in constraint_value)
        
        rule_value = self._extract_numeric_value(constraint_value)
        config_value = self._extract_numeric_from_config(config, rule.get("constraint_type", ""))
        
        operator = self._extract_operator(rule.get("source_text", ""))
        
        is_match = self._apply_operator(rule_value, config_value, operator)
        
        return {
            "type": "numeric_comparison",
            "rule_value": rule_value,
            "config_value": config_value,
            "operator": operator,
            "is_match": is_match,
            "difference": abs(rule_value - config_value) if rule_value and config_value else None
        }
    
    def _compare_scope(self, rule: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        constraint_value = rule.get("constraint_value", "")
        if isinstance(constraint_value, list):
            constraint_value = " ".join(str(v) for v in constraint_value)
        
        rule_scope = self._extract_scope(constraint_value or rule.get("source_text", ""))
        config_scope = self._extract_scope_from_config(config)
        
        overlap = self._calculate_scope_overlap(rule_scope, config_scope)
        
        is_match = overlap >= 0.8
        
        return {
            "type": "scope_comparison",
            "rule_scope": rule_scope,
            "config_scope": config_scope,
            "overlap_ratio": overlap,
            "is_match": is_match
        }
    
    def _compare_conditions(self, rule: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        rule_conditions = self._extract_conditions(rule.get("source_text", ""))
        config_conditions = self._extract_config_conditions(config)
        
        matched = []
        unmatched = []
        
        for condition in rule_conditions:
            if self._condition_matches(condition, config_conditions):
                matched.append(condition)
            else:
                unmatched.append(condition)
        
        is_match = len(unmatched) == 0
        
        return {
            "type": "condition_comparison",
            "rule_conditions": rule_conditions,
            "matched_conditions": matched,
            "unmatched_conditions": unmatched,
            "is_match": is_match
        }
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        if not text:
            return None
        
        if isinstance(text, (list, dict)):
            text = str(text)
        
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
    
    def _extract_numeric_from_config(self, config: Dict[str, Any], field_hint: str) -> Optional[float]:
        if not config:
            return None
        
        keywords = {
            "金额": ["金额", "amount", "max_amount", "price"],
            "预算": ["预算", "budget", "total_budget"],
            "次数": ["次数", "limit", "monthly_limit"],
            "时间": ["天数", "days", "validity_days"],
        }
        
        if field_hint in keywords:
            for key in keywords[field_hint]:
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
        elif any(kw in text for kw in ["等于", "为", "是", "="]):
            return "=="
        elif any(kw in text for kw in ["大于", "超过", ">", "＞"]):
            return ">"
        elif any(kw in text for kw in ["小于", "低于", "<", "＜"]):
            return "<"
        else:
            return "=="
    
    def _apply_operator(self, rule_val: Optional[float], config_val: Optional[float], op: str) -> bool:
        if rule_val is None or config_val is None:
            return True
        
        if op == "<=":
            return config_val <= rule_val
        elif op == ">=":
            return config_val >= rule_val
        elif op == "==":
            return config_val == rule_val
        elif op == ">":
            return config_val > rule_val
        elif op == "<":
            return config_val < rule_val
        else:
            return True
    
    def _extract_scope(self, text: str) -> List[str]:
        scope_keywords = [
            "全部用户", "新用户", "老用户", "VIP用户", "普通用户",
            "新注册用户", "所有渠道", "线上", "线下", "APP", "小程序", "官网",
            "全国", "特定区域", "指定城市"
        ]
        
        found_scopes = []
        for keyword in scope_keywords:
            if keyword in text:
                found_scopes.append(keyword)
        
        return found_scopes if found_scopes else ["未指定"]
    
    def _extract_scope_from_config(self, config: Dict[str, Any]) -> List[str]:
        scopes = []
        
        for key, value in config.items():
            key_lower = key.lower()
            if any(kw in key_lower for kw in ["范围", "scope", "对象", "target", "用户", "渠道"]):
                if isinstance(value, list):
                    scopes.extend(str(v) for v in value)
                else:
                    scopes.append(str(value))
        
        return scopes if scopes else ["未指定"]
    
    def _calculate_scope_overlap(self, scope1: List[str], scope2: List[str]) -> float:
        if not scope1 or not scope2:
            return 0.0
        
        if "未指定" in scope1 or "未指定" in scope2:
            return 1.0
        
        if "全部" in str(scope1) or "所有" in str(scope1):
            return 1.0
        
        set1 = set(scope1)
        set2 = set(scope2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_conditions(self, text: str) -> List[str]:
        conditions = []
        
        condition_patterns = [
            r'(.{0,20})(必须|应当|需要)(.{0,30})',
            r'(.{0,20})(不得|禁止|不能)(.{0,30})',
            r'(.{0,20})(条件|要求|标准)(.{0,30})',
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                condition = ''.join(match).strip()
                if condition:
                    conditions.append(condition)
        
        return conditions
    
    def _extract_config_conditions(self, config: Dict[str, Any]) -> List[str]:
        conditions = []
        
        for key, value in config.items():
            if any(kw in key.lower() for kw in ["条件", "要求", "限制", "constraint"]):
                conditions.append(f"{key}: {value}")
        
        return conditions
    
    def _condition_matches(self, condition: str, config_conditions: List[str]) -> bool:
        for config_cond in config_conditions:
            similarity = SequenceMatcher(None, condition, config_cond).ratio()
            if similarity > 0.6:
                return True
        return False
    
    def _calculate_overall_match(self, comparisons: List[Dict[str, Any]]) -> bool:
        if not comparisons:
            return True
        
        return all(c.get("is_match", True) for c in comparisons)
    
    def batch_compare(self, 
                      rules: List[Dict[str, Any]], 
                      configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        
        for rule in rules:
            for config in configs:
                result = self.compare(rule, config)
                results.append(result)
        
        return results


comparator = Comparator()
