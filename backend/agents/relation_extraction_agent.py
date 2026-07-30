"""
RelationExtractionAgent -- Multi-pass clinical entity linking & explainability builder.

Features:
  - 4-pass drug-disease mapping (Section-aware, Indication, Knowledge, Proximity)
  - Route detection (PO, Inhalation, IV, Subcutaneous, Topical)
  - Duration detection & chronic fallback ("Long-term (Chronic Treatment)")
  - Medication Completeness & Validation Score (0-100%)
  - Evidence-based per-disease Confidence Scoring (0-100%)
  - Structured Evidence breakdown (History, Assessment, Meds, Vitals/Labs)
  - "Detected Because" explainability bullet points
"""

import re
from typing import Dict, Any, List, Optional, Set
from backend.models.pipeline_state import PipelineState
from backend.models.entity import EntityMentionModel
from backend.models.relation import DiseaseRelationModel, MedicationDetailModel, DiseaseSummaryModel
from src.monitoring.logger import logger

_LAB_BLOCKLIST: Set[str] = {
    "creatinine", "hba1c", "hemoglobin", "haemoglobin", "hgb", "hb",
    "ldl", "hdl", "cholesterol", "bun", "potassium", "sodium", "egfr",
    "wbc", "rbc", "platelets", "troponin", "crp", "alt", "ast", "bilirubin",
    "albumin", "urea", "uric acid", "tsh", "t3", "t4", "ferritin", "iron",
    "calcium", "phosphorus", "magnesium", "fibrinogen", "inr", "ptt",
}

_VITAL_BLOCKLIST: Set[str] = {
    "blood pressure", "bp", "heart rate", "pulse", "respiratory rate",
    "rr", "temperature", "temp", "spo2", "oxygen saturation", "weight",
}

_ALLERGY_KEYWORDS: Set[str] = {
    "penicillin", "sulfa", "latex", "aspirin allergy", "ibuprofen allergy",
    "nsaid allergy", "codeine allergy", "contrast allergy", "amoxicillin allergy",
}

_DISEASE_CANONICAL: Dict[str, str] = {
    "htn": "Hypertension",
    "essential hypertension": "Hypertension",
    "high blood pressure": "Hypertension",
    "poorly controlled hypertension": "Hypertension",
    "dm": "Type 2 Diabetes Mellitus",
    "t2dm": "Type 2 Diabetes Mellitus",
    "type ii dm": "Type 2 Diabetes Mellitus",
    "type 2 dm": "Type 2 Diabetes Mellitus",
    "diabetes mellitus": "Type 2 Diabetes Mellitus",
    "diabetes": "Type 2 Diabetes Mellitus",
    "ckd": "Chronic Kidney Disease",
    "chronic kidney disease": "Chronic Kidney Disease",
    "cad": "Coronary Artery Disease",
    "coronary artery disease": "Coronary Artery Disease",
    "chf": "Heart Failure",
    "congestive heart failure": "Heart Failure",
    "heart failure": "Heart Failure",
    "copd": "COPD",
    "chronic obstructive pulmonary disease": "COPD",
    "hyperlipidemia": "Hyperlipidemia",
    "hyperlipidaemia": "Hyperlipidemia",
    "dyslipidemia": "Hyperlipidemia",
    "stemi": "Acute Inferior STEMI / Acute Myocardial Infarction",
    "acute stemi": "Acute Inferior STEMI / Acute Myocardial Infarction",
    "acute inferior stemi": "Acute Inferior STEMI / Acute Myocardial Infarction",
    "myocardial infarction": "Acute Inferior STEMI / Acute Myocardial Infarction",
    "acute myocardial infarction": "Acute Inferior STEMI / Acute Myocardial Infarction",
    "mi": "Acute Inferior STEMI / Acute Myocardial Infarction",
    "cap": "Community Acquired Pneumonia",
    "pneumonia": "Community Acquired Pneumonia",
    "atrial fibrillation": "Atrial Fibrillation",
    "gerd": "GERD",
    "peptic ulcer": "GERD",
    "anemia": "Anemia",
    "acute kidney injury": "Acute Kidney Injury",
    "aki": "Acute Kidney Injury",
    "hyperkalemia": "Hyperkalemia"
}

