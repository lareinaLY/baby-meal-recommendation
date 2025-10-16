"""
Pydantic schemas for Feedback API requests and responses.
"""
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class FeedbackBase(BaseModel):
    """Base schema with common feedback attributes."""
    rating: float = Field(..., ge=1, le=5)
    accepted: bool
    prepared: bool = False
    baby_liked: Optional[bool] = None
    comments: Optional[str] = Field(None, max_length=500)
    rejection_reason: Optional[str] = Field(None, max_length=200)


class FeedbackCreate(FeedbackBase):
    """Schema for creating feedback."""
    baby_id: int = Field(..., gt=0)
    recipe_id: int = Field(..., gt=0)


class FeedbackUpdate(BaseModel):
    """Schema for updating feedback."""
    rating: Optional[float] = Field(None, ge=1, le=5)
    accepted: Optional[bool] = None
    prepared: Optional[bool] = None
    baby_liked: Optional[bool] = None
    comments: Optional[str] = Field(None, max_length=500)
    rejection_reason: Optional[str] = Field(None, max_length=200)


class FeedbackResponse(FeedbackBase):
    """Schema for feedback response."""
    id: int
    baby_id: int
    recipe_id: int
    recommended_at: date
    feedback_at: date
    feedback_score: float  # Computed field

    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    """Schema for requesting recipe recommendations."""
    baby_id: int = Field(..., gt=0)
    count: int = Field(default=5, ge=1, le=20)
    meal_type: Optional[str] = None
    exclude_recently_recommended: bool = True