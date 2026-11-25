# Starts the honeypot, backend and monitor together in development.

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cmd = [
        sys.executable, '-m', 'uvicorn', 'backend.main:app',
        '--host', '127.0.0.1', '--port', '8000',
    ]
    raise SystemExit(subprocess.call(cmd, cwd=ROOT))


if __name__ == '__main__':
    main()
