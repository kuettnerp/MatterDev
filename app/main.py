from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import load_cameras
from app.routes import router
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cameras = load_cameras(settings.cameras_config_path)
    yield


app = FastAPI(title="MatterDev Camera Viewer", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
