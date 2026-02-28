from typing import Dict, List, Any, Optional
import os
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from config.settings import VECTOR_STORE_CONFIG, DATA_DIR


class VectorStore:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or VECTOR_STORE_CONFIG
        self.client = None
        self.collection = None
        self._init_store()
    
    def _init_store(self):
        if not CHROMADB_AVAILABLE:
            print("Warning: chromadb not available, using in-memory storage")
            self._use_memory_storage()
            return
        
        persist_dir = self.config.get("persist_directory", str(DATA_DIR / "vector_db"))
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        collection_name = self.config.get("collection_name", "audit_knowledge")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "审计知识库向量存储"}
        )
    
    def _use_memory_storage(self):
        self.memory_store = {
            "documents": [],
            "metadatas": [],
            "ids": []
        }
    
    def add_documents(self, 
                      documents: List[str], 
                      metadatas: Optional[List[Dict]] = None,
                      ids: Optional[List[str]] = None) -> None:
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        if self.collection is not None:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        else:
            self.memory_store["documents"].extend(documents)
            self.memory_store["metadatas"].extend(metadatas)
            self.memory_store["ids"].extend(ids)
    
    def query(self, 
              query_texts: List[str], 
              n_results: int = 5,
              where: Optional[Dict] = None) -> Dict[str, Any]:
        if self.collection is not None:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )
            return results
        else:
            return self._memory_query(query_texts[0], n_results)
    
    def _memory_query(self, query: str, n_results: int) -> Dict[str, Any]:
        from difflib import SequenceMatcher
        
        docs_with_scores = []
        for i, doc in enumerate(self.memory_store["documents"]):
            score = SequenceMatcher(None, query, doc).ratio()
            docs_with_scores.append((doc, self.memory_store["metadatas"][i], score))
        
        docs_with_scores.sort(key=lambda x: x[2], reverse=True)
        top_results = docs_with_scores[:n_results]
        
        return {
            "documents": [[r[0] for r in top_results]],
            "metadatas": [[r[1] for r in top_results]],
            "distances": [[1 - r[2] for r in top_results]]
        }
    
    def delete(self, ids: List[str]) -> None:
        if self.collection is not None:
            self.collection.delete(ids=ids)
    
    def get_count(self) -> int:
        if self.collection is not None:
            return self.collection.count()
        return len(self.memory_store["documents"])
    
    def clear(self) -> None:
        if self.collection is not None:
            ids = self.collection.get()["ids"]
            if ids:
                self.collection.delete(ids=ids)
        else:
            self.memory_store = {"documents": [], "metadatas": [], "ids": []}


vector_store = VectorStore()
