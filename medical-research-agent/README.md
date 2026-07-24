# Local Multi-Agent Medical Research Assistant

A fully local, multi-agent AI system designed for medical literature synthesis and QA research. It combines live PubMed searches with a local Retrieval-Augmented Generation (RAG) knowledge base built from the MedQuAD dataset. The system is orchestrated using `langgraph` and exposed via a secured FastAPI endpoint (with JWT token auth, STT, and TTS capabilities).

> [!WARNING]
> This is a **research and educational tool** only. It does not provide clinical or diagnostic advice. Every output terminates with a mandatory medical disclaimer.

---

## Architecture and Core Concepts

### 1. LangGraph Orchestration Flow
The system implements a **central supervisor and specialist node pattern** built on LangGraph:

```
                     ┌─────────────┐
        ┌───────────▶│ Supervisor  │◀──────────────────┐
        │            └──────┬──────┘                    │
        │        ┌──────────┼───────────┬────────────┐  │
        │        ▼          ▼           ▼            ▼  │
        │   Planner   Researchers  Synthesizer   Verifier│
        │        │     (PubMed +        │            │  │
        │        │      Local RAG)      │            │  │
        └────────┴──────────┴───────────┴────────────┘  │
                                                          │
                                                Reporter ─┴──▶ END
```

- **Supervisor (Deterministic)**: Decides transitions based on the state machine. If subtasks are not yet set, it routes to the **Planner**. If there are uncovered subtasks, it routes to **Researchers**. If a draft doesn't exist or is rejected, it routes to the **Synthesizer**. If a draft is generated and unchecked, it routes to the **Verifier**. Once verified, it routes to the **Reporter**.
- **Planner (LLM)**: Breaks a complex clinical question into 2-4 focused sub-questions.
- **PubMed Researcher (Tool-calling)**: Executes a live NCBI PubMed search for each uncovered sub-question and parses abstracts.
- **Local KB Researcher (Tool-calling)**: Queries the local vector database of MedQuAD Q&A pairs for each sub-question, then marks them as covered.
- **Synthesizer (LLM)**: Merges all gathered evidence into a structured draft answer, strictly grounded in findings and inline-cited.
- **Verifier (LLM)**: Checks the draft for hallucinations or formatting issues. It allows a maximum of 2 revision iterations before failing open to prevent infinite loops.
- **Reporter**: Formats findings and appends PubMed reference URLs and the mandatory disclaimer.

### 2. JWT Authentication Concept
FastAPI uses OAuth2 Password Flow with JSON Web Tokens (JWT). Calling client requests a token at `POST /token` using login credentials (configured in `.env`). The API validates the credentials, signs a payload (with user ID and expiration time) using HMAC-SHA256, and returns a bearer token. Protected endpoints (`/research` and `/research/audio`) require this token in the header.

### 3. Speech-to-Text (STT) and Text-to-Speech (TTS) Concept
- **STT**: The API accepts query audio uploads via `POST /research/audio`. It leverages Groq's Whisper API (`whisper-large-v3`) to transcribe the spoken audio query into a text string at zero cost.
- **TTS**: Once the research assistant completes, the text findings are synthesized into natural-sounding spoken audio using Google Text-to-Speech (`gTTS`) and saved locally, returning an audio download URL to the client.

---

## Directory Structure

```
medical-research-agent/
├── README.md             # This guide
├── requirements.txt      # Python dependencies
├── .env.example          # Sample environment secrets
├── config.py             # Config validation & warning prints
├── state.py              # ResearchState Shared schemas
├── graph.py              # LangGraph compilation & edges
├── server.py             # FastAPI App with JWT, STT & TTS
├── main.py               # Main CLI and server launcher
├── ingest.py             # MedQuAD ingestion script
├── agents/               # 7 LangGraph agent nodes
│   ├── __init__.py
│   └── nodes.py
└── tools/                # Integrations (PubMed and Chroma)
    ├── __init__.py
    ├── pubmed_tool.py
    └── kb_tool.py
```

---

## Getting Started

### 1. Installation
Ensure Python 3.10+ is installed on Windows. Create a virtual environment:
```bash
# Setup virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration Setup
Create a `.env` file based on `.env.example`:
```bash
copy .env.example .env
```
Open `.env` and fill in:
- `GROQ_API_KEY`: Get a free key from the Groq console.
- `ENTREZ_EMAIL`: NCBI PubMed requires an email address.
- `JWT_SECRET_KEY`: Set a secure string for token signing.
- `API_USERNAME` & `API_PASSWORD`: Credentials for JWT login.

### 3. Seed Local RAG Database
Run `ingest.py` to download the MedQuAD dataset, embed Q&A records, and build the local vector database:
```bash
python ingest.py
```
*Note: This cleans up any existing database at `./data/chroma_db` first to guarantee idempotency and avoid duplicates.*

---

## Usage Guide

### A. Command Line Interface (CLI)
To run a clinical query directly in the terminal (streams node progression and formats using rich console markup):

```bash
# Single query
python main.py "What are the primary symptoms and treatments for Type 2 Diabetes?"

# Interactive loop
python main.py
```

### B. FastAPI Web Server
Start the web server:
```bash
python main.py --server
```
The server will start at `http://127.0.0.1:8000`.

#### 1. Request JWT Access Token
Submit username and password via form-data:
```bash
curl -X POST "http://127.0.0.1:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret-key-123"
```
Response:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

#### 2. Query Text Research
```bash
curl -X POST "http://127.0.0.1:8000/research" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Detail the side effects and contraindications of Lisinopril.\"}"
```

#### 3. Query Audio (STT & TTS)
Upload a query recording (WAV/MP3) to get findings and a speech report:
```bash
curl -X POST "http://127.0.0.1:8000/research/audio" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -F "file=@question.wav"
```
Response:
```json
{
  "transcribed_query": "What is the recommended dosage of Ibuprofen?",
  "final_report": "# Medical Research Assistant - Report ...",
  "audio_url": "/audio/report_abc123.mp3"
}
```
You can download/stream the voice response at `http://127.0.0.1:8000/audio/report_abc123.mp3`.
