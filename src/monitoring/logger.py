import logging
import json
import os
import sys
from contextvars import ContextVar
from typing import Any, Dict

# Context variables to store correlation/session IDs
session_id_var: ContextVar[str] = ContextVar("session_id", default="global")
agent_name_var: ContextVar[str] = ContextVar(
    "agent_name", default="orchestrator")


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON log records.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "file": record.pathname,
            "line": record.lineno,
            "session_id": session_id_var.get(),
            "agent": agent_name_var.get(),
        }

        # Add exception details if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class FlushingStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

def setup_logger(name: str = "multiagent_ner") -> logging.Logger:
    """
    Configures and returns the logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if already setup
    if logger.handlers:
        return logger

    handler = FlushingStreamHandler(sys.stdout)

    # Choose JSON formatting in production/development, or fallback to simple
    env = os.getenv("ENV", "development")
    if env in ("production", "development"):
        formatter = JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%SZ")
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [Session: %(session_id)s] [Agent: %(agent)s] %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Attach file handler to persist logs to logs/app.log
    try:
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"), encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass

    # Avoid propagating to the root logger
    logger.propagate = False

    return logger


# Global logger instance
logger = setup_logger()


def set_log_context(session_id: str, agent_name: str = "orchestrator") -> None:
    """Sets the log context variables."""
    session_id_var.set(session_id)
    agent_name_var.set(agent_name)


def clear_log_context() -> None:
    """Clears/resets the log context variables."""
    session_id_var.set("global")
    agent_name_var.set("orchestrator")
