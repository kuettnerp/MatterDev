import pytest

from app.config import load_cameras


def test_load_cameras(tmp_path):
    config_file = tmp_path / "cameras.yaml"
    config_file.write_text(
        """
cameras:
  - id: front_door
    name: "Front Door"
    rtsp_url: "rtsp://user:pass@192.168.50.10:554/stream"
    enabled: true
  - id: disabled_cam
    name: "Disabled"
    rtsp_url: "rtsp://user:pass@192.168.50.11:554/stream"
    enabled: false
"""
    )

    cameras = load_cameras(str(config_file))

    assert len(cameras) == 2
    assert cameras[0].id == "front_door"
    assert cameras[0].enabled is True
    assert cameras[1].enabled is False


def test_load_cameras_missing_file(tmp_path):
    missing_path = tmp_path / "does_not_exist.yaml"

    with pytest.raises(FileNotFoundError):
        load_cameras(str(missing_path))


def test_load_cameras_empty_file(tmp_path):
    config_file = tmp_path / "cameras.yaml"
    config_file.write_text("")

    assert load_cameras(str(config_file)) == []


def test_camera_hls_url(tmp_path, monkeypatch):
    from app.settings import settings

    monkeypatch.setattr(settings, "public_host", "10.0.0.5")
    monkeypatch.setattr(settings, "mediamtx_hls_port", 8888)

    config_file = tmp_path / "cameras.yaml"
    config_file.write_text(
        """
cameras:
  - id: backyard
    name: "Backyard"
    rtsp_url: "rtsp://192.168.50.12:554/stream"
"""
    )

    cameras = load_cameras(str(config_file))

    assert cameras[0].hls_url == "http://10.0.0.5:8888/backyard/index.m3u8"
