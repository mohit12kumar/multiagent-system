"""
backend/core/pipeline_cache.py

Alias module for PipelineCache (SHA-256 document hashing and result deduplication).
"""

from backend.core.cache import PipelineCache, pipeline_cache

__all__ = ["PipelineCache", "pipeline_cache"]
