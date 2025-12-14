"""API routes package initialization."""

from .jobs import router as job_router
from .sync import router as sync_router
from .tasks import (
    categories_router,
    reminders_router,
    subtasks_router,
    tasks_router,
    time_blocks_router,
)
from .websocket import router as websocket_router

__all__ = [
    "job_router",
    "websocket_router",
    "sync_router",
    "categories_router",
    "tasks_router",
    "subtasks_router",
    "reminders_router",
    "time_blocks_router",
]
