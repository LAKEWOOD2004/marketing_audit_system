import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"

for dir_path in [INPUT_DIR, OUTPUT_DIR, KNOWLEDGE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

LLM_CONFIG = {
    "provider": os.getenv("LLM_PROVIDER", "zhipu"),
    "model": os.getenv("LLM_MODEL", "glm-4"),
<<<<<<< HEAD
    "api_key": os.getenv("ZHIPU_API_KEY", "9d16cdbfdbd8422ba8dd142aae4e9107.SeYx3XbdzNpUZqov"),
=======
    "api_key": os.getenv("ZHIPU_API_KEY", ""),
>>>>>>> ee092ef (first commit)
    "base_url": os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
    "temperature": 0.1,
    "max_tokens": 4096,
}

EMBEDDING_CONFIG = {
    "model": os.getenv("EMBEDDING_MODEL", "embedding-2"),
    "dimension": 1024,
}

VECTOR_STORE_CONFIG = {
    "type": "chromadb",
    "persist_directory": str(DATA_DIR / "vector_db"),
    "collection_name": "audit_knowledge",
}

AUDIT_CONFIG = {
    "risk_levels": ["高", "中", "低"],
    "max_audit_items": 1000,
    "similarity_threshold": 0.85,
}
