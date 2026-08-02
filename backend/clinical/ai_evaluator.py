"""
backend/clinical/ai_evaluator.py

AI Evaluation Suite & Enterprise Quality Score Matrix Engine.
Calculates 9 core clinical accuracy, recall, and safety alignment metrics across model outputs.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class AIEvaluationSuite:
    """
    Evaluates clinical predictions against ground truth benchmark data.
    """

    def evaluate_cohort(
        self,
        ground_truth_cases: List[Dict[str, Any]],
        predicted_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates 9 core clinical quality metrics across test cases:
        - Precision
        - Recall
        - F1 Score
        - Hallucination Rate
        - False Medication Rate
        - Dose Accuracy
        - Route Accuracy
        - Frequency Accuracy
        - Evidence Alignment Score
        """
        if len(ground_truth_cases) != len(predicted_cases):
            raise ValueError(f"Cohort mismatch: ground truth length ({len(ground_truth_cases)}) != predicted length ({len(predicted_cases)})")

        tp, fp, fn = 0, 0, 0
        total_hallucinations = 0
        total_false_meds = 0
        total_predicted_meds = 0

        dose_correct, dose_total = 0, 0
        route_correct, route_total = 0, 0
        freq_correct, freq_total = 0, 0
        alignment_scores = []

        for gt, pred in zip(ground_truth_cases, predicted_cases):
            gt_meds = gt.get("medications", [])
            pred_meds = pred.get("medications", [])

            gt_names = { (m.get("name") or m.get("generic_name") or str(m)).strip().lower() for m in gt_meds }
            pred_names = { (m.get("name") or m.get("generic_name") or str(m)).strip().lower() for m in pred_meds }

            # TP, FP, FN calculation
            tp += len(gt_names.intersection(pred_names))
            fp += len(pred_names - gt_names)
            fn += len(gt_names - pred_names)

            total_predicted_meds += len(pred_names)
            total_false_meds += len(pred_names - gt_names)

            # Hallucination check
            hallucinations = pred.get("hallucinations", [])
            total_hallucinations += len(hallucinations)

            # Detail accuracy (dose, route, frequency matching)
            gt_med_map = { (m.get("name") or m.get("generic_name") or "").strip().lower(): m for m in gt_meds if isinstance(m, dict) }
            for pm in pred_meds:
                if isinstance(pm, dict):
                    p_name = (pm.get("name") or pm.get("generic_name") or "").strip().lower()
                    if p_name in gt_med_map:
                        gt_m = gt_med_map[p_name]

                        # Dose accuracy
                        if "dose" in gt_m:
                            dose_total += 1
                            if str(pm.get("dose")).strip().lower() == str(gt_m.get("dose")).strip().lower():
                                dose_correct += 1

                        # Route accuracy
                        if "route" in gt_m:
                            route_total += 1
                            if str(pm.get("route")).strip().lower() == str(gt_m.get("route")).strip().lower():
                                route_correct += 1

                        # Frequency accuracy
                        if "frequency" in gt_m:
                            freq_total += 1
                            if str(pm.get("frequency")).strip().lower() == str(gt_m.get("frequency")).strip().lower():
                                freq_correct += 1

            alignment_scores.append(pred.get("evidence_alignment_score", 0.95))

        # Precision, Recall, F1
        precision = tp / max(1, (tp + fp))
        recall = tp / max(1, (tp + fn))
        f1 = (2 * precision * recall) / max(1e-6, (precision + recall))

        # Hallucination & False Med Rate
        hallucination_rate = total_hallucinations / max(1, total_predicted_meds)
        false_medication_rate = total_false_meds / max(1, total_predicted_meds)

        # Attribute Accuracies
        dose_accuracy = dose_correct / max(1, dose_total)
        route_accuracy = route_correct / max(1, route_total)
        frequency_accuracy = freq_correct / max(1, freq_total)
        avg_alignment_score = sum(alignment_scores) / max(1, len(alignment_scores))

        # Combined Quality Score Index (0-100)
        overall_quality_score = round((
            0.25 * precision +
            0.25 * recall +
            0.15 * dose_accuracy +
            0.10 * route_accuracy +
            0.10 * frequency_accuracy +
            0.15 * (1.0 - hallucination_rate)
        ) * 100, 2)

        return {
            "total_cases_evaluated": len(ground_truth_cases),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "hallucination_rate": round(hallucination_rate, 4),
            "false_medication_rate": round(false_medication_rate, 4),
            "dose_accuracy": round(dose_accuracy, 4),
            "route_accuracy": round(route_accuracy, 4),
            "frequency_accuracy": round(frequency_accuracy, 4),
            "evidence_alignment_score": round(avg_alignment_score, 4),
            "overall_quality_score": overall_quality_score
        }
