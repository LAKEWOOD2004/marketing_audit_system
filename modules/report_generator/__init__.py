from typing import Dict, List, Any, Optional
from pathlib import Path

from .templates import ReportTemplates
from .report_builder import ReportBuilder, report_builder


class ReportGenerator:
    def __init__(self):
        self.builder = report_builder
        self.templates = ReportTemplates()
    
    def generate_report(self, 
                        audit_result: Dict[str, Any],
                        format: str = "markdown") -> Dict[str, Any]:
        return self.builder.build_report(audit_result, format)
    
    def generate_violation_list(self, 
                                violations: List[Dict[str, Any]],
                                format: str = "csv") -> Dict[str, Any]:
        return self.builder.build_violation_list(violations, format)
    
    def save_all_outputs(self, 
                         audit_result: Dict[str, Any]) -> Dict[str, Path]:
        return self.builder.generate_full_output(audit_result)
    
    def quick_report(self, violations: List[Dict[str, Any]]) -> str:
        report_data = {
            "violations": violations,
            "metadata": {},
            "summary": {
                "total": len(violations),
                "high_risk_count": len([v for v in violations if v.get("risk_level") == "高"]),
                "medium_risk_count": len([v for v in violations if v.get("risk_level") == "中"]),
                "low_risk_count": len([v for v in violations if v.get("risk_level") == "低"])
            }
        }
        return self.templates.audit_report_markdown(report_data)


report_generator = ReportGenerator()
