from typing import Dict, Any
from backend.core.metrics import metrics_collector

class ObservabilityEngine:
    """Tracks system latency, memory usage, API call metrics, and agent confidence distribution."""

    @classmethod
    def get_system_metrics(cls) -> Dict[str, Any]:
        return metrics_collector.get_metrics_summary()
