"""
API routes for baby profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.core.database import get_db
from app.models.baby import Baby
from app.models.feedback import Feedback
from app.schemas.baby import (
    BabyCreate,
    BabyUpdate,
    BabyResponse,
    BabyWithStats
)

router = APIRouter()


@router.post("/", response_model=BabyResponse, status_code=status.HTTP_201_CREATED)
def create_baby(
        baby_data: BabyCreate,
        db: Session = Depends(get_db)
):
    """
    Create a new baby profile.

    Args:
        baby_data: Baby profile information

    Returns:
        Created baby profile with computed fields
    """
    # Create baby instance
    baby = Baby(**baby_data.model_dump())

    db.add(baby)
    db.commit()
    db.refresh(baby)

    # Manually construct response with computed fields
    baby_dict = {
        "id": baby.id,
        "name": baby.name,
        "birth_date": baby.birth_date,
        "weight_kg": baby.weight_kg,
        "height_cm": baby.height_cm,
        "allergies": baby.allergies,
        "dietary_restrictions": baby.dietary_restrictions,
        "liked_ingredients": baby.liked_ingredients,
        "disliked_ingredients": baby.disliked_ingredients,
        "created_at": baby.created_at,
        "age_months": baby.get_age_months(),
        "age_stage": baby.get_age_stage()
    }

    return BabyResponse(**baby_dict)


@router.get("/", response_model=List[BabyResponse])
def list_babies(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    List all baby profiles with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of baby profiles
    """
    babies = db.query(Baby).offset(skip).limit(limit).all()

    # Manually construct responses with computed fields
    responses = []
    for baby in babies:
        baby_dict = {
            "id": baby.id,
            "name": baby.name,
            "birth_date": baby.birth_date,
            "weight_kg": baby.weight_kg,
            "height_cm": baby.height_cm,
            "allergies": baby.allergies,
            "dietary_restrictions": baby.dietary_restrictions,
            "liked_ingredients": baby.liked_ingredients,
            "disliked_ingredients": baby.disliked_ingredients,
            "created_at": baby.created_at,
            "age_months": baby.get_age_months(),
            "age_stage": baby.get_age_stage()
        }
        responses.append(BabyResponse(**baby_dict))

    return responses


@router.get("/{baby_id}", response_model=BabyWithStats)
def get_baby(
        baby_id: int,
        db: Session = Depends(get_db)
):
    """
    Get a specific baby profile by ID with statistics.

    Args:
        baby_id: Baby profile ID

    Returns:
        Baby profile with feedback statistics
    """
    baby = db.query(Baby).filter(Baby.id == baby_id).first()

    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baby with id {baby_id} not found"
        )

    # Calculate statistics
    feedbacks = db.query(Feedback).filter(Feedback.baby_id == baby_id)

    total_feedbacks = feedbacks.count()
    accepted_count = feedbacks.filter(Feedback.accepted == True).count()
    avg_rating = feedbacks.filter(Feedback.accepted == True).with_entities(
        func.avg(Feedback.rating)
    ).scalar() or 0.0

    # Manually construct response with stats
    baby_dict = {
        "id": baby.id,
        "name": baby.name,
        "birth_date": baby.birth_date,
        "weight_kg": baby.weight_kg,
        "height_cm": baby.height_cm,
        "allergies": baby.allergies,
        "dietary_restrictions": baby.dietary_restrictions,
        "liked_ingredients": baby.liked_ingredients,
        "disliked_ingredients": baby.disliked_ingredients,
        "created_at": baby.created_at,
        "age_months": baby.get_age_months(),
        "age_stage": baby.get_age_stage(),
        "total_feedbacks": total_feedbacks,
        "average_rating": round(avg_rating, 2),
        "acceptance_rate": round(accepted_count / total_feedbacks, 2) if total_feedbacks > 0 else 0.0
    }

    return BabyWithStats(**baby_dict)


@router.patch("/{baby_id}", response_model=BabyResponse)
def update_baby(
        baby_id: int,
        baby_data: BabyUpdate,
        db: Session = Depends(get_db)
):
    """
    Update a baby profile.

    Args:
        baby_id: Baby profile ID
        baby_data: Updated baby information (only provided fields will be updated)

    Returns:
        Updated baby profile
    """
    baby = db.query(Baby).filter(Baby.id == baby_id).first()

    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baby with id {baby_id} not found"
        )

    # Update only provided fields
    update_data = baby_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(baby, field, value)

    db.commit()
    db.refresh(baby)

    # Manually construct response with computed fields
    baby_dict = {
        "id": baby.id,
        "name": baby.name,
        "birth_date": baby.birth_date,
        "weight_kg": baby.weight_kg,
        "height_cm": baby.height_cm,
        "allergies": baby.allergies,
        "dietary_restrictions": baby.dietary_restrictions,
        "liked_ingredients": baby.liked_ingredients,
        "disliked_ingredients": baby.disliked_ingredients,
        "created_at": baby.created_at,
        "age_months": baby.get_age_months(),
        "age_stage": baby.get_age_stage()
    }

    return BabyResponse(**baby_dict)


@router.delete("/{baby_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_baby(
        baby_id: int,
        db: Session = Depends(get_db)
):
    """
    Delete a baby profile and all associated feedbacks.

    Args:
        baby_id: Baby profile ID
    """
    baby = db.query(Baby).filter(Baby.id == baby_id).first()

    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baby with id {baby_id} not found"
        )

    db.delete(baby)
    db.commit()

    return None