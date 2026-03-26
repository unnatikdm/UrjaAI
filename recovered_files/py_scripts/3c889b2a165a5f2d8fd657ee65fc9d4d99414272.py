import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import predict, recommendations, explain, whatif

load_dotenv()

app = FastAPI(
    title="Urja AI — Campus Energy Optimization API",
    description=(
        "Backend API for the campus energy consumption prediction and "
        "optimization system. AI/ML endpoints are stubbed — see "
        "app/services/ml.py for integration points."
    ),
    version="1.0.0",
)

# ─────────────────────────────────────────────────────────────────────────────
# CORS — allow all origins in development; restrict in production
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
app.include_router(predict.router)
app.include_router(recommendations.router)
app.include_router(explain.router)
app.include_router(whatif.router)


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "Urja AI Backend",
        "docs": "/docs",
    }


@app.get("/buildings", tags=["Buildings"])
def list_buildings():
    """Return the list of campus buildings supported by the API."""
    from app.services.data import KNOWN_BUILDINGS
    return {"buildings": KNOWN_BUILDINGS}
