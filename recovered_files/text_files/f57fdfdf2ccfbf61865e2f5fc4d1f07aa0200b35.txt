# Urja AI — Campus Energy Optimization

AI-powered energy consumption prediction and optimization system for campus buildings. Built with FastAPI (backend) and React + Vite (frontend).

---

## Quick Start

### 1. Backend

```bash
cd backend
python -m pip install -r requirements.txt
python seed_users.py          # creates default admin/viewer accounts
uvicorn app.main:app --reload
```

API available at **http://localhost:8000** · Swagger UI at **http://localhost:8000/docs**

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard at **http://localhost:5173**

---

## Default Credentials

| Username | Password     | Role   |
|----------|--------------|--------|
| `admin`  | `urjaai123`  | Admin  |
| `viewer` | `urjaai456`  | Viewer |

> ⚠️ Change these before any public deployment.

---

## Project Structure

```
UrjaAI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, scheduler startup
│   │   ├── db.py                # SQLite engine + session
│   │   ├── models/              # SQLAlchemy models (User, SensorReading)
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── routers/             # API endpoints
│   │   │   ├── auth.py          # POST /auth/login, GET /auth/me
│   │   │   ├── predict.py       # POST /predict
│   │   │   ├── recommendations.py
│   │   │   ├── explain.py       # POST /explain
│   │   │   ├── whatif.py        # POST /whatif
│   │   │   └── ingest.py        # POST /ingest (sensor data)
│   │   └── services/
│   │       ├── auth.py          # JWT + bcrypt
│   │       ├── data.py          # CSV / synthetic data access
│   │       ├── ml.py            # ← ML partner integrates here
│   │       └── scheduler.py     # APScheduler (15-min sensor ingestion)
│   ├── data/                    # Drop CSV files here (see data/README.md)
│   ├── seed_users.py            # One-time user seeding script
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx        # Auth gate
│   │   │   └── Dashboard.jsx    # Main dashboard page
│   │   ├── components/          # Header, ForecastChart, etc.
│   │   ├── hooks/
│   │   │   └── useDashboard.js  # Central state + data fetching
│   │   └── services/
│   │       ├── api.js           # Axios client + JWT interceptors
│   │       ├── auth.js          # Token storage + helpers
│   │       └── mockData.js      # Fallback when backend is offline
│   ├── .env.example
│   └── vite.config.js           # Dev proxy to backend
│
└── PARTNER_ML_GUIDE.md          # Instructions for ML integration
```

---

## ML Partner Integration

See [`backend/PARTNER_ML_GUIDE.md`](./backend/PARTNER_ML_GUIDE.md) for full instructions.

Implement these two functions in `backend/app/services/ml.py`:
- `run_forecast(building_id, ...)` → hourly predictions
- `get_explanation(building_id)` → SHAP feature attributions

---

## API Overview

All endpoints (except `/auth/login`, `/`, `/buildings`) require:
```
Authorization: Bearer <jwt_token>
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Get JWT token |
| GET | `/auth/me` | Current user info |
| POST | `/predict` | 24-hour energy forecast |
| POST | `/recommendations` | Load-shifting recommendations |
| POST | `/explain` | SHAP feature explanations |
| POST | `/whatif` | Scenario simulation |
| POST | `/ingest` | Ingest sensor reading (admin) |
| GET | `/ingest/latest` | Latest reading per building (admin) |
| GET | `/buildings` | List of campus buildings |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, APScheduler, python-jose, passlib |
| Database | SQLite (via SQLAlchemy) |
| Frontend | React 18, Vite, Tailwind CSS v3, Recharts, Axios |
| Auth | JWT (HS256, 8h expiry), bcrypt |
