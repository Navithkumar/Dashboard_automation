"""Main FastAPI application factory and static mounts."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    # Ensure all output directories exist
    settings.output_dir
    settings.data_dir
    settings.logs_dir
    settings.screenshots_dir
    yield


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application."""
    app = FastAPI(
        title="OrangeHRM RPA Automation Dashboard",
        description="Dashboard-driven RPA automation system for OrangeHRM with live streaming logs, automated verification, and CSV/Excel exports.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static assets
    static_dir = settings.base_dir / "app" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Serve generated screenshots
    screenshots_dir = settings.screenshots_dir
    app.mount("/screenshots", StaticFiles(directory=str(screenshots_dir)), name="screenshots")

    # Include routes
    app.include_router(router)

    return app


app = create_app()
