"""
API routes for recipe management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.recipe import Recipe
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse
)

router = APIRouter()


@router.post("/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
        recipe_data: RecipeCreate,
        db: Session = Depends(get_db)
):
    """
    Create a new recipe.

    Args:
        recipe_data: Recipe information including nutritional data

    Returns:
        Created recipe with computed nutrition score
    """
    recipe = Recipe(**recipe_data.model_dump())

    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    # Manually construct response with computed field
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
        "nutrition_score": recipe.get_nutrition_score()
    }

    return RecipeResponse(**recipe_dict)


@router.get("/", response_model=List[RecipeResponse])
def list_recipes(
        skip: int = 0,
        limit: int = 100,
        age_min: Optional[int] = Query(None, description="Minimum age in months"),
        age_max: Optional[int] = Query(None, description="Maximum age in months"),
        meal_type: Optional[str] = Query(None, description="Filter by meal type"),
        tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
        db: Session = Depends(get_db)
):
    """
    List recipes with optional filtering and pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        age_min: Filter recipes suitable for this minimum age
        age_max: Filter recipes suitable for this maximum age
        meal_type: Filter by meal type (breakfast, lunch, dinner, snack)
        tags: Filter by tags (comma-separated)

    Returns:
        List of recipes matching the filters
    """
    query = db.query(Recipe)

    # Apply age filters
    if age_min is not None:
        query = query.filter(Recipe.age_min_months <= age_min)

    if age_max is not None:
        query = query.filter(
            (Recipe.age_max_months.is_(None)) |
            (Recipe.age_max_months >= age_max)
        )

    # Apply meal type filter
    if meal_type:
        query = query.filter(Recipe.meal_type == meal_type)

    # Apply tags filter
    if tags:
        tag_list = [t.strip() for t in tags.split(',')]
        for tag in tag_list:
            query = query.filter(Recipe.tags.contains([tag]))

    recipes = query.offset(skip).limit(limit).all()

    # Manually construct responses with computed fields
    responses = []
    for recipe in recipes:
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
            "nutrition_score": recipe.get_nutrition_score()
        }
        responses.append(RecipeResponse(**recipe_dict))

    return responses


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(
        recipe_id: int,
        db: Session = Depends(get_db)
):
    """
    Get a specific recipe by ID.

    Args:
        recipe_id: Recipe ID

    Returns:
        Recipe details with nutrition score
    """
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {recipe_id} not found"
        )

    # Manually construct response with computed field
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
        "nutrition_score": recipe.get_nutrition_score()
    }

    return RecipeResponse(**recipe_dict)


@router.patch("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
        recipe_id: int,
        recipe_data: RecipeUpdate,
        db: Session = Depends(get_db)
):
    """
    Update a recipe.

    Args:
        recipe_id: Recipe ID
        recipe_data: Updated recipe information

    Returns:
        Updated recipe
    """
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {recipe_id} not found"
        )

    # Update only provided fields
    update_data = recipe_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recipe, field, value)

    db.commit()
    db.refresh(recipe)

    # Manually construct response with computed field
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
        "nutrition_score": recipe.get_nutrition_score()
    }

    return RecipeResponse(**recipe_dict)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
        recipe_id: int,
        db: Session = Depends(get_db)
):
    """
    Delete a recipe.

    Args:
        recipe_id: Recipe ID
    """
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {recipe_id} not found"
        )

    db.delete(recipe)
    db.commit()

    return None