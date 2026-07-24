# Setup Local Environment

Follow these steps to initialize and start the Multi-Agent NER application locally.

## Prerequisite
- Python 3.10+
- Docker Desktop or Docker Compose
- Ollama (installed locally and running)

## Step 1: Environment Variables
Copy `.env.example` to `.env` and fill in your settings:
```bash
cp .env.example .env
```

## Step 2: Start Container Services
Use Docker Compose to spin up MySQL database, ChromaDB, Label Studio, Prometheus, and Grafana:
```bash
docker-compose up -d
```
Verify that all containers are healthy:
```bash
docker ps
```

## Step 3: Local LLM Configuration (Ollama)
Pull the default llama3 model in Ollama:
```bash
ollama pull llama3
```

## Step 4: Install Dependencies
Activate your virtual environment and install requirements:
```bash
# Windows
venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS
source venv/bin/activate
pip install -r requirements.txt
```

## Step 5: Seed Canonical Database
Before running disambiguation tests, seed the database with initial canonical entity records:
```bash
# Log in to MySQL container or client and run sql/seed.sql
docker exec -i ner_mysql mysql -uroot -prootpassword multiagent_ner < sql/seed.sql
```

## Step 6: Start API Service
Launch the main FastAPI service:
```bash
uvicorn src.api.main:app --reload --port 8000
```
Swagger UI will be available at `http://localhost:8000/docs`.

## Step 7: Start Human Review Ingestion Server (Optional)
Expose the webhook listener for Label Studio:
```bash
python src/human_review/feedback_ingest.py
```
This starts a service on port `8081` to receive annotations from Label Studio.
