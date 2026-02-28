from typing import Dict, List, Any, Optional
import json

from .vector_store import vector_store
from .rule_extractor import rule_extractor
from utils.llm_client import llm_client
from config.settings import KNOWLEDGE_DIR


class RAGEngine:
    def __init__(self):
        self.vector_store = vector_store
        self.rule_extractor = rule_extractor
        self.knowledge_base = []
    
    def build_knowledge_base(self, documents: List[Dict[str, Any]]) -> None:
        for doc in documents:
            self._process_document(doc)
    
    def _process_document(self, doc: Dict[str, Any]) -> None:
        doc_type = doc.get("document_type", "")
        
        if doc_type == "policy_document":
            self._process_policy_document(doc)
        elif doc_type == "audit_case":
            self._process_audit_case(doc)
        elif doc_type == "regulation":
            self._process_regulation(doc)
    
    def _process_policy_document(self, doc: Dict[str, Any]) -> None:
        content = doc.get("content", [])
        tables = doc.get("tables", [])
        metadata = doc.get("metadata", {})
        
        text_chunks = []
        for item in content:
            text = item.get("text", "")
            if text:
                text_chunks.append(text)
        
        for table in tables:
            table_text = table.get("markdown", "")
            if table_text:
                text_chunks.append(table_text)
        
        rules = self.rule_extractor.extract_rules("\n".join(text_chunks))
        
        documents_to_add = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(text_chunks):
            doc_id = f"policy_{metadata.get('title', 'doc')}_{i}"
            documents_to_add.append(chunk)
            metadatas.append({
                "type": "policy",
                "source": metadata.get("title", ""),
                "doc_type": "policy_document"
            })
            ids.append(doc_id)
        
        for i, rule in enumerate(rules):
            rule_id = f"rule_{metadata.get('title', 'doc')}_{i}"
            rule_text = json.dumps(rule, ensure_ascii=False)
            documents_to_add.append(rule_text)
            metadatas.append({
                "type": "rule",
                "source": metadata.get("title", ""),
                "rule_type": rule.get("rule_type", ""),
                "doc_type": "extracted_rule"
            })
            ids.append(rule_id)
        
        if documents_to_add:
            self.vector_store.add_documents(documents_to_add, metadatas, ids)
        
        self.knowledge_base.extend(rules)
    
    def _process_audit_case(self, doc: Dict[str, Any]) -> None:
        case_text = doc.get("content", "")
        case_metadata = doc.get("metadata", {})
        
        documents_to_add = [case_text]
        metadatas = [{
            "type": "audit_case",
            "case_id": case_metadata.get("case_id", ""),
            "violation_type": case_metadata.get("violation_type", ""),
            "doc_type": "audit_case"
        }]
        ids = [f"case_{case_metadata.get('case_id', 'unknown')}"]
        
        self.vector_store.add_documents(documents_to_add, metadatas, ids)
    
    def _process_regulation(self, doc: Dict[str, Any]) -> None:
        content = doc.get("content", "")
        metadata = doc.get("metadata", {})
        
        rules = self.rule_extractor.extract_rules(content)
        
        documents_to_add = [content]
        metadatas = [{
            "type": "regulation",
            "source": metadata.get("source", ""),
            "doc_type": "regulation"
        }]
        ids = [f"reg_{metadata.get('id', 'unknown')}"]
        
        for i, rule in enumerate(rules):
            rule_id = f"reg_rule_{metadata.get('id', 'unknown')}_{i}"
            documents_to_add.append(json.dumps(rule, ensure_ascii=False))
            metadatas.append({
                "type": "regulation_rule",
                "source": metadata.get("source", ""),
                "doc_type": "regulation_rule"
            })
            ids.append(rule_id)
        
        self.vector_store.add_documents(documents_to_add, metadatas, ids)
        self.knowledge_base.extend(rules)
    
    def retrieve(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        results = self.vector_store.query([query], n_results=n_results)
        
        retrieved_docs = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        for doc, meta, dist in zip(documents, metadatas, distances):
            retrieved_docs.append({
                "content": doc,
                "metadata": meta,
                "relevance_score": 1 - dist
            })
        
        return retrieved_docs
    
    def retrieve_with_rerank(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        initial_results = self.retrieve(query, n_results=n_results * 2)
        
        reranked = self._rerank_with_llm(query, initial_results)
        
        return reranked[:n_results]
    
    def _rerank_with_llm(self, query: str, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not docs:
            return []
        
        system_prompt = """你是一个相关性评估专家。请评估每个文档片段与查询问题的相关性程度。
返回一个JSON数组，每个元素包含：
- index: 文档索引（从0开始）
- relevance_score: 相关性分数（0-1之间，1表示最相关）
- reason: 简短的相关性判断理由

请按相关性从高到低排序返回。"""

        doc_texts = [d["content"][:500] for d in docs]
        user_message = f"查询问题: {query}\n\n文档列表:\n" + "\n---\n".join(
            f"[{i}] {text}" for i, text in enumerate(doc_texts)
        )
        
        try:
            result = llm_client.chat_json(system_prompt, user_message)
            
            if isinstance(result, list):
                score_map = {item["index"]: item["relevance_score"] for item in result}
                for doc in docs:
                    idx = docs.index(doc)
                    doc["llm_relevance_score"] = score_map.get(idx, 0)
                
                docs.sort(key=lambda x: x.get("llm_relevance_score", 0), reverse=True)
        except Exception as e:
            print(f"重排序失败: {e}")
        
        return docs
    
    def generate_answer(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        context_text = "\n\n".join(
            f"【参考文档{i+1}】\n{doc['content'][:1000]}"
            for i, doc in enumerate(context_docs)
        )
        
        system_prompt = """你是一个专业的审计知识助手。请基于提供的参考文档回答用户问题。
要求：
1. 回答必须基于参考文档内容，不要编造信息
2. 如果参考文档中没有相关信息，请明确说明
3. 回答要专业、准确、有条理
4. 如果涉及具体规则或数值，请准确引用"""

        user_message = f"参考文档：\n{context_text}\n\n问题：{query}"
        
        return llm_client.chat_with_system(system_prompt, user_message)
    
    def query(self, question: str, n_context: int = 3) -> Dict[str, Any]:
        context_docs = self.retrieve_with_rerank(question, n_results=n_context)
        answer = self.generate_answer(question, context_docs)
        
        return {
            "question": question,
            "answer": answer,
            "context": context_docs,
            "sources": [d["metadata"] for d in context_docs]
        }
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        return self.knowledge_base
    
    def find_applicable_rules(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        config_text = json.dumps(config_data, ensure_ascii=False)
        
        query = f"适用于以下配置的审计规则: {config_text[:500]}"
        relevant_docs = self.retrieve(query, n_results=10)
        
        applicable_rules = []
        for doc in relevant_docs:
            if doc["metadata"].get("type") in ["rule", "regulation_rule"]:
                try:
                    rule = json.loads(doc["content"])
                    applicable_rules.append(rule)
                except:
                    pass
        
        return applicable_rules


rag_engine = RAGEngine()
