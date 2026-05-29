"""
Database Models — SQLAlchemy ORM tabloları
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database.base import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    jobs = relationship("JobDB", back_populates="user", cascade="all, delete-orphan")


class JobDB(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    # Input
    prompt = Column(String, nullable=False)
    backend = Column(String, nullable=False)
    output_format = Column(String, nullable=False)
    num_steps = Column(Integer, default=64)
    guidance_scale = Column(Float, default=15.0)
    mesh_resolution = Column(Integer, default=128)

    # Runtime state
    status = Column(String, default="pending", index=True)
    progress = Column(Integer, default=0)
    current_stage = Column(String, nullable=True)

    # Output
    output_path = Column(String, nullable=True)
    output_url = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

    # Metadata
    job_metadata = Column(JSON, default=dict)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    user = relationship("UserDB", back_populates="jobs")
