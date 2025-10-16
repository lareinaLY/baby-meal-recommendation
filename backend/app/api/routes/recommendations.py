"""
API routes for recipe recommendations and feedback management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.baby import Baby
from app.models.recipe import Recipe
from app.models.feedback import Feedback
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponse,
    RecommendationRequest
)
from app.schemas.recipe import RecipeWithScore
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter()


@router.post("/", response_model=List[RecipeWithScore])
def get_recommendations(
        request: RecommendationRequest,
        db: Session = Depends(get_db)
):
    """
    Get personalized recipe recommendations for a baby.

    Args:
        request: Recommendation parameters (baby_id, count, meal_type, etc.)

    Returns:
        List of recommended recipes with scores and explanations
    """
    # Verify baby exists
    baby = db.query(Baby).filter(Baby.id == request.baby_id).first()
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baby with id {request.baby_id} not found"
        )

    # Get recommendations
    engine = RecommendationEngine(db)

    exclude_days = 7 if request.exclude_recently_recommended else 0

    recommendations = engine.get_recommendations(
        baby=baby,
        count=request.count,
        meal_type=request.meal_type,
        exclude_recent_days=exclude_days
    )

    # Manually construct responses with all computed fields
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
        db: Session = Depends(get_db)
):
    """
    Submit feedback for a recommended recipe.
    This feedback is used to improve future recommendations.

    Args:
        feedback_data: Feedback information including rating and acceptance

    Returns:
        Created feedback with computed score
    """
    # Verify baby exists
    baby = db.query(Baby).filter(Baby.id == feedback_data.baby_id).first()
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baby with id {feedback_data.baby_id} not found"
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
        db: Session = Depends(get_db)
):
    """
    Get all feedbacks for a specific baby.

    Args:
        baby_id: Baby profile ID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of feedbacks with scores
    """
    # Verify baby exists
    baby = db.query(Baby).filter(Baby.id == baby_id).first()
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baby with id {baby_id} not found"
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
        db: Session = Depends(get_db)
):
    """
    Update an existing feedback.
    Useful when parent initially rejects but later tries the recipe.

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
        db: Session = Depends(get_db)
):
    """
    Delete a feedback entry.

    Args:
        feedback_id: Feedback ID
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found"
        )

    db.delete(feedback)
    db.commit()

    return None