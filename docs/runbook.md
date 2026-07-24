# Operations Runbook

This runbook describes operational tasks, monitoring endpoints, testing routines, and troubleshooting guidelines.

## Health Checks

Verify application components are up:
1. **FastAPI Root**: `curl http://localhost:8000/` (Expects: `{"status": "healthy"}`)
2. **Prometheus Metrics**: `curl http://localhost:8000/metrics`
3. **ChromaDB**: `curl http://localhost:8000/api/v1/heartbeat` (Returns heartbeat epoch time)
4. **Ollama**: `curl http://localhost:11434/` (Expects: "Ollama is running")

## Running Automated Tests

Run the test suite using `pytest`:

```bash
# Activate virtual environment
venv\Scripts\activate

# Run all unit and integration tests
pytest -v
```

## Review Queue Operations

Low-confidence entities are queued for human review. 
1. Get the list of items needing review:
   ```bash
   curl http://localhost:8000/api/v1/review/queue
   ```
2. Submit a correction feedback (action: `APPROVED` | `MODIFIED` | `REJECTED`):
   ```bash
   curl -X POST http://localhost:8000/api/v1/review/feedback \
        -H "Content-Type: application/json" \
        -d '{"entity_mention_id": "mention-uuid-here", "action": "MODIFIED", "new_text": "Microsoft Corp", "new_type": "ORGANIZATION"}'
   ```
   This updates the MySQL database, boosts extraction confidence to 1.0, creates the canonical entity, and registers the name in ChromaDB for future linkage.

## Observability & Metrics

- **Prometheus UI**: Available on `http://localhost:9090`. Scraping target `multiagent-ner-api` handles latency tracking.
- **Grafana Dashboards**: Available on `http://localhost:3000`. Login with default `admin` / `admin`. Add Prometheus as a datasource pointing to `http://prometheus:9090`.
- **LangSmith Tracing**: Set environment variables:
  ```env
  LANGCHAIN_TRACING_V2=true
  LANGCHAIN_API_KEY=your_key
  ```
  Runs, child spans, LLM prompts, similarity hits, and execution times are visualized on the LangSmith Cloud dashboard.

## Troubleshooting

### 1. Database Connection Errors
- Verify MySQL is running: `docker ps`.
- Check `.env` password and username matches `docker-compose.yml`.
- If running locally without Docker, ensure PyMySQL is installed (`pymysql`) and MySQL service is active.

### 2. Ollama is slow or timeouts
- If a document is very large, the router disables Ollama automatically. You can force-enable it by passing `{"force_llm": true}` in the metadata parameter of the API request:
  ```bash
  curl -X POST http://localhost:8000/api/v1/extract \
       -H "Content-Type: application/json" \
       -d '{"text": "your text", "metadata": {"force_llm": true}}'
  ```
- Make sure Ollama has pulled the model: `ollama run llama3`.

### 3. Missing SpaCy models
- The SpaCy Agent will automatically download the configured model if not found. If this fails due to proxy/network rules, download it manually in the virtual environment:
  ```bash
  python -m spacy download en_core_web_sm
  ```
