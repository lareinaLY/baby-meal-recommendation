"""
Baby management API routes with user authentication
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.baby import Baby
from app.schemas.baby import BabyCreate, BabyUpdate, BabyResponse, BabyWithStats

router = APIRouter()


@router.post("/", response_model=BabyResponse, status_code=status.HTTP_201_CREATED)
def create_baby(
    baby: BabyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new baby profile for the current user
    
    Requires authentication
    """
    # Create baby associated with current user
    db_baby = Baby(
        user_id=current_user.id,
        name=baby.name,
        birth_date=baby.birth_date,
        weight_kg=baby.weight_kg,
        height_cm=baby.height_cm,
        allergies=baby.allergies,
        liked_ingredients=baby.liked_ingredients,
        disliked_ingredients=baby.disliked_ingredients
    )
    db.add(db_baby)
    db.commit()
    db.refresh(db_baby)
    
    return db_baby


@router.get("/", response_model=List[BabyResponse])
def list_babies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all babies for the current user
    
    Requires authentication. Only returns babies owned by the current user.
    """
    babies = db.query(Baby).filter(
        Baby.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return babies


@router.get("/{baby_id}", response_model=BabyWithStats)
def get_baby(
    baby_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific baby's details with statistics
    
    Requires authentication. Users can only access their own babies.
    """
    baby = db.query(Baby).filter(
        Baby.id == baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to access it"
        )
    
    # Calculate statistics
    total_feedbacks = len(baby.feedbacks)
    accepted_count = sum(1 for f in baby.feedbacks if f.accepted)
    avg_rating = sum(f.rating for f in baby.feedbacks) / total_feedbacks if total_feedbacks > 0 else 0.0
    
    # Calculate acceptance rate
    acceptance_rate = (accepted_count / total_feedbacks * 100) if total_feedbacks > 0 else 0.0
    
    # Create response with stats
    baby_dict = {
        "id": baby.id,
        "name": baby.name,
        "birth_date": baby.birth_date,
        "weight_kg": baby.weight_kg,
        "height_cm": baby.height_cm,
        "allergies": baby.allergies,
        "liked_ingredients": baby.liked_ingredients,
        "disliked_ingredients": baby.disliked_ingredients,
        "created_at": baby.created_at,
        "age_months": baby.age_months,
        "age_stage": baby.get_age_stage(),
        "total_feedbacks": total_feedbacks,
        "average_rating": round(avg_rating, 2),
        "acceptance_rate": round(acceptance_rate, 1)
    }
    
    return baby_dict


@router.patch("/{baby_id}", response_model=BabyResponse)
def update_baby(
    baby_id: int,
    baby_update: BabyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a baby's profile
    
    Requires authentication. Users can only update their own babies.
    """
    db_baby = db.query(Baby).filter(
        Baby.id == baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not db_baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to update it"
        )
    
    # Update only provided fields
    update_data = baby_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_baby, field, value)
    
    db.commit()
    db.refresh(db_baby)
    
    return db_baby


@router.delete("/{baby_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_baby(
    baby_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a baby profile
    
    Requires authentication. Users can only delete their own babies.
    """
    db_baby = db.query(Baby).filter(
        Baby.id == baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not db_baby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baby not found or you don't have permission to delete it"
        )
    
    db.delete(db_baby)
    db.commit()
    
    return None