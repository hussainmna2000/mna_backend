from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class ScamReport(Base):
    __tablename__ = "scam_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # 'phone', 'message', 'whatsapp', 'url', 'email', 'crypto', 'banking', 'investment', 'impersonation', 'other'
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    suspicious_phone = Column(String(50), nullable=True, index=True)
    suspicious_url = Column(String(500), nullable=True, index=True)
    suspicious_email = Column(String(255), nullable=True, index=True)
    evidence_url = Column(String(500), nullable=True)
    financial_loss = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)  # 'pending', 'under_review', 'verified', 'rejected', 'resolved'
    admin_notes = Column(Text, nullable=True)
    assigned_reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id], back_populates="reports")
    reviewer = relationship("User", foreign_keys=[assigned_reviewer_id])
