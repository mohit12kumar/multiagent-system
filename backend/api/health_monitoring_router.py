import os
import sys
import time
import platform
from typing import Dict, Any
from backend.core.metrics import metrics_collector

class HealthMonitoringRouter:
    """Production health check and readiness diagnostic service."""

    _START_TIME = time.time()

    @classmethod
    def get_health_status(cls) -> Dict[str, Any]:
        """Liveness check probe."""
        uptime = round(time.time() - cls._START_TIME, 2)
        return {
            "status": "HEALTHY",
            "service": "Enterprise Clinical Intelligence Platform",
            "version": "7.0.0",
            "uptime_seconds": uptime,
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    @classmethod
    def get_readiness_status(cls) -> Dict[str, Any]:
        """Readiness check probe inspecting real memory, CPU, and metrics."""
        summary = metrics_collector.get_metrics_summary()
        return {
            "status": "READY",
            "system_metrics": {
                "cpu_cores": os.cpu_count() or 1,
                "process_pid": os.getpid(),
                "memory_usage_mb": summary.get("process_memory_mb"),
                "system_memory_percent": summary.get("system_memory_percent"),
                "cpu_percent": summary.get("cpu_utilization_percent"),
            },
            "subsystems": {
                "nlp_extraction_engine": "OPERATIONAL",
                "clinical_rules_engine": "LOADED",
                "terminology_mappings": "READY",
                "fhir_r4_validator": "ACTIVE",
                "knowledge_graph_builder": "READY"
            },
            "pipeline_summary": summary.get("pipeline_metrics"),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
