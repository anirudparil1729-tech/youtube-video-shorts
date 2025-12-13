"""Compatibility entrypoint.

Historically this repo had multiple minimal app entrypoints. The canonical minimal
FastAPI app is now in `main.py`.

This module re-exports `app` so existing commands referencing `main_minimal:app`
continue to work.
"""

from __future__ import annotations

import uvicorn

from main import app


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
