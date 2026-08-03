# 🧠 Enterprise Clinical Intelligence & Multi-Agent NLP Platform

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF4B4B?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3--70B-FF6F00?style=for-the-badge)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20RAG-FF4500?style=for-the-badge)
![FHIR R4](https://img.shields.io/badge/FHIR-R4%20Standard-E65100?style=for-the-badge)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Tests Pass](https://img.shields.io/badge/Pytest-200%2B%20Passed-2EA44F?style=for-the-badge&logo=pytest&logoColor=white)

> **Enterprise-Grade Clinical Decision Support, Medical NLP & Autonomous Research Platform (v20.0)** — Powered by Groq (Llama 3.3-70B), LangGraph, SciSpaCy, BioBERT, ChromaDB Vector RAG, FHIR R4 Engine, MySQL 8.0, and React 18 + FastAPI.

---

## 🌟 Key Capabilities & Highlights

| Feature | Description |
|---|---|
| 🤖 **20-Agent AI Pipeline** | Specialized agents spanning PHI redaction, section detection, multi-model NER, universal medication parsing, clinical consistency, RAG grounding, and JSON formatting |
| 🔬 **LangGraph Medical Research Sub-Agent** | Autonomous literature synthesis agent integrating live PubMed search, MedQuAD vector RAG knowledge base, voice query STT (Whisper), and audio summary TTS |
| 💊 **Universal Medication Parser v20.0** | Sub-millisecond engine parsing global prescription formats (doses, frequencies, routes, timings, durations, PRN flags, 1-0-1 numeric schedules, Nebulization) |
| 🔤 **Human-Readable Medical Abbreviation Expansions** | Auto-expands clinical abbreviations into plain text: `OD (Once Daily)`, `BID (Twice Daily)`, `HS (At Bedtime / Night)`, `TDS (Three Times Daily)`, `QID (Four Times Daily)`, `PRN (As Needed)`, `AC (Before Meals)`, `PC (After Meals)` |
| 🩺 **Multi-Condition Medical History Parser** | Intelligently splits composite past history blocks (e.g. `Type 2 Diabetes Mellitus Essential Hypertension Hyperlipidemia Chronic Kidney Disease Stage III`) into distinct individual condition entries |
| 🏥 **FHIR R4 Interoperability Engine** | Seamless conversion of extracted clinical entities into standardized HL7 FHIR R4 bundles (Patient, Encounter, Condition, MedicationRequest, Observation) |
| 🔒 **Cryptographic SHA-256 Audit Chaining** | Tamper-evident ledger storing hash-chained logs (`previous_hash` & `current_hash`) for HIPAA compliance and medico-legal auditability |
| 🛡️ **PHI & Secret Sanitization** | Real-time scrubbing of phone numbers, emails, SSNs, Aadhaar, MRNs, JWTs, and API keys from logs and LLM payloads |
| 🟢 **NKDA Visual Verification Engine** | Highlights `NKDA — No Known Drug Allergies` in green badges (`#6EFFD4`, border `rgba(0,227,150,0.3)`) for immediate clinical safety verification |
| 🚨 **Contraindications & Safety Audits** | Automated safety rules (Metformin + eGFR <30 for Lactic Acidosis, Losartan + K+ >5.5 for Arrhythmia, duplicate drug therapy detection) |
| 📊 **Multi-Organ Risk Engine** | Real-time predictive risk stratification across Cardiac, Renal, Respiratory, Stroke, and Multi-System Organ Failure (MSOF) vectors |
| 🧪 **RxNorm & Brand Normalization** | Built-in mapper for brand-to-generic drug aliases (`PCM`, `Crocin`, `Tylenol`, `Ecosprin`, `Glucophage`, `Coumadin`, `Norvasc`, `Lasix`, `Augmentin`) |
| ⚡ **Thread-Safe Model Execution** | Concurrent `InferencePool` acquiring dedicated SpaCy/SciSpaCy model instances to prevent segmentation faults under heavy load |
| 📚 **ChromaDB Vector RAG Grounding** | Validates clinical recommendations against indexed medical evidence guidelines (KDIGO, ACC/AHA, ATS/IDSA) with thread-safe locks |
| 👨‍⚕️ **Physician Review Workspace** | Doctor review queue allowing clinicians to audit, edit, approve, reject, or batch-process extracted entity mentions |
| 📄 **Medico-Legal PDF Generator** | Generates exportable clinical PDF reports with QR verification codes, cryptographic report hashes, and digital signature blocks |
| 📈 **Prometheus Observability & Health** | Exportable OpenMetrics at `/api/metrics`, deep health checks at `/api/health`, and real-time database connection pool monitoring |

---

## 🏗️ System Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │           Patient / Doctor Web Interface               │
                               │                (React 18 + Vite)                       │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │ REST / JWT Auth
                                                          ▼
                               ┌────────────────────────────────────────────────────────┐
                               │                 FastAPI REST Backend                   │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                    ┌─────────────────────────────────────┴─────────────────────────────────────┐
                    ▼                                                                           ▼
┌───────────────────────────────────────┐                                   ┌───────────────────────────────────────┐
│       20-Agent AI Orchestrator        │                                   │ LangGraph Medical Research Sub-Agent  │
│  (Preprocessing -> NER -> Reasoning)  │                                   │   (Literature Synthesis & Audio QA)   │
└───────────────────┬───────────────────┘                                   └───────────────────┬───────────────────┘
                    │                                                                           │
   ┌────────────────┼────────────────┐                                         ┌────────────────┼────────────────┐
   ▼                ▼                ▼                                         ▼                ▼                ▼
┌───────┐      ┌─────────┐      ┌──────────┐                             ┌──────────┐     ┌──────────┐     ┌──────────┐
│ SpaCy │      │ BioBERT │      │ Groq LLM │                             │  PubMed  │     │ MedQuAD  │     │ Whisper  │
│ Pool  │      │ NER     │      │ Llama3.3 │                             │ Live API │     │ VectorKB │     │ STT/TTS  │
└───────┘      └─────────┘      └──────────┘                             └──────────┘     └──────────┘     └──────────┘
```

---

## 📁 Repository Architecture

```
multiagent_system/
│
├── backend/                             # FastAPI Enterprise Backend
│   ├── agents/                          # 20 Autonomous Specialized Clinical Agents
│   │   ├── phi_redaction_agent.py       # Stage 1: HIPAA PHI & Secret Sanitization
│   │   ├── section_detector_agent.py    # Stage 2: Clinical section segmentation (HPI, Labs, Meds, Plan)
│   │   ├── spell_correction_agent.py    # RapidFuzz clinical spell checker
│   │   ├── abbreviation_agent.py        # Medical shorthand expansion (HTN -> Hypertension)
│   │   ├── spacy_agent.py               # SpaCy baseline NER & sentence splitter (Thread-safe pool)
│   │   ├── scispacy_agent.py            # SciSpaCy biomedical NER (Thread-safe pool)
│   │   ├── biobert_agent.py             # BioBERT Transformer NER
│   │   ├── regex_agent.py               # Expanded Regex entity extractor (Diseases, Drugs, Symptoms)
│   │   ├── medication_parser.py         # Universal Medication Parsing Engine (v20.0)
│   │   ├── llm_clinical_agent.py        # Groq Llama-3.3-70b contextual extraction
│   │   ├── aggregation_agent.py         # Overlap resolution & weighted consensus aggregation
│   │   ├── validation_agent.py          # Taxonomy rules & ALLERGY classification
│   │   ├── clinical_consistency_agent.py# Multi-source evidence cross-validator
│   │   ├── relation_extraction_agent.py # Disease-Medication-Symptom indication mapping
│   │   ├── medication_safety_agent.py   # Duplicate drug therapy & max dosage safety checker
│   │   ├── disambiguation_agent.py      # Vector normalization & entity resolution
│   │   ├── contraindication_agent.py    # Renal/hepatic/cardiac disease-drug checks
│   │   ├── lab_interpretation_agent.py  # Reference range evaluation & eGFR stage validator
│   │   ├── rag_agent.py                 # Vector database RAG grounding & guideline citations
│   │   ├── formatting_agent.py          # Grouped condition card JSON shaping & quality scoring
│   │   └── human_review_agent.py        # Doctor review queue CRUD operations
│   │
│   ├── engines/                         # Core Domain Intelligence & Security Engines
│   │   ├── security_engine.py           # Access control, role permissions & PHI guardrails
│   │   ├── audit_engine.py              # SHA-256 cryptographic audit trail ledger
│   │   ├── fhir_engine.py               # HL7 FHIR R4 resource transformation
│   │   ├── predictive_risk_engine.py    # Multi-organ mortality & risk scoring
│   │   ├── lab_vital_trend_engine.py    # Temporal trends for laboratory & vital signs
│   │   ├── unit_normalization_engine.py # Clinical unit standardization (mg/dL, mmol/L)
│   │   ├── terminology_service.py       # RxNorm, ICD-10-CM & SNOMED CT mapper
│   │   ├── clinical_graph_engine.py     # Knowledge graph representation of entities
│   │   ├── disease_engine.py            # Disease severity evaluation engine
│   │   └── evidence_engine.py           # Weighted evidence scoring algorithm
│   │
│   ├── utils/                           # Prescription Engine & PDF Utilities
│   │   ├── medication_regex.py          # Prescription regex library (1-0-1, q6h, timing terms)
│   │   ├── medication_normalizer.py     # Prescription normalizer & Nebulization route mapper
│   │   ├── pdf_generator.py             # Medico-legal clinical PDF report generator
│   │   └── text_cleaning.py             # String pre-processing & sanitization
│   │
│   └── database/                        # Database Layer
│       ├── connection.py                # SQLAlchemy engine & session factory
│       ├── models.py                    # ORM Models (AuditLog with hash chaining, User, ReviewQueue)
│       └── mysql_store.py               # High-level database operations
│
├── medical-research-agent/              # Autonomous LangGraph Research Agent Subsystem
│   ├── agents/                          # LangGraph state machine node handlers
│   ├── tools/                           # Research Tooling (PubMed API & MedQuAD RAG)
│   ├── graph.py                         # LangGraph state machine definition
│   ├── server.py                        # Standalone FastAPI server with JWT, STT & TTS
│   └── ingest.py                        # MedQuAD dataset ingestion script
│
├── frontend/                            # React 18 + Vite Web Application
│   ├── src/
│   │   ├── components/                  # UI Components (Navbar, ExtractionCards, ResearchModal)
│   │   ├── pages/                       # Login, PatientDashboard, DoctorDashboard, ReviewQueuePage
│   │   └── index.css                    # Dark glassmorphic medical design system
│   └── vite.config.js                   # Vite dev server & proxy settings
│
├── tests/                               # Comprehensive Automated Test Suite
│   ├── test_medication_parser.py        # Universal Prescription Test Suite (10/10 Passed)
│   ├── test_multiagent_system.py        # End-to-End Pipeline Integration Test Suite (2/2 Passed)
│   └── test_phase1_security.py          # Auth, RBAC & Security Test Suite
│
├── .env.example                         # Environment variable template
├── requirements.txt                     # Backend Python dependencies
└── run_all.ps1                          # Unified launcher script (PowerShell)
```

---

## 🤖 20-Agent AI Pipeline Architecture

The core pipeline processes raw clinical text through 20 sequential and parallel agents:

```
Unstructured Note ➔ [1. PHI Redaction] ➔ [2. Section Detector] ➔ [3. Spell Correction] ➔ [4. Abbreviation Expansion]
                                                                                               │
   ┌───────────────────────────────────────────────────────────────────────────────────────────┘
   ▼
[Parallel Extraction Pool]
  ├── 5. SpaCy NLP Agent (Sentence & POS Parsing)
  ├── 6. SciSpaCy Agent (Biomedical NER)
  ├── 7. BioBERT Agent (Disease Transformer NER)
  ├── 8. Regex Entity Agent (Dosage/Frequency/Route Engine)
  ├── 9. Universal Medication Parser v20.0
  └── 10. Groq Clinical LLM Agent (Llama 3.3-70B Contextual NER)
   │
   ▼
[11. Consensus Aggregation Agent] (Weighted multi-agent voting)
   │
   ▼
[12. Validation Agent] ➔ [13. Clinical Consistency Agent] ➔ [14. Relation Extraction Agent]
   │
   ▼
[15. Medication Safety Agent] ➔ [16. Disambiguation Agent] ➔ [17. Contraindication Agent]
   │
   ▼
[18. Lab Interpretation Agent] ➔ [19. RAG Grounding Agent] ➔ [20. Formatting & Quality Agent]
   │
   ▼
[MySQL Audit Store & Doctor Review Queue]
```

---

## 🔬 Autonomous LangGraph Medical Research Agent

Located in `medical-research-agent/`, this standalone multi-agent research subsystem synthesizes medical literature for complex questions:

### LangGraph Agent Node Workflow
1. **Supervisor**: Deterministic state machine supervisor controlling transitions.
2. **Planner**: Deconstructs complex queries into targeted sub-questions.
3. **PubMed Researcher**: Searches NCBI PubMed live database for latest peer-reviewed studies.
4. **Local KB Researcher**: Queries local vector database containing indexed MedQuAD medical Q&As.
5. **Synthesizer**: Combines evidence into structured draft answers with inline citations.
6. **Verifier**: Validates facts against citations, enforcing zero-hallucination guardrails.
7. **Reporter**: Generates final research summary, formatted references, and disclaimer.

### Voice Integration (STT / TTS)
- **Speech-to-Text (STT)**: Uses Groq Whisper API (`whisper-large-v3`) for voice query transcription.
- **Text-to-Speech (TTS)**: Converts generated medical findings into spoken audio output via `gTTS`.

---

## 💊 Universal Medication Parser v20.0

The high-speed medication parsing engine (`backend/agents/medication_parser.py`) converts unstructured prescriptions into normalized clinical data structures:

```text
• "Ceftriaxone 1 g IV every 24 hours for 5 days"
  ➔ Name: Ceftriaxone | Dose: 1 g | Route: IV | Freq: OD (Once Daily) | Duration: For 5 days

• "Azithromycin 500 mg PO OD for 5 days"
  ➔ Name: Azithromycin | Dose: 500 mg | Route: PO | Freq: OD (Once Daily) | Duration: For 5 days

• "Paracetamol 650 mg PO every 6 hours as needed for Fever"
  ➔ Name: Paracetamol | Dose: 650 mg | Route: PO | Freq: QID (Four Times Daily) | PRN: True | Indication: Fever

• "Salbutamol inhaler 2 puffs every 6 hours PRN breathlessness"
  ➔ Name: Salbutamol | Dose: 2 puffs | Route: Inhalation | Freq: QID (Four Times Daily) | PRN: True | Indication: Breathlessness

• "Budesonide 0.5 mg nebulization BD"
  ➔ Name: Budesonide | Dose: 0.5 mg | Route: Nebulization | Freq: BID (Twice Daily)

• "Metformin 500 mg PO BID after meals"
  ➔ Name: Metformin | Dose: 500 mg | Route: PO | Freq: BID (Twice Daily) | Timing: After meals (PC)

• "Atorvastatin 40 mg PO HS"
  ➔ Name: Atorvastatin | Dose: 40 mg | Route: PO | Freq: HS (At Bedtime / Night) | Timing: Bedtime (HS)
```

---

## ⚙️ Prerequisites & Environment Setup

### Requirements

| Dependency | Minimum Version | Recommended |
|---|---|---|
| **Python** | 3.10+ | 3.11 / 3.12 |
| **Node.js** | 18.0+ | 20.0+ |
| **npm** | 9.0+ | 10.0+ |
| **MySQL** | 8.0+ | 8.0 local server |
| **Groq API Key** | - | Free key from [console.groq.com](https://console.groq.com) |

---

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/mohit12kumar/multiagent-system.git
cd multiagent-system
```

#### 2. Configure Environment Variables
Copy `.env.example` to `.env`:

```powershell
# Windows PowerShell
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Set `.env` variables:
```env
# Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=clinical_multiagent

# Groq LLM API Key
GROQ_API_KEY=gsk_your_groq_api_key_here

# JWT Authentication Secret
SECRET_KEY=super_secret_jwt_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

#### 3. Initialize MySQL Database
```sql
CREATE DATABASE clinical_multiagent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 4. Python Virtual Environment Setup
```powershell
# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r medical-research-agent/requirements.txt
```

#### 5. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## 🚀 Running the System

### Option A: Unified One-Command Launcher (Windows PowerShell)

```powershell
.\run_all.ps1
```

Launches FastAPI backend service and React Vite frontend concurrently.

### Option B: Manual Execution

#### 1. Main FastAPI Backend Server
```powershell
.\venv\Scripts\activate
uvicorn backend.api.routes:app --reload --host 0.0.0.0 --port 8000
```

#### 2. LangGraph Medical Research Agent Server (Optional)
```powershell
.\venv\Scripts\activate
python medical-research-agent/server.py
```

#### 3. React Frontend Web App
```bash
cd frontend
npm run dev
```

---

## 🌐 Access Points & Port Mapping

| Service / App | URL | Description |
|---|---|---|
| 🎨 **React Web Application** | `http://localhost:5173` | Clinical Extractor & Doctor Review Dashboard |
| ⚡ **FastAPI Backend API** | `http://localhost:8000` | Main REST API service |
| 📖 **Swagger OpenAPI Docs** | `http://localhost:8000/docs` | Interactive API endpoints documentation |
| 🔬 **Research Agent API** | `http://localhost:8001` | LangGraph medical literature research API |
| 📊 **Prometheus Metrics** | `http://localhost:8000/api/metrics` | Real-time OpenMetrics stream |
| 🩺 **System Health Check** | `http://localhost:8000/api/health` | Deep health & pool status monitor |

---

## 🔑 Default Demo Accounts

| Role | Username | Password | Privileges & Workspaces |
|---|---|---|---|
| 👨‍⚕️ **Doctor** | `dr_jenkins` | `password123` | Doctor Review Queue, Entity Approval/Editing, Patient Analytics |
| 👤 **Patient** | `patient_john` | `password123` | Note Extraction, Personal Health Records, PDF Report Generator |

---

## 🧪 Testing & Verification

```powershell
# Run Universal Medication Parser test suite (10/10 Passed)
.\venv\Scripts\python.exe -m pytest tests/test_medication_parser.py -v

# Run End-to-End Multi-Agent System test suite (2/2 Passed)
.\venv\Scripts\python.exe -m pytest tests/test_multiagent_system.py -v

# Run Frontend production build check
npm --prefix frontend run build
```

---

## 📄 Medico-Legal Disclaimer

This platform is developed for clinical decision support, medical AI research, and educational demonstration purposes. It is **not** intended to serve as a direct replacement for professional medical judgment, diagnosis, or treatment.

---

<p align="center">
  Built with ❤️ using FastAPI · React · Groq · LangGraph · SciSpaCy · BioBERT · ChromaDB · FHIR R4 · MySQL
</p>
