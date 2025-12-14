"""Offline sync endpoints for task/time-management domain."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.security import require_app_password
from app.db.database import get_session
from app.schemas.task_schemas import SyncPayload, SyncUpsertPayload, SyncUpsertResponse
from app.services.tasks import apply_sync_upserts, get_sync_payload


router = APIRouter(prefix="/sync", tags=["sync"], dependencies=[Depends(require_app_password)])


@router.get("/", response_model=SyncPayload)
def sync_get(
    since: datetime | None = Query(default=None, description="Return changes after this timestamp"),
    session: Session = Depends(get_session),
) -> SyncPayload:
    categories, tasks, subtasks, reminders, time_blocks = get_sync_payload(session, since=since)

    return SyncPayload(
        categories=[c for c in categories],
        tasks=[t for t in tasks],
        subtasks=[s for s in subtasks],
        reminders=[r for r in reminders],
        time_blocks=[tb for tb in time_blocks],
        server_time=datetime.utcnow(),
    )


@router.post("/", response_model=SyncUpsertResponse)
def sync_post(payload: SyncUpsertPayload, session: Session = Depends(get_session)) -> SyncUpsertResponse:
    applied, conflicts = apply_sync_upserts(session, payload)
    return SyncUpsertResponse(applied=applied, conflicts=conflicts, server_time=datetime.utcnow())
