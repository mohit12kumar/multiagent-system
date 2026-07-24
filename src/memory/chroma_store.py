import os
import yaml
import chromadb
from chromadb.config import Settings
from typing import Any, Dict, List, Optional
from src.utils.embedding_model import EmbeddingModel
from src.monitoring.logger import logger


class ChromaStore:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        CONFIG_PATH = os.path.join(BASE_DIR, "config", "chroma_config.yaml")

        self.host = os.getenv("CHROMA_HOST", "localhost")
        self.port = int(os.getenv("CHROMA_PORT", "8000"))
        self.collection_name = "medical_canonical_entities"

        default_emb = "all-MiniLM-L6-v2"
        fallback_emb = "emilyalsentzer/Bio_ClinicalBERT"

        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                yaml_config = yaml.safe_load(f)
                self.host = os.getenv("CHROMA_HOST") or yaml_config.get(
                    "host", "localhost")
                self.port = int(os.getenv("CHROMA_PORT")
                                or yaml_config.get("port", 8000))
                self.collection_name = yaml_config.get(
                    "collection_name", "medical_canonical_entities")

                emb_cfg = yaml_config.get("embedding", {})
                default_emb = emb_cfg.get("default_model", default_emb)
                fallback_emb = emb_cfg.get("fallback_model", fallback_emb)

        # Initialize manual embedding model manager
        self.embedding_model = EmbeddingModel(
            default_model=default_emb, fallback_model=fallback_emb)

        # Only attempt HttpClient if USE_CHROMA_SERVER env var is explicitly enabled
        use_server = os.getenv("USE_CHROMA_SERVER", "false").lower() == "true"
        server_alive = False
        if use_server and os.getenv("ENV") != "test":
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                res = sock.connect_ex((self.host, self.port))
                sock.close()
                if res == 0:
                    server_alive = True
            except Exception:
                server_alive = False

        try:
            if os.getenv("ENV") == "test":
                logger.info("Using ephemeral in-memory ChromaDB client for testing")
                self.client = chromadb.EphemeralClient()
            elif use_server and server_alive:
                logger.info(f"Connecting to ChromaDB server at {self.host}:{self.port}")
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                persist_dir = os.path.join(BASE_DIR, "chroma_db")
                os.makedirs(persist_dir, exist_ok=True)
                self.client = chromadb.PersistentClient(path=persist_dir)
        except Exception as e:
            logger.warning(f"Could not connect to Chroma server: {e}. Falling back to persistent local client.")
            persist_dir = os.path.join(BASE_DIR, "chroma_db")
            os.makedirs(persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(path=persist_dir)

        # Initialize medical entity collections
        # We define a custom space (cosine)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.collection_fallback = self.client.get_or_create_collection(
            name=self.collection_name + "_fallback",
            metadata={"hnsw:space": "cosine"}
        )

    def add_entity(self, entity_id: str, name: str, entity_type: str) -> None:
        """Generates embedding and indexes the canonical entity in Chroma."""
        try:
            # Generate default embedding (384-dim)
            emb = self.embedding_model.get_embeddings(
                [name], use_fallback=False)[0]
            # Store in default collection
            self.collection.add(
                ids=[entity_id],
                embeddings=[emb],
                documents=[name],
                metadatas=[{"type": entity_type, "name": name}]
            )

            # Generate fallback embedding (768-dim)
            emb_fallback = self.embedding_model.get_embeddings(
                [name], use_fallback=True)[0]
            # Store in fallback collection
            self.collection_fallback.add(
                ids=[entity_id],
                embeddings=[emb_fallback],
                documents=[name],
                metadatas=[{"type": entity_type, "name": name}]
            )
            logger.info(
                f"Indexed medical entity in Chroma: id={entity_id}, name={name}")
        except Exception as e:
            logger.error(f"Failed to add medical entity to Chroma: {e}")

    def query_similar_entities(self, text: str, entity_type: Optional[str] = None, n_results: int = 5, use_fallback: bool = False) -> List[Dict[str, Any]]:
        """
        Queries similarity matches using either the default MiniLM model or
        the fallback Bio_ClinicalBERT model for specialized medical terms.
        """
        try:
            # Generate target embedding
            emb = self.embedding_model.get_embeddings(
                [text], use_fallback=use_fallback)[0]

            where_clause = {}
            if entity_type:
                where_clause = {"type": entity_type}

            target_collection = self.collection_fallback if use_fallback else self.collection
            results = target_collection.query(
                query_embeddings=[emb],
                n_results=n_results,
                where=where_clause if where_clause else None
            )

            candidates = []
            if results and results.get("ids") and results["ids"][0]:
                ids = results["ids"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results else [
                    0.0] * len(ids)

                for i in range(len(ids)):
                    similarity = 1.0 - \
                        distances[i] if distances[i] is not None else 0.0
                    candidates.append({
                        "id": ids[i],
                        "name": documents[i],
                        "type": metadatas[i].get("type"),
                        "similarity": similarity
                    })
            return candidates
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []

    def reset_collection(self) -> None:
        """Resets the collections."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.client.delete_collection(
                name=self.collection_name + "_fallback")
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.collection_fallback = self.client.get_or_create_collection(
                name=self.collection_name + "_fallback",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB collections reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset ChromaDB collection: {e}")
