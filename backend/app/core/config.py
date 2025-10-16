"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Create a .env file in the backend root directory with:
        DATABASE_URL=postgresql://user:password@localhost:5432/baby_meals
        DEBUG=True
        API_PREFIX=/api/v1
    """

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/baby_meals"

    # Application
    API_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Baby Meal Recommendation System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # CORS settings
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
    ]

    # Recommendation settings
    MIN_RECOMMENDATION_COUNT: int = 5  # Minimum recipes to recommend
    MAX_RECOMMENDATION_COUNT: int = 10  # Maximum recipes to recommend

    # Feature engineering (for future ML phases)
    FEATURE_COUNT: int = 50  # Target number of engineered features

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()