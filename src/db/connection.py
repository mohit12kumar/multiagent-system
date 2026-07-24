import os
import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env
load_dotenv()

# Locate paths
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "mysql_config.yaml")

# Load configuration values
host = os.getenv("MYSQL_HOST")
port = os.getenv("MYSQL_PORT")
user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
database = os.getenv("MYSQL_DATABASE")
pool_size = 10
max_overflow = 20

# Fallback to YAML config if environment variables are not set
if not all([host, port, user, password, database]):
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            yaml_config = yaml.safe_load(f)
            host = host or yaml_config.get("host", "localhost")
            port = port or yaml_config.get("port", 3306)
            user = user or yaml_config.get("user", "root")
            password = password or yaml_config.get("password", "")
            database = database or yaml_config.get(
                "database", "multiagent_ner")

            pool_config = yaml_config.get("pool", {})
            pool_size = pool_config.get("size", 10)
            max_overflow = pool_config.get("max_overflow", 20)

# Build connection string
# Standard SQLAlchemy URI format for mysql: mysql+pymysql://user:password@host:port/database
# We use pymysql driver because it is standard and easy to install
DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

# For sqlite fallback in case MySQL isn't available during simple test setups
if os.getenv("ENV") == "test" or not host:
    DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(DATABASE_URL, connect_args={
                           "check_same_thread": False})
else:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=3600,
            echo=False
        )
        # Proactively test connection
        with engine.connect() as conn:
            pass
    except Exception as e:
        from src.monitoring.logger import logger
        logger.warning(
            f"MySQL connection failed ({e}). Falling back to SQLite local database.")
        DATABASE_URL = "sqlite:///./development.db"
        engine = create_engine(DATABASE_URL, connect_args={
                               "check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency generator for FastAPI routes and DB access."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
