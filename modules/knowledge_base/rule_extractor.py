from typing import Dict, List, Any, Optional
import json
import re


class RuleExtractor:
    def __init__(self):
        self.rule_patterns = [
            r'(.{0,50})(不得|禁止|必须|应当|要求)(.{0,100})',
            r'(.{0,30})(限额|上限|下限|范围)(.{0,50})(\d+(?:\.\d+)?(?:万|千|百)?(?:元|%)?)',
            r'(.{0,30})(条件|标准|要求)(.{0,100})',
        ]
    
    def extract_rules(self, text: str) -> List[Dict[str, Any]]:
        rules = []
        
        pattern_rules = self._extract_by_patterns(text)
        rules.extend(pattern_rules)
        
        return self._deduplicate_rules(rules)
    
    def _extract_by_patterns(self, text: str) -> List[Dict[str, Any]]:
        rules = []
        paragraphs = text.split('\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if self._contains_rule(para):
                rule = {
                    "source_text": para,
                    "rule_type": self._determine_rule_type(para),
                    "constraint_type": self._extract_constraint_type(para),
                    "constraint_value": self._extract_values(para),
                    "extraction_method": "pattern"
                }
                rules.append(rule)
        
        return rules
    
    def _contains_rule(self, text: str) -> bool:
        rule_keywords = [
            "应当", "必须", "不得", "禁止", "要求", "规定",
            "限额", "上限", "下限", "范围", "条件", "标准",
            "不超过", "不得超过", "不得少于", "仅限"
        ]
        return any(kw in text for kw in rule_keywords)
    
    def _determine_rule_type(self, text: str) -> str:
        if any(kw in text for kw in ['不得', '禁止', '严禁']):
            return "禁止事项"
        elif any(kw in text for kw in ['必须', '应当', '需要']):
            return "必做事项"
        elif any(kw in text for kw in ['限额', '上限', '不超过', '不得超过']):
            return "上限约束"
        elif any(kw in text for kw in ['下限', '不低于', '不少于', '不得少于']):
            return "下限约束"
        elif any(kw in text for kw in ['仅限', '范围']):
            return "范围限制"
        else:
            return "条件约束"
    
    def _extract_constraint_type(self, text: str) -> str:
        constraint_keywords = {
            "金额": ["金额", "费用", "成本", "预算", "元"],
            "比例": ["比例", "百分比", "%", "折扣"],
            "范围": ["范围", "对象", "用户", "渠道", "仅限"],
            "时间": ["时间", "期限", "日期", "周期", "天"],
            "数量": ["数量", "次数", "件数", "人数"]
        }
        
        for ctype, keywords in constraint_keywords.items():
            if any(kw in text for kw in keywords):
                return ctype
        
        return "其他"
    
    def _extract_values(self, text: str) -> List[str]:
        value_patterns = [
            r'\d+(?:\.\d+)?(?:万|千|百)?(?:元|%)?',
            r'[一二三四五六七八九十]+(?:万|千|百)?(?:元|%)?',
        ]
        
        values = []
        for pattern in value_patterns:
            values.extend(re.findall(pattern, text))
        
        return list(set(values))
    
    def _deduplicate_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique_rules = []
        
        for rule in rules:
            source = rule.get("source_text", "")[:100]
            if source not in seen:
                seen.add(source)
                unique_rules.append(rule)
        
        return unique_rules
    
    def convert_to_checkable_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        checkable = {
            "rule_id": rule.get("rule_id", ""),
            "rule_name": rule.get("rule_name", rule.get("source_text", "")[:50]),
            "rule_type": rule.get("rule_type", ""),
            "constraint_field": rule.get("constraint_field", ""),
            "constraint_value": rule.get("constraint_value", ""),
            "operator": rule.get("operator", ""),
            "description": rule.get("description", rule.get("source_text", "")),
            "source_text": rule.get("source_text", ""),
        }
        return checkable


rule_extractor = RuleExtractor()
