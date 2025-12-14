"""Task/time-management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.security import require_app_password
from app.db.database import get_session
from app.schemas.task_schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    ReminderCreate,
    ReminderRead,
    SubTaskCreate,
    SubTaskRead,
    SubTaskToggleRequest,
    TaskCreate,
    TaskRead,
    TaskUpdate,
    TimeBlockCreate,
    TimeBlockRead,
)
from app.services import tasks as task_service


categories_router = APIRouter(
    prefix="/categories",
    tags=["task-categories"],
    dependencies=[Depends(require_app_password)],
)

tasks_router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(require_app_password)],
)

subtasks_router = APIRouter(
    prefix="/subtasks",
    tags=["subtasks"],
    dependencies=[Depends(require_app_password)],
)

reminders_router = APIRouter(
    prefix="/reminders",
    tags=["reminders"],
    dependencies=[Depends(require_app_password)],
)

time_blocks_router = APIRouter(
    prefix="/time-blocks",
    tags=["time-blocks"],
    dependencies=[Depends(require_app_password)],
)


@categories_router.get("/", response_model=list[CategoryRead])
def list_categories(session: Session = Depends(get_session)) -> list[CategoryRead]:
    categories = task_service.list_categories(session)
    return [CategoryRead.model_validate(category) for category in categories]


@categories_router.post(
    "/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED
)
def create_category(
    payload: CategoryCreate, session: Session = Depends(get_session)
) -> CategoryRead:
    category = task_service.create_category(session, payload)
    return CategoryRead.model_validate(category)


@categories_router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: str, payload: CategoryUpdate, session: Session = Depends(get_session)
) -> CategoryRead:
    category = task_service.update_category(session, category_id, payload)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return CategoryRead.model_validate(category)


@categories_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, session: Session = Depends(get_session)) -> None:
    ok = task_service.delete_category(session, category_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


@tasks_router.get("/", response_model=list[TaskRead])
def list_tasks(
    category_id: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[TaskRead]:
    tasks = task_service.list_tasks(session, category_id=category_id)
    return [TaskRead.model_validate(task) for task in tasks]


@tasks_router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, session: Session = Depends(get_session)) -> TaskRead:
    task = task_service.create_task(session, payload)
    return TaskRead.model_validate(task)


@tasks_router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, session: Session = Depends(get_session)) -> TaskRead:
    task = task_service.get_task(session, task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskRead.model_validate(task)


@tasks_router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: str, payload: TaskUpdate, session: Session = Depends(get_session)
) -> TaskRead:
    task = task_service.update_task(session, task_id, payload)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskRead.model_validate(task)


@tasks_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, session: Session = Depends(get_session)) -> None:
    ok = task_service.delete_task(session, task_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")


@tasks_router.put("/{task_id}/recurrence", response_model=TaskRead)
def set_recurrence(
    task_id: str,
    payload: dict,
    session: Session = Depends(get_session),
) -> TaskRead:
    task = task_service.update_task(session, task_id, TaskUpdate(recurrence=payload))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskRead.model_validate(task)


@subtasks_router.post(
    "/", response_model=SubTaskRead, status_code=status.HTTP_201_CREATED
)
def create_subtask(payload: SubTaskCreate, session: Session = Depends(get_session)) -> SubTaskRead:
    subtask = task_service.create_subtask(session, payload)
    return SubTaskRead.model_validate(subtask)


@subtasks_router.post("/{subtask_id}/toggle", response_model=SubTaskRead)
def toggle_subtask(
    subtask_id: str, payload: SubTaskToggleRequest, session: Session = Depends(get_session)
) -> SubTaskRead:
    subtask = task_service.toggle_subtask(session, subtask_id, payload)
    if not subtask:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subtask not found")
    return SubTaskRead.model_validate(subtask)


@reminders_router.post(
    "/", response_model=ReminderRead, status_code=status.HTTP_201_CREATED
)
def create_reminder(
    payload: ReminderCreate, session: Session = Depends(get_session)
) -> ReminderRead:
    reminder = task_service.create_reminder(session, payload)
    return ReminderRead.model_validate(reminder)


@time_blocks_router.post(
    "/", response_model=TimeBlockRead, status_code=status.HTTP_201_CREATED
)
def create_time_block(
    payload: TimeBlockCreate, session: Session = Depends(get_session)
) -> TimeBlockRead:
    time_block = task_service.create_time_block(session, payload)
    return TimeBlockRead.model_validate(time_block)

