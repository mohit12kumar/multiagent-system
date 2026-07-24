import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "clinical_multiagent")

SERVER_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

FALLBACK_DB_URL = "sqlite:///./development.db"

# 1. Try auto-creating database schema in MySQL server first
try:
    server_engine = create_engine(SERVER_URL, pool_pre_ping=True)
    with server_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}`;"))
        conn.commit()
    server_engine.dispose()
    print(f"[MySQL Setup] Verified database '{MYSQL_DATABASE}' in MySQL Workbench.")
except Exception as e:
    print(f"[MySQL Setup Warning] MySQL root server check: {e}")

# 2. Connect to the target database engine
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
    # Run schema migrations exactly once using a tracking table
    with engine.connect() as conn:
        # Create migrations tracker table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_id VARCHAR(100) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

        # Map of migration_id -> SQL to run once
        _migrations = {
            "add_documents_user_id":           "ALTER TABLE documents ADD COLUMN user_id VARCHAR(36);",
            "add_documents_redacted_content":   "ALTER TABLE documents ADD COLUMN redacted_content TEXT;",
            "add_entity_mentions_needs_review": "ALTER TABLE entity_mentions ADD COLUMN needs_review BOOLEAN DEFAULT FALSE;",
            "drop_disease_relations_fk1":        "ALTER TABLE disease_relations DROP FOREIGN KEY disease_relations_ibfk_1;",
            "drop_medication_relations_fk1":     "ALTER TABLE medication_relations DROP FOREIGN KEY medication_relations_ibfk_1;",
            "drop_entity_mentions_fk2":          "ALTER TABLE entity_mentions DROP FOREIGN KEY entity_mentions_ibfk_2;",
            "drop_entity_mentions_fk3":          "ALTER TABLE entity_mentions DROP FOREIGN KEY entity_mentions_ibfk_3;",
            "add_canonical_entities_rxnorm_id": "ALTER TABLE canonical_entities ADD COLUMN rxnorm_id VARCHAR(50);",
            "drop_documents_fk1":               "ALTER TABLE documents DROP FOREIGN KEY documents_ibfk_1;",
            "drop_patient_history_fk1":          "ALTER TABLE patient_history DROP FOREIGN KEY patient_history_ibfk_1;",
        }

        for migration_id, sql in _migrations.items():
            applied = conn.execute(
                text("SELECT 1 FROM schema_migrations WHERE migration_id = :id"),
                {"id": migration_id}
            ).fetchone()
            if not applied:
                try:
                    conn.execute(text(sql))
                    conn.execute(
                        text("INSERT INTO schema_migrations (migration_id) VALUES (:id)"),
                        {"id": migration_id}
                    )
                    conn.commit()
                    print(f"[Migration] Applied: {migration_id}")
                except Exception:
                    conn.rollback()  # Column/FK already exists — skip silently

except Exception as e:
    print(f"[Database Connection] Using SQLite local database fallback ({e}).")
    engine = create_engine(
        FALLBACK_DB_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
