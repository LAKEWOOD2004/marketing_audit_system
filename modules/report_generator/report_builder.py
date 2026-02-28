from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import csv

from .templates import ReportTemplates
from config.settings import OUTPUT_DIR


class ReportBuilder:
    def __init__(self):
        self.templates = ReportTemplates
        self.output_dir = OUTPUT_DIR
    
    def build_report(self, 
                     audit_result: Dict[str, Any],
                     output_format: str = "markdown") -> Dict[str, Any]:
        report_data = self._prepare_report_data(audit_result)
        
        if output_format == "markdown":
            content = self.templates.audit_report_markdown(report_data)
            filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        elif output_format == "json":
            content = self.templates.audit_summary_json(report_data)
            filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            content = self.templates.audit_report_markdown(report_data)
            filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        return {
            "report_data": report_data,
            "content": content,
            "filename": filename,
            "format": output_format
        }
    
    def build_violation_list(self, 
                             violations: List[Dict[str, Any]],
                             output_format: str = "csv") -> Dict[str, Any]:
        if output_format == "csv":
            content = self.templates.violation_list_csv(violations)
            filename = f"violation_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        elif output_format == "json":
            content = json.dumps(violations, ensure_ascii=False, indent=2)
            filename = f"violation_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            content = self.templates.violation_list_csv(violations)
            filename = f"violation_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return {
            "content": content,
            "filename": filename,
            "format": output_format,
            "count": len(violations)
        }
    
    def save_report(self, 
                    content: str, 
                    filename: str,
                    output_dir: Optional[Path] = None) -> Path:
        output_path = output_dir or self.output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def save_violation_excel(self, 
                             violations: List[Dict[str, Any]],
                             filename: Optional[str] = None) -> Path:
        try:
            import pandas as pd
            
            if not violations:
                df = pd.DataFrame(columns=["违规ID", "标题", "风险等级", "描述", "政策依据"])
            else:
                df = pd.DataFrame([
                    {
                        "违规ID": v.get("violation_id", ""),
                        "标题": v.get("title", ""),
                        "风险等级": v.get("risk_level", ""),
                        "描述": v.get("description", ""),
                        "政策依据": v.get("policy_reference", "")[:200],
                        "配置值": json.dumps(v.get("config_value", {}), ensure_ascii=False)[:500],
                        "置信度": f"{v.get('confidence', 0):.2%}"
                    }
                    for v in violations
                ])
            
            filename = filename or f"violation_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = self.output_dir / filename
            
            df.to_excel(filepath, index=False, sheet_name="违规清单")
            
            return filepath
        except ImportError:
            return self.save_report(
                self.templates.violation_list_csv(violations),
                filename or f"violation_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
    
    def _prepare_report_data(self, audit_result: Dict[str, Any]) -> Dict[str, Any]:
        violations = audit_result.get("violations", [])
        
        summary = {
            "total": len(violations),
            "high_risk_count": len([v for v in violations if v.get("risk_level") == "高"]),
            "medium_risk_count": len([v for v in violations if v.get("risk_level") == "中"]),
            "low_risk_count": len([v for v in violations if v.get("risk_level") == "低"]),
            "message": self._generate_summary_message(violations)
        }
        
        violations_by_category = self._categorize_violations(violations)
        
        recommendations = self._generate_recommendations(violations)
        
        return {
            "metadata": audit_result.get("metadata", {}),
            "summary": summary,
            "violations_by_category": violations_by_category,
            "recommendations": recommendations,
            "detailed_violations": violations
        }
    
    def _generate_summary_message(self, violations: List[Dict[str, Any]]) -> str:
        if not violations:
            return "本次审计未发现违规问题，系统配置符合政策要求。"
        
        high = len([v for v in violations if v.get("risk_level") == "高"])
        medium = len([v for v in violations if v.get("risk_level") == "中"])
        low = len([v for v in violations if v.get("risk_level") == "低"])
        
        return f"本次审计共发现 {len(violations)} 个违规问题，其中高风险 {high} 个，中风险 {medium} 个，低风险 {low} 个。"
    
    def _categorize_violations(self, violations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        categories = {
            "金额超限": [],
            "范围越界": [],
            "条件不符": [],
            "逻辑冲突": [],
            "其他": []
        }
        
        for v in violations:
            title = v.get("title", "")
            if "金额" in title or "超限" in title:
                categories["金额超限"].append(v)
            elif "范围" in title or "越界" in title:
                categories["范围越界"].append(v)
            elif "条件" in title:
                categories["条件不符"].append(v)
            elif "逻辑" in title or "冲突" in title:
                categories["逻辑冲突"].append(v)
            else:
                categories["其他"].append(v)
        
        return {k: v for k, v in categories.items() if v}
    
    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        if not violations:
            return ["当前配置符合政策要求，建议继续保持。", "建议定期进行合规审计，确保配置持续合规。"]
        
        recommendations = []
        
        high_risk = [v for v in violations if v.get("risk_level") == "高"]
        if high_risk:
            recommendations.append(f"【紧急】发现 {len(high_risk)} 个高风险违规项，建议立即整改。")
        
        categories = self._categorize_violations(violations)
        for category, items in categories.items():
            if items:
                recommendations.append(f"建议检查 {category} 相关配置，共发现 {len(items)} 处问题。")
        
        recommendations.append("建议建立配置变更审核机制，从源头预防违规。")
        recommendations.append("建议定期进行合规审计，确保配置持续合规。")
        
        return recommendations
    
    def generate_full_output(self, 
                             audit_result: Dict[str, Any]) -> Dict[str, Path]:
        outputs = {}
        
        report = self.build_report(audit_result, "markdown")
        outputs["markdown_report"] = self.save_report(report["content"], report["filename"])
        
        violation_list = self.build_violation_list(audit_result.get("violations", []), "csv")
        outputs["violation_csv"] = self.save_report(violation_list["content"], violation_list["filename"])
        
        try:
            outputs["violation_excel"] = self.save_violation_excel(audit_result.get("violations", []))
        except:
            pass
        
        json_report = self.build_report(audit_result, "json")
        outputs["json_report"] = self.save_report(json_report["content"], json_report["filename"])
        
        return outputs


report_builder = ReportBuilder()
