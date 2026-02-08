"""
API routes for recipe recommendations and feedback management.
Includes both basic (MVP) and AI-enhanced endpoints with user authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.baby import Baby
from app.models.recipe import Recipe
from app.models.feedback import Feedback

# Original schemas
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponse,
    RecommendationRequest
)
from app.schemas.recipe import RecipeWithScore

# New AI-enhanced schemas
from app.schemas.smart_recommendation import (
    SmartRecommendationResponse,
    AlternativeRequest,
    RetryStrategyRequest,
    ChatRequest,
    ChatResponse,
    WeeklyPlanRequest,
    NutritionAnalysisResponse,
    RecipeAdaptationRequest,
    RecipeAdaptationResponse,
    AlternativesForIngredient,
    EnhancedRecommendation,
    RetryStrategy,
    AlternativeRecipe,
    LLMAlternativeSuggestion
)

# Original engine
from app.services.recommendation_engine import RecommendationEngine

# New AI-enhanced services
try:
    from app.services.smart_recommendation_engine import SmartRecommendationEngine
    from app.services.llm_service import LLMService
    from app.services.preference_handler import PreferenceHandler
    SMART_FEATURES_AVAILABLE = True
except ImportError:
    SMART_FEATURES_AVAILABLE = False
    print("Warning: Smart features not available. Install dependencies and create service files.")


router = APIRouter()


# ============================================================================
# BASIC ENDPOINTS (MVP - Original with authentication)
# ============================================================================

@router.post("/", response_model=List[RecipeWithScore])
def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get basic rule-based recipe recommendations.
    
    This is the MVP endpoint - fast, no LLM calls, no API key needed.
    Requires authentication. Users can only get recommendations for their own babies.
    
    Args:
        request: Recommendation parameters (baby_id, count, meal_type, etc.)
        
    Returns:
        List of recommended recipes with scores and basic explanations
    """
    # Verify baby exists and belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    # Get recommendations using original engine
    engine = RecommendationEngine(db)
    
    exclude_days = 7 if request.exclude_recently_recommended else 0
    
    recommendations = engine.get_recommendations(
        baby=baby,
        count=request.count,
        meal_type=request.meal_type,
        exclude_recent_days=exclude_days
    )
    
    # Format response
    responses = []
    for recipe, score, reason in recommendations:
        recipe_dict = {
            "id": recipe.id,
            "name": recipe.name,
            "description": recipe.description,
            "age_min_months": recipe.age_min_months,
            "age_max_months": recipe.age_max_months,
            "preparation_time_min": recipe.preparation_time_min,
            "difficulty_level": recipe.difficulty_level,
            "ingredients": recipe.ingredients,
            "instructions": recipe.instructions,
            "calories": recipe.calories,
            "protein_g": recipe.protein_g,
            "carbs_g": recipe.carbs_g,
            "fat_g": recipe.fat_g,
            "fiber_g": recipe.fiber_g,
            "sugar_g": recipe.sugar_g,
            "iron_mg": recipe.iron_mg,
            "calcium_mg": recipe.calcium_mg,
            "vitamin_a_mcg": recipe.vitamin_a_mcg,
            "vitamin_c_mg": recipe.vitamin_c_mg,
            "vitamin_d_mcg": recipe.vitamin_d_mcg,
            "meal_type": recipe.meal_type,
            "cuisine": recipe.cuisine,
            "tags": recipe.tags,
            "allergens": recipe.allergens,
            "serving_size_g": recipe.serving_size_g,
            "nutrition_score": recipe.get_nutrition_score(),
            "recommendation_score": round(score, 3),
            "match_reason": reason
        }
        responses.append(RecipeWithScore(**recipe_dict))
    
    return responses


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit feedback for a recommended recipe.
    This feedback is used to improve future recommendations.
    
    Requires authentication. Users can only submit feedback for their own babies.
    
    Args:
        feedback_data: Feedback information including rating and acceptance
        
    Returns:
        Created feedback with computed score
    """
    # Verify baby exists and belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == feedback_data.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    # Verify recipe exists
    recipe = db.query(Recipe).filter(Recipe.id == feedback_data.recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {feedback_data.recipe_id} not found"
        )
    
    # Create feedback
    feedback = Feedback(**feedback_data.model_dump())
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    # Manually construct response with computed field
    feedback_dict = {
        "id": feedback.id,
        "baby_id": feedback.baby_id,
        "recipe_id": feedback.recipe_id,
        "rating": feedback.rating,
        "accepted": feedback.accepted,
        "prepared": feedback.prepared,
        "baby_liked": feedback.baby_liked,
        "comments": feedback.comments,
        "rejection_reason": feedback.rejection_reason,
        "recommended_at": feedback.recommended_at,
        "feedback_at": feedback.feedback_at,
        "feedback_score": feedback.get_feedback_score()
    }
    
    return FeedbackResponse(**feedback_dict)


@router.get("/feedback/{baby_id}", response_model=List[FeedbackResponse])
def get_baby_feedbacks(
    baby_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all feedbacks for a specific baby.
    
    Requires authentication. Users can only access feedbacks for their own babies.
    
    Args:
        baby_id: Baby profile ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of feedbacks with scores
    """
    # Verify baby exists and belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    feedbacks = db.query(Feedback).filter(
        Feedback.baby_id == baby_id
    ).offset(skip).limit(limit).all()
    
    # Manually construct responses with computed fields
    responses = []
    for feedback in feedbacks:
        feedback_dict = {
            "id": feedback.id,
            "baby_id": feedback.baby_id,
            "recipe_id": feedback.recipe_id,
            "rating": feedback.rating,
            "accepted": feedback.accepted,
            "prepared": feedback.prepared,
            "baby_liked": feedback.baby_liked,
            "comments": feedback.comments,
            "rejection_reason": feedback.rejection_reason,
            "recommended_at": feedback.recommended_at,
            "feedback_at": feedback.feedback_at,
            "feedback_score": feedback.get_feedback_score()
        }
        responses.append(FeedbackResponse(**feedback_dict))
    
    return responses


