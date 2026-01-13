"""
Pydantic schemas for AI-enhanced recommendation features.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import date

from app.schemas.recipe import RecipeResponse


class AlternativeRecipe(BaseModel):
    """Alternative recipe suggestion for disliked ingredient."""
    recipe: RecipeResponse
    alternative_ingredient: str
    similarity_score: float = Field(..., ge=0, le=1)
    reason: str


class LLMAlternativeSuggestion(BaseModel):
    """LLM-generated alternative suggestion."""
    ingredient: str
    reason: str
    preparation_tip: str


class PreparationVariation(BaseModel):
    """Different preparation method for same ingredient."""
    recipe: RecipeResponse
    preparation_method: str


class RetryStrategy(BaseModel):
    """Retry strategy for disliked ingredient."""
    ingredient: str
    should_retry: bool
    reason: str
    different_preparations: List[str]  # Simplified: list of descriptions
    strategy: Dict[str, str]
    attempt_count: int
    next_retry_date: Optional[date] = None


class AlternativesForIngredient(BaseModel):
    """Complete alternatives package for a disliked ingredient."""
    ingredient: str
    nutrition_importance: str
    alternative_recipes: List[AlternativeRecipe]
    llm_suggestions: List[LLMAlternativeSuggestion]


class EnhancedRecommendation(BaseModel):
    """Enhanced recommendation with AI features."""
    recipe: RecipeResponse
    score: float = Field(..., ge=0, le=1)
    explanation: str  # LLM-generated explanation
    is_retry: bool  # Contains previously disliked ingredient
    penalty_applied: bool  # Was preference penalty applied
    original_score: float  # Score before penalty
    nutritional_highlights: Optional[str] = None  # LLM-generated highlights


class SmartRecommendationResponse(BaseModel):
    """Complete smart recommendation response."""
    primary_recommendations: List[EnhancedRecommendation]
    alternatives: Dict[str, AlternativesForIngredient]
    retry_suggestions: List[RetryStrategy]
    overall_explanation: str  # LLM summary of the recommendation strategy
    nutrition_analysis: Optional[str] = None  # LLM nutrition trend analysis


class ChatMessage(BaseModel):
    """Chat message for conversational interface."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    """Request for chat with AI assistant."""
    baby_id: int
    message: str
    conversation_history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response from AI assistant."""
    message: str
    suggested_actions: Optional[List[str]] = None  # e.g., ["view_recipe:1", "get_alternatives:carrot"]


class AlternativeRequest(BaseModel):
    """Request for ingredient alternatives."""
    baby_id: int
    disliked_ingredient: str
    reason: str = "baby_refused"


class RetryStrategyRequest(BaseModel):
    """Request for retry strategy."""
    baby_id: int
    ingredient: str


class WeeklyMealPlan(BaseModel):
    """Weekly meal plan structure."""
    monday: Dict[str, str]
    tuesday: Dict[str, str]
    wednesday: Dict[str, str]
    thursday: Dict[str, str]
    friday: Dict[str, str]
    saturday: Dict[str, str]
    sunday: Dict[str, str]


class WeeklyPlanRequest(BaseModel):
    """Request for weekly meal plan generation."""
    baby_id: int
    preferences: Optional[Dict[str, Any]] = None


class NutritionAnalysisResponse(BaseModel):
    """Nutrition analysis for a time period."""
    period: str
    total_meals: int
    nutrient_totals: Dict[str, float]
    nutrient_targets: Dict[str, float]
    assessment: str  # LLM-generated
    recommendations: str  # LLM-generated
    deficiencies: List[str]
    excesses: List[str]


class RecipeAdaptationRequest(BaseModel):
    """Request to adapt a recipe."""
    recipe_id: int
    baby_id: int
    adaptation_request: str  # e.g., "make dairy-free", "increase iron"


class RecipeAdaptationResponse(BaseModel):
    """Adapted recipe response."""
    original_recipe: RecipeResponse
    modified_ingredients: List[Dict[str, str]]
    modified_instructions: str
    nutritional_impact: str
    safety_notes: str