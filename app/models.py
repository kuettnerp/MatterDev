from pydantic import BaseModel

from app.settings import settings


class Camera(BaseModel):
    id: str
    name: str
    rtsp_url: str
    enabled: bool = True

    @property
    def hls_url(self) -> str:
        return f"http://{settings.public_host}:{settings.mediamtx_hls_port}/{self.id}/index.m3u8"
