import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.db import engine, Base
from app.routers import predict, recommendations, explain, whatif
from app.routers import auth as auth_router
from app.routers import ingest as ingest_router
from app.services.scheduler import create_scheduler

# Register models with Base so create_all works
import app.models.user    # noqa
import app.models.reading  # noqa

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables + start scheduler
    Base.metadata.create_all(bind=engine)
    scheduler = create_scheduler()
    scheduler.start()
    print("[Urja AI] DB ready. Scheduler started — ingesting every 15 min.")
    yield
    # Shutdown
    scheduler.shutdown(wait=False)
    print("[Urja AI] Scheduler stopped.")


app = FastAPI(
    title="Urja AI — Campus Energy Optimization API",
    description=(
        "Backend API for campus energy optimization. "
        "Authenticate via POST /auth/login, then include "
        "'Authorization: Bearer <token>' on all other requests."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(predict.router)
app.include_router(recommendations.router)
app.include_router(explain.router)
app.include_router(whatif.router)
app.include_router(ingest_router.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Urja AI Backend v2", "docs": "/docs"}


@app.get("/buildings", tags=["Buildings"])
def list_buildings():
    from app.services.data import KNOWN_BUILDINGS
    return {"buildings": KNOWN_BUILDINGS}
