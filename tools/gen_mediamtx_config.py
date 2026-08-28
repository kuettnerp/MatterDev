#!/usr/bin/env python3
"""Generate deploy/mediamtx/mediamtx.generated.yml from config/cameras.yaml +
config/mediamtx.template.yml. Run automatically by mediamtx.service before
MediaMTX starts (see deploy/systemd/mediamtx.service) - cameras.yaml is the
only file you should ever hand-edit.
"""

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CAMERAS_PATH = REPO_ROOT / "config" / "cameras.yaml"
TEMPLATE_PATH = REPO_ROOT / "config" / "mediamtx.template.yml"
OUTPUT_PATH = REPO_ROOT / "deploy" / "mediamtx" / "mediamtx.generated.yml"


def main() -> int:
    if not CAMERAS_PATH.exists():
        print(
            f"error: {CAMERAS_PATH} not found. Copy config/cameras.example.yaml "
            "to config/cameras.yaml and fill in your cameras first.",
            file=sys.stderr,
        )
        return 1

    base_config = yaml.safe_load(TEMPLATE_PATH.read_text()) or {}
    cameras = yaml.safe_load(CAMERAS_PATH.read_text()).get("cameras", [])

    paths = {}
    for camera in cameras:
        if not camera.get("enabled", True):
            continue
        paths[camera["id"]] = {"source": camera["rtsp_url"]}

    base_config["paths"] = paths

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(yaml.safe_dump(base_config, sort_keys=False))
    print(f"wrote {OUTPUT_PATH} with {len(paths)} camera path(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
