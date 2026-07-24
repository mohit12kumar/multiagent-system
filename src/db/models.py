import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.db.connection import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    sessions = relationship(
        "PipelineSession", back_populates="document", cascade="all, delete-orphan")
    entity_mentions = relationship(
        "EntityMention", back_populates="document", cascade="all, delete-orphan")


class PipelineSession(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey(
        "documents.id", ondelete="CASCADE"), nullable=False)
    # PENDING, IN_PROGRESS, COMPLETED, FAILED
    status = Column(String(50), nullable=False)
    # PREPROCESSING, EXTRACTION, AGGREGATION, DISAMBIGUATION, etc.
    current_stage = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="sessions")
    entity_mentions = relationship(
        "EntityMention", back_populates="session", cascade="all, delete-orphan")
    review_items = relationship(
        "ReviewQueue", back_populates="session", cascade="all, delete-orphan")
    phi_audit_logs = relationship(
        "PHIAuditLog", back_populates="session", cascade="all, delete-orphan")


class CanonicalEntity(Base):
    __tablename__ = "canonical_entities"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    wikidata_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    mentions = relationship("EntityMention", back_populates="canonical")


class EntityMention(Base):
    __tablename__ = "entity_mentions"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey(
        "documents.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(36), ForeignKey(
        "sessions.id", ondelete="CASCADE"), nullable=False)
    text = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    # comma-separated string, e.g. "spacy,hf"
    source_agents = Column(String(255), nullable=False)
    canonical_id = Column(String(36), ForeignKey(
        "canonical_entities.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="entity_mentions")
    session = relationship("PipelineSession", back_populates="entity_mentions")
    canonical = relationship("CanonicalEntity", back_populates="mentions")
    review_queue_item = relationship(
        "ReviewQueue", back_populates="entity_mention", uselist=False, cascade="all, delete-orphan")
    review_logs = relationship(
        "ReviewLog", back_populates="entity_mention", cascade="all, delete-orphan")


class ReviewQueue(Base):
    __tablename__ = "review_queue"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey(
        "sessions.id", ondelete="CASCADE"), nullable=False)
    entity_mention_id = Column(String(36), ForeignKey(
        "entity_mentions.id", ondelete="CASCADE"), nullable=False)
    # PENDING, RESOLVED, IGNORED
    status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    session = relationship("PipelineSession", back_populates="review_items")
    entity_mention = relationship(
        "EntityMention", back_populates="review_queue_item")


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(String(36), primary_key=True)
    entity_mention_id = Column(String(36), ForeignKey(
        "entity_mentions.id", ondelete="CASCADE"), nullable=False)
    reviewer = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)  # APPROVED, REJECTED, MODIFIED
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    entity_mention = relationship(
        "EntityMention", back_populates="review_logs")


class PHIAuditLog(Base):
    __tablename__ = "phi_audit_log"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey(
        "sessions.id", ondelete="CASCADE"), nullable=False)
    field_type = Column(String(50), nullable=False)
    original_value = Column(String(255), nullable=False)
    redacted_value = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    session = relationship("PipelineSession", back_populates="phi_audit_logs")
