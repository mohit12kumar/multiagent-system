"""
backend/core/circuit_breaker.py

Circuit Breaker pattern for external services (Ollama, Groq, ChromaDB, MySQL).
Prevents system resource exhaustion and cascading failures when external dependencies are down or timing out.
"""

import time
import logging
import threading
from typing import Callable, Any, Dict, Type, Tuple

logger = logging.getLogger(__name__)

class CircuitState:
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Tripped, immediately rejects calls
    HALF_OPEN = "HALF_OPEN"# Probing recovery

class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()
        self._lock = threading.Lock()

    def __call__(self, fn: Callable[..., Any], *args, **kwargs) -> Any:
        with self._lock:
            now = time.time()
            if self.state == CircuitState.OPEN:
                if now - self.last_state_change > self.recovery_timeout:
                    logger.info(f"[CircuitBreaker] '{self.name}' transition OPEN -> HALF_OPEN (probing recovery).")
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = now
                else:
                    raise RuntimeError(
                        f"CircuitBreaker '{self.name}' is OPEN. Fast-failing request (recovery in "
                        f"{round(self.recovery_timeout - (now - self.last_state_change), 1)}s)."
                    )

        try:
            result = fn(*args, **kwargs)
            with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    logger.info(f"[CircuitBreaker] '{self.name}' probe succeeded. Transition HALF_OPEN -> CLOSED.")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.last_state_change = time.time()
            return result
        except self.expected_exceptions as exc:
            with self._lock:
                self.failure_count += 1
                logger.warning(
                    f"[CircuitBreaker] '{self.name}' failure #{self.failure_count}/{self.failure_threshold}: {exc}"
                )
                if self.failure_count >= self.failure_threshold:
                    logger.error(f"[CircuitBreaker] '{self.name}' threshold reached. Tripping to OPEN state.")
                    self.state = CircuitState.OPEN
                    self.last_state_change = time.time()
            raise exc

_breakers: Dict[str, CircuitBreaker] = {}
_breaker_lock = threading.Lock()

def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> CircuitBreaker:
    with _breaker_lock:
        if name not in _breakers:
            _breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exceptions=expected_exceptions
            )
        return _breakers[name]