@router.patch("/feedback/{feedback_id}", response_model=FeedbackResponse)
def update_feedback(
    feedback_id: int,
    feedback_data: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing feedback.
    Useful when parent initially rejects but later tries the recipe.
    
    Requires authentication. Users can only update their own feedbacks.
    
    Args:
        feedback_id: Feedback ID
        feedback_data: Updated feedback information
        
    Returns:
        Updated feedback
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found"
        )
    
    # Verify the feedback's baby belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == feedback.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this feedback"
        )
    
    # Update only provided fields
    update_data = feedback_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feedback, field, value)
    
    db.commit()
    db.refresh(feedback)
    
    # Manually construct response with computed field
    feedback_dict = {
        "id": feedback.id,
        "baby_id": feedback.baby_id,
        "recipe_id": feedback.recipe_id,
        "rating": feedback.rating,
        "accepted": feedback.accepted,
        "prepared": feedback.prepared,
        "baby_liked": feedback.baby_liked,
        "comments": feedback.comments,
        "rejection_reason": feedback.rejection_reason,
        "recommended_at": feedback.recommended_at,
        "feedback_at": feedback.feedback_at,
        "feedback_score": feedback.get_feedback_score()
    }
    
    return FeedbackResponse(**feedback_dict)


@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a feedback entry.
    
    Requires authentication. Users can only delete their own feedbacks.
    
    Args:
        feedback_id: Feedback ID
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found"
        )
    
    # Verify the feedback's baby belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == feedback.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this feedback"
        )
    
    db.delete(feedback)
    db.commit()
    
    return None


# ============================================================================
# AI-ENHANCED ENDPOINTS (Phase 2 - New with authentication)
# ============================================================================

@router.post("/smart", response_model=SmartRecommendationResponse)
def get_smart_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-enhanced recommendations with intelligent preference handling.
    
    Differences from basic endpoint:
    - LLM-generated personalized explanations
    - Nutritional alternatives for disliked ingredients
    - Retry strategies for rejected foods
    - Overall nutrition analysis
    
    Requires: OPENAI_API_KEY environment variable and authentication
    
    Args:
        request: Recommendation parameters
        
    Returns:
        Enhanced recommendations with alternatives and strategies
    """
    if not SMART_FEATURES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Smart features not available. Check service files and dependencies."
        )
    
    # Verify baby exists and belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    # Initialize services
    try:
        llm_service = LLMService()
        engine = SmartRecommendationEngine(db, llm_service)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize AI services: {str(e)}"
        )
    
    # Get smart recommendations
    result = engine.get_smart_recommendations(
        baby=baby,
        count=request.count,
        meal_type=request.meal_type
    )
    
    return SmartRecommendationResponse(**result)


@router.post("/alternatives", response_model=AlternativesForIngredient)
def get_ingredient_alternatives(
    request: AlternativeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get nutritional alternatives for a disliked ingredient.
    
    Example: Baby dislikes spinach (iron source)
    Returns: Red lentils, beef, fortified cereal (other iron sources)
    
    Requires authentication.
    
    Args:
        request: Disliked ingredient and baby ID
        
    Returns:
        Alternative recipes and LLM suggestions
    """
    if not SMART_FEATURES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Smart features not available"
        )
    
    # Verify baby exists and belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    # Initialize services
    llm_service = LLMService()
    handler = PreferenceHandler(db, llm_service)
    
    # Get alternatives
    result = handler.handle_disliked_ingredient(
        ingredient=request.disliked_ingredient,
        baby=baby,
        reason=request.reason
    )
    
    return result


