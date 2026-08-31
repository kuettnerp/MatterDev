from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates

from app.auth import require_auth
from app.models import Camera

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/healthz", response_class=PlainTextResponse)
def healthz() -> str:
    return "ok"


@router.get("/api/cameras")
def api_cameras(request: Request, _: None = Depends(require_auth)) -> list[dict]:
    cameras: list[Camera] = request.app.state.cameras
    return [
        {"id": c.id, "name": c.name, "hls_url": c.hls_url}
        for c in cameras
        if c.enabled
    ]


@router.get("/")
def index(request: Request, embed: bool = False, _: None = Depends(require_auth)):
    cameras: list[Camera] = request.app.state.cameras
    enabled_cameras = [c for c in cameras if c.enabled]
    return templates.TemplateResponse(
        request, "index.html", {"cameras": enabled_cameras, "embed": embed}
    )
