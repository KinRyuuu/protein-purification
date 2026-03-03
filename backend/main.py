"""FastAPI app entry point for the Protein Purification web backend."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import sessions, mixtures, separation, fractions, electrophoresis, files
from .dependencies import get_session_store, get_settings, get_data_dir, _WEB_PROJECT_ROOT


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown tasks."""
    settings = get_settings()
    store = get_session_store()
    app.state.settings = settings
    app.state.data_dir = get_data_dir(settings)
    yield
    store.cleanup_expired()


app = FastAPI(
    title="Protein Purification",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(mixtures.router)
app.include_router(separation.router)
app.include_router(fractions.router)
app.include_router(electrophoresis.router)
app.include_router(files.router)


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


# Serve the built frontend as static files. This is only active when
# frontend/dist exists (i.e. after `npm run build`), so dev mode is unaffected.
_frontend_dist = _WEB_PROJECT_ROOT / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="static")
