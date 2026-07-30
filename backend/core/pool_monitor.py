"""
backend/core/pool_monitor.py

Monitors SQLAlchemy database connection pool health: active checkout count, pool size, overflow,
and pool wait times to detect connection leaks or pool exhaustion.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConnectionPoolMonitor:
    @classmethod
    def inspect_pool(cls, engine: Any) -> Dict[str, Any]:
        """
        Inspect engine connection pool status.
        """
        try:
            pool = engine.pool
            size = pool.size()
            checkedin = pool.checkedin()
            checkedout = pool.checkedout()
            overflow = pool.overflow()

            status = "HEALTHY"
            if checkedout >= size + overflow * 0.8:
                status = "WARNING_HIGH_LOAD"
            if checkedout >= size + overflow:
                status = "CRITICAL_EXHAUSTED"

            return {
                "pool_status": status,
                "pool_size": size,
                "checked_in_connections": checkedin,
                "checked_out_active_connections": checkedout,
                "current_overflow": overflow,
                "max_overflow": getattr(pool, "_max_overflow", 20),
            }
        except Exception as e:
            logger.warning(f"[PoolMonitor] Unable to inspect DB pool: {e}")
            return {
                "pool_status": "UNKNOWN",
                "error": str(e)
            }
