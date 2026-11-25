# Shared FastAPI dependencies: DB session and authentication.

from backend.database.connection import get_db  # noqa: F401
from backend.auth import require_auth            # noqa: F401

# Re-export so routes can import from one place:
#   from backend.api.dependencies import get_db, require_auth
