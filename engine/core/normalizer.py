"""Shared input normalization for honeypot detectors."""

import re
import unicodedata
from urllib.parse import unquote, unquote_plus

MAX_INPUT_LENGTH = 8_192
_WHITESPACE_RE = re.compile(r"\s+")


def normalize(
    value: str,
    *,
    max_rounds: int = 3,
    plus_as_space: bool = False,
) -> str:
    """Normalize untrusted text into a standard form for pattern matching.

    Steps:
    1. Bound input length to ``MAX_INPUT_LENGTH`` characters.
    2. URL-decode repeatedly until stable or ``max_rounds`` is reached.
    3. Strip null bytes (``\\x00``).
    4. Apply Unicode NFKC normalization.
    5. Collapse whitespace runs to a single space and lowercase.
    6. When ``plus_as_space`` is True, decode ``+`` as space (form data).

    Never resolves ``..``, never raises on strange input, and performs no I/O.
    """
    if not value:
        return ""
    if not isinstance(value, str):
        value = str(value)

    text = value[:MAX_INPUT_LENGTH]

    decoder = unquote_plus if plus_as_space else unquote
    for _ in range(max(0, max_rounds)):
        decoded = decoder(text)
        if decoded == text:
            break
        text = decoded

    text = text.replace("\x00", "")
    text = unicodedata.normalize("NFKC", text)
    text = _WHITESPACE_RE.sub(" ", text).lower()
    return text
