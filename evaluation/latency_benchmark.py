import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.connection import Base
from src.orchestrator.coordinator import Coordinator
from src.monitoring.logger import logger

# Isolated SQLite in-memory DB for benchmarking
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)

BENCHMARK_NOTE = """
Patient Alice Smith (SSN: 000-12-3456, MRN: MRN-987654) was seen in clinic today, July 17th, 2026.
She presents with a history of Hypertension and Type 2 Diabetes.
Prescribed Metformin 500mg daily. Discussed daily exercise.
"""

def run_latency_benchmark():
    db = SessionLocal()
    coordinator = Coordinator(db)
    
    # Restrict router extractors to the active set
    coordinator.router.active_extractors = ["scispacy", "biobert", "dosage_frequency"]
    
    print("\n" + "="*50)
    print("STARTING CLINICAL NER PIPELINE CPU LATENCY BENCHMARK")
    print("="*50 + "\n")
    
    # Run pipeline and measure total and stage-specific durations
    start_time = time.time()
    
    # 1. Preprocessing
    pre_start = time.time()
    state = coordinator.preprocessing_agent.process(
        type(coordinator.preprocessing_agent).process.__globals__["PipelineState"](
            session_id="benchmark-session",
            document_id="benchmark-doc",
            text=BENCHMARK_NOTE
        )
    )
    pre_dur = time.time() - pre_start
    print(f"[-] Preprocessing Agent Latency: {pre_dur*1000:.2f} ms")
    
    # 2. PHI Redaction
    phi_start = time.time()
    state = coordinator.phi_redaction_agent.process(state)
    phi_dur = time.time() - phi_start
    print(f"[-] PHI Redaction Agent Latency: {phi_dur*1000:.2f} ms")
    
    # 3. Extraction: SciSpacy (falls back to local CSV)
    sci_start = time.time()
    sci_ext = coordinator.scispacy_agent.extract(state.sentences)
    sci_dur = time.time() - sci_start
    print(f"[-] SciSpacy Extraction Agent Latency: {sci_dur*1000:.2f} ms")
    
    # 4. Extraction: BioBERT (HuggingFace CPU)
    bio_start = time.time()
    bio_ext = coordinator.biobert_agent.extract(state.sentences)
    bio_dur = time.time() - bio_start
    print(f"[-] BioBERT Extraction Agent Latency: {bio_dur*1000:.2f} ms")
    
    # 5. Extraction: Dosage / Frequency
    df_start = time.time()
    df_ext = coordinator.dosage_frequency_agent.extract(state.sentences)
    df_dur = time.time() - df_start
    print(f"[-] Dosage & Frequency Agent Latency: {df_dur*1000:.2f} ms")
    
    # Aggregate extractions
    state.raw_extractions = {
        "scispacy": sci_ext,
        "biobert": bio_ext,
        "dosage_frequency": df_ext
    }
    
    # 6. Aggregation
    agg_start = time.time()
    state = coordinator.aggregation_agent.process(state)
    agg_dur = time.time() - agg_start
    print(f"[-] Aggregation Agent Latency: {agg_dur*1000:.2f} ms")
    
    # 7. Validation
    val_start = time.time()
    state = coordinator.validation_agent.process(state)
    val_dur = time.time() - val_start
    print(f"[-] Validation Agent Latency: {val_dur*1000:.2f} ms")
    
    # 8. Disambiguation (UMLS CSV)
    dis_start = time.time()
    state = coordinator.disambiguation_agent.process(state)
    dis_dur = time.time() - dis_start
    print(f"[-] Disambiguation Agent Latency: {dis_dur*1000:.2f} ms")
    
    # 9. Formatting
    fmt_start = time.time()
    formatted = coordinator.formatting_agent.process(state)
    fmt_dur = time.time() - fmt_start
    print(f"[-] Formatting Agent Latency: {fmt_dur*1000:.2f} ms")
    
    total_dur = time.time() - start_time
    print("\n" + "="*50)
    print(f"TOTAL CLINICAL PIPELINE LATENCY: {total_dur:.4f} seconds")
    print("="*50 + "\n")
    
    # Print Markdown Summary
    print("| Agent Module | Latency (ms) |")
    print("|--------------|--------------|")
    print(f"| Preprocessing | {pre_dur*1000:.1f} |")
    print(f"| PHI Redaction | {phi_dur*1000:.1f} |")
    print(f"| SciSpacy Ext | {sci_dur*1000:.1f} |")
    print(f"| BioBERT Ext  | {bio_dur*1000:.1f} |")
    print(f"| Dosage/Freq  | {df_dur*1000:.1f} |")
    print(f"| Aggregation  | {agg_dur*1000:.1f} |")
    print(f"| Validation   | {val_dur*1000:.1f} |")
    print(f"| Disambiguation| {dis_dur*1000:.1f} |")
    print(f"| Formatting   | {fmt_dur*1000:.1f} |")
    print(f"| **Total**    | **{total_dur*1000:.1f}** |")
    print()

if __name__ == "__main__":
    run_latency_benchmark()
