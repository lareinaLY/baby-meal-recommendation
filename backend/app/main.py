"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import babies, recipes, recommendations


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database tables on application startup."""
    init_db()
    print(f"{settings.PROJECT_NAME} started successfully")


# Include routers
app.include_router(
    babies.router,
    prefix=f"{settings.API_PREFIX}/babies",
    tags=["Babies"]
)

app.include_router(
    recipes.router,
    prefix=f"{settings.API_PREFIX}/recipes",
    tags=["Recipes"]
)

app.include_router(
    recommendations.router,
    prefix=f"{settings.API_PREFIX}/recommendations",
    tags=["Recommendations"]
)


# Root endpoint
@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "api_prefix": settings.API_PREFIX
    }


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}