# 🧠 Enterprise Clinical Intelligence & Multi-Agent NLP Platform

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3--70B-FF6F00?style=for-the-badge)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20RAG-FF4500?style=for-the-badge)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Tests Pass](https://img.shields.io/badge/Pytest-16%2F16%20Passed-2EA44F?style=for-the-badge&logo=pytest&logoColor=white)

> **Production-Ready Multi-Agent Clinical Decision Support & NER System** — Powered by Groq (Llama 3.3-70B), SciSpaCy, BioBERT, EasyOCR, ChromaDB, MySQL, and React + FastAPI.

An end-to-end clinical intelligence platform designed to ingest raw doctor notes, discharge summaries, laboratory reports, and scanned prescription images. It routes inputs through a **19-agent AI pipeline** performing HIPAA PHI redaction, medical spelling correction, abbreviation expansion, multi-model entity extraction, clinical relation mapping, RAG grounding via ChromaDB, drug interaction checking, and a human-in-the-loop physician review workflow.

---

## 🌟 Key Capabilities & Highlights

| Feature | Description |
|---|---|
| 🤖 **19-Agent Architecture** | Autonomous, modular micro-agents covering pre-processing, multi-model NER, validation, RAG, and clinical formatting |
| 🎴 **Grouped Disease Cards** | Intelligently clusters clinical findings into single condition cards with mapped medications, symptoms, and rationale |
| 🎯 **Indication-Based Drug Mapping** | Connects prescribed drugs to specific target diseases based on medical indication rather than simple text proximity |
| 💊 **Preserved Prescription Instructions** | Preserves raw clinical frequencies (`SOS`, `PRN`, `STAT`, `OD`, `BD`, `TDS`, `QID`, `HS`) without loss of context |
| 🛡️ **HIPAA PHI Redaction** | Strips SSNs, dates of birth, patient names, phone numbers, and MRNs prior to external LLM calls |
| 🧪 **Lab Marker Protection** | Strictly categorizes lab values (HbA1c, Creatinine, eGFR, K+, Na+) under `LAB_VALUE` to prevent misclassification |
| 🚨 **Drug Interaction & Safety Engine** | Automatically identifies co-prescription risks with severity ratings (Critical / Major / Moderate) |
| 📚 **ChromaDB RAG Grounding** | Verifies clinical recommendations against indexed medical evidence to suppress model hallucinations |
| 👨‍⚕️ **Physician Review Queue** | Human-in-the-loop workflow allowing doctors to audit, edit, approve, or reject extracted clinical entities |
| 📊 **Doctor Analytics Dashboard** | Real-time disease prevalence charts, processing metrics, and review queue throughput tracking |
| 📄 **Automated PDF Discharge Reports** | Generates exportable, formatted clinical discharge reports for patient records |
| 🔑 **Role-Based Access Control** | Dedicated JWT-authenticated portals for Doctors (review, analytics, export) and Patients (submit notes, view history) |

---

## 📁 Directory Structure

```
multiagent_system/
│
├── backend/                             # FastAPI Backend Service
│   ├── agents/                          # 19 Specialized Autonomous Agents
│   │   ├── phi_redaction_agent.py       # HIPAA PHI Sanitization
│   │   ├── section_detector_agent.py    # Clinical section segmentation
│   │   ├── spell_correction_agent.py    # RapidFuzz clinical spell checker
│   │   ├── abbreviation_agent.py        # Medical shorthand expansion (HTN -> Hypertension)
│   │   ├── spacy_agent.py               # SpaCy baseline NER & sentence splitter
│   │   ├── scispacy_agent.py            # SciSpaCy biomedical NER (en_core_sci_sm)
│   │   ├── biobert_agent.py             # BioBERT Transformer NER
│   │   ├── regex_agent.py               # Dosage, Frequency & Lab regex parser
│   │   ├── llm_clinical_agent.py        # Groq Llama-3.3-70b contextual extraction
│   │   ├── aggregation_agent.py         # Overlap resolution & weighted consensus
│   │   ├── validation_agent.py          # Taxonomy rules & ALLERGY classification
│   │   ├── relation_extraction_agent.py # Disease-Medication-Symptom indication mapping
│   │   ├── medication_validation_agent.py # RxNorm & Wikidata drug verification
│   │   ├── disambiguation_agent.py      # ChromaDB vector normalization
│   │   ├── contraindication_agent.py    # Renal/hepatic/cardiac disease-drug checks
│   │   ├── lab_interpretation_agent.py  # Reference range evaluation & alert tagging
│   │   ├── rag_agent.py                 # Vector database RAG grounding & citations
│   │   ├── formatting_agent.py          # Grouped disease card JSON shaping
│   │   └── human_review_agent.py        # Doctor review queue CRUD operations
│   │
│   ├── api/                             # REST API Routers
│   │   ├── routes.py                    # Root router, auth endpoints & FastAPI startup
│   │   ├── doctor_routes.py             # Doctor queue, approval & analytics endpoints
│   │   ├── patient_routes.py            # Patient note extraction, history & PDF downloads
│   │   └── auth.py                      # OAuth2 JWT token authentication
│   │
│   ├── database/                        # Database Layer
│   │   ├── connection.py                # SQLAlchemy engine, session factory & auto-migration
│   │   ├── models.py                    # SQLAlchemy ORM models (User, Document, PipelineSession, EntityMention)
│   │   └── mysql_store.py               # High-level database queries & persistence
│   │
│   ├── orchestrator/                    # Execution Engine
│   │   ├── coordinator.py               # Pipeline orchestrator managing all 19 agents
│   │   └── router.py                    # Agent execution routing
│   │
│   ├── services/                        # External Knowledge Services
│   │   ├── chroma_service.py            # Vector database connection & RAG query client
│   │   ├── rxnorm_service.py            # NIH RxNorm REST API integration
│   │   └── wikidata_service.py          # SPARQL medical ontology client
│   │
│   └── utils/                           # Helper Utilities
│       ├── pdf_generator.py             # ReportLab clinical PDF summary generator
│       └── text_cleaning.py             # String pre-processing & sanitization
│
├── frontend/                            # React 18 + Vite Web Application
│   ├── src/
│   │   ├── components/                  # UI Components (Navbar, Toast, Modals)
│   │   ├── context/                     # AuthContext & Session state management
│   │   ├── pages/                       # Login, PatientDashboard, DoctorDashboard, ReviewQueue
│   │   ├── services/                    # Axios API client with interceptors
│   │   ├── index.css                    # Dark glassmorphic design system
│   │   └── App.jsx                      # Router & root state provider
│   └── vite.config.js                   # Vite build & proxy settings
│
├── config/                              # System Configuration YAMLs
│   ├── agents.yaml                      # Agent weights, thresholds & system prompts
│   ├── entity_taxonomy.yaml             # Supported clinical entity types (DISEASE, DRUG, etc.)
│   ├── pipeline.yaml                    # Pipeline stage parameters & routing rules
│   ├── phi_redaction_rules.yaml         # Regex rules for HIPAA compliance
│   └── clinical_vocab.json              # Medical abbreviation lookup database
│
├── sql/                                 # MySQL database DDL schemas & seed data
├── tests/                               # Pytest test suite (16 tests, 0 failures)
├── .env.example                         # Environment variable template
├── requirements.txt                     # Python dependencies
└── run_all.ps1                          # Unified launcher script (PowerShell)
```

---

## ⚙️ Environment Setup & Prerequisites

### Requirements

| Dependency | Minimum Version | Recommended |
|---|---|---|
| **Python** | 3.10+ | 3.11 |
| **Node.js** | 18.0+ | 20.0+ |
| **npm** | 9.0+ | 10.0+ |
| **MySQL** | 8.0+ | 8.0 local server |
| **Groq API Key** | - | Free key from [console.groq.com](https://console.groq.com) |

---

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd multiagent_system
```

#### 2. Configure Environment Variables
Copy `.env.example` to `.env`:

```powershell
# Windows PowerShell
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Update `.env` with your local database credentials and Groq API key:

```env
# Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=multiagent_ner

# Groq LLM API Key
GROQ_API_KEY=gsk_your_groq_api_key_here

# JWT Authentication Secret
SECRET_KEY=super_secret_jwt_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

#### 3. Create MySQL Database
Start your local MySQL service, open MySQL CLI or Workbench, and execute:

```sql
CREATE DATABASE multiagent_ner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

> **Note:** Database tables and default demo accounts are automatically initialized by SQLAlchemy when the backend starts.

#### 4. Setup Python Virtual Environment
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

#### 5. Setup React Frontend
```bash
cd frontend
npm install
cd ..
```

---

## 🚀 Running the Application

### Option A: One-Command Startup (Windows PowerShell)

Run the unified launcher script:

```powershell
.\run_all.ps1
```

This starts both the FastAPI backend and Vite React frontend concurrently.

### Option B: Manual Startup

#### 1. Start FastAPI Backend (Terminal 1)
```powershell
.\venv\Scripts\activate
uvicorn backend.api.routes:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Start React Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

### Access Ports & URLs

| Service | Access URL | Description |
|---|---|---|
| 🎨 **React Frontend** | `http://localhost:5173` | Patient portal & Doctor dashboard |
| ⚡ **FastAPI Backend** | `http://localhost:8000` | REST API service |
| 📖 **Swagger UI Docs** | `http://localhost:8000/docs` | Interactive OpenAPI documentation |
| 📑 **ReDoc API Docs** | `http://localhost:8000/redoc` | Alternative API reference |

---

## 🔑 Demo Credentials

The platform seeds default accounts upon initial database creation:

| Role | Username | Password | Purpose |
|---|---|---|---|
| 👨‍⚕️ **Doctor** | `dr_jenkins` | `password123` | Review queue management, entity approvals, analytics dashboard |
| 👤 **Patient** | `patient_john` | `password123` | Clinical note extraction, personal history, PDF download |

---

## 🔌 API Reference & Usage Examples

All API endpoints support both `/api/v1` and direct `/api` paths.

### 1. Authentication

#### `POST /api/v1/auth/login`
Authenticates a user and returns a JWT access token.

**Request Body:**
```json
{
  "username": "dr_jenkins",
  "password": "password123"
}
```

**Curl Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"dr_jenkins","password":"password123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer",
  "role": "doctor",
  "username": "dr_jenkins"
}
```

---

### 2. Clinical Note Extraction

#### `POST /api/v1/extract`
Processes raw clinical text through the 19-agent pipeline.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "text": "Patient: 68-year-old male with HTN, T2DM, and CKD. Prescribed Metformin 1000mg BD and Lisinopril 20mg OD. Complains of mild shortness of breath. Labs: HbA1c 10.2%, Creatinine 3.6 mg/dL.",
  "role": "patient"
}
```

**Curl Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
     -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Patient with HTN and T2DM. Taking Metformin 500mg BD. HbA1c 9.5%.",
       "role": "patient"
     }'