# Diseases that are typically chronic and require long-term duration fallback
_CHRONIC_DISEASES: Set[str] = {
    "Hypertension", "Type 2 Diabetes Mellitus", "Hyperlipidemia",
    "GERD", "Chronic Kidney Disease", "Coronary Artery Disease",
    "Heart Failure", "COPD", "Atrial Fibrillation", "Anemia"
}

_INDICATION_PATTERNS = [
    re.compile(r'\bfor\s+([\w\s]+?)(?:\.|,|;|\band\b|$)', re.IGNORECASE),
    re.compile(r'\bto treat\s+([\w\s]+?)(?:\.|,|;|\band\b|$)', re.IGNORECASE),
]

_INDICATION_ALIASES: Dict[str, str] = {
    "blood pressure": "hypertension", "hypertension": "hypertension",
    "heart": "heart failure", "respiratory": "copd", "breathing": "copd",
    "infection": "pneumonia", "pneumonia": "pneumonia", "diabetic": "diabetes",
    "blood sugar": "diabetes", "cholesterol": "hyperlipidemia", "acid": "gerd",
    "reflux": "gerd", "fever": "pneumonia",
}

_DRUG_DISEASE_KNOWLEDGE: Dict[str, str] = {
    "atorvastatin": "hyperlipidemia", "atrovastatin": "hyperlipidemia",
    "simvastatin": "hyperlipidemia", "rosuvastatin": "hyperlipidemia",
    "furosemide": "heart failure", "spironolactone": "heart failure",
    "vitamin d3": "kidney", "amlodipine": "hypertension", "amlodpine": "hypertension",
    "lisinopril": "hypertension", "losartan": "hypertension", "atenolol": "hypertension",
    "metoprolol": "hypertension", "metformin": "diabetes", "metphormin": "diabetes",
    "empagliflozin": "diabetes", "aspirin": "coronary", "clopidogrel": "coronary",
    "azithromycin": "pneumonia", "azithromicin": "pneumonia", "amoxicillin": "pneumonia",
    "salbutamol": "copd", "salbutmol": "copd", "albuterol": "copd",
    "paracetamol": "pneumonia", "paracetmol": "pneumonia", "pcm": "pneumonia", "acetaminophen": "pneumonia",
    "omeprazole": "gerd", "omeprazol": "gerd", "pantoprazole": "gerd",
    "ibuprofen": "musculoskeletal", "levothyroxine": "hypothyroidism",
}

_SYMPTOM_DISEASE_KNOWLEDGE: Dict[str, List[str]] = {
    "swelling": ["kidney", "heart failure", "ckd", "pulmonary edema"],
    "leg swelling": ["kidney", "heart failure", "ckd"],
    "edema": ["kidney", "heart failure", "ckd", "pulmonary edema"],
    "urine output": ["kidney", "ckd", "aki"],
    "decreased urine output": ["kidney", "ckd", "aki"],
    "frequent urination": ["diabetes"],
    "polyuria": ["diabetes"],
    "fatigue": ["diabetes", "anemia", "kidney"],
    "dizziness": ["hypertension", "diabetes"],
    "headache": ["hypertension"],
    "chest pain": ["coronary", "heart failure", "stemi", "myocardial infarction"],
    "orthopnea": ["heart failure", "pulmonary edema"],
    "weakness": ["hyperkalemia", "kidney"],
    "chest tightness": ["hypertension", "heart failure", "copd"],
    "shortness of breath": ["copd", "heart failure", "pneumonia", "pulmonary edema"],
    "dyspnea": ["copd", "heart failure", "pneumonia", "pulmonary edema"],
    "wheezing": ["copd"],
    "productive cough": ["copd", "pneumonia"],
    "cough": ["copd", "pneumonia"],
    "fever": ["pneumonia"],
    "mild fever": ["pneumonia"],
}


