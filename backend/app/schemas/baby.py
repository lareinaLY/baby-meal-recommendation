"""
Pydantic schemas for Baby API requests and responses.
"""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class BabyBase(BaseModel):
    """Base schema with common baby attributes."""
    name: str = Field(..., min_length=1, max_length=100)
    birth_date: date
    weight_kg: Optional[float] = Field(None, gt=0, le=30)
    height_cm: Optional[float] = Field(None, gt=0, le=150)
    allergies: list[str] = Field(default_factory=list)
    liked_ingredients: list[str] = Field(default_factory=list)
    disliked_ingredients: list[str] = Field(default_factory=list)


class BabyCreate(BabyBase):
    """Schema for creating a new baby profile."""
    pass


class BabyUpdate(BaseModel):
    """Schema for updating a baby profile. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_date: Optional[date] = None
    weight_kg: Optional[float] = Field(None, gt=0, le=30)
    height_cm: Optional[float] = Field(None, gt=0, le=150)
    allergies: Optional[list[str]] = None
    liked_ingredients: Optional[list[str]] = None
    disliked_ingredients: Optional[list[str]] = None


class BabyResponse(BabyBase):
    """Schema for baby profile response."""
    id: int
    created_at: datetime
    age_months: int  # Computed field
    age_stage: str  # Computed field

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models


class BabyWithStats(BabyResponse):
    """Extended baby response with statistics."""
    total_feedbacks: int = 0
    average_rating: float = 0.0
    acceptance_rate: float = 0.0