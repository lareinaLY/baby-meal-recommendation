"""
Baby profile model for storing infant information and preferences.
"""
from sqlalchemy import Column, Integer, String, Date, Float, JSON
from sqlalchemy.orm import relationship
from datetime import date

from app.core.database import Base


class Baby(Base):
    """
    Represents a baby profile in the system.
    Stores basic info, health data, and taste preferences.
    """
    __tablename__ = "babies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)

    # Health information
    weight_kg = Column(Float)  # Current weight in kilograms
    height_cm = Column(Float)  # Current height in centimeters
    allergies = Column(JSON, default=list)  # List of allergens to avoid

    # Dietary preferences and restrictions
    dietary_restrictions = Column(JSON, default=list)  # e.g., ["vegetarian", "no_dairy"]
    liked_ingredients = Column(JSON, default=list)  # Ingredients baby enjoys
    disliked_ingredients = Column(JSON, default=list)  # Ingredients baby dislikes

    # Metadata
    created_at = Column(Date, default=date.today)

    # Relationships
    feedbacks = relationship("Feedback", back_populates="baby", cascade="all, delete-orphan")

    def get_age_months(self) -> int:
        """Calculate baby's age in months."""
        today = date.today()
        months = (today.year - self.birth_date.year) * 12 + today.month - self.birth_date.month
        return months

    def get_age_stage(self) -> str:
        """
        Determine developmental stage based on age.

        Stages:
        - 4-6 months: introduction to solids
        - 6-8 months: pureed foods
        - 8-10 months: mashed foods
        - 10-12 months: chopped foods
        - 12+ months: family foods
        """
        months = self.get_age_months()

        if months < 4:
            return "milk_only"
        elif months < 6:
            return "introduction"
        elif months < 8:
            return "pureed"
        elif months < 10:
            return "mashed"
        elif months < 12:
            return "chopped"
        else:
            return "family_foods"