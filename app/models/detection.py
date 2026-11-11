from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class ScamDetection(Base):
    __tablename__ = "scam_detections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # 'phone', 'message', 'whatsapp', 'url', 'email', 'transaction', 'analyze'
    query_target = Column(Text, nullable=False)  # Phone number, URL, message text, email, or transaction hash
    risk_score = Column(Float, nullable=False)  # 0 to 100
    risk_level = Column(String(50), nullable=False, index=True)  # 'SAFE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    verdict = Column(String(100), nullable=False)  # 'Likely Scam', 'High Risk Phishing', 'Safe Verified', etc.
    threat_indicators = Column(JSON, nullable=True)  # List of identified red flags / indicators
    explanation = Column(Text, nullable=True)  # Detailed AI / rule-based assessment
    recommendations = Column(JSON, nullable=True)  # Guidance / actionable security advice
    metadata_info = Column(JSON, nullable=True)  # Additional intelligence (carrier, domain age, registrar, etc.)
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="detections")
