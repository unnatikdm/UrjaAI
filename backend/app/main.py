import os

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.db import engine, Base
from app.routers import predict, recommendations, explain, whatif, rag
from app.routers import auth as auth_router
from app.routers import ingest as ingest_router
from app.routers import enhanced_recommendations
from app.services.scheduler import create_scheduler
from app.routers import sustainability
from app.routers import browniepoint1
# from app.routers import browniepoint2
from app.routers import rag_integration
from app.services.rag.rag_service import rag_service

# Import models so SQLAlchemy registers them with Base
import app.models.user    # noqa
import app.models.reading  # noqa

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Start sensor data scheduler
    scheduler = create_scheduler()
    scheduler.start()
    print("[Urja AI] DB ready. Scheduler started — ingesting every 15 min.")

    # # from app.services.tabtransformer_manager import manager

    # Initialize RAG Service (handled by rag_integration router startup)
    # try:
    #     rag_service.initialize()
    # except Exception as e:
    #     print(f"[Urja AI] Error initializing RAG: {e}")

    yield  # app runs here

    # ── Shutdown ─────────────────────────────────────────────────────────────
    scheduler.shutdown(wait=False)
    print("[Urja AI] Scheduler stopped.")


app = FastAPI(
    title="Urja AI — Campus Energy Optimization API",
    description=(
        "Backend API for the campus energy consumption prediction and "
        "optimization system. Authenticate via POST /auth/login to get a JWT, "
        "then include it as 'Authorization: Bearer <token>' on all other requests."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────────────────────
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(predict.router)
app.include_router(recommendations.router)
app.include_router(explain.router)
app.include_router(whatif.router)
app.include_router(ingest_router.router)
app.include_router(sustainability.router)
app.include_router(browniepoint1.router)
# app.include_router(browniepoint2.router)
# app.include_router(rag.router)
app.include_router(rag_integration.router)
app.include_router(enhanced_recommendations.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Urja AI Backend v2", "docs": "/docs"}


@app.get("/buildings", tags=["Buildings"])
def list_buildings():
    from app.services.data import KNOWN_BUILDINGS
    return {"buildings": KNOWN_BUILDINGS}
