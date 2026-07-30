"""
backend/core/chroma_lock.py

Thread-safe Read-Write / Mutual Exclusion Lock for ChromaDB operations.
Prevents database corruption or lock file collisions when multiple pipeline requests write to
ChromaDB persistent collections concurrently.
"""

import threading
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_chroma_write_lock = threading.RLock()

@contextmanager
def chroma_write_lock(timeout: float = 10.0):
    """
    Acquire exclusive write lock for ChromaDB modification operations (add, update, delete).
    """
    acquired = _chroma_write_lock.acquire(timeout=timeout)
    if not acquired:
        logger.error(f"[ChromaLock] Failed to acquire ChromaDB write lock within {timeout}s.")
        raise TimeoutError("ChromaDB write lock acquisition timed out.")
    try:
        yield
    finally:
        _chroma_write_lock.release()
