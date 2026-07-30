"""
backend/core/prompt_budget.py

Prompt token budgeting and automatic text truncation to prevent LLM token explosion
and HTTP 413 / context length errors when sending long clinical notes or RAG contexts.
"""

import logging

logger = logging.getLogger(__name__)

MAX_PROMPT_TOKENS = 4000  # Safe default for Ollama / Groq context budgets

def estimate_tokens(text: str) -> int:
    """Approximate token count (roughly 1 token per 4 characters for English/medical text)."""
    if not text:
        return 0
    return len(text) // 4

def truncate_text_to_token_budget(text: str, max_tokens: int = MAX_PROMPT_TOKENS) -> str:
    """
    Truncates text if it exceeds max_tokens budget.
    Appends a truncation notice if trimmed.
    """
    if not text:
        return ""

    est = estimate_tokens(text)
    if est <= max_tokens:
        return text

    max_chars = max_tokens * 4
    truncated = text[:max_chars]
    # Try to trim at end of sentence
    last_period = truncated.rfind(".")
    if last_period > max_chars * 0.8:
        truncated = truncated[:last_period + 1]

    notice = "\n\n[...Clinical note truncated to fit LLM token budget...]"
    logger.warning(f"[PromptBudget] Text truncated from ~{est} tokens to ~{max_tokens} tokens.")
    return truncated + notice
