# Baby Meal Recommendation AI System

AI-driven nutrition planner that recommends balanced recipes based on infant health and taste preferences.

## 🎯 Project Status: Phase 1 - MVP

**Current Features:**
- ✅ RESTful API with FastAPI
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ Basic content-based recommendation engine
- ✅ Baby profile management
- ✅ Recipe CRUD operations
- ✅ Feedback tracking system
- ✅ Docker containerization

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL, SQLAlchemy
- **Containerization**: Docker, Docker Compose
- **Testing**: Pytest

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+

### Installation

1. Clone the repository
2. Start services: `docker-compose up -d`
3. Seed database: `docker-compose exec backend python seed_database.py`
4. Access API docs: http://localhost:8000/docs

## 📖 API Endpoints

- **Babies**: `/api/v1/babies/` - Manage baby profiles
- **Recipes**: `/api/v1/recipes/` - Manage recipes
- **Recommendations**: `/api/v1/recommendations/` - Get personalized recommendations

## 🔄 Development Roadmap

- **Phase 1 (Current)**: MVP with basic recommendation engine
- **Phase 2**: ML-based recommendations (TensorFlow, XGBoost)
- **Phase 3**: Collaborative filtering
- **Phase 4**: Reinforcement learning & CI/CD

## 📝 License

MIT License

---

**Author**: CS Align Student - Northeastern University
