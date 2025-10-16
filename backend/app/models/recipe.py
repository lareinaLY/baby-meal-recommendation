"""
Recipe model for storing meal information and nutritional data.
"""
from sqlalchemy import Column, Integer, String, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recipe(Base):
    """
    Represents a baby meal recipe with nutritional information.
    """
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)

    # Recipe details
    age_min_months = Column(Integer, nullable=False)  # Minimum age in months
    age_max_months = Column(Integer)  # Maximum age (null = no limit)
    preparation_time_min = Column(Integer)  # Time in minutes
    difficulty_level = Column(String)  # easy, medium, hard

    # Ingredients and instructions
    ingredients = Column(JSON, nullable=False)  # List of ingredients with quantities
    instructions = Column(Text)

    # Nutritional information (per 100g)
    calories = Column(Float)
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fat_g = Column(Float)
    fiber_g = Column(Float)
    sugar_g = Column(Float)

    # Micronutrients (per 100g)
    iron_mg = Column(Float)
    calcium_mg = Column(Float)
    vitamin_a_mcg = Column(Float)
    vitamin_c_mg = Column(Float)
    vitamin_d_mcg = Column(Float)

    # Categories and tags
    meal_type = Column(String)  # breakfast, lunch, dinner, snack
    cuisine = Column(String)  # e.g., "Asian", "Mediterranean"
    tags = Column(JSON, default=list)  # e.g., ["vegetarian", "high_protein", "iron_rich"]
    allergens = Column(JSON, default=list)  # e.g., ["dairy", "eggs", "nuts"]

    # Metadata
    serving_size_g = Column(Float, default=100.0)  # Default serving size

    # Relationships
    feedbacks = relationship("Feedback", back_populates="recipe", cascade="all, delete-orphan")

    def is_suitable_for_age(self, age_months: int) -> bool:
        """Check if recipe is suitable for given age."""
        if age_months < self.age_min_months:
            return False
        if self.age_max_months and age_months > self.age_max_months:
            return False
        return True

    def has_allergen(self, allergen_list: list) -> bool:
        """Check if recipe contains any allergens from the list."""
        if not self.allergens or not allergen_list:
            return False
        return any(allergen in self.allergens for allergen in allergen_list)

    def get_nutrition_score(self) -> float:
        """
        Calculate a simple nutrition score (0-100).
        Higher protein, fiber, and micronutrients increase score.
        Higher sugar decreases score.
        """
        score = 50.0  # Base score

        # Protein boost (up to +20)
        if self.protein_g:
            score += min(self.protein_g * 2, 20)

        # Fiber boost (up to +10)
        if self.fiber_g:
            score += min(self.fiber_g * 3, 10)

        # Micronutrients boost (up to +15)
        if self.iron_mg:
            score += min(self.iron_mg, 5)
        if self.calcium_mg:
            score += min(self.calcium_mg / 20, 5)
        if self.vitamin_a_mcg:
            score += min(self.vitamin_a_mcg / 50, 5)

        # Sugar penalty (up to -20)
        if self.sugar_g:
            score -= min(self.sugar_g, 20)

        # Clamp between 0 and 100
        return max(0, min(score, 100))