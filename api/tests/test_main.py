import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_redis():
    with patch("main.r") as mock_r:
        yield mock_r


@pytest.fixture
def client(mock_redis):
    from main import app

    return TestClient(app)


def test_health_ok(client, mock_redis):
    mock_redis.ping.return_value = True
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_redis_down(client, mock_redis):
    import redis as redis_lib

    mock_redis.ping.side_effect = redis_lib.exceptions.ConnectionError("down")
    response = client.get("/health")
    assert response.status_code == 503


def test_create_job(client, mock_redis):
    mock_redis.lpush.return_value = 1
    mock_redis.hset.return_value = 1
    response = client.post("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36


def test_get_job_found(client, mock_redis):
    mock_redis.hget.return_value = "queued"
    response = client.get("/jobs/test-job-id")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-job-id"
    assert data["status"] == "queued"


def test_get_job_not_found(client, mock_redis):
    mock_redis.hget.return_value = None
    response = client.get("/jobs/nonexistent-id")
    assert response.status_code == 404


def test_create_job_uses_correct_queue_key(client, mock_redis):
    mock_redis.lpush.return_value = 1
    mock_redis.hset.return_value = 1
    client.post("/jobs")
    call_args = mock_redis.lpush.call_args
    assert call_args[0][0] == "jobs"