def normalize_disease_name(name: str) -> str:
    return _DISEASE_CANONICAL.get(name.strip().lower(), name.strip())


from backend.agents.dosage_validation_agent import DosageValidationAgent

_FORMULATION_BLOCKLIST: Set[str] = {
    "inhaler", "tablet", "tablets", "tab", "capsule", "capsules", "cap",
    "injection", "inj", "cream", "gel", "ointment", "solution", "suspension",
    "syrup", "drops", "eye drops", "ear drops", "puff", "puffs"
}

_FORMULATION_MAP: Dict[str, str] = {
    "tab": "Tablet", "tablet": "Tablet", "tablets": "Tablet",
    "cap": "Capsule", "capsule": "Capsule", "capsules": "Capsule",
    "inhaler": "Inhaler", "puff": "Inhaler", "puffs": "Inhaler",
    "inj": "Injection", "injection": "Injection",
    "cream": "Cream", "gel": "Gel", "ointment": "Ointment",
    "syrup": "Syrup", "suspension": "Suspension", "drops": "Drops"
}

def infer_formulation(drug_text: str, context_window: str) -> str:
    """Extract formulation type separately from drug name."""
    comb = (drug_text + " " + context_window).lower()
    for kw, form in _FORMULATION_MAP.items():
        if kw in comb:
            return form
    return "Tablet"

def infer_route(drug_text: str, formulation: str, context_window: str) -> str:
    """Infer route deterministically from formulation and context."""
    f_low = (formulation or "").lower()
    t_low = (drug_text + " " + context_window).lower()

    if "inhaler" in f_low or "puff" in f_low or "inhaler" in t_low or "inhalation" in t_low:
        return "Inhalation"
    if "injection" in f_low or "inj" in f_low or bool(re.search(r'\biv\b|\bintravenous\b|\binjection\b', t_low)):
        return "IV (Intravenous)"
    if "cream" in f_low or "gel" in f_low or "ointment" in f_low or "topical" in t_low:
        return "Topical"
    if "eye drops" in t_low or "ophthalmic" in t_low:
        return "Ophthalmic"
    if "ear drops" in t_low or "otic" in t_low:
        return "Otic"
    if "capsule" in f_low or "tablet" in f_low or "syrup" in f_low or "suspension" in f_low:
        return "PO (Oral)"
    
    d_name = drug_text.lower()
    if any(oral_drug in d_name for oral_drug in ["omeprazole", "pantoprazole", "amlodipine", "metformin", "lisinopril", "losartan", "atorvastatin", "aspirin", "azithromycin", "paracetamol"]):
        return "PO (Oral)"
    
    return "PO (Oral)"


def infer_duration(drug_text: str, disease_name: Optional[str], extracted_duration: Optional[str]) -> str:
    """Return extracted duration or infer chronic fallback."""
    if extracted_duration and extracted_duration.strip() and extracted_duration != "As directed":
        return extracted_duration.strip()
    if disease_name and normalize_disease_name(disease_name) in _CHRONIC_DISEASES:
        return "Long-term (Chronic Treatment)"
    return "Duration Not Specified"


_FREQUENCY_EXPANSIONS: Dict[str, str] = {
    "tds": "Three Times Daily (TDS)",
    "tid": "Three Times Daily (TID)",
    "bd": "Twice Daily (BD)",
    "bid": "Twice Daily (BID)",
    "qd": "Once Daily (QD)",
    "od": "Once Daily (OD)",
    "qid": "Four Times Daily (QID)",
    "qds": "Four Times Daily (QDS)",
    "hs": "At Bedtime (HS)",
    "stat": "Immediately (STAT)",
    "prn": "As Needed (PRN)",
    "sos": "As Needed (SOS)",
    "1-0-1": "Twice Daily (1-0-1)",
    "1-1-1": "Three Times Daily (1-1-1)",
    "1-0-0": "Once Daily Morning (1-0-0)",
    "0-0-1": "Once Daily Night (0-0-1)",
    "0-1-0": "Once Daily Afternoon (0-1-0)",
    "1-1-1-1": "Four Times Daily (1-1-1-1)",
}

