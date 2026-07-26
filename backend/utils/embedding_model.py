import os
from typing import List, Dict, Any
from src.monitoring.logger import logger


class EmbeddingModel:
    """
    Utility class to manage dual embedding models on CPU with shared class-level caching.
    """
    _MODELS_CACHE: Dict[str, Any] = {}
    _TOKENIZERS_CACHE: Dict[str, Any] = {}
    _INITIALIZED_CACHE: Dict[str, bool] = {}

    def __init__(self, default_model: str = "all-MiniLM-L6-v2", fallback_model: str = "emilyalsentzer/Bio_ClinicalBERT"):
        self.default_model = default_model
        self.fallback_model = fallback_model

    def initialize(self, model_name: str) -> bool:
        """Loads a transformers model dynamically on GPU/CPU with class-level caching."""
        if EmbeddingModel._INITIALIZED_CACHE.get(model_name, False):
            return True

        try:
            from transformers import AutoTokenizer, AutoModel
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(
                f"Initializing embedding model: {model_name} on device: {device}")
            path = model_name
            if not os.path.exists(path) and "/" not in path:
                path = f"sentence-transformers/{path}"

            EmbeddingModel._TOKENIZERS_CACHE[model_name] = AutoTokenizer.from_pretrained(path)
            model = AutoModel.from_pretrained(path)
            EmbeddingModel._MODELS_CACHE[model_name] = model.to(device)
            EmbeddingModel._INITIALIZED_CACHE[model_name] = True
            return True
        except Exception as e:
            logger.error(f"Failed to load embedding model '{model_name}': {e}")
            EmbeddingModel._INITIALIZED_CACHE[model_name] = False
            return False

    def get_embeddings(self, texts: List[str], use_fallback: bool = False) -> List[List[float]]:
        """Generates embeddings using either the primary or fallback clinical model on GPU/CPU."""
        model_name = self.fallback_model if use_fallback else self.default_model

        success = self.initialize(model_name)
        if not success:
            logger.warning(
                f"Embedding model '{model_name}' unavailable. Returning dummy vectors.")
            return [[0.0] * 384 for _ in texts]

        try:
            import torch
            tokenizer = EmbeddingModel._TOKENIZERS_CACHE[model_name]
            model = EmbeddingModel._MODELS_CACHE[model_name]
            device = "cuda" if torch.cuda.is_available() else "cpu"

            inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = model(**inputs)
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy().tolist()
            return embeddings
        except Exception as e:
            logger.error(f"Error computing embeddings with {model_name}: {e}")
            return [[0.0] * 384 for _ in texts]
