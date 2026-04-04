from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, index=True)
    preferred_language = Column(String, default="English")
    current_language = Column(String, default="English")
    conversation_score = Column(Integer, default=0)
    is_hot_lead = Column(Boolean, default=False)
    manager_notified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())