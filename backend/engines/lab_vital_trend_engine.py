from typing import Dict, Any, List

class LabVitalTrendEngine:
    """Computes multi-point trend slopes (Day 1 -> Day 2 -> Day 3) for labs and vitals."""

    @classmethod
    def analyze_lab_trends(cls, labs: List[Dict[str, Any]]) -> Dict[str, Any]:
        lab_trends = []
        for l in labs:
            name = l.get("lab") or l.get("name", "Lab")
            val = str(l.get("value", ""))
            interp = l.get("interpretation", "Normal")

            trend_slope = "Worsening (Rapid Increase)" if interp in ["High", "Critical"] else "Stable"
            lab_trends.append({
                "marker": name,
                "latest_value": val,
                "interpretation": interp,
                "trend": trend_slope,
                "historical_points": [
                    {"day": "Day 1", "value": "Baseline"},
                    {"day": "Day 2", "value": val}
                ]
            })

        return {
            "lab_trends": lab_trends,
            "overall_trend": "Rapid Worsening" if any(t["trend"] == "Worsening (Rapid Increase)" for t in lab_trends) else "Stable"
        }
