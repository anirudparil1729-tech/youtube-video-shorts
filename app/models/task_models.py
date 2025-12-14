"""Task/time-management domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Column, DateTime, Field, Integer, JSON, SQLModel, String, Text


def _uuid_str() -> str:
    return str(uuid.uuid4())


class SyncMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False),
    )
    is_deleted: bool = Field(default=False)
    deleted_at: datetime | None = Field(default=None, sa_column=Column(DateTime, nullable=True))


class TaskCategory(SyncMixin, table=True):
    __tablename__ = "task_categories"

    id: str = Field(default_factory=_uuid_str, sa_column=Column(String, primary_key=True, index=True))
    name: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    color: str | None = Field(default=None, sa_column=Column(String, nullable=True))


class Task(SyncMixin, table=True):
    __tablename__ = "tasks"

    id: str = Field(default_factory=_uuid_str, sa_column=Column(String, primary_key=True, index=True))

    category_id: str | None = Field(default=None, foreign_key="task_categories.id", index=True)

    title: str = Field(sa_column=Column(String, nullable=False))
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    due_at: datetime | None = Field(default=None, sa_column=Column(DateTime, nullable=True))
    recurrence: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))

    estimated_minutes: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    actual_minutes: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))

    priority: int = Field(default=0, ge=0, le=10)

    is_completed: bool = Field(default=False)
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime, nullable=True))
    completion_notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))


class SubTask(SyncMixin, table=True):
    __tablename__ = "subtasks"

    id: str = Field(default_factory=_uuid_str, sa_column=Column(String, primary_key=True, index=True))
    task_id: str = Field(foreign_key="tasks.id", index=True)

    title: str = Field(sa_column=Column(String, nullable=False))
    is_completed: bool = Field(default=False)
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime, nullable=True))


class Reminder(SyncMixin, table=True):
    __tablename__ = "reminders"

    id: str = Field(default_factory=_uuid_str, sa_column=Column(String, primary_key=True, index=True))
    task_id: str = Field(foreign_key="tasks.id", index=True)

    remind_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    note: str | None = Field(default=None, sa_column=Column(Text, nullable=True))


class TimeBlock(SyncMixin, table=True):
    __tablename__ = "time_blocks"

    id: str = Field(default_factory=_uuid_str, sa_column=Column(String, primary_key=True, index=True))
    task_id: str | None = Field(default=None, foreign_key="tasks.id", index=True)

    start_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    end_at: datetime = Field(sa_column=Column(DateTime, nullable=False))

    planned_minutes: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    actual_minutes: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))

    note: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
