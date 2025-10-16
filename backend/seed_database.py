"""
Script to seed the database with initial recipe data.
Run this after the database tables are created.

Usage:
    python seed_database.py
"""
import json
from pathlib import Path

from app.core.database import SessionLocal
from app.models.recipe import Recipe


def load_seed_recipes():
    """Load recipes from seed_recipes.json into the database."""

    # Load JSON data
    seed_file = Path(__file__).parent / "data" / "seed_recipes.json"

    if not seed_file.exists():
        print(f"Error: {seed_file} not found")
        return

    with open(seed_file, 'r') as f:
        recipes_data = json.load(f)

    # Create database session
    db = SessionLocal()

    try:
        # Check if recipes already exist
        existing_count = db.query(Recipe).count()

        if existing_count > 0:
            print(f"Database already contains {existing_count} recipes.")
            response = input("Do you want to add more recipes? (y/n): ")
            if response.lower() != 'y':
                print("Seed operation cancelled.")
                return

        # Add recipes
        added_count = 0
        for recipe_data in recipes_data:
            # Check if recipe with same name exists
            existing = db.query(Recipe).filter(
                Recipe.name == recipe_data['name']
            ).first()

            if existing:
                print(f"Recipe '{recipe_data['name']}' already exists, skipping...")
                continue

            # Create new recipe
            recipe = Recipe(**recipe_data)
            db.add(recipe)
            added_count += 1
            print(f"Added recipe: {recipe_data['name']}")

        # Commit all changes
        db.commit()
        print(f"\n✓ Successfully added {added_count} recipes to the database")

        # Display summary
        total_recipes = db.query(Recipe).count()
        print(f"Total recipes in database: {total_recipes}")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    print("Baby Meal Recommendation System - Database Seeding")
    print("=" * 60)
    load_seed_recipes()