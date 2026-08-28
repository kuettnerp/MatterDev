from pathlib import Path

import yaml

from app.models import Camera


def load_cameras(path: str) -> list[Camera]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"{path} not found. Copy config/cameras.example.yaml to config/cameras.yaml "
            "and fill in your cameras (see tools/discover_cameras.py)."
        )

    data = yaml.safe_load(config_path.read_text()) or {}
    return [Camera(**entry) for entry in data.get("cameras", [])]
