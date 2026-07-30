"""
backend/core/retry.py

Generic retry-with-backoff utility for external service calls.

Usage:
    from backend.core.retry import with_retry

    result = with_retry(
        lambda: call_llm_api(prompt),
        max_attempts=3,
        backoff_seconds=1.0,
        exceptions=(requests.Timeout, groq.RateLimitError),
        label="LLM-Groq"
    )
"""

import time
import logging
from typing import Any, Callable, Tuple, Type

logger = logging.getLogger(__name__)


def with_retry(
    fn: Callable[[], Any],
    *,
    max_attempts: int = 3,
    backoff_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    label: str = "operation",
) -> Any:
    """
    Execute `fn` with exponential backoff retry on failure.

    Parameters
    ----------
    fn                : Zero-argument callable to retry.
    max_attempts      : Total number of attempts (including the first).
    backoff_seconds   : Initial wait time between retries (seconds).
    backoff_multiplier: Multiply backoff by this factor on each retry.
    exceptions        : Tuple of exception types to catch and retry on.
                        Other exceptions propagate immediately.
    label             : Human-readable name for logging.

    Returns
    -------
    The return value of fn() on success.

    Raises
    ------
    The last exception raised by fn() after all retries are exhausted.

    Example
    -------
    >>> def call_api():
    ...     return requests.get("https://api.example.com", timeout=10)
    >>> result = with_retry(call_api, max_attempts=3, label="ExampleAPI")
    """
    last_exc: Exception = RuntimeError("No attempts were made")

    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except exceptions as exc:
            last_exc = exc
            if attempt == max_attempts:
                logger.error(
                    f"[Retry] {label} failed after {max_attempts} attempts: {exc}"
                )
                break

            wait = backoff_seconds * (backoff_multiplier ** (attempt - 1))
            logger.warning(
                f"[Retry] {label} attempt {attempt}/{max_attempts} failed: {exc}. "
                f"Retrying in {wait:.1f}s..."
            )
            time.sleep(wait)

    raise last_exc


def with_db_retry(
    fn: Callable[[], Any],
    max_attempts: int = 3,
    backoff_seconds: float = 0.2,
    label: str = "DB Operation"
) -> Any:
    """
    Retry DB operations specifically on MySQL deadlock (1213) or lock wait timeout (1205).
    """
    from sqlalchemy.exc import OperationalError, DBAPIError

    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except (OperationalError, DBAPIError) as exc:
            last_exc = exc
            err_msg = str(exc)
            # Check for MySQL deadlock or lock wait timeout error codes
            is_deadlock = "1213" in err_msg or "Deadlock" in err_msg or "1205" in err_msg
            if not is_deadlock or attempt == max_attempts:
                logger.error(f"[DB Retry] {label} failed on attempt {attempt}/{max_attempts}: {exc}")
                raise exc

            wait = backoff_seconds * (2 ** (attempt - 1))
            logger.warning(
                f"[DB Retry] {label} hit DB lock/deadlock on attempt {attempt}/{max_attempts}. Retrying in {wait:.2f}s..."
            )
            time.sleep(wait)
        except Exception as exc:
            raise exc

    if last_exc:
        raise last_exc

