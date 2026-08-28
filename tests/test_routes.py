from fastapi.testclient import TestClient

from app.main import app
from app.models import Camera


def _client_with_cameras(cameras: list[Camera]) -> TestClient:
    client = TestClient(app)
    app.state.cameras = cameras
    return client


def test_healthz():
    client = _client_with_cameras([])
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.text == "ok"


def test_index_with_no_cameras():
    client = _client_with_cameras([])
    response = client.get("/")
    assert response.status_code == 200
    assert "No cameras configured" in response.text


def test_index_with_cameras():
    cameras = [
        Camera(id="front_door", name="Front Door", rtsp_url="rtsp://x/stream", enabled=True),
        Camera(id="hidden", name="Hidden", rtsp_url="rtsp://y/stream", enabled=False),
    ]
    client = _client_with_cameras(cameras)
    response = client.get("/")
    assert response.status_code == 200
    assert "Front Door" in response.text
    assert "Hidden" not in response.text


def test_api_cameras():
    cameras = [Camera(id="front_door", name="Front Door", rtsp_url="rtsp://x/stream", enabled=True)]
    client = _client_with_cameras(cameras)
    response = client.get("/api/cameras")
    assert response.status_code == 200
    body = response.json()
    assert body == [
        {
            "id": "front_door",
            "name": "Front Door",
            "hls_url": cameras[0].hls_url,
        }
    ]


def test_basic_auth_enforced(monkeypatch):
    from app.settings import settings

    monkeypatch.setattr(settings, "basic_auth_user", "admin")
    monkeypatch.setattr(settings, "basic_auth_pass", "secret")

    client = _client_with_cameras([])

    response = client.get("/")
    assert response.status_code == 401

    response = client.get("/", auth=("admin", "secret"))
    assert response.status_code == 200
