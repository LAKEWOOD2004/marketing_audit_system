import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path


def generate_id(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()[:12]


def save_json(data: Dict[str, Any], filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: Path) -> Dict[str, Any]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def truncate_text(text: str, max_length: int = 500) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def merge_dicts(dict_list: List[Dict]) -> Dict:
    result = {}
    for d in dict_list:
        result.update(d)
    return result


def flatten_nested_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_nested_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def format_audit_result(violation: Dict) -> str:
    template = """
【违规事项】{title}
【风险等级】{risk_level}
【违规描述】{description}
【政策依据】{policy_reference}
【配置参数】{config_value}
【判定逻辑】{reasoning}
"""
    return template.format(
        title=violation.get('title', '未知'),
        risk_level=violation.get('risk_level', '中'),
        description=violation.get('description', ''),
        policy_reference=violation.get('policy_reference', ''),
        config_value=violation.get('config_value', ''),
        reasoning=violation.get('reasoning', '')
    )
