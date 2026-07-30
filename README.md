# 🧠 Enterprise Clinical Intelligence & Multi-Agent NLP Platform

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3--70B-FF6F00?style=for-the-badge)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20RAG-FF4500?style=for-the-badge)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Tests Pass](https://img.shields.io/badge/Pytest-200%2B%20Passed-2EA44F?style=for-the-badge&logo=pytest&logoColor=white)

> **Enterprise-Grade Clinical Decision Support & Universal NER Platform (v20.0)** — Powered by Groq (Llama 3.3-70B), SciSpaCy, BioBERT, ChromaDB Vector RAG, MySQL 8.0, and React 18 + FastAPI.

An end-to-end clinical intelligence platform designed to ingest raw physician notes, discharge summaries, laboratory reports, and scanned prescription text. It routes clinical inputs through a **20-agent AI orchestrator** featuring **Universal Medication Parsing (v20.0)**, thread-safe inference pooling, per-request context isolation, HIPAA PHI sanitization, multi-model NER consensus, indication-based drug relation mapping, eGFR stage calculation, multi-organ risk stratification, cryptographic SHA-256 audit chaining, and a human-in-the-loop physician review workspace.

---

## 🌟 Key Capabilities & Highlights

| Feature | Description |
|---|---|
| 🤖 **20-Agent AI Pipeline** | Micro-agents covering pre-processing, multi-model NER, universal medication parsing, clinical consistency, RAG, and schema formatting |
| 💊 **Universal Medication Parser v20.0** | Sub-millisecond engine parsing nearly every global prescription style (doses, frequencies, routes, timings, durations, PRN flags, 1-0-1 numeric schedules) |
| 🧪 **RxNorm & Brand Normalization** | Built-in brand & generic alias mapper (`PCM`, `Crocin`, `Tylenol`, `Ecosprin`, `Glucophage`, `Coumadin`, `Norvasc`, `Lasix`, `Augmentin`) |
| ⚡ **Thread-Safe Model Execution** | Concurrent `InferencePool` acquiring dedicated SpaCy/SciSpaCy model instances to prevent segmentation faults under peak traffic |
| 🔒 **Stateless Request Context** | Per-request `AgentContext` isolation ensuring zero data leakage or variable cross-contamination between parallel users |
| 🔐 **SHA-256 Hash-Chained Audit Trail** | Tamper-evident cryptographic ledger storing `previous_hash` and `current_hash` for HIPAA compliance verification |
| 🛡️ **PHI & Secret Sanitization** | Real-time scrubbing of phone numbers, emails, SSNs, Aadhaar, MRNs, JWTs, and API keys from logs and external LLM payloads |
| 🎴 **Grouped Clinical Condition Cards** | Intelligently aggregates disease findings into single condition cards with linked medications, symptoms, and rationale |
| 🎯 **Indication-Based Drug Mapping** | Maps prescribed medications to specific underlying diseases based on clinical indication rather than text proximity |
| 🚨 **Contraindications & Safety Audits** | Automated checks for Metformin + eGFR <30 (Lactic Acidosis), Losartan + K+ >5.5 (Arrhythmia), and duplicate drug therapy |
| 📊 **Multi-Organ Risk Engine** | Real-time risk stratification across Cardiac, Renal, Respiratory, Stroke, and Multi-system organ failure vectors |
| 📚 **ChromaDB Vector RAG Grounding** | Validates clinical recommendations against indexed medical evidence (KDIGO, ACC/AHA, ATS/IDSA guidelines) with thread-safe write locks |
| 👨‍⚕️ **Physician Review Workspace** | Human-in-the-loop review queue allowing doctors to audit, edit, approve, or reject extracted clinical entities |
| 📄 **Medico-Legal PDF Generator** | Generates exportable clinical PDF summaries with QR verification codes, cryptographic report hashes, and digital signature blocks |
| 📈 **Prometheus Observability & Health** | Exportable OpenMetrics at `/api/metrics`, deep health checks at `/api/health`, and real-time database connection pool monitoring |

---

## 📁 Repository Architecture

```
multiagent_system/
│
├── backend/                             # FastAPI Enterprise Backend
│   ├── agents/                          # 20 Autonomous Specialized Agents
│   │   ├── phi_redaction_agent.py       # HIPAA PHI & Secret Sanitization
│   │   ├── section_detector_agent.py    # Clinical section segmentation (HPI, Labs, Meds, Plan)
│   │   ├── spell_correction_agent.py    # RapidFuzz clinical spell checker
│   │   ├── abbreviation_agent.py        # Medical shorthand expansion (HTN -> Hypertension)
│   │   ├── spacy_agent.py               # SpaCy baseline NER & sentence splitter (Thread-safe pool)
│   │   ├── scispacy_agent.py            # SciSpaCy biomedical NER (Thread-safe pool)
│   │   ├── biobert_agent.py             # BioBERT Transformer NER
│   │   ├── regex_agent.py               # Expanded Regex entity extractor
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
│   ├── clinical/                        # Domain Engines
│   │   ├── clinical_knowledge_graph.py  # Interconnected clinical graph & drug mapper
│   │   ├── differential_diagnosis_engine.py # Differential diagnoses & alias deduplication
│   │   ├── evidence_confidence_engine.py# Weighted evidence scoring algorithm
│   │   ├── final_clinical_validator.py  # Pre-render sanity validator
│   │   ├── medical_coder.py             # ICD-10-CM & SNOMED CT terminology mapper
│   │   ├── medication_coverage_checker.py# Prescription completeness auditor
│   │   ├── quality_audit_report.py      # Pipeline error & quality report generator
│   │   ├── severity_risk_engine.py      # Multi-organ risk stratification & severity classifier
│   │   └── timeline_extractor.py        # Chronological clinical timeline engine
│   │
│   ├── core/                            # Enterprise Infrastructure
│   │   ├── agent_context.py             # Request-scoped AgentContext dataclass
│   │   ├── inference_pool.py            # Thread-safe ModelPool acquisition
│   │   ├── chroma_lock.py               # Multi-threaded ChromaDB write lock
│   │   ├── retry.py                     # Database deadlock & lock wait retry wrappers
│   │   ├── metrics.py                   # Prometheus OpenMetrics exporter
│   │   ├── model_registry.py            # Model version & prompt provenance tracker
│   │   ├── phi_filter.py                # Logging filter for scrubbing PHI/secrets
│   │   └── pool_monitor.py              # SQLAlchemy connection pool health monitor
│   │
│   ├── api/                             # REST API Routers
│   │   ├── routes.py                    # Main router with auth, pipeline, health & metrics
│   │   ├── doctor_routes.py             # Review queue management, batch approve & analytics
│   │   ├── patient_routes.py            # Clinical note extraction, patient history & PDF reports
│   │   └── auth.py                      # OAuth2 JWT token authentication
│   │
│   ├── database/                        # Database Persistence
│   │   ├── connection.py                # SQLAlchemy engine & session factory
│   │   ├── models.py                    # ORM Models (AuditLog with hash chaining, User, Session)
│   │   └── mysql_store.py               # High-level database operations
│   │
│   ├── orchestrator/                    # Pipeline Execution
│   │   ├── coordinator.py               # Central orchestrator managing 20 agents & context
│   │   └── router.py                    # Dynamic agent execution router
│   │
│   └── utils/                           # Core Utilities
│       ├── medication_regex.py          # Pre-compiled prescription regex library
│       ├── medication_normalizer.py     # Prescription normalizer & 1-0-1 schedule parser
│       ├── pdf_generator.py             # Medico-legal clinical PDF report generator
│       └── text_cleaning.py             # String pre-processing & sanitization
│
├── frontend/                            # React 18 + Vite Web Application
│   ├── src/
│   │   ├── components/                  # UI Components (Navbar, Modals, ExtractionCards)
│   │   ├── context/                     # AuthContext & global state management
│   │   ├── pages/                       # Login, PatientDashboard, DoctorDashboard, ReviewQueue
│   │   ├── services/                    # Axios API client with bearer token interceptors
│   │   ├── index.css                    # Dark glassmorphic medical design system
│   │   └── App.jsx                      # App router & layout providers
│   └── vite.config.js                   # Vite dev server & proxy settings
│
├── tests/                               # Comprehensive Pytest Suite
│   ├── test_medication_parser.py        # 200+ Universal Prescription Test Cases
│   └── test_phase1_security.py          # Auth, RBAC & Security Test Suite
│
├── .env.example                         # Environment variable template
├── requirements.txt                     # Backend Python dependencies
└── run_all.ps1                          # Unified launcher script (PowerShell)
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

Configure `.env` with your database credentials and API key:

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
Create database in MySQL Workbench or CLI:

```sql
CREATE DATABASE clinical_multiagent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

> **Note:** Tables and demo user accounts are automatically created by SQLAlchemy when the backend starts.

#### 4. Python Virtual Environment Setup
```powershell
# Create virtual environment
python -m venv venv

# Activate on Windows PowerShell
.\venv\Scripts\activate

# Activate on Linux / macOS
# source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## 🚀 Running the Platform

### Option A: Unified One-Command Launcher (Windows PowerShell)

```powershell
.\run_all.ps1
```

Starts the FastAPI backend service and Vite React frontend concurrently.

### Option B: Manual Terminal Execution

#### Terminal 1 — FastAPI Backend
```powershell
.\venv\Scripts\activate
uvicorn backend.api.routes:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 — React Frontend
```bash
cd frontend
npm run dev
```

### Access Points

| Portal / Service | URL | Description |
|---|---|---|
| 🎨 **React Web Application** | `http://localhost:5173` | Patient workspace & Doctor Review Queue |
| ⚡ **FastAPI Backend API** | `http://localhost:8000` | REST API service |
| 📖 **Swagger OpenAPI Docs** | `http://localhost:8000/docs` | Interactive API documentation |
| 📊 **Prometheus Metrics** | `http://localhost:8000/api/metrics` | Real-time OpenMetrics export |
| 🩺 **System Health Check** | `http://localhost:8000/api/health` | Deep health & pool monitoring |

---

## 🔑 Default Demo Accounts

Initial seed credentials for local testing:

| Role | Username | Password | Access & Features |
|---|---|---|---|
| 👨‍⚕️ **Doctor** | `dr_jenkins` | `password123` | Physician Review Queue, Batch Approvals, Patient Analytics |
| 👤 **Patient** | `patient_john` | `password123` | Clinical Note Extractor, Personal Medical History, Medico-Legal PDF Download |

---

## 💊 Universal Medication Parser v20.0

The system includes a high-speed, pre-compiled Universal Medication Parsing Engine (`backend/agents/medication_parser.py`) capable of recognizing complex prescription syntax:

### Supported Prescription Formats & Examples:

```text
• "Metformin 500 mg PO BID after meals for 30 days"
  ➔ Name: Metformin | Dose: 500 mg | Route: PO | Freq: BID (Twice Daily) | Timing: After meals | Duration: 30 days

• "Tab PCM 500mg 1-0-1"
  ➔ Name: Paracetamol | Dose: 500 mg | Route: PO | Freq: BID (Twice Daily - 1-0-1)

• "Aspirin 150 mg PO OD"
  ➔ Name: Aspirin | Dose: 150 mg | Route: PO | Freq: OD (Once Daily)

• "Atorvastatin 40 mg PO HS"
  ➔ Name: Atorvastatin | Dose: 40 mg | Route: PO | Freq: HS (At Bedtime)

• "Warfarin 1/2 tablet HS"
  ➔ Name: Warfarin | Dose: 1/2 tablet | Route: PO | Freq: HS (At Bedtime)

• "Ondansetron 4mg IV PRN for nausea"
  ➔ Name: Ondansetron | Dose: 4 mg | Route: IV | Freq: PRN (As Needed) | PRN: True
```

---

## 🧪 Testing & Verification

Execute the complete automated test suite (including 200+ medication parser test cases and security checks):

```powershell
# Run Universal Medication Parser test suite
.\venv\Scripts\python.exe -m pytest tests/test_medication_parser.py -v

# Run Frontend build verification
npm --prefix frontend run build
```

---

## 📄 Medico-Legal Disclaimer

This platform is developed for clinical decision support, medical AI research, and educational demonstration purposes. It is **not** intended to serve as a standalone replacement for professional medical judgment, diagnosis, or treatment.

---

<p align="center">
  Built with ❤️ using FastAPI · React · Groq · SciSpaCy · BioBERT · ChromaDB · MySQL
</p>
