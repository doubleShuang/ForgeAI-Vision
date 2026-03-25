from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.api import api_router
from app.core.config import settings
from app.db.session import engine, Base
# 导入系统管理模型，确保 create_all 时建表
from app.models import system as system_models  # noqa: F401
import os

# 创建所有数据库表（包括系统管理表）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount workspaces for static file serving
os.makedirs("workspaces", exist_ok=True)
app.mount("/workspaces", StaticFiles(directory="workspaces"), name="workspaces")

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to YOLOv8 Platform API"}
