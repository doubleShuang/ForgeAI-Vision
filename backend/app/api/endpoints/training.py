from fastapi import APIRouter, Depends, Form, HTTPException, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.training_service import training_service
from app.models.model import TrainingTask
from pydantic import BaseModel

router = APIRouter()

class TrainingRequest(BaseModel):
    model_name: str
    project_id: int
    epochs: int = 10
    batch_size: int = 16
    device: str = "cpu"
    imgsz: int = 640
    optimizer: str = "auto"
    base_model: str = "yolov8n.pt"

@router.post("/")
def start_training(
    request: TrainingRequest,
    db: Session = Depends(get_db)
):
    # Create config dict
    config = {
        "device": request.device,
        "imgsz": request.imgsz,
        "optimizer": request.optimizer,
        "base_model": request.base_model
    }
    
    # Create task in DB
    task = training_service.create_task(db, request.model_name, request.project_id, request.epochs, request.batch_size, config)
    
    # Start training
    training_service.start_training(task.id, db)
    
    return {"code": 200, "message": "Training started", "task_id": task.id}

@router.get("/status/{task_id}")
def get_status(task_id: int, db: Session = Depends(get_db)):
    status = training_service.get_status(task_id, db)
    return {"code": 200, "data": status}

@router.get("/history")
def get_history(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    tasks = db.query(TrainingTask).order_by(TrainingTask.created_at.desc()).offset(skip).limit(limit).all()
    return {"code": 200, "data": tasks}

@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    # Stop training if running
    training_service.stop_training(task_id, db)
    
    task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
    return {"code": 200, "message": "Task deleted"}
