from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class ReportTemplates:
    @staticmethod
    def audit_report_markdown(report_data: Dict[str, Any]) -> str:
        metadata = report_data.get("metadata", {})
        summary = report_data.get("summary", {})
        violations_by_category = report_data.get("violations_by_category", {})
        recommendations = report_data.get("recommendations", [])
        detailed_violations = report_data.get("detailed_violations", [])
        
        template = f"""# 营销审计分析报告

## 一、报告基本信息

| 项目 | 内容 |
|------|------|
| 生成时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 审计类型 | 营销配置合规审计 |
| 政策文件数 | {len(metadata.get("policy_files", []))} |
| 配置文件数 | {len(metadata.get("config_files", []))} |
| 审计规则数 | {metadata.get("total_rules", 0)} |
| 配置项数量 | {metadata.get("total_configs", 0)} |

## 二、审计结果摘要

{summary.get("message", "暂无审计结果")}

### 风险分布统计

| 风险等级 | 数量 |
|----------|------|
| 高风险 | {summary.get("high_risk_count", 0)} |
| 中风险 | {summary.get("medium_risk_count", 0)} |
| 低风险 | {summary.get("low_risk_count", 0)} |
| **合计** | **{summary.get("total", 0)}** |

## 三、违规问题分类详情

"""
        for category, violations in violations_by_category.items():
            template += f"### {category}\n\n"
            for i, v in enumerate(violations, 1):
                template += f"**问题{i}**: {v.get('title', '未知问题')}\n"
                template += f"- 风险等级: {v.get('risk_level', '中')}\n"
                template += f"- 违规描述: {v.get('description', '暂无描述')}\n"
                template += f"- 政策依据: {v.get('policy_reference', '暂无依据')[:100]}...\n\n"
        
        template += """## 四、整改建议

"""
        for i, rec in enumerate(recommendations, 1):
            template += f"{i}. {rec}\n"
        
        template += """

## 五、详细违规清单

"""
        for i, v in enumerate(detailed_violations, 1):
            template += f"""### 违规项 {i}: {v.get('title', '未知')}

| 属性 | 内容 |
|------|------|
| 违规ID | {v.get('violation_id', 'N/A')} |
| 风险等级 | {v.get('risk_level', '中')} |
| 置信度 | {v.get('confidence', 0):.2%} |

**违规描述**
{v.get('description', '暂无描述')}

**政策依据**
{v.get('policy_reference', '暂无依据')}

**配置值**
```json
{json.dumps(v.get('config_value', {}), ensure_ascii=False, indent=2)}
```

---

"""
        
        template += f"""
## 六、报告说明

本报告由营销审计智能系统自动生成，审计结果仅供参考，具体整改措施请结合业务实际情况。

---
*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        return template
    
    @staticmethod
    def violation_list_csv(violations: List[Dict[str, Any]]) -> str:
        headers = ["违规ID", "标题", "风险等级", "违规描述", "政策依据", "置信度"]
        csv_lines = [",".join(headers)]
        
        for v in violations:
            row = [
                v.get("violation_id", ""),
                v.get("title", "").replace(",", "，"),
                v.get("risk_level", ""),
                v.get("description", "").replace(",", "，").replace("\n", " ")[:200],
                v.get("policy_reference", "").replace(",", "，").replace("\n", " ")[:200],
                f"{v.get('confidence', 0):.2%}"
            ]
            csv_lines.append(",".join(row))
        
        return "\n".join(csv_lines)
    
    @staticmethod
    def audit_summary_json(report_data: Dict[str, Any]) -> str:
        summary_data = {
            "report_type": "audit_summary",
            "generated_at": datetime.now().isoformat(),
            "metadata": report_data.get("metadata", {}),
            "summary": report_data.get("summary", {}),
            "violations_count": len(report_data.get("detailed_violations", [])),
            "recommendations": report_data.get("recommendations", [])
        }
        return json.dumps(summary_data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def excel_template() -> Dict[str, List[str]]:
        return {
            "违规清单": [
                "序号,违规ID,违规标题,风险等级,违规描述,政策依据,配置值,置信度,发现时间"
            ],
            "统计汇总": [
                "风险等级,数量,占比",
                "高,0,0%",
                "中,0,0%",
                "低,0,0%"
            ],
            "整改跟踪": [
                "违规ID,整改状态,整改负责人,整改期限,整改说明,验证结果"
            ]
        }
