# Medical NER Agents & System Reference

This document provides a comprehensive reference of all agents, database stores, and helper components used in the Medical Multi-Agent Named Entity Recognition (NER) system, detailing their primary function, purpose, and configuration.

---

## 1. Pipeline Agents

### Preprocessing Agent
- **File**: `src/agents/preprocessing_agent.py`
- **Purpose**: Cleans raw clinical note texts and segments them into sentence-level offsets.
- **How it works**:
  - Normalizes Unicode accents and scrubs double whitespace/tabs using `src/utils/text_cleaning.py`.
  - Splits text into sentences while tracking the absolute character start and end indexes inside the document using `src/utils/tokenizer.py` (with regex abbreviation lookbehinds to prevent breaking on terms like "Dr." or "Mr.").
- **Input**: Raw document text.
- **Output**: Cleaned text and sentence segments with character boundary indices.

### PHI Redaction Agent
- **File**: `src/agents/phi_redaction_agent.py`
- **Purpose**: Scrubs HIPAA Protected Health Information (PHI) to guarantee compliance before downstream ML extraction.
- **How it works**:
  - Matches HIPAA Safe Harbor patterns (such as SSNs, ZIP codes, phone numbers, emails, MRNs, dates, and names) using regex and context keywords.
  - Replaces identified PHI with placeholders (`[REDACTED_NAME]`, `[REDACTED_SSN]`) using end-to-start string slicing to prevent index shifting.
  - Logs audit trails mapping original values to placeholders in the `phi_audit_log` table via `MySQLStore`.
- **Input**: Sentence segments.
- **Output**: Anonymized document text.

### SciSpacy Extraction Agent
- **File**: `src/agents/extraction/scispacy_agent.py`
- **Purpose**: Primary medical extractor for conditions, chemical compounds, and body parts.
- **How it works**:
  - Loads SciSpacy models (e.g. `en_core_sci_sm`).
  - If SciSpacy is absent locally, it falls back to matching text against CSV gazetteers (`disease_list.csv`, `drug_list.csv`, `anatomy_terms.csv`) using word-bounded regex lookups to extract mentions offline.
- **Extracts**: `DISEASE`, `DRUG`, `ANATOMY`.

### BioBERT Extraction Agent
- **File**: `src/agents/extraction/biobert_agent.py`
- **Purpose**: Contextual deep learning transformer model acting as clinical disease/drug extractor.
- **How it works**:
  - Executes BioBERT token classification pipelines on CPU (forced via `device=-1`) or GPU (CUDA `device=0` auto-detected).
  - Supports ONNX Runtime configurations (exported via Optimum) for fast inference on CPU hosts.
- **Extracts**: `DISEASE`, `DRUG`.

### Ollama Extraction Agent
- **File**: `src/agents/extraction/ollama_agent.py`
- **Purpose**: Local Large Language Model (LLM) extractor for unstructured/messy free-text clinical notes.
- **How it works**:
  - Connects to local Ollama services running `llama3.2:3b` with a 120-second timeout budget.
  - Enforces structured JSON output schema mapping.
  - Truncates incoming sentences to a strict `max_llm_calls_per_document` cap (default: 5) to control latency on CPU.
- **Extracts**: `DISEASE`, `DRUG`, `DOSAGE`, `FREQUENCY`, `ANATOMY`.

### Dosage & Frequency Agent
- **File**: `src/agents/extraction/dosage_frequency_agent.py`
- **Purpose**: Fast regex-based pattern matcher for medication prescriptions.
- **How it works**:
  - Uses regular expressions to extract dosages (e.g. "500 mg", "10 ml") and frequency schedules (e.g. "twice daily", "q.h.s.", "every 8 hours").
  - Employs negative lookbehinds (e.g. `(?<!once\s)`) to prevent duplicate matching of sub-terms like `daily` inside composite phrases.
- **Extracts**: `DOSAGE`, `FREQUENCY`.

### Aggregation Agent
- **File**: `src/agents/aggregation_agent.py`
- **Purpose**: Overlap boundary resolver and consensus confidence score aggregator.
- **How it works**:
  - Groups overlapping entity spans from different agents into clusters.
  - Within each cluster, resolves overlapping boundaries by picking the winner based on agent weights (Dosage/Frequency: 2.0, BioBERT: 1.5, SciSpacy: 1.2, Ollama: 1.0) and text length.
  - Computes a unified consensus confidence score, boosting confidence when multiple agents agree on a span.

### Validation Agent
- **File**: `src/agents/validation_agent.py`
- **Purpose**: Standardizes taxonomy and filters entities against validation constraints.
- **How it works**:
  - Maps custom extractor labels to the clinical taxonomy (e.g. `CHEMICAL` -> `DRUG`, `GPE` -> `LOCATION`) using `config/entity_taxonomy.yaml`.
  - Runs checks against minimum length and regex constraints.

### Disambiguation Agent
- **File**: `src/agents/disambiguation_agent.py`
- **Purpose**: Maps clinical entity mentions to unified medical concepts.
- **How it works**:
  - Queries `ChromaStore` for candidates using default `MiniLM` embeddings.
  - Falls back to `Bio_ClinicalBERT` vector searches if similarity is low.
  - Queries REST terminology clients (`RxNormClient`, `SnomedClient`, `UmlsClient`), falling back to local CSV gazetteers if offline.
  - Links matches above the `similarity_threshold` (0.80) to MySQL canonical records.

### Formatting Agent
- **File**: `src/agents/formatting_agent.py`
- **Purpose**: Structures the final response payload.
- **How it works**: Formats session identifiers, metadata, confidence scores, and source extractors into the final JSON output.

---

## 2. Storage & Memory

### MySQL Store
- **File**: `src/memory/mysql_store.py`
- **Purpose**: Persistent database manager (replaces Redis for session state tracking).
- **How it works**: Uses SQLAlchemy to insert documents, sessions, entity mentions, review queue items, and PHI audit trails.

### Chroma Store
- **File**: `src/memory/chroma_store.py`
- **Purpose**: Semantic vector storage for entity linking.
- **How it works**: Generates embeddings via `EmbeddingModel` and performs cosine vector similarity checks against canonical entity text.

---

## 3. Medical Knowledge Base Clients

- **RxNorm Client** (`src/medical_kb/rxnorm_client.py`): Queries NLM RxNorm APIs to resolve drug names to RxCUIs, falling back to local `drug_list.csv` if offline.
- **Snomed Client** (`src/medical_kb/snomed_client.py`): Resolves condition names to SNOMED codes, falling back to `disease_list.csv`.
- **UMLS Client** (`src/medical_kb/umls_client.py`): Resolves anatomical terms to UMLS CUIs, falling back to `anatomy_terms.csv`.
