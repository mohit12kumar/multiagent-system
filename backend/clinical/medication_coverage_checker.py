"""
Medication Coverage Checker.
Audits all detected drug mentions to guarantee complete coverage and zero medication loss.
Categorizes medications into: mapped, unmapped, rejected, and unknown.
Calculates dynamic coverage percentage.
"""

from typing import Dict, Any, List
from src.monitoring.logger import logger


class MedicationCoverageChecker:
    """Audits extracted medications to ensure 100% accounting and zero medication loss."""

    @classmethod
    def audit_coverage(
        cls,
        raw_drug_mentions: List[str],
        medication_relations: List[Any],
        rejected_drugs: List[str] = None
    ) -> Dict[str, Any]:
        """
        Audits raw drug mentions against mapped relations and rejected drugs.
        Returns detailed coverage metrics.
        """
        rejected_drugs = rejected_drugs or []
        
        # Deduplicate raw mentions
        raw_unique = list(dict.fromkeys([d.strip().lower() for d in raw_drug_mentions if d and d.strip()]))
        total_detected = len(raw_unique)

        if total_detected == 0:
            return {
                "total_detected": 0,
                "mapped_count": 0,
                "unmapped_count": 0,
                "rejected_count": 0,
                "coverage_percentage": 100.0,
                "mapped_medications": [],
                "unmapped_medications": [],
                "rejected_medications": [],
                "audit_passed": True
            }

        mapped_set = set()
        mapped_meds_list = []

        for m in medication_relations:
            if isinstance(m, dict):
                m_name = (m.get("name") or m.get("medication_name") or "").strip().lower()
                dis_name = m.get("disease_name")
            else:
                m_name = (getattr(m, "name", "") or getattr(m, "medication_name", "")).strip().lower()
                dis_name = getattr(m, "disease_name", None)

            if m_name:
                mapped_set.add(m_name)
                mapped_meds_list.append({"name": m_name, "disease": dis_name})

        unmapped_meds = []
        for raw in raw_unique:
            if raw not in mapped_set and raw not in [r.lower() for r in rejected_drugs]:
                unmapped_meds.append(raw)

        mapped_count = len(mapped_set)
        unmapped_count = len(unmapped_meds)
        rejected_count = len(set([r.lower() for r in rejected_drugs]))

        coverage_pct = round(((mapped_count + rejected_count) / float(total_detected)) * 100.0, 1)
        coverage_pct = min(100.0, max(0.0, coverage_pct))

        logger.info(f"Medication Coverage Audit: Total {total_detected}, Mapped {mapped_count}, Unmapped {unmapped_count}, Coverage {coverage_pct}%")

        return {
            "total_detected": total_detected,
            "mapped_count": mapped_count,
            "unmapped_count": unmapped_count,
            "rejected_count": rejected_count,
            "coverage_percentage": coverage_pct,
            "mapped_medications": mapped_meds_list,
            "unmapped_medications": unmapped_meds,
            "rejected_medications": list(set(rejected_drugs)),
            "audit_passed": unmapped_count == 0
        }
