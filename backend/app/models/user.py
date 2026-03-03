from sqlalchemy import Column, Integer, String, Boolean
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="viewer")   # "admin" | "viewer"
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