```

**Response Overview:**
```json
{
  "session_id": "c7f4e912-34ab-4cd8-b112-9876543210fe",
  "status": "COMPLETED",
  "entities": [
    { "text": "HTN", "type": "DISEASE", "confidence": 0.96 },
    { "text": "Metformin 500mg BD", "type": "DRUG", "confidence": 0.98 },
    { "text": "HbA1c 9.5%", "type": "LAB_VALUE", "confidence": 0.99 }
  ],
  "patient_summary": {
    "structured_summary": [
      {
        "disease": "Type 2 Diabetes Mellitus",
        "status": "Poorly Controlled",
        "medications": [
          {
            "name": "Metformin",
            "dosage": "500mg",
            "frequency": "BD",
            "validation_status": "Correct"
          }
        ]
      }
    ]
  },
  "laboratory_values": [
    {
      "lab": "HbA1c",
      "value": "9.5%",
      "reference": "< 7.0%",
      "interpretation": "Elevated"
    }
  ]
}
```

---

### 3. Doctor Review Queue

#### `GET /api/v1/review/queue`
Retrieves pending extracted entity mentions for physician verification.

#### `POST /api/v1/review/feedback`
Submits approval, rejection, or modification for a specific entity.

**Request Body:**
```json
{
  "entity_mention_id": "e91a2b3c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "reviewer": "dr_jenkins",
  "action": "APPROVED"
}
```

---

### 4. Patient History & Exports

#### `GET /api/v1/patient/history`
Returns structured history of all extraction sessions for the logged-in patient.

#### `GET /api/v1/patient/download-pdf/{session_id}`
Generates and downloads a formatted PDF report for a completed session.

---

## 🧬 Entity Taxonomy & Parsing Rules

The platform categorizes extracted text into 8 standardized entity types:

| Entity Type | Description | Sample Tokens | Special Rules |
|---|---|---|---|
| `DISEASE` | Medical conditions & diagnoses | Hypertension, T2DM, CKD Stage III | Standardized via BioBERT / SciSpaCy |
| `SYMPTOM` | Patient complaints & signs | Dyspnea, Leg edema, Chest pain | Mapped to related diseases |
| `DRUG` | Active pharmaceutical ingredients | Metformin, Lisinopril, Furosemide | Preserves drug strength & form |
| `DOSAGE` | Measured medication quantity | 500 mg, 10 ml, 1 tablet | Regex normalized |
| `FREQUENCY` | Administration schedule | OD, BD, TDS, QID, HS, SOS, PRN | Preserved verbatim |
| `ANATOMY` | Anatomical sites & body parts | Right kidney, Left ventricle | SpaCy / SciSpaCy tagged |
| `LAB_VALUE` | Quantitative lab tests & values | HbA1c 10.2%, Creatinine 3.6 mg/dL | Protected from drug classification |
| `ALLERGY` | Hypersensitivities & adverse reactions | Penicillin allergy, Sulfa allergy | Blocked from generic DRUG tag |

---

## 🤖 Multi-Agent Architecture (19 Agents)

```
                       [ Unstructured Clinical Note ]
                                     │
                                     ▼
                        [ 1. PHI Redaction Agent ] (HIPAA Sanitization)
                                     │
                                     ▼
                      [ 2. Section Detector Agent ]
                                     │
                                     ▼
                     [ 3. Spell Correction Agent ]
                                     │
                                     ▼
                    [ 4. Abbreviation Expansion Agent ]
                                     │
                                     ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │                      PARALLEL EXTRACTION LAYER                        │
 │  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────┐  │
 │  │ 5. SpaCy Agent  │  │ 6. SciSpaCy Agent│  │  7. BioBERT Agent   │  │
 │  └─────────────────┘  └──────────────────┘  └─────────────────────┘  │
 │  ┌─────────────────┐  ┌──────────────────┐                           │
 │  │ 8. Regex Agent  │  │ 9. LLM Clinical  │                           │
 │  └─────────────────┘  └──────────────────┘                           │
 └───────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                       [ 10. Aggregation Agent ] (Consensus Voting)
                                     │
                                     ▼
                        [ 11. Validation Agent ] (Taxonomy Rules)
                                     │
                                     ▼
                  [ 12. Relation Extraction Agent ] (Indication Mapping)
                                     │
                                     ▼
                 [ 13. Medication Validation Agent ] (RxNorm/Wikidata)
                                     │
                                     ▼
                    [ 14. Disambiguation Agent ] (Vector Grounding)
                                     │
                                     ▼
                   [ 15. Contraindication Agent ] (Safety Checks)
                                     │
                                     ▼
                  [ 16. Lab Interpretation Agent ] (Reference Ranges)
                                     │
                                     ▼
                        [ 17. RAG Grounding Agent ] (ChromaDB)
                                     │
                                     ▼
                     [ 18. Formatting Agent ] (Disease Cards)
                                     │
                                     ▼
                   [ 19. Human Review Queue Agent ] (Doctor Audit)
```

---

## 🧪 Testing & Code Quality

### Running Unit & Integration Tests

The project includes a full pytest suite covering agent aggregation, disambiguation, regex parsing, PHI redaction, and end-to-end pipeline execution.

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run all 16 tests
pytest -v

# Run tests with coverage summary
pytest --cov=backend --cov-report=term-missing
```

### Code Formatting & Linting

```powershell
# Python Flake8 linting
flake8 backend --select=F401,F841,E302 --max-line-length=120

# Frontend ESLint check
cd frontend
npx eslint src
```

---

## 📄 License & Disclaimer

This software is developed for research, educational, and clinical decision support demonstration purposes. It is **not** intended to replace direct professional medical advice, diagnosis, or treatment.

---

<p center>
  Built with ❤️ using FastAPI · React · Groq · SciSpaCy · BioBERT · ChromaDB · MySQL
</p>
