import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# LangChain Tracing (Optional)
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "medical-research-agent")

# NCBI Entrez Configuration
ENTREZ_EMAIL = os.getenv("ENTREZ_EMAIL", "you@example.com")
ENTREZ_API_KEY = os.getenv("ENTREZ_API_KEY")

# Vector Database and Embeddings Configuration
CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# API Security Configuration (JWT and basic auth credentials)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretjwtkeychangeinproduction12345")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
API_USERNAME = os.getenv("API_USERNAME", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "secret-key-123")

# Non-diagnostic medical disclaimer requirement
MEDICAL_DISCLAIMER = (
    "DISCLAIMER: This report is for research and educational purposes only. "
    "It is not a diagnostic, clinical, or treatment tool. It should not be used "
    "as a substitute for professional medical advice, diagnosis, or treatment. "
    "Always consult with a licensed physician or healthcare professional for any medical concerns."
)

# Print a clear warning if GROQ_API_KEY is missing (rather than crashing at startup)
if not GROQ_API_KEY:
    print("\n" + "=" * 80)
    print("WARNING: 'GROQ_API_KEY' is missing from the environment or .env file.")
    print("The Planner, Synthesizer, and Verifier agents will fail during execution.")
    print("Please make sure to set GROQ_API_KEY in your .env file.")
    print("=" * 80 + "\n")
