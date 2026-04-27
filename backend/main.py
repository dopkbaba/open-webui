import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# Environment configuration
ENV = os.environ.get("ENV", "dev")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
SECRET_KEY = os.environ.get("SECRET_KEY", "open-webui-secret-key")
VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    log.info(f"Starting Open WebUI v{VERSION} (ENV={ENV})")
    # Startup logic (DB init, model loading, etc.) goes here
    yield
    # Shutdown logic (cleanup, closing connections) goes here
    log.info("Shutting down Open WebUI")


app = FastAPI(
    title="Open WebUI",
    description="A user-friendly web interface for interacting with LLMs.",
    version=VERSION,
    docs_url="/docs" if ENV == "dev" else None,
    redoc_url="/redoc" if ENV == "dev" else None,
    lifespan=lifespan,
)

# Session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS middleware — allow frontend origin in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to return structured error responses."""
    log.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint used by load balancers and container orchestrators."""
    return {"status": "ok", "version": VERSION}


@app.get("/version", tags=["info"])
async def get_version():
    """Return the current application version."""
    return {"version": VERSION}


# ---------------------------------------------------------------------------
# Router registration (routers will be added as the project grows)
# ---------------------------------------------------------------------------
# from apps.auth.routers import router as auth_router
# from apps.chat.routers import router as chat_router
# from apps.models.routers import router as models_router
#
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
# app.include_router(models_router, prefix="/api/v1/models", tags=["models"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=ENV == "dev",
        log_level="info",
    )
