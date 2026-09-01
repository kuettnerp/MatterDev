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


def test_index_embed_hides_header():
    cameras = [Camera(id="front_door", name="Front Door", rtsp_url="rtsp://x/stream", enabled=True)]
    client = _client_with_cameras(cameras)

    normal = client.get("/")
    embed = client.get("/", params={"embed": "1"})

    assert "<header>" in normal.text
    assert "<header>" not in embed.text
    assert "Front Door" in embed.text


def test_index_filtered_to_single_camera():
    cameras = [
        Camera(id="front_door", name="Front Door", rtsp_url="rtsp://x/stream", enabled=True),
        Camera(id="backyard", name="Backyard", rtsp_url="rtsp://y/stream", enabled=True),
    ]
    client = _client_with_cameras(cameras)

    response = client.get("/", params={"camera_id": "backyard"})
    assert response.status_code == 200
    assert "Backyard" in response.text
    assert "Front Door" not in response.text


def test_index_unknown_camera_id_404s():
    cameras = [Camera(id="front_door", name="Front Door", rtsp_url="rtsp://x/stream", enabled=True)]
    client = _client_with_cameras(cameras)

    response = client.get("/", params={"camera_id": "nonexistent"})
    assert response.status_code == 404


def test_motion_event_accepted_for_known_camera():
    cameras = [Camera(id="front_door", name="Front Door", rtsp_url="rtsp://x/stream", enabled=True)]
    client = _client_with_cameras(cameras)

    response = client.post("/api/events/front_door/motion")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_motion_event_rejected_for_unknown_camera():
    client = _client_with_cameras([])

    response = client.post("/api/events/nonexistent/motion")
    assert response.status_code == 404


def test_basic_auth_enforced(monkeypatch):
    from app.settings import settings

    monkeypatch.setattr(settings, "basic_auth_user", "admin")
    monkeypatch.setattr(settings, "basic_auth_pass", "secret")

    client = _client_with_cameras([])

    response = client.get("/")
    assert response.status_code == 401

    response = client.get("/", auth=("admin", "secret"))
    assert response.status_code == 200
