import os
import yaml
import chromadb
from chromadb.config import Settings
from typing import Any, Dict, List, Optional
from backend.utils.embedding_model import EmbeddingModel
from src.monitoring.logger import logger


class ChromaService:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        CONFIG_PATH = os.path.join(BASE_DIR, "config", "chroma_config.yaml")

        self.host = os.getenv("CHROMA_HOST", "localhost")
        self.port = int(os.getenv("CHROMA_PORT", "8000"))
        self.collection_name = "medical_canonical_entities"

        default_emb = "all-MiniLM-L6-v2"
        fallback_emb = "emilyalsentzer/Bio_ClinicalBERT"

        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                yaml_config = yaml.safe_load(f) or {}
                self.host = os.getenv("CHROMA_HOST") or yaml_config.get("host", "localhost")
                self.port = int(os.getenv("CHROMA_PORT") or yaml_config.get("port", 8000))
                self.collection_name = yaml_config.get("collection_name", "medical_canonical_entities")

        # Embedding model — heavy transformer load deferred to first actual query
        self.embedding_model = EmbeddingModel(default_model=default_emb, fallback_model=fallback_emb)

        # Persistent client path
        persist_dir = os.path.join(BASE_DIR, "chroma_db")
        os.makedirs(persist_dir, exist_ok=True)
        try:
            self.client = chromadb.PersistentClient(path=persist_dir)
        except Exception as e:
            logger.warning(f"Using ephemeral ChromaDB client fallback: {e}")
            self.client = chromadb.EphemeralClient()

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.disease_collection = self.client.get_or_create_collection(
            name="canonical_diseases",
            metadata={"hnsw:space": "cosine"}
        )
        self.drug_collection = self.client.get_or_create_collection(
            name="canonical_drugs",
            metadata={"hnsw:space": "cosine"}
        )

    def add_entity(self, entity_id: str, name: str, entity_type: str) -> None:
        from backend.core.chroma_lock import chroma_write_lock
        try:
            emb = self.embedding_model.get_embeddings([name], use_fallback=False)[0]
            with chroma_write_lock():
                self.collection.add(
                    ids=[entity_id],
                    embeddings=[emb],
                    documents=[name],
                    metadatas=[{"type": entity_type, "name": name}]
                )
                target_coll = self.disease_collection if entity_type.upper() == "DISEASE" else self.drug_collection
                target_coll.add(
                    ids=[entity_id],
                    embeddings=[emb],
                    documents=[name],
                    metadatas=[{"type": entity_type, "name": name}]
                )
        except Exception as e:
            logger.error(f"Failed to add entity to ChromaDB: {e}")

    def query_similar_entities(self, text: str, entity_type: Optional[str] = None, n_results: int = 5) -> List[Dict[str, Any]]:
        try:
            emb = self.embedding_model.get_embeddings([text], use_fallback=False)[0]
            where_clause = {"type": entity_type.upper()} if entity_type else None

            results = self.collection.query(
                query_embeddings=[emb],
                n_results=n_results,
                where=where_clause
            )

            candidates = []
            if results and results.get("ids") and results["ids"][0]:
                ids = results["ids"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results else [0.0] * len(ids)

                for i in range(len(ids)):
                    similarity = 1.0 - (distances[i] if distances[i] is not None else 0.0)
                    candidates.append({
                        "id": ids[i],
                        "name": documents[i],
                        "type": metadatas[i].get("type"),
                        "similarity": round(max(0.0, min(1.0, similarity)), 4)
                    })
            return candidates
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []
