"""
Baby model - Updated with user relationship
"""
from sqlalchemy import Column, Integer, String, Float, Date, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from app.core.database import Base


class Baby(Base):
    """Baby profile model"""
    __tablename__ = "babies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # NEW
    name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    allergies = Column(JSON, default=list)
    liked_ingredients = Column(JSON, default=list)
    disliked_ingredients = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="babies")  # NEW
    feedbacks = relationship("Feedback", back_populates="baby", cascade="all, delete-orphan")

    @property
    def age_months(self) -> int:
        """Calculate baby's age in months"""
        today = date.today()
        delta = relativedelta(today, self.birth_date)
        return delta.years * 12 + delta.months
    
    @property
    def age_months(self) -> int:
        """Calculate baby's age in months"""
        today = date.today()
        delta = relativedelta(today, self.birth_date)
        return delta.years * 12 + delta.months

    @property
    def age_stage(self) -> str:
        """Get baby's developmental stage"""
        months = self.age_months
        if months < 6:
            return "early_infancy"
        elif months < 12:
            return "late_infancy"
        elif months < 24:
            return "toddler"
        else:
            return "preschooler"

    def __repr__(self):
        return f"<Baby {self.name}, {self.age_months} months>"