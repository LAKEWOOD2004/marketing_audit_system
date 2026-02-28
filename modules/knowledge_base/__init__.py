from typing import Dict, List, Any, Optional

from .vector_store import VectorStore, vector_store
from .rule_extractor import RuleExtractor, rule_extractor
from .rag_engine import RAGEngine, rag_engine


class KnowledgeBase:
    def __init__(self):
        self.rag_engine = rag_engine
        self.vector_store = vector_store
        self.rule_extractor = rule_extractor
    
    def build_from_documents(self, documents: List[Dict[str, Any]]) -> None:
        self.rag_engine.build_knowledge_base(documents)
    
    def query(self, question: str, n_context: int = 3) -> Dict[str, Any]:
        return self.rag_engine.query(question, n_context)
    
    def retrieve_rules(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        return self.rag_engine.retrieve(query, n_results)
    
    def get_applicable_rules(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.rag_engine.find_applicable_rules(config_data)
    
    def extract_rules_from_text(self, text: str) -> List[Dict[str, Any]]:
        return self.rule_extractor.extract_rules(text)
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        return self.rag_engine.get_all_rules()
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_documents": self.vector_store.get_count(),
            "total_rules": len(self.get_all_rules())
        }


knowledge_base = KnowledgeBase()
