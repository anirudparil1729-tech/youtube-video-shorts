"""Reusable security dependencies."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_app_password(
    x_app_password: str | None = Header(default=None, alias="X-App-Password"),
) -> None:
    if not settings.app_password:
        return

    if x_app_password != settings.app_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-App-Password",
        )
