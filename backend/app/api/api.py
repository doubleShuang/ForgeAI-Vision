from fastapi import APIRouter
from app.api.endpoints import models, training, inference, history, projects, system, auth

api_router = APIRouter()

# 注册认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# 注册系统管理路由
api_router.include_router(system.router, prefix="/system", tags=["系统管理"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(training.router, prefix="/train", tags=["training"])
api_router.include_router(inference.router, prefix="/predict", tags=["inference"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
# 系统管理模块路由
