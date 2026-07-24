import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Counter, Histogram
from src.db.connection import engine, Base
from src.api.routes import router
from src.monitoring.logger import logger

app = FastAPI(
    title="Multi-Agent Named Entity Recognition (NER) API",
    description="A multi-agent architecture for scalable entity extraction, disambiguation, and human-in-the-loop review.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics setup
# Expose /metrics endpoint for prometheus scraping
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Prometheus instruments
REQUEST_COUNT = Counter(
    "api_requests_total", "Total count of API requests", [
        "method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds", "Request latency in seconds", [
        "method", "endpoint"]
)


@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """
    Middleware to calculate latency and increment metrics.
    """
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time

    endpoint = request.url.path
    method = request.method
    status = str(response.status_code)

    # Increment metrics counters
    REQUEST_COUNT.labels(method=method, endpoint=endpoint,
                         http_status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

    return response

# Include routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {
        "service": "multiagent-ner-pipeline-api",
        "status": "healthy",
        "docs_url": "/docs",
        "metrics_url": "/metrics"
    }


@app.on_event("startup")
def startup_event():
    logger.info("Starting up Multi-Agent NER API Service...")
    try:
        logger.info("Verifying database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down Multi-Agent NER API Service...")
