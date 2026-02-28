from typing import Dict, List, Any, Optional, Tuple
import re


class TableReconstructor:
    def __init__(self):
        self.merge_indicators = ['同上', '同前', '同左', '同右', '---', '...']
    
    def reconstruct(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        reconstructed = []
        
        for table in tables:
            processed = self._process_single_table(table)
            reconstructed.append(processed)
        
        merged_tables = self._merge_cross_page_tables(reconstructed)
        
        return merged_tables
    
    def _process_single_table(self, table: Dict[str, Any]) -> Dict[str, Any]:
        rows = table.get("rows", [])
        if not rows:
            return table
        
        processed_rows = []
        for row in rows:
            processed_row = self._process_row(row, processed_rows)
            processed_rows.append(processed_row)
        
        table["rows"] = processed_rows
        table["reconstructed"] = True
        
        return table
    
    def _process_row(self, row: List[str], previous_rows: List[List[str]]) -> List[str]:
        if not previous_rows:
            return row
        
        processed = []
        prev_row = previous_rows[-1]
        
        for i, cell in enumerate(row):
            if self._is_merge_indicator(cell) and i < len(prev_row):
                processed.append(prev_row[i])
            else:
                processed.append(cell)
        
        return processed
    
    def _is_merge_indicator(self, cell: str) -> bool:
        cell = str(cell).strip().lower()
        return cell in [m.lower() for m in self.merge_indicators]
    
    def _merge_cross_page_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(tables) <= 1:
            return tables
        
        merged = []
        current_table = None
        
        for table in tables:
            if current_table is None:
                current_table = table.copy()
                continue
            
            if self._should_merge(current_table, table):
                current_table = self._merge_two_tables(current_table, table)
            else:
                merged.append(current_table)
                current_table = table.copy()
        
        if current_table:
            merged.append(current_table)
        
        return merged
    
    def _should_merge(self, table1: Dict[str, Any], table2: Dict[str, Any]) -> bool:
        headers1 = table1.get("headers", [])
        headers2 = table2.get("headers", [])
        
        if not headers1 or not headers2:
            return False
        
        if len(headers1) != len(headers2):
            return False
        
        similarity = self._calculate_header_similarity(headers1, headers2)
        return similarity >= 0.8
    
    def _calculate_header_similarity(self, headers1: List[str], headers2: List[str]) -> float:
        if not headers1 or not headers2:
            return 0.0
        
        matches = sum(1 for h1, h2 in zip(headers1, headers2) 
                     if str(h1).strip() == str(h2).strip())
        
        return matches / max(len(headers1), len(headers2))
    
    def _merge_two_tables(self, table1: Dict[str, Any], table2: Dict[str, Any]) -> Dict[str, Any]:
        merged = table1.copy()
        
        rows1 = table1.get("rows", [])
        rows2 = table2.get("rows", [])
        
        if rows2 and rows2[0] == table2.get("headers"):
            rows2 = rows2[1:]
        
        merged["rows"] = rows1 + rows2
        merged["row_count"] = len(merged["rows"])
        merged["is_cross_page_merged"] = True
        merged["markdown"] = self._regenerate_markdown(merged)
        
        return merged
    
    def _regenerate_markdown(self, table: Dict[str, Any]) -> str:
        rows = table.get("rows", [])
        if not rows:
            return ""
        
        lines = []
        for i, row in enumerate(rows):
            line = "| " + " | ".join(str(cell).replace('\n', ' ') for cell in row) + " |"
            lines.append(line)
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(row)) + " |"
                lines.append(separator)
        
        return "\n".join(lines)
    
    def extract_structured_data(self, table: Dict[str, Any]) -> List[Dict[str, Any]]:
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        
        if not headers or not rows:
            return []
        
        data_rows = rows[1:] if rows[0] == headers else rows
        
        structured = []
        for row in data_rows:
            if len(row) != len(headers):
                row = self._adjust_row_length(row, len(headers))
            
            item = dict(zip(headers, row))
            item["_source_table_index"] = table.get("table_index", 0)
            structured.append(item)
        
        return structured
    
    def _adjust_row_length(self, row: List[str], target_length: int) -> List[str]:
        if len(row) >= target_length:
            return row[:target_length]
        else:
            return row + [''] * (target_length - len(row))
    
    def detect_nested_structure(self, table: Dict[str, Any]) -> Dict[str, Any]:
        rows = table.get("rows", [])
        if not rows:
            return {"has_nested": False}
        
        nested_info = {
            "has_nested": False,
            "hierarchical_columns": [],
            "parent_child_relations": []
        }
        
        headers = rows[0] if rows else []
        for i, header in enumerate(headers):
            if '\n' in str(header) or '/' in str(header):
                nested_info["has_nested"] = True
                nested_info["hierarchical_columns"].append({
                    "index": i,
                    "header": header,
                    "sub_headers": re.split(r'[/\n]', str(header))
                })
        
        return nested_info
