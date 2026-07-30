"""
backend/core/cache.py

In-memory LRU Pipeline Cache & Duplicate Request Deduplicator.
Hashes clinical document text (SHA-256) to cache pipeline results and prevent double-execution
when users submit duplicate requests concurrently.
"""

import hashlib
import time
import threading
from typing import Dict, Any, Optional

class PipelineCache:
    """
    Thread-safe LRU cache and duplicate request tracker.
    """
    def __init__(self, max_entries: int = 200, ttl_seconds: int = 3600):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._pending_requests: Dict[str, float] = {}
        self._lock = threading.Lock()

    @staticmethod
    def compute_hash(text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def get(self, text: str) -> Optional[Dict[str, Any]]:
        key = self.compute_hash(text)
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry["timestamp"] < self.ttl_seconds:
                    return entry["data"]
                else:
                    del self._cache[key]
        return None

    def put(self, text: str, result_data: Dict[str, Any]):
        key = self.compute_hash(text)
        with self._lock:
            if len(self._cache) >= self.max_entries:
                # Evict oldest entry
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
                del self._cache[oldest_key]

            self._cache[key] = {
                "timestamp": time.time(),
                "data": result_data
            }
            self._pending_requests.pop(key, None)

    def is_processing(self, text: str) -> bool:
        key = self.compute_hash(text)
        with self._lock:
            if key in self._pending_requests:
                # Clean stale pending locks older than 120s
                if time.time() - self._pending_requests[key] > 120:
                    del self._pending_requests[key]
                    return False
                return True
            return False

    def mark_processing(self, text: str):
        key = self.compute_hash(text)
        with self._lock:
            self._pending_requests[key] = time.time()

    def clear_processing(self, text: str):
        key = self.compute_hash(text)
        with self._lock:
            self._pending_requests.pop(key, None)

pipeline_cache = PipelineCache()
