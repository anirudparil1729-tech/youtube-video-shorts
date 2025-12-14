import time

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.db.database import engine, init_db
from app.models.task_models import Reminder, SubTask, Task, TimeBlock
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_task_tables():
    init_db()
    with Session(engine) as session:
        session.exec(delete(SubTask))
        session.exec(delete(Reminder))
        session.exec(delete(TimeBlock))
        session.exec(delete(Task))
        session.commit()
    yield


def _headers() -> dict[str, str]:
    return {"X-App-Password": settings.app_password}


def test_task_creation():
    response = client.post("/api/v1/tasks/", json={"title": "Test task"}, headers=_headers())
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Test task"
    assert data["is_completed"] is False
    assert data["recurrence"] is None
    assert "id" in data


def test_recurrence_serialization_round_trip():
    recurrence = {"frequency": "daily", "interval": 2}
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Recurring", "recurrence": recurrence},
        headers=_headers(),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["recurrence"] == recurrence

    task_id = data["id"]
    get_response = client.get(f"/api/v1/tasks/{task_id}", headers=_headers())
    assert get_response.status_code == 200
    assert get_response.json()["recurrence"] == recurrence


def test_sync_since_filters_results():
    first = client.post("/api/v1/tasks/", json={"title": "First"}, headers=_headers()).json()
    since = first["updated_at"]

    time.sleep(0.02)

    second = client.post("/api/v1/tasks/", json={"title": "Second"}, headers=_headers()).json()

    sync_response = client.get("/api/v1/sync/", params={"since": since}, headers=_headers())
    assert sync_response.status_code == 200

    payload = sync_response.json()
    task_ids = {task["id"] for task in payload["tasks"]}
    assert second["id"] in task_ids
    assert first["id"] not in task_ids
