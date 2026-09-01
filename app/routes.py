import asyncio
import json
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.auth import require_auth
from app.events import broker
from app.models import Camera

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# How often to send an SSE keepalive comment while waiting for a real event,
# so proxies/browsers don't time out an idle connection.
_SSE_KEEPALIVE_SECONDS = 15


@router.get("/healthz", response_class=PlainTextResponse)
def healthz() -> str:
    return "ok"


@router.post("/api/events/{camera_id}/motion")
async def motion_event(camera_id: str, request: Request) -> dict:
    """Webhook a camera (or any detector) hits to report motion.

    No auth - matches this app's LAN-only posture (see app/auth.py) and cameras
    generally can't be configured to send Basic Auth credentials on their event
    HTTP actions anyway.
    """
    cameras: list[Camera] = request.app.state.cameras
    if not any(c.id == camera_id for c in cameras):
        raise HTTPException(status_code=404, detail=f"Unknown camera '{camera_id}'")

    await broker.publish({"camera_id": camera_id, "event": "motion", "ts": time.time()})
    return {"status": "ok"}


@router.get("/api/events/stream")
async def events_stream(request: Request, _: None = Depends(require_auth)) -> StreamingResponse:
    queue = broker.subscribe()

    async def event_source():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=_SSE_KEEPALIVE_SECONDS)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            broker.unsubscribe(queue)

    return StreamingResponse(event_source(), media_type="text/event-stream")


@router.get("/api/cameras")
def api_cameras(request: Request, _: None = Depends(require_auth)) -> list[dict]:
    cameras: list[Camera] = request.app.state.cameras
    return [
        {"id": c.id, "name": c.name, "hls_url": c.hls_url}
        for c in cameras
        if c.enabled
    ]


@router.get("/")
def index(
    request: Request,
    embed: bool = False,
    camera_id: str | None = None,
    muted: bool = True,
    _: None = Depends(require_auth),
):
    cameras: list[Camera] = request.app.state.cameras
    enabled_cameras = [c for c in cameras if c.enabled]

    if camera_id is not None:
        enabled_cameras = [c for c in enabled_cameras if c.id == camera_id]
        if not enabled_cameras:
            raise HTTPException(status_code=404, detail=f"Unknown camera '{camera_id}'")

    return templates.TemplateResponse(
        request, "index.html", {"cameras": enabled_cameras, "embed": embed, "muted": muted}
    )
