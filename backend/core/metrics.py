"""
backend/core/metrics.py

Real production observability metrics engine for the Clinical Multi-Agent System.
Replaces the hardcoded mock ObservabilityEngine with thread-safe counters, latency histograms,
and Prometheus OpenMetrics export.
"""

import time
import os
import psutil
import threading
from collections import defaultdict, deque
from typing import Dict, Any, List

class MetricsCollector:
    """
    Thread-safe operational metrics collector.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsCollector, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.start_time = time.time()
        self.counters = defaultdict(int)
        self.latencies = defaultdict(lambda: deque(maxlen=100))
        self.stage_durations = defaultdict(lambda: deque(maxlen=100))
        self.confidence_scores = deque(maxlen=200)

    def record_stage(self, stage_name: str, duration_seconds: float, success: bool = True):
        with self._lock:
            self.stage_durations[stage_name].append(duration_seconds)
            self.counters[f"stage_{stage_name}_total"] += 1
            if not success:
                self.counters[f"stage_{stage_name}_failed"] += 1

    def record_pipeline(self, duration_seconds: float, success: bool = True):
        with self._lock:
            self.latencies["pipeline"].append(duration_seconds)
            self.counters["pipeline_requests_total"] += 1
            if success:
                self.counters["pipeline_requests_success"] += 1
            else:
                self.counters["pipeline_requests_failed"] += 1

    def record_confidence(self, score: float):
        with self._lock:
            self.confidence_scores.append(score)

    def record_retry(self, service: str):
        with self._lock:
            self.counters[f"retries_{service}"] += 1

    def get_metrics_summary(self) -> Dict[str, Any]:
        with self._lock:
            uptime = round(time.time() - self.start_time, 2)
            mem = psutil.virtual_memory()
            proc = psutil.Process(os.getpid())
            proc_mem = proc.memory_info().rss / (1024 * 1024)  # MB

            pipeline_lats = list(self.latencies["pipeline"])
            avg_pipeline_lat = round(sum(pipeline_lats) / len(pipeline_lats), 3) if pipeline_lats else 0.0

            stage_stats = {}
            for stage, durations in self.stage_durations.items():
                dur_list = list(durations)
                stage_stats[stage] = {
                    "avg_ms": round((sum(dur_list) / len(dur_list)) * 1000, 2) if dur_list else 0.0,
                    "count": self.counters[f"stage_{stage}_total"],
                    "failures": self.counters[f"stage_{stage}_failed"],
                }

            scores = list(self.confidence_scores)
            conf_stats = {
                "high_pct": f"{round(sum(1 for s in scores if s >= 0.85) / len(scores) * 100, 1)}%" if scores else "0%",
                "moderate_pct": f"{round(sum(1 for s in scores if 0.65 <= s < 0.85) / len(scores) * 100, 1)}%" if scores else "0%",
                "review_required_pct": f"{round(sum(1 for s in scores if s < 0.65) / len(scores) * 100, 1)}%" if scores else "0%",
            }

            return {
                "uptime_seconds": uptime,
                "process_memory_mb": round(proc_mem, 2),
                "system_memory_percent": mem.percent,
                "cpu_utilization_percent": psutil.cpu_percent(interval=None),
                "pipeline_metrics": {
                    "total_requests": self.counters["pipeline_requests_total"],
                    "successful_requests": self.counters["pipeline_requests_success"],
                    "failed_requests": self.counters["pipeline_requests_failed"],
                    "avg_latency_seconds": avg_pipeline_lat,
                },
                "stage_metrics": stage_stats,
                "confidence_distribution": conf_stats,
                "observability_status": "OPERATIONAL",
            }

    def export_openmetrics(self) -> str:
        summary = self.get_metrics_summary()
        lines = [
            "# HELP pipeline_requests_total Total number of clinical NLP pipeline requests",
            "# TYPE pipeline_requests_total counter",
            f"pipeline_requests_total {summary['pipeline_metrics']['total_requests']}",
            f"pipeline_requests_success {summary['pipeline_metrics']['successful_requests']}",
            f"pipeline_requests_failed {summary['pipeline_metrics']['failed_requests']}",
            f"pipeline_avg_latency_seconds {summary['pipeline_metrics']['avg_latency_seconds']}",
            f"process_memory_mb {summary['process_memory_mb']}",
            f"system_memory_percent {summary['system_memory_percent']}",
            f"system_cpu_percent {summary['cpu_utilization_percent']}",
        ]
        for stage, stats in summary["stage_metrics"].items():
            lines.append(f'stage_latency_avg_ms{{stage="{stage}"}} {stats["avg_ms"]}')
            lines.append(f'stage_requests_total{{stage="{stage}"}} {stats["count"]}')
            lines.append(f'stage_requests_failed{{stage="{stage}"}} {stats["failures"]}')
        return "\n".join(lines) + "\n"

metrics_collector = MetricsCollector()
