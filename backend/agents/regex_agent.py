import re
from typing import Dict, Any, List, Optional
from backend.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class RegexAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.agent_name = "regex"

        self.patterns = {
            # ── Dosage ───────────────────────────────────────────────────
            # Match drug dosages (mg, g, mcg, ml, IU, units) but NOT lab values (mg/dL)
            "DOSAGE": [
                r'\b\d+(?:\.\d+)?\s*(?:mg|g|mcg|ug|ml|IU|units?|pills?|tablets?|capsules?|puff|puffs|drops)\b(?!\s*/\s*(?:dL|L|mL))'
            ],

            # ── Frequency ────────────────────────────────────────────────
            "FREQUENCY": [
                # Numeric forms: '1 time daily', '3 times a day'
                r'(?i)\b(?:1 time|2 times|3 times|4 times|5 times|6 times)\s+(?:daily|a day|per day|weekly|monthly)\b',
                # Word forms with spelled-out numbers
                r'(?i)\b(?:once|twice|three times|four times|five times|six times)\s+(?:daily|a day|per day|weekly|monthly|a week|per week|a month|per month)\b',
                # Time-of-day patterns
                r'(?i)\b(?:every\s+night|every\s+morning|every\s+evening|at\s+bedtime|at\s+night|at\s+breakfast|in\s+the\s+morning|in\s+the\s+evening)\b',
                # Interval patterns: 'every 8 hours', 'every other day'
                r'(?i)\bevery\s+(?:\d+\s+hours?|other\s+day|alternate\s+day)\b',
                # Latin/short abbreviations (TDS, TID, BD, QID, PRN, SOS, etc.)
                r'(?i)\b(?:once daily|twice daily|thrice daily|three times daily|four times daily|daily|qd|bid|bd|tid|tds|qid|prn|sos|as needed|as required)\b'
            ],

            # ── Duration ─────────────────────────────────────────────────
            "DURATION": [
                # Numeric: 'for 7 days', '2 weeks', etc.
                r'(?i)\b(?:for\s+)?\d+\s+(?:days?|weeks?|months?|years?)\b',
                # Word-form: 'for one month', 'for two weeks', 'after one month'
                r'(?i)\b(?:for|after)\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:days?|weeks?|months?|years?)\b'
            ],

            # ── Route ────────────────────────────────────────────────────
            "ROUTE": [
                r'(?i)\b(?:orally|oral|by mouth|IV|intravenous(?:ly)?|subcutaneous(?:ly)?|topical(?:ly)?|inhalation|inhaled|sublingual(?:ly)?|rectal(?:ly)?|intramuscular(?:ly)?|IM|SC)\b'
            ],

            # ── Date ─────────────────────────────────────────────────────
            "DATE": [
                r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})\b'
            ],

            # ── Time ─────────────────────────────────────────────────────
            "TIME": [
                r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b'
            ],

            # ── Drug ─────────────────────────────────────────────────────
            "DRUG": [
                # Pharmacology suffix patterns
                r'(?i)\b[a-z]{3,20}(?:cillin|mycin|statin|olol|pril|sartan|prazole|dipine|gliptin|gliflozin|tidine|thromycin|cycline|xacin|terol|dronate|zepam|triptan|nidazole|zolam|sone|lamide|mab|nib)\b',
                # Vitamin supplements — D3, B12, C, etc. (must come before generic drug DB)
                r'(?i)\bvitamin\s+[a-dA-D][0-9]?\b',
                r'(?i)\b(?:cholecalciferol|ergocalciferol|calcitriol|cyanocobalamin|methylcobalamin)\b',
                r'(?i)\b(?:calcium\s+carbonate|calcium\s+citrate|ferrous\s+(?:sulfate|gluconate|fumarate))\b',
                # Large explicit database of known drugs
                r'(?i)\b(?:amlodipine|lisinopril|losartan|metformin|insulin|albuterol|fluticasone|'
                r'amoxicillin|azithromycin|ciprofloxacin|sertraline|atorvastatin|ibuprofen|'
                r'acetaminophen|paracetamol|panadol|crocin|calpol|aspirin|naproxen|'
                r'omeprazole|pantoprazole|ranitidine|famotidine|doxycycline|ceftriaxone|'
                r'cefuroxime|cephalexin|augmentin|metronidazole|gabapentin|pregabalin|'
                r'levothyroxine|furosemide|torsemide|hydrochlorothiazide|spironolactone|'
                r'warfarin|apixaban|rivaroxaban|clopidogrel|prednisone|prednisolone|'
                r'dexamethasone|salbutamol|montelukast|tiotropium|budesonide|atenolol|'
                r'metoprolol|carvedilol|rosuvastatin|simvastatin|pravastatin|sitagliptin|'
                r'empagliflozin|duloxetine|fluoxetine|escitalopram|citalopram|alprazolam|'
                r'lorazepam|tramadol|diclofenac|allopurinol|colchicine|tamsulosin|'
                r'finasteride|sildenafil|tadalafil|alendronate|risedronate|valsartan|'
                r'enalapril|levofloxacin|indapamide|chlorthalidone|methylprednisolone)\b'
            ],

            # ── Lab Values ───────────────────────────────────────────────
            # Capture lab results like "Serum Creatinine: 2.2 mg/dL" as LAB_VALUE entities
            "LAB_VALUE": [
                r'(?i)\b(?:serum\s+creatinine|creatinine|bun|blood\s+urea\s+nitrogen|'
                r'ldl|hdl|total\s+cholesterol|triglycerides|hba1c|blood\s+glucose|fasting\s+glucose|'
                r'random\s+glucose|glucose|hemoglobin|wbc|platelets|sodium|potassium|calcium|tsh|egfr|gfr|'
                r'alt|ast|bilirubin|albumin|troponin|bnp|natriuretic|ejection\s+fraction|ef|st\s+elevation)\s*[:\s]+\d+(?:\.\d+)?\s*(?:mg/dL|mmol/L|g/dL|IU/L|mEq/L|%|U/L|ng/mL|pg/mL)?\b'
            ],

            # ── Clinical Symptoms ─────────────────────────────────────────
            "SYMPTOM": [
                r'(?i)\b(?:increased\s+thirst|frequent\s+urination|excessive\s+thirst|excessive\s+urination|'
                r'polydipsia|polyuria|polyphagia|fatigue|weakness|shortness\s+of\s+breath|dyspnea|orthopnea|'
                r'pedal\s+edema|leg\s+swelling|chest\s+pain|dizziness|nausea|vomiting|fever|cough|sweating|diaphoresis)\b'
            ],

            # ── Critical Disease Extractions ─────────────────────────────
            "DISEASE": [
                r'(?i)\b(?:acute\s+myocardial\s+infarction|acute\s+mi|stemi|myocardial\s+infarction)\b',
                r'(?i)\b(?:congestive\s+heart\s+failure|heart\s+failure|chf)\b',
                r'(?i)\b(?:hyperkalemia|hyperlipidaemia|hyperlipidemia)\b',
                r'(?i)\b(?:pulmonary\s+edema|pulmonary\s+oedema)\b'
            ]
        }

    def extract(self, sentences: List[dict], full_text: Optional[str] = None) -> List[EntityMentionModel]:
        logger.info("Regex Agent extracting dosage, frequency, duration, route, dates, times, drugs")
        entities = []
        if not full_text:
            full_text = " ".join([s.get("text", "") for s in sentences]) if sentences else ""
        if not full_text:
            return entities

        extracted_spans = set()

        for etype, pattern_list in self.patterns.items():
            confidence = 0.96 if etype in ("DOSAGE", "FREQUENCY", "DURATION", "ROUTE", "DRUG") else 0.88
            for pat in pattern_list:
                for match in re.finditer(pat, full_text):
                    span_key = (match.start(), match.end(), etype)
                    if span_key not in extracted_spans:
                        # Skip LAB_VALUE patterns from polluting DOSAGE (mg/dL values)
                        extracted_spans.add(span_key)
                        entities.append(EntityMentionModel(
                            text=match.group(0).strip(),
                            type=etype,
                            start_char=match.start(),
                            end_char=match.end(),
                            confidence=confidence,
                            source_agents=[self.agent_name]
                        ))

        logger.info(f"Regex Agent extracted {len(entities)} entities")
        return entities
