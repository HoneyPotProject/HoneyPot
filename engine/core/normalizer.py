import unicodedata
from urllib.parse import unquote

from engine.core.config import EngineConfig

_DEFAULT_CONFIG = EngineConfig()


def normalize(text: str, config: EngineConfig = _DEFAULT_CONFIG) -> str:
    """Decode, clean and lowercase untrusted text.

    Steps:
      1. Bounded repeated URL-decoding (up to config.max_decode_rounds).
      2. Remove null bytes.
      3. Unicode NFKC normalization (lookalikes → standard form).
      4. Lowercase.
    """
    # Step 1 — bounded URL decode
    result = text
    for _ in range(config.max_decode_rounds):
        decoded = unquote(result)
        if decoded == result:      # nothing changed, stop early
            break
        result = decoded

    # Step 2 — remove null bytes
    result = result.replace("\x00", "")

    # Step 3 — Unicode normalization
    result = unicodedata.normalize("NFKC", result)

    # Step 4 — lowercase
    return result.lower()