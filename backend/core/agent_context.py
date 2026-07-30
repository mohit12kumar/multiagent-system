"""
backend/core/agent_context.py

Request-scoped AgentContext object passed to all agents in the pipeline.
Agents must never store request-specific state in `self.*`. All transient request state,
correlations, metadata, and sentences are held inside this context object.
"""

import uuid
import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class AgentContext:
    session_id: str
    document_id: str
    user_id: Optional[str] = "anonymous"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat(),
            "text_length": len(self.text),
            "metadata": self.metadata,
        }
