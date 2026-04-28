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

# Personal note: I run this locally on port 5174 (Vite sometimes picks it when
# 5173 is already occupied), so added it to the default CORS origins list.
# Also added 5175 since I've seen Vite bump to that too on my machine.
EXTRA_CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("EXTRA_CORS_ORIGINS", "").split(",")
    if origin.strip()
]


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
# Personal note: bumped max_age from the default (2 weeks) to 7 days so my
# local sessions expire sooner — easier to test the login flow repeatedly.
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=60 * 60 * 24 * 7)

# CORS middleware — allow frontend origin in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:5174",  # fallback Vite dev server port
        "http://localhost:5175",  # Vite sometimes increments again if 5174 is taken
        "http://localhost:8080",
        *EXTRA_CORS_ORIGINS,
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


# --------------------------------------
