"""
backend/core/inference_pool.py

Thread-safe InferencePool for heavy NLP models (SpaCy, SciSpaCy, BioBERT tokenizers).
Prevents segmentation faults and race conditions when multiple threads invoke `.predict()`
or `__call__()` on non-thread-safe model instances simultaneously.
"""

import queue
import logging
import threading
from contextlib import contextmanager
from typing import Any, Callable, Generator, Dict

logger = logging.getLogger(__name__)

class ModelPool:
    """
    Generic thread-safe object pool for NLP models.
    """
    def __init__(self, name: str, factory: Callable[[], Any], pool_size: int = 2):
        self.name = name
        self.factory = factory
        self.pool_size = max(1, pool_size)
        self._pool: queue.Queue = queue.Queue(maxsize=self.pool_size)
        self._lock = threading.Lock()
        self._initialized = False

    def _initialize(self):
        with self._lock:
            if self._initialized:
                return
            logger.info(f"[InferencePool] Initializing '{self.name}' with pool_size={self.pool_size}...")
            for i in range(self.pool_size):
                try:
                    model = self.factory()
                    if model is not None and model is not False:
                        self._pool.put(model)
                        logger.info(f"[InferencePool] Warm instance #{i+1} loaded for '{self.name}'.")
                except Exception as e:
                    logger.error(f"[InferencePool] Error instantiating model for '{self.name}': {e}")
            self._initialized = True

    @contextmanager
    def acquire(self, timeout: float = 10.0) -> Generator[Any, None, None]:
        if not self._initialized:
            self._initialize()

        if self._pool.empty():
            logger.warning(f"[InferencePool] Pool '{self.name}' is currently empty (all {self.pool_size} workers busy). Waiting...")

        model = None
        try:
            model = self._pool.get(block=True, timeout=timeout)
            yield model
        except queue.Empty:
            logger.error(f"[InferencePool] Timeout acquiring model from pool '{self.name}' after {timeout}s.")
            yield None
        finally:
            if model is not None:
                self._pool.put(model)


_pools: Dict[str, ModelPool] = {}
_registry_lock = threading.Lock()

def get_model_pool(name: str, factory: Callable[[], Any], pool_size: int = 2) -> ModelPool:
    with _registry_lock:
        if name not in _pools:
            _pools[name] = ModelPool(name=name, factory=factory, pool_size=pool_size)
        return _pools[name]
