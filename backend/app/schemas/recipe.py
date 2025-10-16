"""
Pydantic schemas for Recipe API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional


class RecipeBase(BaseModel):
    """Base schema with common recipe attributes."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    age_min_months: int = Field(..., ge=4, le=36)
    age_max_months: Optional[int] = Field(None, ge=4, le=36)
    preparation_time_min: Optional[int] = Field(None, ge=1, le=300)
    difficulty_level: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")

    ingredients: list[dict] = Field(..., min_length=1)
    instructions: Optional[str] = None

    # Nutritional information
    calories: Optional[float] = Field(None, ge=0)
    protein_g: Optional[float] = Field(None, ge=0)
    carbs_g: Optional[float] = Field(None, ge=0)
    fat_g: Optional[float] = Field(None, ge=0)
    fiber_g: Optional[float] = Field(None, ge=0)
    sugar_g: Optional[float] = Field(None, ge=0)

    # Micronutrients
    iron_mg: Optional[float] = Field(None, ge=0)
    calcium_mg: Optional[float] = Field(None, ge=0)
    vitamin_a_mcg: Optional[float] = Field(None, ge=0)
    vitamin_c_mg: Optional[float] = Field(None, ge=0)
    vitamin_d_mcg: Optional[float] = Field(None, ge=0)

    # Categories
    meal_type: Optional[str] = None
    cuisine: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    serving_size_g: float = Field(default=100.0, gt=0)


class RecipeCreate(RecipeBase):
    """Schema for creating a new recipe."""
    pass


class RecipeUpdate(BaseModel):
    """Schema for updating a recipe. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    age_min_months: Optional[int] = Field(None, ge=4, le=36)
    age_max_months: Optional[int] = Field(None, ge=4, le=36)
    preparation_time_min: Optional[int] = Field(None, ge=1, le=300)
    difficulty_level: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    ingredients: Optional[list[dict]] = None
    instructions: Optional[str] = None
    calories: Optional[float] = Field(None, ge=0)
    protein_g: Optional[float] = Field(None, ge=0)
    carbs_g: Optional[float] = Field(None, ge=0)
    fat_g: Optional[float] = Field(None, ge=0)
    fiber_g: Optional[float] = Field(None, ge=0)
    sugar_g: Optional[float] = Field(None, ge=0)
    iron_mg: Optional[float] = Field(None, ge=0)
    calcium_mg: Optional[float] = Field(None, ge=0)
    vitamin_a_mcg: Optional[float] = Field(None, ge=0)
    vitamin_c_mg: Optional[float] = Field(None, ge=0)
    vitamin_d_mcg: Optional[float] = Field(None, ge=0)
    meal_type: Optional[str] = None
    cuisine: Optional[str] = None
    tags: Optional[list[str]] = None
    allergens: Optional[list[str]] = None
    serving_size_g: Optional[float] = Field(None, gt=0)


class RecipeResponse(RecipeBase):
    """Schema for recipe response."""
    id: int
    nutrition_score: float  # Computed field

    class Config:
        from_attributes = True


class RecipeWithScore(RecipeResponse):
    """Recipe with recommendation score."""
    recommendation_score: float = Field(..., ge=0, le=1)
    match_reason: str  # Why this recipe was recommended