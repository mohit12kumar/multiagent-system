import sys
import os
sys.path.insert(0, os.path.abspath("."))

import time
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.connection import Base
from backend.orchestrator.coordinator import Coordinator


# Isolated SQLite in-memory DB for clean benchmark execution
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)

# ---------------------------------------------------------------------------
# Synthetic Dataset Generation: 50 Healthy Cases + 50 Abnormal Cases
# ---------------------------------------------------------------------------

HEALTHY_TEMPLATES = [
    "Patient {name}, {age}-year-old {gender}, presenting for routine annual physical examination. Vital signs: BP 118/76 mmHg, HR 72 bpm, Temp 98.6F, SpO2 99% on room air. Physical exam unremarkable. No active medical complaints, no chronic diseases, and no active prescriptions.",
    "Patient {name}, {age}-year-old {gender}, seen for routine wellness check. Patient reports feeling well with normal energy and regular sleep. Laboratory results within normal limits: Fasting blood glucose 88 mg/dL, HbA1c 5.2%, Lipid panel normal. No medications prescribed.",
    "Patient {name}, {age}-year-old {gender}, presenting for occupational health baseline screening. Heart sounds normal S1/S2, lungs clear to auscultation bilaterally. Abdomen soft, non-tender. Patient takes no daily medications and has no known drug allergies.",
    "Patient {name}, {age}-year-old {gender}, presents for pre-employment physical. All organ systems reviewed and negative for pathology. BMI 22.4. Patient maintains active exercise regimen. No medical conditions reported.",
    "Patient {name}, {age}-year-old {gender}, routine follow-up visit. Physical exam completely normal. Patient asymptomatic. No diagnoses recorded and no drug therapy indicated."
]

ABNORMAL_TEMPLATES = [
    "Patient {name}, {age}-year-old {gender}, with history of Type 2 Diabetes Mellitus and Essential Hypertension. Patient reports fatigue and morning headache. BP 154/92 mmHg, Fasting Glucose 198 mg/dL. Prescribed Metformin 1000mg PO BID and Lisinopril 20mg PO daily.",
    "Patient {name}, {age}-year-old {gender}, presenting with acute Asthma exacerbation and wheezing. Patient exhibits shortness of breath and cough. Prescribed Albuterol 90mcg inhalation 2 puffs every 4 hours as needed and Prednisone 40mg PO daily for 5 days.",
    "Patient {name}, {age}-year-old {gender}, known case of Coronary Artery Disease and Hyperlipidemia. Patient complains of intermittent exertional chest discomfort. Prescribed Atorvastatin 40mg PO daily, Aspirin 81mg PO daily, and Nitroglycerin 0.4mg SL PRN for chest pain.",
    "Patient {name}, {age}-year-old {gender}, diagnosed with Chronic Kidney Disease Stage 3 and Secondary Hyperparathyroidism. eGFR 42 mL/min. Prescribed Losartan 50mg PO daily. Advised low sodium and low potassium diet.",
    "Patient {name}, {age}-year-old {gender}, presenting with Major Depressive Disorder and Generalized Anxiety. Patient reports persistent low mood and insomnia. Prescribed Sertraline 50mg PO daily and Zolpidem 5mg PO at bedtime.",
    "Patient {name}, {age}-year-old {gender}, history of Rheumatoid Arthritis and Osteoarthritis. Patient experiences morning joint stiffness and knee swelling. Prescribed Methotrexate 15mg PO weekly and Folic Acid 1mg PO daily.",
    "Patient {name}, {age}-year-old {gender}, presenting with Gastroesophageal Reflux Disease (GERD) and Gastritis. Patient complains of epigastric burning and acid regurgitation. Prescribed Omeprazole 20mg PO daily before breakfast.",
    "Patient {name}, {age}-year-old {gender}, diagnosed with Hypothyroidism. TSH elevated at 8.4 mIU/L. Patient notes mild weight gain and sluggishness. Prescribed Levothyroxine 75mcg PO daily in the morning.",
    "Patient {name}, {age}-year-old {gender}, presenting with Atrial Fibrillation and Chronic Heart Failure. Patient experiences palpitations and bilateral lower extremity edema. Prescribed Apixaban 5mg PO BID and Furosemide 40mg PO daily.",
    "Patient {name}, {age}-year-old {gender}, presenting with Pneumonia and Fever. Chest X-ray reveals right lower lobe infiltrate. Prescribed Azithromycin 500mg PO day 1 then 250mg PO daily for 4 days."
]

FIRST_NAMES = ["John", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "William", "Linda", "David", "Elizabeth", "James", "Barbara", "Joseph", "Susan", "Thomas", "Jessica"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]

def generate_100_cases():
    cases = []
    
    # 50 Healthy Cases
    for i in range(1, 51):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        age = random.randint(20, 65)
        gender = random.choice(["male", "female"])
        template = random.choice(HEALTHY_TEMPLATES)
        text = template.format(name=name, age=age, gender=gender)
        cases.append({
            "case_id": f"HEALTHY-{i:03d}",
            "category": "Healthy / Wellness",
            "is_healthy": True,
            "text": text
        })
        
    # 50 Abnormal Cases
    for i in range(1, 51):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        age = random.randint(35, 80)
        gender = random.choice(["male", "female"])
        template = random.choice(ABNORMAL_TEMPLATES)
        text = template.format(name=name, age=age, gender=gender)
        cases.append({
            "case_id": f"ABNORMAL-{i:03d}",
            "category": "Abnormal / Pathological",
            "is_healthy": False,
            "text": text
        })
        
    return cases

