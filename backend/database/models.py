import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime,
    ForeignKey, JSON, Boolean
)
from sqlalchemy.orm import relationship
from backend.database.connection import Base

# ── UTC helper ────────────────────────────────────────────────────────────────
# datetime.utcnow() is deprecated in Python 3.12+; use timezone-aware datetimes.
def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id              = Column(String(36),  primary_key=True)
    username        = Column(String(100), unique=True, nullable=False, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(50),  default="patient")  # 'doctor', 'patient', 'admin'
    full_name       = Column(String(255), nullable=True)
    is_active       = Column(Boolean,     default=True)
    last_login      = Column(DateTime,    nullable=True)
    login_count     = Column(Integer,     default=0)
    created_at      = Column(DateTime,    default=_utcnow)

    # Relationships
    documents        = relationship("Document",       back_populates="user", cascade="all, delete-orphan")
    patient_histories= relationship("PatientHistory", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id               = Column(String(36), primary_key=True)
    user_id          = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content          = Column(Text,       nullable=False)
    redacted_content = Column(Text,       nullable=True)
    meta_data        = Column(JSON,       nullable=True)
    # Soft delete
    is_deleted       = Column(Boolean,    default=False, index=True)
    deleted_at       = Column(DateTime,   nullable=True)
    deleted_by       = Column(String(36), nullable=True)
    created_at       = Column(DateTime,   default=_utcnow)

    # Relationships
    user           = relationship("User",           back_populates="documents")
    sessions       = relationship("PipelineSession",back_populates="document", cascade="all, delete-orphan")
    entity_mentions= relationship("EntityMention",  back_populates="document", cascade="all, delete-orphan")


class PipelineSession(Base):
    __tablename__ = "sessions"

    id            = Column(String(36), primary_key=True)
    document_id   = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    status        = Column(String(50), nullable=False)   # PENDING, IN_PROGRESS, COMPLETED, FAILED
    current_stage = Column(String(50), nullable=False)
    error_message = Column(Text,       nullable=True)
    created_at    = Column(DateTime,   default=_utcnow)
    updated_at    = Column(DateTime,   default=_utcnow, onupdate=_utcnow)

    # Relationships
    document          = relationship("Document",         back_populates="sessions")
    entity_mentions   = relationship("EntityMention",    back_populates="session",  cascade="all, delete-orphan")
    disease_relations = relationship("DiseaseRelation",  back_populates="session",  cascade="all, delete-orphan")
    medication_relations = relationship("MedicationRelation", back_populates="session", cascade="all, delete-orphan")
    review_items      = relationship("ReviewQueue",      back_populates="session",  cascade="all, delete-orphan")
    phi_audit_logs    = relationship("PHIAuditLog",      back_populates="session",  cascade="all, delete-orphan")
    patient_histories = relationship("PatientHistory",   back_populates="session",  cascade="all, delete-orphan")


class CanonicalEntity(Base):
    __tablename__ = "canonical_entities"

    id          = Column(String(36),  primary_key=True)
    name        = Column(String(255), unique=True, nullable=False, index=True)
    type        = Column(String(50),  nullable=False)
    description = Column(Text,        nullable=True)
    wikidata_id = Column(String(50),  nullable=True)
    rxnorm_id   = Column(String(50),  nullable=True)
    created_at  = Column(DateTime,    default=_utcnow)
    updated_at  = Column(DateTime,    default=_utcnow, onupdate=_utcnow)

    mentions = relationship("EntityMention", back_populates="canonical")


class EntityMention(Base):
    __tablename__ = "entity_mentions"

    id            = Column(String(36), primary_key=True)
    document_id   = Column(String(36), ForeignKey("documents.id",  ondelete="CASCADE"), nullable=False)
    session_id    = Column(String(36), ForeignKey("sessions.id",   ondelete="CASCADE"), nullable=False)
    text          = Column(String(255),nullable=False)
    type          = Column(String(50), nullable=False)
    start_char    = Column(Integer,    nullable=False)
    end_char      = Column(Integer,    nullable=False)
    confidence    = Column(Float,      nullable=False)
    source_agents = Column(String(255),nullable=False)
    canonical_id  = Column(String(36), ForeignKey("canonical_entities.id", ondelete="SET NULL"), nullable=True)
    needs_review  = Column(Boolean,    default=False)
    created_at    = Column(DateTime,   default=_utcnow)

    document          = relationship("Document",        back_populates="entity_mentions")
    session           = relationship("PipelineSession", back_populates="entity_mentions")
    canonical         = relationship("CanonicalEntity", back_populates="mentions")
    review_queue_item = relationship("ReviewQueue",     back_populates="entity_mention",
                                     uselist=False, cascade="all, delete-orphan")


class DiseaseRelation(Base):
    __tablename__ = "disease_relations"

    id           = Column(String(36),  primary_key=True)
    session_id   = Column(String(36),  ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    disease_name = Column(String(255), nullable=False)
    symptom_name = Column(String(255), nullable=False)
    confidence   = Column(Float,       nullable=False)
    created_at   = Column(DateTime,    default=_utcnow)

    session = relationship("PipelineSession", back_populates="disease_relations")


class MedicationRelation(Base):
    __tablename__ = "medication_relations"

    id                = Column(String(36),  primary_key=True)
    session_id        = Column(String(36),  ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    disease_name      = Column(String(255), nullable=False)
    medication_name   = Column(String(255), nullable=False)
    correct           = Column(Boolean,     default=True)
    confidence        = Column(Float,       nullable=False)
    dosage            = Column(String(100), nullable=True)
    frequency         = Column(String(100), nullable=True)
    duration          = Column(String(100), nullable=True)
    route             = Column(String(100), nullable=True)
    validation_status = Column(Text,        nullable=True)
    validation_reason = Column(Text,        nullable=True)
    created_at        = Column(DateTime,    default=_utcnow)

    session           = relationship("PipelineSession", back_populates="medication_relations")
    review_queue_item = relationship("ReviewQueue",     back_populates="medication_relation",
                                     uselist=False, cascade="all, delete-orphan")


class ReviewQueue(Base):
    """
    Doctor review queue entry.

    Optimistic locking:
        version_number is incremented on every update. If two doctors try
        to resolve the same item simultaneously, the second update will detect
        a version mismatch and raise a ConcurrentUpdateError (HTTP 409).

    Soft delete:
        is_deleted=True marks items as deleted without removing from DB.
        All queries must filter is_deleted=False (enforced by MySQLStore).

    Locking:
        locked_by / lock_time support "under review" status so the UI can
        warn the second doctor that someone else is reviewing this item.
    """
    __tablename__ = "review_queue"

    id                    = Column(String(36), primary_key=True)
    session_id            = Column(String(36), ForeignKey("sessions.id",          ondelete="CASCADE"), nullable=False)
    entity_mention_id     = Column(String(36), ForeignKey("entity_mentions.id",   ondelete="CASCADE"), nullable=True)
    medication_relation_id= Column(String(36), ForeignKey("medication_relations.id", ondelete="CASCADE"), nullable=True)
    status                = Column(String(50), default="PENDING")  # PENDING, APPROVED, REJECTED, MODIFIED
    reason                = Column(Text,       nullable=True)
    # Optimistic locking
    version_number        = Column(Integer,    default=0, nullable=False)
    # Lock tracking (who is currently reviewing)
    locked_by             = Column(String(36), nullable=True)
    lock_time             = Column(DateTime,   nullable=True)
    # Resolution tracking
    reviewed_by           = Column(String(100),nullable=True)
    reviewed_at           = Column(DateTime,   nullable=True)
    # Soft delete
    is_deleted            = Column(Boolean,    default=False, index=True)
    deleted_at            = Column(DateTime,   nullable=True)
    deleted_by            = Column(String(36), nullable=True)

    created_at = Column(DateTime, default=_utcnow)

    session            = relationship("PipelineSession", back_populates="review_items")
    entity_mention     = relationship("EntityMention",   back_populates="review_queue_item")
    medication_relation= relationship("MedicationRelation", back_populates="review_queue_item")


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id                = Column(String(36), primary_key=True)
    entity_mention_id = Column(String(36), nullable=True)
    review_queue_id   = Column(String(36), nullable=True)
    reviewer          = Column(String(100),nullable=False)
    action            = Column(String(50), nullable=False)  # APPROVED, REJECTED, MODIFIED, APPROVED_ALL
    old_value         = Column(Text,       nullable=True)
    new_value         = Column(Text,       nullable=True)
    created_at        = Column(DateTime,   default=_utcnow)


class PatientHistory(Base):
    __tablename__ = "patient_history"

    id           = Column(String(36), primary_key=True)
    user_id      = Column(String(36), ForeignKey("users.id",    ondelete="CASCADE"), nullable=False)
    session_id   = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    summary_json = Column(JSON,       nullable=False)
    # Soft delete
    is_deleted   = Column(Boolean,    default=False, index=True)
    deleted_at   = Column(DateTime,   nullable=True)
    deleted_by   = Column(String(36), nullable=True)
    created_at   = Column(DateTime,   default=_utcnow)

    user    = relationship("User",           back_populates="patient_histories")
    session = relationship("PipelineSession",back_populates="patient_histories")


class PHIAuditLog(Base):
    __tablename__ = "phi_audit_log"

    id              = Column(String(36),  primary_key=True)
    session_id      = Column(String(36),  ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    field_type      = Column(String(50),  nullable=False)
    original_value  = Column(String(255), nullable=False)
    redacted_value  = Column(String(255), nullable=False)
    created_at      = Column(DateTime,    default=_utcnow)

    session = relationship("PipelineSession", back_populates="phi_audit_logs")


class AuditLog(Base):
    """
    Immutable audit trail for all significant actions in the system.

    Satisfies HIPAA requirement: every access to or modification of PHI
    must be logged with actor, timestamp, and change details.

    Never deleted — this table grows forever (archive to cold storage after 7 years).
    """
    __tablename__ = "audit_logs"

    id            = Column(String(36),  primary_key=True)
    actor_user_id = Column(String(36),  nullable=True,  index=True)   # NULL = system action
    action        = Column(String(100), nullable=False,  index=True)  # e.g. "REVIEW_APPROVE"
    resource_type = Column(String(50),  nullable=True)                # e.g. "ReviewQueue"
    resource_id   = Column(String(36),  nullable=True,  index=True)   # PK of affected record
    old_value     = Column(Text,        nullable=True)
    new_value     = Column(Text,        nullable=True)
    ip_address    = Column(String(45),  nullable=True)                # IPv4 or IPv6
    notes         = Column(Text,        nullable=True)
    previous_hash = Column(String(64),  nullable=True)                # SHA-256 cryptographic chain
    current_hash  = Column(String(64),  nullable=True)                # SHA-256 cryptographic chain
    timestamp     = Column(DateTime,    default=_utcnow, index=True)
