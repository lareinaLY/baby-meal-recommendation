"""
Basic content-based recommendation engine for MVP.
Later phases will add collaborative filtering and ML models.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple
from datetime import date, timedelta

from app.models.baby import Baby
from app.models.recipe import Recipe
from app.models.feedback import Feedback


class RecommendationEngine:
    """
    MVP version: Simple content-based filtering.
    Recommends recipes based on:
    1. Age appropriateness
    2. Allergen avoidance
    3. Ingredient preferences
    4. Nutritional score
    5. Past feedback (if available)
    """

    def __init__(self, db: Session):
        self.db = db

    def get_recommendations(
            self,
            baby: Baby,
            count: int = 5,
            meal_type: str = None,
            exclude_recent_days: int = 7
    ) -> List[Tuple[Recipe, float, str]]:
        """
        Get recipe recommendations for a baby.

        Args:
            baby: Baby profile
            count: Number of recommendations to return
            meal_type: Filter by meal type (optional)
            exclude_recent_days: Exclude recipes recommended in last N days

        Returns:
            List of tuples: (recipe, score, reason)
        """
        # Get all eligible recipes
        query = self.db.query(Recipe).filter(
            Recipe.age_min_months <= baby.age_months
        )

        # Filter by age maximum if specified
        query = query.filter(
            (Recipe.age_max_months.is_(None)) |
            (Recipe.age_max_months >= baby.age_months)
        )

        # Filter by meal type if specified
        if meal_type:
            query = query.filter(Recipe.meal_type == meal_type)

        recipes = query.all()

        # Exclude recently recommended recipes
        if exclude_recent_days > 0:
            recent_cutoff = date.today() - timedelta(days=exclude_recent_days)
            recent_feedbacks = self.db.query(Feedback.recipe_id).filter(
                Feedback.baby_id == baby.id,
                Feedback.recommended_at >= recent_cutoff
            ).distinct().all()

            # Extract recipe_id from query results (each result is a tuple)
            recent_recipe_ids = set(f[0] for f in recent_feedbacks)
            recipes = [r for r in recipes if r.id not in recent_recipe_ids]

        # Score each recipe
        scored_recipes = []
        for recipe in recipes:
            score, reason = self._calculate_recipe_score(baby, recipe)
            if score > 0:  # Only include recipes with positive scores
                scored_recipes.append((recipe, score, reason))

        # Sort by score and return top N
        scored_recipes.sort(key=lambda x: x[1], reverse=True)
        return scored_recipes[:count]

    def _calculate_recipe_score(
            self,
            baby: Baby,
            recipe: Recipe
    ) -> Tuple[float, str]:
        """
        Calculate recommendation score for a recipe (0-1).

        Scoring components:
        1. Base nutrition score (0.3 weight)
        2. Preference match (0.3 weight)
        3. Historical performance (0.4 weight)

        Returns:
            (score, reason_for_recommendation)
        """
        reasons = []

        # Check for allergens (immediate disqualification)
        if recipe.has_allergen(baby.allergies):
            return 0.0, "Contains allergens"

        # 1. Nutrition score (0-1)
        nutrition_score = recipe.get_nutrition_score() / 100.0

        # 2. Preference match score (0-1)
        preference_score = self._calculate_preference_score(baby, recipe)

        # 3. Historical performance score (0-1)
        historical_score = self._calculate_historical_score(baby, recipe)

        # Weighted combination
        final_score = (
                0.3 * nutrition_score +
                0.3 * preference_score +
                0.4 * historical_score
        )

        # Build explanation
        if nutrition_score > 0.7:
            reasons.append("high nutritional value")

        if preference_score > 0.6:
            reasons.append("matches taste preferences")

        if historical_score > 0.7:
            reasons.append("similar recipes were enjoyed")
        elif historical_score > 0:
            reasons.append("appropriate for age stage")

        if not reasons:
            reasons.append("suitable for baby's age")

        reason_text = ", ".join(reasons).capitalize()

        return final_score, reason_text

    def _calculate_preference_score(self, baby: Baby, recipe: Recipe) -> float:
        """Calculate score based on ingredient preferences."""
        if not recipe.ingredients:
            return 0.5  # Neutral score if no ingredients listed

        # Extract ingredient names from recipe
        ingredient_names = [
            ing.get('name', '').lower()
            for ing in recipe.ingredients
        ]

        liked_count = sum(
            1 for liked in baby.liked_ingredients
            if any(liked.lower() in ing for ing in ingredient_names)
        )

        disliked_count = sum(
            1 for disliked in baby.disliked_ingredients
            if any(disliked.lower() in ing for ing in ingredient_names)
        )

        # Strong penalty for disliked ingredients
        if disliked_count > 0:
            return 0.1

        # Bonus for liked ingredients
        if liked_count > 0:
            return min(0.5 + (liked_count * 0.2), 1.0)

        return 0.5  # Neutral score

    def _calculate_historical_score(self, baby: Baby, recipe: Recipe) -> float:
        """
        Calculate score based on past feedback.
        If no feedback exists, use general recipe performance.
        """
        # Check baby's specific feedback for this recipe
        baby_feedback = self.db.query(Feedback).filter(
            Feedback.baby_id == baby.id,
            Feedback.recipe_id == recipe.id
        ).first()

        if baby_feedback:
            return baby_feedback.get_feedback_score()

        # Check general performance of this recipe
        avg_score = self.db.query(
            func.avg(Feedback.rating)
        ).filter(
            Feedback.recipe_id == recipe.id,
            Feedback.accepted == True
        ).scalar()

        if avg_score:
            return avg_score / 5.0  # Normalize to 0-1

        # No history - return neutral score
        return 0.5