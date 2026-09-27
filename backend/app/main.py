from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.db_setup import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown hooks."""
    # Startup: инициализация базы данных и сидинг
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Интерактивный тренажер проводников скоростного поезда (ВСМ) — API Service",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Настройка CORS для взаимодействия с Frontend (Vite / Bun / Production)
origins = [str(origin) for origin in settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов версии 1
app.include_router(api_router, prefix=settings.API_V1_STR)

# Раздача статики storage (если доступна локально или примонтирована в контейнер)
from fastapi.staticfiles import StaticFiles
from app.core.config import PROJECT_ROOT, BACKEND_DIR

_storage_dir = PROJECT_ROOT / "storage"
if not _storage_dir.exists():
    _storage_dir = BACKEND_DIR / "storage"
if _storage_dir.exists():
    app.mount("/storage", StaticFiles(directory=str(_storage_dir)), name="storage")


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Корневой эндпоинт со ссылкой на документацию."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
