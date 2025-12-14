"""Pydantic schemas for the task/time-management domain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str
    color: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    is_deleted: bool | None = None


class CategoryRead(BaseModel):
    id: str
    name: str
    color: str | None = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    category_id: str | None = None
    notes: str | None = None
    due_at: datetime | None = None
    recurrence: dict[str, Any] | None = None
    estimated_minutes: int | None = Field(default=None, ge=0)
    actual_minutes: int | None = Field(default=None, ge=0)
    priority: int = Field(default=0, ge=0, le=10)


class TaskUpdate(BaseModel):
    title: str | None = None
    category_id: str | None = None
    notes: str | None = None
    due_at: datetime | None = None
    recurrence: dict[str, Any] | None = None
    estimated_minutes: int | None = Field(default=None, ge=0)
    actual_minutes: int | None = Field(default=None, ge=0)
    priority: int | None = Field(default=None, ge=0, le=10)
    is_completed: bool | None = None
    completion_notes: str | None = None


class TaskRead(BaseModel):
    id: str
    title: str
    category_id: str | None = None
    notes: str | None = None
    due_at: datetime | None = None
    recurrence: dict[str, Any] | None = None
    estimated_minutes: int | None = None
    actual_minutes: int | None = None
    priority: int
    is_completed: bool
    completed_at: datetime | None = None
    completion_notes: str | None = None

    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: datetime | None = None

    class Config:
        from_attributes = True


class SubTaskCreate(BaseModel):
    task_id: str
    title: str


class SubTaskUpdate(BaseModel):
    title: str | None = None
    is_completed: bool | None = None


class SubTaskToggleRequest(BaseModel):
    is_completed: bool = True


class SubTaskRead(BaseModel):
    id: str
    task_id: str
    title: str
    is_completed: bool
    completed_at: datetime | None = None

    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: datetime | None = None

    class Config:
        from_attributes = True


class ReminderCreate(BaseModel):
    task_id: str
    remind_at: datetime
    note: str | None = None


class ReminderRead(BaseModel):
    id: str
    task_id: str
    remind_at: datetime
    note: str | None = None

    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: datetime | None = None

    class Config:
        from_attributes = True


class TimeBlockCreate(BaseModel):
    task_id: Optional[str] = None
    start_at: datetime
    end_at: datetime
    planned_minutes: int | None = Field(default=None, ge=0)
    actual_minutes: int | None = Field(default=None, ge=0)
    note: str | None = None


class TimeBlockRead(BaseModel):
    id: str
    task_id: str | None = None
    start_at: datetime
    end_at: datetime
    planned_minutes: int | None = None
    actual_minutes: int | None = None
    note: str | None = None

    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: datetime | None = None

    class Config:
        from_attributes = True


class SyncUpsertResponse(BaseModel):
    applied: dict[str, list[str]]
    conflicts: dict[str, list[str]]
    server_time: datetime


class SyncPayload(BaseModel):
    categories: list[CategoryRead] = Field(default_factory=list)
    tasks: list[TaskRead] = Field(default_factory=list)
    subtasks: list[SubTaskRead] = Field(default_factory=list)
    reminders: list[ReminderRead] = Field(default_factory=list)
    time_blocks: list[TimeBlockRead] = Field(default_factory=list)
    server_time: datetime


class SyncUpsertPayload(BaseModel):
    categories: list[CategoryRead] = Field(default_factory=list)
    tasks: list[TaskRead] = Field(default_factory=list)
    subtasks: list[SubTaskRead] = Field(default_factory=list)
    reminders: list[ReminderRead] = Field(default_factory=list)
    time_blocks: list[TimeBlockRead] = Field(default_factory=list)
