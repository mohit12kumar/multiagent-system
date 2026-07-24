import re
import unicodedata


def remove_extra_whitespace(text: str) -> str:
    """Replaces multiple whitespaces or tabs with a single space."""
    return re.sub(r'[ \t]+', ' ', text)


def remove_extra_newlines(text: str) -> str:
    """Replaces multiple consecutive newlines with at most two newlines."""
    return re.sub(r'\n{3,}', '\n\n', text)


def normalize_unicode(text: str) -> str:
    """Normalizes accented characters and special unicode symbols."""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')


def clean_text(text: str, remove_whitespace: bool = True, normalize: bool = True) -> str:
    """Applies pipeline text cleaning options."""
    if not text:
        return ""

    cleaned = text
    if normalize:
        cleaned = normalize_unicode(cleaned)
    if remove_whitespace:
        cleaned = remove_extra_whitespace(cleaned)
        cleaned = remove_extra_newlines(cleaned)

    return cleaned.strip()
