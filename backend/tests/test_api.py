"""
Basic tests for API endpoints.
Run with: pytest tests/test_api.py
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta

from app.main import app

client = TestClient(app)


class TestRootEndpoints:
    """Test root and health check endpoints."""

    def test_root(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestBabyEndpoints:
    """Test baby profile CRUD operations."""

    @pytest.fixture
    def sample_baby_data(self):
        """Sample baby profile data."""
        return {
            "name": "Test Baby",
            "birth_date": (date.today() - timedelta(days=180)).isoformat(),  # 6 months old
            "weight_kg": 7.5,
            "height_cm": 65.0,
            "allergies": [],
            "dietary_restrictions": [],
            "liked_ingredients": ["banana", "avocado"],
            "disliked_ingredients": []
        }

    def test_create_baby(self, sample_baby_data):
        """Test creating a new baby profile."""
        response = client.post("/api/v1/babies/", json=sample_baby_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_baby_data["name"]
        assert "id" in data
        assert "age_months" in data
        assert "age_stage" in data

    def test_list_babies(self, sample_baby_data):
        """Test listing baby profiles."""
        # Create a baby first
        client.post("/api/v1/babies/", json=sample_baby_data)

        # List babies
        response = client.get("/api/v1/babies/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_baby(self, sample_baby_data):
        """Test getting a specific baby profile."""
        # Create a baby
        create_response = client.post("/api/v1/babies/", json=sample_baby_data)
        baby_id = create_response.json()["id"]

        # Get the baby
        response = client.get(f"/api/v1/babies/{baby_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == baby_id
        assert "total_feedbacks" in data
        assert "average_rating" in data

    def test_update_baby(self, sample_baby_data):
        """Test updating a baby profile."""
        # Create a baby
        create_response = client.post("/api/v1/babies/", json=sample_baby_data)
        baby_id = create_response.json()["id"]

        # Update the baby
        update_data = {"weight_kg": 8.0}
        response = client.patch(f"/api/v1/babies/{baby_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["weight_kg"] == 8.0


class TestRecipeEndpoints:
    """Test recipe CRUD operations."""

    @pytest.fixture
    def sample_recipe_data(self):
        """Sample recipe data."""
        return {
            "name": "Test Recipe",
            "description": "A test recipe",
            "age_min_months": 6,
            "age_max_months": 12,
            "preparation_time_min": 15,
            "difficulty_level": "easy",
            "ingredients": [
                {"name": "banana", "quantity": "1", "unit": "whole"}
            ],
            "instructions": "Mash the banana",
            "calories": 100.0,
            "protein_g": 1.5,
            "carbs_g": 20.0,
            "fat_g": 0.5,
            "fiber_g": 2.0,
            "sugar_g": 12.0,
            "meal_type": "snack",
            "tags": ["fruit", "easy"],
            "allergens": []
        }

    def test_create_recipe(self, sample_recipe_data):
        """Test creating a new recipe."""
        response = client.post("/api/v1/recipes/", json=sample_recipe_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_recipe_data["name"]
        assert "nutrition_score" in data

    def test_list_recipes(self, sample_recipe_data):
        """Test listing recipes."""
        # Create a recipe first
        client.post("/api/v1/recipes/", json=sample_recipe_data)

        # List recipes
        response = client.get("/api/v1/recipes/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestRecommendations:
    """Test recommendation functionality."""

    @pytest.fixture
    def setup_data(self):
        """Set up baby and recipes for recommendation tests."""
        # Create baby
        baby_data = {
            "name": "Test Baby",
            "birth_date": (date.today() - timedelta(days=210)).isoformat(),
            "allergies": [],
            "liked_ingredients": ["banana"]
        }
        baby_response = client.post("/api/v1/babies/", json=baby_data)
        baby_id = baby_response.json()["id"]

        # Create recipe
        recipe_data = {
            "name": "Banana Puree",
            "age_min_months": 4,
            "ingredients": [{"name": "banana", "quantity": "1", "unit": "whole"}],
            "calories": 100.0,
            "protein_g": 1.0,
            "tags": ["fruit"]
        }
        recipe_response = client.post("/api/v1/recipes/", json=recipe_data)
        recipe_id = recipe_response.json()["id"]

        return {"baby_id": baby_id, "recipe_id": recipe_id}

    def test_get_recommendations(self, setup_data):
        """Test getting recipe recommendations."""
        request_data = {
            "baby_id": setup_data["baby_id"],
            "count": 5
        }
        response = client.post("/api/v1/recommendations/", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for recipe in data:
            assert "recommendation_score" in recipe
            assert "match_reason" in recipe

    def test_submit_feedback(self, setup_data):
        """Test submitting feedback."""
        feedback_data = {
            "baby_id": setup_data["baby_id"],
            "recipe_id": setup_data["recipe_id"],
            "rating": 4.5,
            "accepted": True,
            "prepared": True,
            "baby_liked": True
        }
        response = client.post("/api/v1/recommendations/feedback", json=feedback_data)
        assert response.status_code == 201
        data = response.json()
        assert "feedback_score" in data
        assert data["rating"] == 4.5