@router.post("/retry-strategy")
def get_retry_strategy(
    request: RetryStrategyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get intelligent retry strategy for a disliked ingredient.
    
    Suggests:
    - Different preparation methods
    - Mixing strategies
    - Optimal retry timing
    
    Requires authentication.
    
    Args:
        request: Ingredient and baby ID
        
    Returns:
        Retry strategy with personalized suggestions
    """
    if not SMART_FEATURES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Smart features not available"
        )
    
    # Verify baby exists and belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    llm_service = LLMService()
    handler = PreferenceHandler(db, llm_service)
    
    # Check if should retry
    should_retry, reason = handler.should_retry_ingredient(
        request.ingredient, baby
    )
    
    if not should_retry:
        return {
            "should_retry": False,
            "reason": reason,
            "suggestion": "Focus on nutritional alternatives for now"
        }
    
    # Get different preparations
    different_preps = handler.suggest_different_preparations(
        request.ingredient, baby
    )
    
    # Get attempt count
    attempt_count = handler._get_attempt_count(baby, request.ingredient)
    
    # Generate retry strategy
    strategy = handler.generate_retry_recommendation(
        request.ingredient, baby, attempt_count
    )
    
    return {
        "should_retry": True,
        "reason": reason,
        "different_preparations": [
            {"recipe_name": r.name, "method": m} 
            for r, m in different_preps
        ],
        "strategy": strategy,
        "attempt_count": attempt_count
    }


@router.post("/chat", response_model=ChatResponse)
def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chat with AI nutrition assistant.
    
    Context-aware: Automatically includes baby's profile and history.
    Requires authentication.
    
    Args:
        request: Chat message with conversation history
        
    Returns:
        AI response with optional suggested actions
    """
    if not SMART_FEATURES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Smart features not available"
        )
    
    # Verify baby exists and belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    llm_service = LLMService()
    
    # Convert conversation history to LLM format
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in request.conversation_history
    ]
    
    # Get AI response
    response = llm_service.chat_with_context(
        user_message=request.message,
        baby=baby,
        conversation_history=history
    )
    
    return ChatResponse(
        message=response,
        suggested_actions=None
    )


@router.post("/weekly-plan", response_model=Dict)
def generate_weekly_plan(
    request: WeeklyPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI-powered weekly meal plan.
    
    Ensures:
    - Nutritional balance across the week
    - Age-appropriate recipes
    - Variety in ingredients
    - Allergen avoidance
    
    Requires authentication.
    
    Args:
        request: Baby ID and preferences
        
    Returns:
        7-day structured meal plan
    """
    if not SMART_FEATURES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Smart features not available"
        )
    
    # Verify baby exists and belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    llm_service = LLMService()
    
    # Generate weekly plan
    plan = llm_service.generate_weekly_meal_plan(
        baby=baby,
        preferences=request.preferences
    )
    
    return plan


@router.get("/nutrition-analysis/{baby_id}", response_model=NutritionAnalysisResponse)
def get_nutrition_analysis(
    baby_id: int,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered nutrition analysis for recent meals.
    
    Analyzes:
    - Nutrient totals vs recommended intake
    - Deficiencies or excesses
    - Personalized suggestions
    
    Requires authentication.
    
    Args:
        baby_id: Baby ID
        days: Number of days to analyze
        
    Returns:
        Nutrition analysis with AI insights
    """
    if not SMART_FEATURES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Smart features not available"
        )
    
    # Verify baby exists and belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    # Get recent meals from feedback
    from datetime import date, timedelta
    cutoff_date = date.today() - timedelta(days=days)
    
    recent_feedbacks = db.query(Feedback).filter(
        Feedback.baby_id == baby_id,
        Feedback.recommended_at >= cutoff_date,
        Feedback.prepared == True
    ).all()
    
    # Get recipes
    recipe_ids = [f.recipe_id for f in recent_feedbacks]
    recent_recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
    
    if not recent_recipes:
        return NutritionAnalysisResponse(
            period=f"past {days} days",
            total_meals=0,
            nutrient_totals={},
            nutrient_targets={},
            assessment="No meals recorded in this period",
            recommendations="Start tracking meals to see nutrition analysis",
            deficiencies=[],
            excesses=[]
        )
    
    # Calculate nutrient totals
    nutrient_totals = {
        "iron_mg": sum(r.iron_mg or 0.0 for r in recent_recipes),
        "calcium_mg": sum(r.calcium_mg or 0.0 for r in recent_recipes),
        "protein_g": sum(r.protein_g or 0.0 for r in recent_recipes),
        "fiber_g": sum(r.fiber_g or 0.0 for r in recent_recipes),
        "vitamin_a_mcg": sum(r.vitamin_a_mcg or 0.0 for r in recent_recipes)
    }
    
    # Recommended targets (for the time period)
    daily_targets = {
        "iron_mg": 11,
        "calcium_mg": 260,
        "protein_g": 11,
        "fiber_g": 5,
        "vitamin_a_mcg": 500
    }
    
    nutrient_targets = {k: v * days for k, v in daily_targets.items()}
    
    # Get LLM analysis
    llm_service = LLMService()
    analysis = llm_service.analyze_nutrition_trend(
        baby=baby,
        recent_meals=recent_recipes,
        time_period=f"past {days} days"
    )
    
    # Identify deficiencies and excesses
    deficiencies = [
        nutrient for nutrient, total in nutrient_totals.items()
        if total < nutrient_targets[nutrient] * 0.7
    ]
    
    excesses = [
        nutrient for nutrient, total in nutrient_totals.items()
        if total > nutrient_targets[nutrient] * 1.5
    ]
    
    return NutritionAnalysisResponse(
        period=f"past {days} days",
        total_meals=len(recent_recipes),
        nutrient_totals=nutrient_totals,
        nutrient_targets=nutrient_targets,
        assessment=analysis,
        recommendations=analysis,
        deficiencies=deficiencies,
        excesses=excesses
    )


