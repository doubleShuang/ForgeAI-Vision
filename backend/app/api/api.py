from fastapi import APIRouter
from app.api.endpoints import models, training, inference, history, projects

api_router = APIRouter()
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(training.router, prefix="/train", tags=["training"])
api_router.include_router(inference.router, prefix="/predict", tags=["inference"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
