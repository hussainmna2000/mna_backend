from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(50), unique=True, index=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)  # 'user', 'admin', 'superadmin'
    status = Column(String(50), default="active", nullable=False)  # 'active', 'suspended', 'pending'
    is_verified = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Real estate client project assignment
    project_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    detections = relationship("ScamDetection", back_populates="user")
    reports = relationship("ScamReport", foreign_keys="[ScamReport.user_id]", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    project = relationship("Property", foreign_keys=[project_id], back_populates="assigned_clients")
    inquiries = relationship("Inquiry", foreign_keys="[Inquiry.user_id]", back_populates="user")
    bookings = relationship("SiteVisitBooking", foreign_keys="[SiteVisitBooking.user_id]", back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