@router.post("/adapt-recipe", response_model=RecipeAdaptationResponse)
def adapt_recipe(
    request: RecipeAdaptationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adapt a recipe based on specific needs.
    
    Examples:
    - "Make this dairy-free"
    - "Increase iron content"
    - "Simplify for beginner cook"
    
    Requires authentication.
    
    Args:
        request: Recipe ID, baby ID, and adaptation request
        
    Returns:
        Adapted recipe with modifications
    """
    if not SMART_FEATURES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Smart features not available"
        )
    
    recipe = db.query(Recipe).filter(Recipe.id == request.recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {request.recipe_id} not found"
        )
    
    # Verify baby exists and belongs to current user
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    # Get adapted recipe from LLM
    llm_service = LLMService()
    adapted = llm_service.adapt_recipe(
        recipe=recipe,
        adaptation_request=request.adaptation_request,
        baby=baby
    )
    
    # Format original recipe
    original_recipe_dict = {
        "id": recipe.id,
        "name": recipe.name,
        "description": recipe.description,
        "age_min_months": recipe.age_min_months,
        "age_max_months": recipe.age_max_months,
        "preparation_time_min": recipe.preparation_time_min,
        "difficulty_level": recipe.difficulty_level,
        "ingredients": recipe.ingredients,
        "instructions": recipe.instructions,
        "calories": recipe.calories,
        "protein_g": recipe.protein_g,
        "carbs_g": recipe.carbs_g,
        "fat_g": recipe.fat_g,
        "fiber_g": recipe.fiber_g,
        "sugar_g": recipe.sugar_g,
        "iron_mg": recipe.iron_mg,
        "calcium_mg": recipe.calcium_mg,
        "vitamin_a_mcg": recipe.vitamin_a_mcg,
        "vitamin_c_mg": recipe.vitamin_c_mg,
        "vitamin_d_mcg": recipe.vitamin_d_mcg,
        "meal_type": recipe.meal_type,
        "cuisine": recipe.cuisine,
        "tags": recipe.tags,
        "allergens": recipe.allergens,
        "serving_size_g": recipe.serving_size_g,
        "nutrition_score": recipe.get_nutrition_score()
    }
    
    return RecipeAdaptationResponse(
        original_recipe=original_recipe_dict,
        modified_ingredients=adapted.get('modified_ingredients', []),
        modified_instructions=adapted.get('modified_instructions', ''),
        nutritional_impact=adapted.get('nutritional_impact', ''),
        safety_notes=adapted.get('safety_notes', '')
    )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/status")
def get_ai_status(db: Session = Depends(get_db)):
    """
    Check status of AI features.
    
    Returns:
        Status of smart features and available endpoints
    """
    from app.core.config import settings
    
    status_info = {
        "smart_features_available": SMART_FEATURES_AVAILABLE,
        "openai_api_key_configured": bool(settings.OPENAI_API_KEY),
        "endpoints": {
            "basic": [
                "POST /recommendations/",
                "POST /recommendations/feedback",
                "GET /recommendations/feedback/{baby_id}"
            ],
            "smart": [
                "POST /recommendations/smart",
                "POST /recommendations/alternatives",
                "POST /recommendations/retry-strategy",
                "POST /recommendations/chat",
                "POST /recommendations/weekly-plan",
                "GET /recommendations/nutrition-analysis/{baby_id}",
                "POST /recommendations/adapt-recipe"
            ] if SMART_FEATURES_AVAILABLE else []
        }
    }
    
    return status_info