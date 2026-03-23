import json
import uuid
from datetime import datetime

import pytest

from fastapi import status

from api.models.job import Job, JobStatus, JobType
from api.models.user import User
from api.utils.security import get_password_hash


def _make_dummy_job(task_name: str, model_type: str, parameters: dict) -> Job:
    return Job(
        job_id="job_dummy_001",
        user_id=1,
        job_type=JobType.MODEL_TRAIN,
        status=JobStatus.SUBMITTED,
        progress=0,
        current_step="已提交，等待执行",
        input_params=json.dumps(
            {
                "task_name": task_name,
                "model_type": model_type,
                "training_type": "ignored",
                "parameters": parameters,
                "dataset_path": None,
            },
            ensure_ascii=False,
        ),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        result_file=None,
        error_message=None,
    )


@pytest.mark.parametrize(
    "endpoint, model_type, method_name",
    [
        ("/api/v1/training/supervised", "cnn", "create_supervised_task"),
        ("/api/v1/training/unsupervised", "vae", "create_unsupervised_task"),
        ("/api/v1/training/semi-supervised", "ladder", "create_semi_supervised_task"),
    ],
)
def test_training_router_passes_email_to_service(
    client, test_db, monkeypatch, endpoint: str, model_type: str, method_name: str
):
    called = {}

    # 为避免与固定 fixture 用户冲突，这里每次创建唯一用户并登录
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    test_db.add(
        User(
            username=username,
            email=email,
            password_hash=get_password_hash("Password123"),
            is_active=True,
            is_admin=False,
        )
    )
    test_db.commit()

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "Password123"},
    )
    assert login_resp.status_code == status.HTTP_200_OK
    token = login_resp.json()["access_token"]

    async def fake_create(*args, **kwargs):
        called.update(kwargs)
        return _make_dummy_job("task_dummy", model_type, parameters={"strategy": "upload"})

    monkeypatch.setattr(f"api.routers.training.TrainingService.{method_name}", fake_create)

    resp = client.post(
        endpoint,
        json={
            "task_name": "task_dummy",
            "model_type": model_type,
            "parameters": {"strategy": "upload"},
            "email": "user_notify@example.com",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert called.get("email") == "user_notify@example.com"

