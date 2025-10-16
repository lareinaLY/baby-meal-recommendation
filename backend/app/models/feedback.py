"""
Feedback model for tracking parental responses to recipe recommendations.
This enables the reinforcement learning loop.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from datetime import date

from app.core.database import Base


class Feedback(Base):
    """
    Stores parental feedback on recommended recipes.
    Used to improve future recommendations via reinforcement learning.
    """
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    baby_id = Column(Integer, ForeignKey("babies.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)

    # Feedback data
    rating = Column(Float, nullable=False)  # 1-5 star rating
    accepted = Column(Boolean, nullable=False)  # Did parent accept the recommendation?
    prepared = Column(Boolean, default=False)  # Did parent actually prepare it?
    baby_liked = Column(Boolean)  # Did baby enjoy the meal?

    # Additional feedback
    comments = Column(String)  # Optional text feedback
    rejection_reason = Column(String)  # Why was it rejected? (if applicable)

    # Metadata
    recommended_at = Column(Date, default=date.today)
    feedback_at = Column(Date, default=date.today)

    # Relationships
    baby = relationship("Baby", back_populates="feedbacks")
    recipe = relationship("Recipe", back_populates="feedbacks")

    def get_feedback_score(self) -> float:
        """
        Calculate a composite feedback score (0-1).
        Used for training the recommendation model.

        Scoring logic:
        - If rejected: 0.0
        - If accepted but not prepared: 0.3
        - If prepared but baby didn't like: 0.4
        - If prepared and baby liked: rating/5.0
        """
        if not self.accepted:
            return 0.0

        if not self.prepared:
            return 0.3

        if self.baby_liked is False:
            return 0.4

        # Baby liked it or no info - use rating
        return self.rating / 5.0

    @classmethod
    def get_rejection_rate_for_recipe(cls, session, recipe_id: int) -> float:
        """Calculate rejection rate for a specific recipe."""
        total = session.query(cls).filter(cls.recipe_id == recipe_id).count()
        if total == 0:
            return 0.0

        rejected = session.query(cls).filter(
            cls.recipe_id == recipe_id,
            cls.accepted == False
        ).count()

        return rejected / total