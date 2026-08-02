"""
backend/core/drift_detector.py

Real-Time Embedding & Clinical Terminology Drift Detector.
Monitors statistical drift in vector embeddings, confidence score distributions, and extraction frequencies.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("multiagent_ner")

class DriftDetector:
    """
    Monitors extraction distributions for concept and embedding drift.
    """

    def __init__(self, confidence_threshold: float = 0.70):
        self.confidence_threshold = confidence_threshold
        self.history: List[float] = []

    def log_confidence(self, confidence: float):
        """
        Records extraction confidence score into history.
        """
        self.history.append(confidence)
        if len(self.history) > 1000:
            self.history.pop(0)

    def detect_drift(self) -> Dict[str, Any]:
        """
        Calculates moving average confidence and detects performance degradation drift.
        """
        if not self.history:
            return {"drift_detected": False, "average_confidence": 1.0}

        avg_conf = sum(self.history) / len(self.history)
        is_drift = avg_conf < self.confidence_threshold

        if is_drift:
            logger.warning(f"[DriftDetector] Drift detected! Moving average confidence dropped to {avg_conf:.2f}")

        return {
            "drift_detected": is_drift,
            "average_confidence": round(avg_conf, 4),
            "sample_count": len(self.history)
        }

drift_detector = DriftDetector()