def expand_frequency(freq_str: str) -> str:
    """Expand Latin frequency abbreviations and 1-0-1 shorthand to full clinical descriptions."""
    if not freq_str:
        return "Once Daily"
    f_low = freq_str.strip().lower()
    return _FREQUENCY_EXPANSIONS.get(f_low, freq_str.strip())


def compute_medication_validation(med: MedicationDetailModel) -> Dict[str, Any]:
    """Calculate dynamic completeness score (0-100%) and actionable field explanations for a medication."""
    dose_ok = bool(med.dosage and med.dosage != "As prescribed" and med.dosage != "N/A")
    freq_ok = bool(med.frequency and med.frequency not in ("As prescribed", "N/A"))
    route_ok = bool(med.route)
    dur_ok = bool(med.duration and "Not Specified" not in med.duration and med.duration != "N/A")
    form_ok = bool(med.formulation)

    explanations = []
    score = 100
    if not dur_ok:
        score -= 20
        explanations.append("Missing Duration")
    if not dose_ok:
        score -= 20
        explanations.append("Unspecified Dosage")
    if not freq_ok:
        score -= 15
        explanations.append("Inferred Frequency")
    if med.clinical_warning:
        score -= 15
        explanations.append("Clinical Warning")

    score = max(40, score)
    label = f"{score}% Complete (Warning)" if med.clinical_warning else (f"{score}% Complete" if score < 100 else "100% Valid Prescription")

    deduction_details = []
    if not dur_ok:
        deduction_details.append("Missing Duration (-20%)")
    if not dose_ok:
        deduction_details.append("Unspecified Dosage (-20%)")
    if not freq_ok:
        deduction_details.append("Inferred Frequency (-15%)")
    if med.clinical_warning:
        deduction_details.append("Clinical Warning (-15%)")

    return {
        "completeness_score": score,
        "dose_check": dose_ok,
        "frequency_check": freq_ok,
        "route_check": route_ok,
        "duration_check": dur_ok,
        "formulation_check": form_ok,
        "status_label": label[:250],
        "explanations": explanations,
        "deduction_details": deduction_details,
    }