# ---------------------------------------------------------------------------
# Benchmark Runner
# ---------------------------------------------------------------------------

def run_benchmark():
    print("=" * 65)
    print(" STARTING 100-CASE CLINICAL MULTI-AGENT PIPELINE EVALUATION")
    print("=" * 65 + "\n")

    cases = generate_100_cases()
    db = SessionLocal()
    coordinator = Coordinator(db)

    results = []
    start_all = time.time()

    healthy_processed = 0
    healthy_false_positives = 0
    abnormal_processed = 0
    abnormal_entities_extracted = 0
    abnormal_relations_extracted = 0

    total_latency_healthy = 0.0
    total_latency_abnormal = 0.0

    print(f"[*] Processing 100 Clinical Cases (50 Healthy, 50 Abnormal)...\n")


    for idx, c in enumerate(cases, 1):
        t0 = time.time()
        try:
            res = coordinator.run_pipeline(document_content=c["text"], user_id=f"user_{idx}")
            latency = time.time() - t0
            status = res.get("status", "UNKNOWN")
            
            entities = res.get("entities", [])
            relations = res.get("relations", [])
            patient_summary = res.get("patient_summary", [])
            
            if c["is_healthy"]:
                healthy_processed += 1
                total_latency_healthy += latency
                # For healthy cases, entities count should be low/zero for diseases
                dis_entities = [e for e in entities if e.get("type") in ("DISEASE", "CONDITION")]
                if len(dis_entities) > 0:
                    healthy_false_positives += 1
            else:
                abnormal_processed += 1
                total_latency_abnormal += latency
                abnormal_entities_extracted += len(entities)
                abnormal_relations_extracted += len(relations)

            results.append({
                "case_id": c["case_id"],
                "category": c["category"],
                "is_healthy": c["is_healthy"],
                "latency_sec": round(latency, 3),
                "status": status,
                "entity_count": len(entities),
                "relation_count": len(relations),
                "summary_count": len(patient_summary)
            })

            if idx % 10 == 0 or idx == 100:
                print(f" Progress: [{idx:3d}/100] cases processed... (Last Latency: {latency:.2f}s, Status: {status})")

        except Exception as e:
            latency = time.time() - t0
            results.append({
                "case_id": c["case_id"],
                "category": c["category"],
                "is_healthy": c["is_healthy"],
                "latency_sec": round(latency, 3),
                "status": "FAILED",
                "error": str(e)
            })
            print(f" [!] Case {c['case_id']} failed: {e}")

    total_time = time.time() - start_all

    # ---------------------------------------------------------------------------
    # Statistics & Metric Aggregations
    # ---------------------------------------------------------------------------
    avg_latency_all = total_time / len(cases)
    avg_latency_healthy = total_latency_healthy / max(healthy_processed, 1)
    avg_latency_abnormal = total_latency_abnormal / max(abnormal_processed, 1)

    completed_count = sum(1 for r in results if r["status"] in ("COMPLETED", "PARTIAL_SUCCESS"))
    success_rate = (completed_count / len(cases)) * 100.0

    healthy_specificity = ((healthy_processed - healthy_false_positives) / max(healthy_processed, 1)) * 100.0

    summary_data = {
        "total_cases_tested": len(cases),
        "total_execution_time_sec": round(total_time, 2),
        "overall_success_rate_percent": round(success_rate, 1),
        "healthy_cases": {
            "count": healthy_processed,
            "avg_latency_sec": round(avg_latency_healthy, 3),
            "false_positive_cases": healthy_false_positives,
            "specificity_percent": round(healthy_specificity, 1)
        },
        "abnormal_cases": {
            "count": abnormal_processed,
            "avg_latency_sec": round(avg_latency_abnormal, 3),
            "total_entities_extracted": abnormal_entities_extracted,
            "avg_entities_per_case": round(abnormal_entities_extracted / max(abnormal_processed, 1), 1),
            "total_relations_extracted": abnormal_relations_extracted,
            "avg_relations_per_case": round(abnormal_relations_extracted / max(abnormal_processed, 1), 1)
        },
        "results": results
    }

    # Save JSON metrics
    with open("evaluation_100_cases_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print("\n" + "=" * 65)
    print(" EVALUATION SUMMARY METRICS")

    print("=" * 65)
    print(f" - Total Cases Evaluated   : {len(cases)}")
    print(f" - Total Benchmark Time   : {total_time:.2f} seconds")
    print(f" - Pipeline Success Rate   : {success_rate:.1f}%")
    print(f" - Healthy Case Specificity: {healthy_specificity:.1f}%")
    print(f" - Avg Latency (Healthy)   : {avg_latency_healthy:.3f}s")
    print(f" - Avg Latency (Abnormal)  : {avg_latency_abnormal:.3f}s")
    print(f" - Avg Entities/Abnormal   : {abnormal_entities_extracted / max(abnormal_processed, 1):.1f}")
    print(f" - Avg Relations/Abnormal  : {abnormal_relations_extracted / max(abnormal_processed, 1):.1f}")
    print("=" * 65 + "\n")

    return summary_data

if __name__ == "__main__":
    run_benchmark()
