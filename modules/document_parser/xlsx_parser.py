from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd


class XlsxParser:
    def __init__(self):
        self.supported_extensions = ['.xlsx', '.xls', '.csv']
    
    def parse(self, filepath: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        filepath = Path(filepath)
        ext = filepath.suffix.lower()
        
        if ext == '.csv':
            return self._parse_csv(filepath)
        else:
            return self._parse_excel(filepath, sheet_name)
    
    def _parse_excel(self, filepath: Path, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        result = {
            "file_info": {
                "filename": filepath.name,
                "filepath": str(filepath),
                "type": "excel"
            },
            "sheets": {},
            "summary": {}
        }
        
        excel_file = pd.ExcelFile(filepath)
        sheets_to_parse = [sheet_name] if sheet_name else excel_file.sheet_names
        
        for sheet in sheets_to_parse:
            df = pd.read_excel(filepath, sheet_name=sheet)
            result["sheets"][sheet] = self._parse_dataframe(df, sheet)
        
        result["summary"] = self._generate_summary(result["sheets"])
        
        return result
    
    def _parse_csv(self, filepath: Path) -> Dict[str, Any]:
        df = pd.read_csv(filepath)
        
        return {
            "file_info": {
                "filename": filepath.name,
                "filepath": str(filepath),
                "type": "csv"
            },
            "sheets": {
                "data": self._parse_dataframe(df, "data")
            },
            "summary": self._generate_summary({"data": self._parse_dataframe(df, "data")})
        }
    
    def _parse_dataframe(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        df = df.fillna('')
        
        columns = df.columns.tolist()
        data_rows = df.values.tolist()
        
        column_types = {}
        for col in columns:
            non_empty = df[col][df[col] != '']
            if len(non_empty) > 0:
                column_types[col] = str(non_empty.iloc[0].__class__.__name__)
            else:
                column_types[col] = 'unknown'
        
        return {
            "sheet_name": sheet_name,
            "columns": columns,
            "column_types": column_types,
            "row_count": len(df),
            "col_count": len(columns),
            "data": [
                dict(zip(columns, row))
                for row in data_rows
            ],
            "markdown": self._to_markdown(df)
        }
    
    def _to_markdown(self, df: pd.DataFrame, max_rows: int = 50) -> str:
        df_display = df.head(max_rows)
        
        lines = []
        lines.append("| " + " | ".join(str(col) for col in df_display.columns) + " |")
        lines.append("| " + " | ".join("---" for _ in df_display.columns) + " |")
        
        for _, row in df_display.iterrows():
            line = "| " + " | ".join(str(v).replace('\n', ' ')[:50] for v in row) + " |"
            lines.append(line)
        
        if len(df) > max_rows:
            lines.append(f"\n... 共 {len(df)} 行数据，仅显示前 {max_rows} 行")
        
        return "\n".join(lines)
    
    def _generate_summary(self, sheets: Dict[str, Dict]) -> Dict[str, Any]:
        total_rows = 0
        total_cols = 0
        all_columns = set()
        
        for sheet_data in sheets.values():
            total_rows += sheet_data.get("row_count", 0)
            total_cols = max(total_cols, sheet_data.get("col_count", 0))
            all_columns.update(sheet_data.get("columns", []))
        
        return {
            "total_sheets": len(sheets),
            "total_rows": total_rows,
            "total_columns": total_cols,
            "unique_columns": list(all_columns),
            "column_count": len(all_columns)
        }
    
    def extract_business_config(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        configs = []
        
        for sheet_name, sheet_data in parsed_data.get("sheets", {}).items():
            for row in sheet_data.get("data", []):
                config_item = {
                    "source_sheet": sheet_name,
                    "config_data": row,
                    "config_type": self._detect_config_type(row)
                }
                configs.append(config_item)
        
        return configs
    
    def _detect_config_type(self, row: Dict[str, Any]) -> str:
        keys = set(str(k).lower() for k in row.keys())
        
        if any(k in keys for k in ['优惠券', 'coupon', '折扣']):
            return "coupon_config"
        elif any(k in keys for k in ['促销', 'promotion', '活动']):
            return "promotion_config"
        elif any(k in keys for k in ['用户', 'user', '客户']):
            return "user_config"
        elif any(k in keys for k in ['金额', 'amount', '价格', 'price']):
            return "price_config"
        else:
            return "unknown_config"
    
    def to_json_format(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "document_type": "business_config",
            "file_info": parsed_data["file_info"],
            "summary": parsed_data["summary"],
            "sheets": {
                name: {
                    "columns": data["columns"],
                    "row_count": data["row_count"],
                    "data": data["data"]
                }
                for name, data in parsed_data.get("sheets", {}).items()
            }
        }
