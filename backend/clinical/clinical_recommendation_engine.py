from typing import Dict, Any, List

class ClinicalRecommendationEngine:
    """Generates disease-specific, prioritized clinical action recommendations for enterprise CDS."""

    RECOMMENDATION_CATALOG = {
        "Acute Inferior STEMI": [
            {"timeframe": "Immediate", "action": "Activate Cardiac Cath Lab STAT for Primary PCI"},
            {"timeframe": "Immediate", "action": "Administer Dual Antiplatelet Therapy (Aspirin 300mg + Clopidogrel 300mg loading dose)"},
            {"timeframe": "Within 1 Hour", "action": "Cardiology Consultation & Cardiac ICU admission"},
            {"timeframe": "Today", "action": "High-Intensity Statin Therapy (Atorvastatin 80mg)"},
            {"timeframe": "24 Hours", "action": "Echocardiogram to assess Wall Motion Abnormality & LVEF"}
        ],
        "Heart Failure": [
            {"timeframe": "Immediate", "action": "IV Loop Diuretic Therapy (Furosemide 40mg IV STAT)"},
            {"timeframe": "Within 1 Hour", "action": "Continuous SpO2 & Cardiac Telemetry Monitoring"},
            {"timeframe": "Today", "action": "Transthoracic Echocardiography & Daily Weight Tracking"},
            {"timeframe": "24 Hours", "action": "Initiate Guideline-Directed Medical Therapy (ARNI/ACEi + Beta-blocker + MRA + SGLT2i)"},
            {"timeframe": "Follow-up", "action": "Low-Sodium & Fluid Restriction (<2L/day) Counseling"}
        ],
        "Chronic Kidney Disease": [
            {"timeframe": "Immediate", "action": "Discontinue Nephrotoxic Medications & Adjust Renal Drug Dosing"},
            {"timeframe": "Within 1 Hour", "action": "Nephrology Consultation for Stage IV Discrepancy & eGFR 15 mL/min"},
            {"timeframe": "Today", "action": "Serum Electrolytes & Renal Ultrasound Evaluation"},
            {"timeframe": "24 Hours", "action": "24-Hour Urine Protein & Albumin-to-Creatinine Ratio"},
            {"timeframe": "Follow-up", "action": "Arteriovenous Fistula (AVF) Planning & Vascular Access Evaluation"}
        ],
        "Acute Kidney Injury": [
            {"timeframe": "Immediate", "action": "Hold Nephrotoxic Agents (NSAIDs, Aminoglycosides, Contrast)"},
            {"timeframe": "Within 1 Hour", "action": "Strict Fluid Balance & Hourly Urine Output Tracking"},
            {"timeframe": "Today", "action": "Repeat Serum Creatinine & BUN in 12 Hours"},
            {"timeframe": "24 Hours", "action": "Renal Sonogram to Rule Out Post-Renal Obstruction"}
        ],
        "Hyperkalemia": [
            {"timeframe": "Immediate", "action": "STAT 12-Lead ECG to Assess for Peaked T Waves / QRS Widening"},
            {"timeframe": "Immediate", "action": "IV Calcium Gluconate 10% (10mL over 2-3 mins) for Membrane Stabilization"},
            {"timeframe": "Within 1 Hour", "action": "IV Regular Insulin 10 Units + Dextrose 50% 50mL to Shift Potassium"},
            {"timeframe": "Today", "action": "Discontinue Potassium-Retaining Drugs (Losartan, Spironolactone)"},
            {"timeframe": "24 Hours", "action": "Repeat Serum Electrolytes every 4-6 Hours until Potassium <5.0 mmol/L"}
        ],
        "Community Acquired Pneumonia": [
            {"timeframe": "Immediate", "action": "Supplemental Oxygen Therapy to Maintain SpO2 >92%"},
            {"timeframe": "Within 1 Hour", "action": "Blood & Sputum Cultures prior to Antibiotic Administration"},
            {"timeframe": "Within 1 Hour", "action": "Empiric Broad-Spectrum IV Antibiotic Therapy (Ceftriaxone 1g IV + Azithromycin 500mg PO)"},
            {"timeframe": "Today", "action": "Repeat Chest X-Ray & Inflammatory Markers (WBC, CRP)"},
            {"timeframe": "Follow-up", "action": "Pneumococcal & Influenza Vaccination Counseling"}
        ],
        "Diabetes Mellitus": [
            {"timeframe": "Immediate", "action": "Monitor Capillary Blood Glucose every 4 Hours"},
            {"timeframe": "Within 1 Hour", "action": "Hold Metformin if eGFR <30 mL/min to prevent Lactic Acidosis"},
            {"timeframe": "Today", "action": "Initiate Basal-Bolus Insulin Regimen as Clinically Indicated"},
            {"timeframe": "24 Hours", "action": "Diabetic Nephropathy & Retinopathy Screening Audit"},
            {"timeframe": "Follow-up", "action": "HbA1c Target <7.0% Optimization & Diabetic Foot Care"}
        ],
        "Hypertension": [
            {"timeframe": "Within 1 Hour", "action": "Evaluate for Hypertensive Emergency / End-Organ Damage"},
            {"timeframe": "Today", "action": "Optimize Antihypertensive Therapy (Losartan / Amlodipine)"},
            {"timeframe": "24 Hours", "action": "Ambulatory Blood Pressure Monitoring (ABPM) & Home BP Log"},
            {"timeframe": "Follow-up", "action": "DASH Diet & Sodium Restriction (<2g/day) Lifestyle Counseling"}
        ],
        "Hyperlipidemia": [
            {"timeframe": "Today", "action": "Initiate High-Intensity Statin Therapy (Atorvastatin 80mg Nightly)"},
            {"timeframe": "24 Hours", "action": "10-Year ASCVD Risk Calculation & Cardiovascular Assessment"},
            {"timeframe": "Follow-up", "action": "Fasting Lipid Profile Re-evaluation in 8-12 Weeks"}
        ]
    }

    @classmethod
    def generate_recommendations(cls, disease_name: str) -> List[Dict[str, str]]:
        d_norm = disease_name.strip()
        for k, recs in cls.RECOMMENDATION_CATALOG.items():
            if k.lower() in d_norm.lower() or d_norm.lower() in k.lower():
                return recs
        return [
            {"timeframe": "Today", "action": f"Guideline-directed medical evaluation for {disease_name}"},
            {"timeframe": "24 Hours", "action": f"Monitor clinical response and laboratory parameters for {disease_name}"}
        ]
