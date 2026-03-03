"""
seed_users.py — Run once to create default user accounts.

Usage:
    cd backend
    python seed_users.py
"""
import sys
from pathlib import Path

# Ensure the app package is importable
sys.path.insert(0, str(Path(__file__).parent))

from app.db import engine, SessionLocal, Base
from app.models.user import User
from app.services.auth import hash_password

# Import all models so they are registered with Base
import app.models.reading  # noqa

DEFAULT_USERS = [
    {"username": "admin",  "password": "urjaai123",  "role": "admin"},
    {"username": "viewer", "password": "urjaai456",  "role": "viewer"},
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for u in DEFAULT_USERS:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if existing:
                print(f"  [skip] '{u['username']}' already exists")
                continue
            user = User(
                username=u["username"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
            )
            db.add(user)
            print(f"  [create] '{u['username']}' (role={u['role']})")
        db.commit()
        print("\nSeeding complete. Credentials:")
        for u in DEFAULT_USERS:
            print(f"  {u['username']} / {u['password']}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding users...")
    seed()
