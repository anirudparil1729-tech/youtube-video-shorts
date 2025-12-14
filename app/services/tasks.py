"""CRUD/service helpers for tasks/time-management domain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from sqlmodel import Session, select

from app.models.task_models import Reminder, SubTask, Task, TaskCategory, TimeBlock
from app.schemas.task_schemas import (
    CategoryCreate,
    CategoryUpdate,
    ReminderCreate,
    SubTaskCreate,
    SubTaskToggleRequest,
    TaskCreate,
    TaskUpdate,
    TimeBlockCreate,
)


DEFAULT_CATEGORIES: tuple[tuple[str, str | None], ...] = (
    ("Personal", None),
    ("Work", None),
)


def seed_default_categories(session: Session) -> None:
    for name, color in DEFAULT_CATEGORIES:
        statement = select(TaskCategory).where(TaskCategory.name == name)
        category = session.exec(statement).first()
        if category:
            if category.is_deleted:
                category.is_deleted = False
                category.deleted_at = None
                category.updated_at = datetime.utcnow()
                session.add(category)
            continue

        session.add(TaskCategory(name=name, color=color))

    session.commit()


def list_categories(session: Session, *, include_deleted: bool = False) -> list[TaskCategory]:
    statement = select(TaskCategory)
    if not include_deleted:
        statement = statement.where(TaskCategory.is_deleted.is_(False))
    statement = statement.order_by(TaskCategory.name.asc())
    return list(session.exec(statement).all())


def create_category(session: Session, payload: CategoryCreate) -> TaskCategory:
    category = TaskCategory(name=payload.name, color=payload.color)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def update_category(
    session: Session, category_id: str, payload: CategoryUpdate
) -> TaskCategory | None:
    category = session.get(TaskCategory, category_id)
    if not category:
        return None

    fields_set = getattr(payload, "model_fields_set", payload.__fields_set__)

    if "name" in fields_set:
        category.name = payload.name
    if "color" in fields_set:
        category.color = payload.color
    if "is_deleted" in fields_set:
        category.is_deleted = bool(payload.is_deleted)
        category.deleted_at = datetime.utcnow() if category.is_deleted else None

    category.updated_at = datetime.utcnow()
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def delete_category(session: Session, category_id: str) -> bool:
    category = session.get(TaskCategory, category_id)
    if not category:
        return False
    category.is_deleted = True
    category.deleted_at = datetime.utcnow()
    category.updated_at = datetime.utcnow()
    session.add(category)
    session.commit()
    return True


def create_task(session: Session, payload: TaskCreate) -> Task:
    task = Task(
        title=payload.title,
        category_id=payload.category_id,
        notes=payload.notes,
        due_at=payload.due_at,
        recurrence=payload.recurrence,
        estimated_minutes=payload.estimated_minutes,
        actual_minutes=payload.actual_minutes,
        priority=payload.priority,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_task(session: Session, task_id: str) -> Task | None:
    return session.get(Task, task_id)


def list_tasks(
    session: Session,
    *,
    include_deleted: bool = False,
    category_id: str | None = None,
) -> list[Task]:
    statement = select(Task)
    if not include_deleted:
        statement = statement.where(Task.is_deleted.is_(False))
    if category_id is not None:
        statement = statement.where(Task.category_id == category_id)
    statement = statement.order_by(Task.updated_at.desc())
    return list(session.exec(statement).all())


def update_task(session: Session, task_id: str, payload: TaskUpdate) -> Task | None:
    task = session.get(Task, task_id)
    if not task:
        return None

    fields_set = getattr(payload, "model_fields_set", payload.__fields_set__)

    if "title" in fields_set:
        task.title = payload.title  # type: ignore[assignment]
    if "category_id" in fields_set:
        task.category_id = payload.category_id
    if "notes" in fields_set:
        task.notes = payload.notes
    if "due_at" in fields_set:
        task.due_at = payload.due_at
    if "recurrence" in fields_set:
        task.recurrence = payload.recurrence
    if "estimated_minutes" in fields_set:
        task.estimated_minutes = payload.estimated_minutes
    if "actual_minutes" in fields_set:
        task.actual_minutes = payload.actual_minutes
    if "priority" in fields_set and payload.priority is not None:
        task.priority = payload.priority

    if "is_completed" in fields_set:
        task.is_completed = bool(payload.is_completed)
        task.completed_at = datetime.utcnow() if task.is_completed else None

    if "completion_notes" in fields_set:
        task.completion_notes = payload.completion_notes

    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task_id: str) -> bool:
    task = session.get(Task, task_id)
    if not task:
        return False

    task.is_deleted = True
    task.deleted_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    return True


def create_subtask(session: Session, payload: SubTaskCreate) -> SubTask:
    subtask = SubTask(task_id=payload.task_id, title=payload.title)
    session.add(subtask)
    session.commit()
    session.refresh(subtask)
    return subtask


def toggle_subtask(
    session: Session, subtask_id: str, payload: SubTaskToggleRequest
) -> SubTask | None:
    subtask = session.get(SubTask, subtask_id)
    if not subtask:
        return None

    subtask.is_completed = payload.is_completed
    subtask.completed_at = datetime.utcnow() if payload.is_completed else None
    subtask.updated_at = datetime.utcnow()
    session.add(subtask)
    session.commit()
    session.refresh(subtask)
    return subtask


def create_reminder(session: Session, payload: ReminderCreate) -> Reminder:
    reminder = Reminder(task_id=payload.task_id, remind_at=payload.remind_at, note=payload.note)
    session.add(reminder)
    session.commit()
    session.refresh(reminder)
    return reminder


def create_time_block(session: Session, payload: TimeBlockCreate) -> TimeBlock:
    time_block = TimeBlock(
        task_id=payload.task_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        planned_minutes=payload.planned_minutes,
        actual_minutes=payload.actual_minutes,
        note=payload.note,
    )
    session.add(time_block)
    session.commit()
    session.refresh(time_block)
    return time_block


def _since_filter(model: Any, since: datetime | None) -> Any:
    if since is None:
        return True
    return model.updated_at > since


def get_sync_payload(session: Session, *, since: datetime | None) -> tuple[
    list[TaskCategory],
    list[Task],
    list[SubTask],
    list[Reminder],
    list[TimeBlock],
]:
    categories = list(session.exec(select(TaskCategory).where(_since_filter(TaskCategory, since))).all())
    tasks = list(session.exec(select(Task).where(_since_filter(Task, since))).all())
    subtasks = list(session.exec(select(SubTask).where(_since_filter(SubTask, since))).all())
    reminders = list(session.exec(select(Reminder).where(_since_filter(Reminder, since))).all())
    time_blocks = list(session.exec(select(TimeBlock).where(_since_filter(TimeBlock, since))).all())
    return categories, tasks, subtasks, reminders, time_blocks


def _choose_update(existing_updated_at: datetime | None, incoming_updated_at: datetime) -> bool:
    if existing_updated_at is None:
        return True
    return incoming_updated_at > existing_updated_at


def _apply_sync_entity(
    session: Session,
    model_cls: Any,
    incoming: Any,
    apply_fields: Iterable[str],
) -> tuple[bool, str]:
    existing = session.get(model_cls, incoming.id)
    if existing is None:
        entity = model_cls(**incoming.model_dump())
        session.add(entity)
        return True, incoming.id

    if not _choose_update(getattr(existing, "updated_at", None), incoming.updated_at):
        return False, incoming.id

    for field in apply_fields:
        setattr(existing, field, getattr(incoming, field))

    existing.created_at = incoming.created_at
    existing.updated_at = incoming.updated_at
    existing.is_deleted = incoming.is_deleted
    existing.deleted_at = incoming.deleted_at

    session.add(existing)
    return True, incoming.id


def apply_sync_upserts(session: Session, payload: Any) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    applied: dict[str, list[str]] = {"categories": [], "tasks": [], "subtasks": [], "reminders": [], "time_blocks": []}
    conflicts: dict[str, list[str]] = {"categories": [], "tasks": [], "subtasks": [], "reminders": [], "time_blocks": []}

    for incoming in payload.categories:
        ok, entity_id = _apply_sync_entity(session, TaskCategory, incoming, ["name", "color"])
        (applied if ok else conflicts)["categories"].append(entity_id)

    for incoming in payload.tasks:
        ok, entity_id = _apply_sync_entity(
            session,
            Task,
            incoming,
            [
                "title",
                "category_id",
                "notes",
                "due_at",
                "recurrence",
                "estimated_minutes",
                "actual_minutes",
                "priority",
                "is_completed",
                "completed_at",
                "completion_notes",
            ],
        )
        (applied if ok else conflicts)["tasks"].append(entity_id)

    for incoming in payload.subtasks:
        ok, entity_id = _apply_sync_entity(
            session,
            SubTask,
            incoming,
            ["task_id", "title", "is_completed", "completed_at"],
        )
        (applied if ok else conflicts)["subtasks"].append(entity_id)

    for incoming in payload.reminders:
        ok, entity_id = _apply_sync_entity(
            session,
            Reminder,
            incoming,
            ["task_id", "remind_at", "note"],
        )
        (applied if ok else conflicts)["reminders"].append(entity_id)

    for incoming in payload.time_blocks:
        ok, entity_id = _apply_sync_entity(
            session,
            TimeBlock,
            incoming,
            [
                "task_id",
                "start_at",
                "end_at",
                "planned_minutes",
                "actual_minutes",
                "note",
            ],
        )
        (applied if ok else conflicts)["time_blocks"].append(entity_id)

    session.commit()
    return applied, conflicts