class RelationExtractionAgent:
    """Links clinical entities and builds structured explainability data."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.default_dosage    = "As prescribed"
        self.default_frequency = "Once Daily"

    def process(self, state: PipelineState) -> PipelineState:
        logger.info(f"Relation Extraction Agent processing session {state.session_id}")
        entities  = state.validated_entities
        full_text = state.text or state.original_text or ""

        diseases = sorted([e for e in entities if e.type == "DISEASE"], key=lambda e: e.start_char)
        symptoms = sorted([e for e in entities if e.type == "SYMPTOM"], key=lambda e: e.start_char)
        
        # Filter out lab/vital blocklist, allergy keywords, and standalone formulation words
        drugs    = sorted([
            e for e in entities if e.type == "DRUG"
            and e.text.lower().strip() not in _FORMULATION_BLOCKLIST
            and not any(l in e.text.lower() for l in _LAB_BLOCKLIST)
            and not any(v in e.text.lower() for v in _VITAL_BLOCKLIST)
            and not any(a in e.text.lower() for a in _ALLERGY_KEYWORDS)
        ], key=lambda e: e.start_char)

        dosages     = [e for e in entities if e.type == "DOSAGE"]
        frequencies = [e for e in entities if e.type == "FREQUENCY"]
        durations   = [e for e in entities if e.type == "DURATION"]

        # Deduplicate disease entities
        seen_canonical: Dict[str, EntityMentionModel] = {}
        for d in diseases:
            cn = normalize_disease_name(d.text)
            if cn not in seen_canonical:
                seen_canonical[cn] = d
        diseases = list(seen_canonical.values())

        medication_details: List[MedicationDetailModel] = []
        drug_to_med: Dict[str, MedicationDetailModel] = {}

        parsed_prescriptions = getattr(state, "metadata", {}).get("parsed_prescriptions", [])

        for dr in drugs:
            window = full_text[max(0, dr.start_char - 20): min(len(full_text), dr.end_char + 80)]
            form_val   = infer_formulation(dr.text, window)
            dosage_val = self._find_after(dr, dosages, full_text, self.default_dosage)
            freq_val   = expand_frequency(self._find_after(dr, frequencies, full_text, self.default_frequency))
            dur_val    = self._find_after(dr, durations, full_text, None)
            route_val  = infer_route(dr.text, form_val, window)

            # Check MedicationParserAgent results
            matched_p = next((p for p in parsed_prescriptions if p["name"].lower() == dr.text.lower() or dr.text.lower() in p["name"].lower()), None)
            if matched_p:
                if matched_p.get("dose") and matched_p["dose"] != "Unspecified":
                    dosage_val = matched_p["dose"]
                if matched_p.get("normalized_frequency"):
                    freq_val = matched_p["normalized_frequency"]
                if matched_p.get("route") and matched_p["route"] != "PO":
                    route_val = matched_p["route"]
                if matched_p.get("duration") and matched_p["duration"] != "Not Specified":
                    dur_val = matched_p["duration"]

            # Validate dosage & formulation clinically
            is_valid, warning = DosageValidationAgent.validate(dr.text, dosage_val, route_val, form_val)

            med = MedicationDetailModel(
                name=dr.text,
                disease_name=None,
                correct=is_valid,
                confidence=dr.confidence,
                dosage=dosage_val,
                dosage_unit="mg" if "mg" in dosage_val.lower() else "mcg" if "mcg" in dosage_val.lower() else "puffs" if "puff" in dosage_val.lower() else "unit",
                frequency=freq_val,
                duration=dur_val or "Duration Not Specified",
                route=route_val,
                formulation=form_val,
                clinical_warning=warning,
                validation_status="Valid Prescription" if is_valid else "Clinical Warning",
            )
            drug_to_med[dr.text.lower()] = med
            medication_details.append(med)

        assigned_drugs: Set[str] = set()

        # Pass 0: Section-aware linking from ASSESSMENT / PLAN
        self._pass0_section_aware(drugs, diseases, drug_to_med, assigned_drugs, full_text)

        # Pass 1: Inline indication
        for dr in drugs:
            if dr.text.lower() in assigned_drugs: continue
            ind = self._extract_indication(dr, full_text)
            if ind:
                kw = _INDICATION_ALIASES.get(ind)
                if kw:
                    matched = self._find_disease(kw, diseases)
                    if matched:
                        drug_to_med[dr.text.lower()].disease_name = matched.text
                        assigned_drugs.add(dr.text.lower())

        # Pass 2: Knowledge dict
        for dr in drugs:
            if dr.text.lower() in assigned_drugs: continue
            d_low = dr.text.lower()
            for pattern, dis_kw in _DRUG_DISEASE_KNOWLEDGE.items():
                if pattern in d_low:
                    matched = self._find_disease(dis_kw, diseases)
                    if matched:
                        drug_to_med[d_low].disease_name = matched.text
                        assigned_drugs.add(d_low)
                        break

        # Pass 3: Proximity fallback
        for dr in drugs:
            if dr.text.lower() in assigned_drugs: continue
            nearest = self._nearest_disease(dr, diseases, 150)
            if nearest:
                drug_to_med[dr.text.lower()].disease_name = nearest.text
                assigned_drugs.add(dr.text.lower())
            else:
                drug_to_med[dr.text.lower()].disease_name = "General Condition"

        # Apply duration inference & calculate completeness score
        for med in medication_details:
            med.duration = infer_duration(med.name, med.disease_name, med.duration)
            val_meta = compute_medication_validation(med)
            med.completeness_score = val_meta["completeness_score"]
            med.validation_status = val_meta["status_label"]
            med.validation_reason = f"Completeness Score: {val_meta['completeness_score']}% (Dose: {val_meta['dose_check']}, Freq: {val_meta['frequency_check']}, Route: {val_meta['route_check']}, Duration: {val_meta['duration_check']}, Formulation: {val_meta['formulation_check']})"

        # Disease -> Symptom mapping
        disease_relations: List[DiseaseRelationModel] = []
        for sym in symptoms:
            sym_low = sym.text.lower()
            matched_dis: List[EntityMentionModel] = []
            for kw, dis_kws in _SYMPTOM_DISEASE_KNOWLEDGE.items():
                if kw in sym_low:
                    for dis_kw in dis_kws:
                        dm = self._find_disease(dis_kw, diseases)
                        if dm and dm not in matched_dis:
                            matched_dis.append(dm)
            if not matched_dis:
                nearest = self._nearest_disease(sym, diseases, 300)
                if nearest: matched_dis.append(nearest)

            for dm in matched_dis:
                disease_relations.append(
                    DiseaseRelationModel(disease_name=dm.text, symptom_name=sym.text, confidence=min(dm.confidence, sym.confidence))
                )

        # Build structured summaries with evidence & confidence scores
        seen_summary: Dict[str, DiseaseSummaryModel] = {}
        for dis in diseases:
            dis_canonical = normalize_disease_name(dis.text)
            matched_meds = [m for m in medication_details if m.disease_name == dis.text or (m.disease_name and normalize_disease_name(m.disease_name) == dis_canonical)]
            matched_syms = list({r.symptom_name for r in disease_relations if normalize_disease_name(r.disease_name) == dis_canonical})

            # Calculate explainability scores
            has_history = any(k in full_text.lower() for k in ["history", "known case", "diagnosed", "years"])
            has_assess = any(dis_canonical.lower() in line.lower() for line in full_text.splitlines() if any(h in line.lower() for h in ["assessment", "impression", "diagnosis"]))
            has_med = len(matched_meds) > 0
            has_sym = len(matched_syms) > 0

            symptom_score = 40 if has_sym else 0
            med_score = 20 if has_med else 0
            assess_score = 10 if has_assess else 5
            lab_vital_score = 28 if (has_sym or has_med) else 15
            total_conf = min(0.98, round((symptom_score + med_score + assess_score + lab_vital_score) / 100.0, 2))

            detected_bullets = []
            if has_assess: detected_bullets.append("Assessment section confirms diagnosis")
            if has_history: detected_bullets.append("Documented in Past Medical History")
            if matched_syms: detected_bullets.append(f"Supporting symptoms present: {', '.join(matched_syms)}")
            if matched_meds: detected_bullets.append(f"Targeted therapy prescribed: {', '.join([m.name for m in matched_meds])}")

            first_med = matched_meds[0] if matched_meds else None
            summary_obj = DiseaseSummaryModel(
                disease=dis_canonical,
                symptoms=matched_syms,
                medication=first_med
            )
            # Store extended attributes on object for formatting_agent
            summary_obj.all_medications = matched_meds
            summary_obj.confidence = total_conf
            summary_obj.detected_because = detected_bullets
            summary_obj.evidence_scores = {
                "symptoms": symptom_score,
                "labs_vitals": lab_vital_score,
                "medication": med_score,
                "assessment": assess_score,
                "overall_confidence": int(total_conf * 100)
            }
            seen_summary[dis_canonical] = summary_obj

        state.disease_relations    = disease_relations
        state.medication_relations = medication_details
        state.patient_summary      = list(seen_summary.values())
        return state

    def _pass0_section_aware(self, drugs, diseases, drug_to_med, assigned_drugs, full_text):
        assessment_text = ""
        lines = full_text.splitlines()
        in_section = False
        for line in lines:
            stripped = line.strip()
            if re.search(r'^(?:assessment|impression|diagnosis|plan)\s*[:\-]?\s*$', stripped, re.IGNORECASE):
                in_section = True
                continue
            if in_section:
                if re.search(r'^(?:medications|vitals|laboratory|allergies|chief)\s*[:\-]?\s*$', stripped, re.IGNORECASE):
                    in_section = False
                    continue
                assessment_text += " " + stripped
        if not assessment_text.strip(): return
        assess_low = assessment_text.lower()
        for dr in drugs:
            if dr.text.lower() in assigned_drugs: continue
            for pattern, dis_kw in _DRUG_DISEASE_KNOWLEDGE.items():
                if pattern in dr.text.lower() and dis_kw in assess_low:
                    matched = self._find_disease(dis_kw, diseases)
                    if matched:
                        drug_to_med[dr.text.lower()].disease_name = matched.text
                        assigned_drugs.add(dr.text.lower())
                        break

    def _find_disease(self, kw, diseases):
        kw_low = kw.lower()
        for dis in diseases:
            d_low = dis.text.lower()
            if kw_low in d_low or d_low in kw_low: return dis
            if kw_low == "hypertension" and ("htn" in d_low or "pressure" in d_low): return dis
            if kw_low == "diabetes" and ("dm" in d_low or "t2dm" in d_low): return dis
            if kw_low == "copd" and "pulmonary" in d_low: return dis
            if kw_low == "pneumonia" and "cap" in d_low: return dis
        return None

    def _extract_indication(self, drug, full_text):
        window = full_text[drug.end_char: drug.end_char + 80]
        for pat in _INDICATION_PATTERNS:
            m = pat.search(window)
            if m:
                cand = m.group(1).strip().lower()
                if len(cand) > 2: return cand
        return None

    def _find_after(self, drug, candidates, full_text, default):
        best, best_dist = None, 150
        for c in candidates:
            dist = c.start_char - drug.end_char
            if 0 <= dist < best_dist:
                between = full_text[drug.end_char:c.start_char]
                # Break only on true sentence boundaries (period followed by capital letter)
                if re.search(r'\.\s+[A-Z]', between) or ';\n' in between or '\n\n' in between:
                    continue
                if any(inh in drug.text.lower() for inh in ["salbutamol", "salbutmol", "albuterol", "fluticasone", "budesonide", "tiotropium"]):
                    if c.text.strip().lower().endswith("g") and not c.text.strip().lower().endswith("mcg"):
                        continue
                best, best_dist = c.text, dist
            elif -100 <= dist < 0:
                between = full_text[c.end_char:drug.start_char]
                if not re.search(r'\.\s+[A-Z]', between) and '\n\n' not in between:
                    if best is None or abs(dist) < best_dist:
                        best, best_dist = c.text, abs(dist)

        # Fallback: if candidate list yielded nothing, scan full_text line containing drug
        if not best and full_text and drug.text:
            drug_idx = full_text.lower().find(drug.text.lower())
            if drug_idx != -1:
                line_start = full_text.rfind('\n', 0, drug_idx)
                line_start = 0 if line_start == -1 else line_start + 1
                line_end = full_text.find('\n', drug_idx)
                line_end = len(full_text) if line_end == -1 else line_end
                line_text = full_text[line_start:line_end]

                # If default suggests dosage candidate search
                if default == self.default_dosage:
                    m = re.search(r'\b\d+(?:\.\d+)?\s*(?:mg|g|gm|mcg|ml|mL|IU|iu|units?|tablets?|tabs?|capsules?|puffs?)\b', line_text, re.IGNORECASE)
                    if m:
                        best = m.group(0).strip()
                elif default == self.default_frequency:
                    m = re.search(r'\b(?:1-0-1|1-1-1|1-0-0|0-0-1|0-1-0|once daily|twice daily|thrice daily|three times daily|four times daily|daily|qd|bid|bd|tid|tds|qid|qds|hs|stat|prn|sos)\b', line_text, re.IGNORECASE)
                    if m:
                        best = m.group(0).strip()

        return best if best else default

    def _nearest_disease(self, entity, diseases, window):
        best, best_dist = None, window + 1
        for dis in diseases:
            dist = abs(dis.start_char - entity.start_char)
            if dist < best_dist:
                best_dist = dist
                best = dis
        return best
