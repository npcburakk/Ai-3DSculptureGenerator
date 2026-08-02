"""
Text-to-3D Generator — Main Application Entry Point
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.paths import get_frontend_dir
from app.database.db_store import store
from app.utils.error_messages import GENERIC_ERROR, INVALID_INPUT_ERROR

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    store.initialize()  # Veritabanı tablolarını oluştur
    yield
    print("🛑 Application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Text-to-3D model generator",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")
app.include_router(router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc}")
    return JSONResponse(status_code=422, content={"detail": INVALID_INPUT_ERROR})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": GENERIC_ERROR})


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "jobs_in_db": store.count()}


# Frontend (index.html + static/) — tüm API route'larından ve
# exception handler'lardan SONRA, en son mount edilir. Starlette route'ları
# tanımlanma sırasına göre dener; bu mount en sonda olmazsa "/health" gibi
# sonradan eklenen route'ları gölgeleyip 404 döndürür. Eşleşmeyen her şey
# (ör. "/", "/static/images/...") için devreye girer.
app.mount("/", StaticFiles(directory=str(get_frontend_dir()), html=True), name="frontend")
