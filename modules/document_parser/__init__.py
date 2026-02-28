from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from .docx_parser import DocxParser
from .xlsx_parser import XlsxParser
from .table_reconstructor import TableReconstructor


class DocumentParser:
    def __init__(self):
        self.docx_parser = DocxParser()
        self.xlsx_parser = XlsxParser()
        self.table_reconstructor = TableReconstructor()
    
    def parse(self, filepath: str) -> Dict[str, Any]:
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        ext = path.suffix.lower()
        
        if ext in ['.docx', '.doc']:
            return self._parse_docx(filepath)
        elif ext in ['.xlsx', '.xls', '.csv']:
            return self._parse_xlsx(filepath)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def _parse_docx(self, filepath: str) -> Dict[str, Any]:
        parsed = self.docx_parser.parse(filepath)
        
        if parsed.get("tables"):
            parsed["tables"] = self.table_reconstructor.reconstruct(parsed["tables"])
        
        json_data = self.docx_parser.to_json_format(parsed)
        json_data["file_path"] = filepath
        
        return json_data
    
    def _parse_xlsx(self, filepath: str) -> Dict[str, Any]:
        parsed = self.xlsx_parser.parse(filepath)
        json_data = self.xlsx_parser.to_json_format(parsed)
        json_data["file_path"] = filepath
        
        return json_data
    
    def parse_batch(self, filepaths: List[str]) -> List[Dict[str, Any]]:
        results = []
        for filepath in filepaths:
            try:
                result = self.parse(filepath)
                result["parse_status"] = "success"
                results.append(result)
            except Exception as e:
                results.append({
                    "file_path": filepath,
                    "parse_status": "error",
                    "error_message": str(e)
                })
        return results
    
    def extract_policy_rules(self, parsed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        rules = []
        
        content = parsed_doc.get("content", [])
        tables = parsed_doc.get("tables", [])
        
        for item in content:
            text = item.get("text", "")
            if self._contains_rule(text):
                rules.append({
                    "type": "text_rule",
                    "content": text,
                    "section": item.get("section", ""),
                    "source": "policy_document"
                })
        
        for table in tables:
            structured_data = self.table_reconstructor.extract_structured_data(table)
            for row in structured_data:
                rules.append({
                    "type": "table_rule",
                    "content": row,
                    "source": "policy_table"
                })
        
        return rules
    
    def _contains_rule(self, text: str) -> bool:
        rule_keywords = [
            "应当", "必须", "不得", "禁止", "要求", "规定",
            "限额", "上限", "下限", "范围", "条件", "标准"
        ]
        return any(kw in text for kw in rule_keywords)
    
    def extract_business_config(self, parsed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.xlsx_parser.extract_business_config(parsed_doc)


document_parser = DocumentParser()
