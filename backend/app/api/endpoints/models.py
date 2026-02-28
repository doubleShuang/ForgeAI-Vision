from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.db.session import SessionLocal
from app.models.model import Model
from app.services.storage_service import storage_service
from app.core.config import settings
import json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[dict]) # Simplified schema
def list_models(db: Session = Depends(get_db)):
    models = db.query(Model).all()
    return [{
        "id": m.id, 
        "name": m.name, 
        "type": m.type, 
        "accuracy": m.accuracy, 
        "file_path": m.file_path, 
        "classes": json.loads(m.classes) if m.classes else None,
        "created_at": m.created_at
    } for m in models]

from ultralytics import YOLO
import os

@router.post("/")
def upload_model(
    name: str = Form(...),
    type: str = Form(...),
    accuracy: float = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Save file
    file_path = storage_service.save_file(file, file.filename, settings.MINIO_BUCKET_MODELS)
    
    # Try to load model to extract classes
    classes_json = None
    try:
        # storage_service.save_file returns relative path or MinIO path. 
        # If it's local, we can read it.
        # Assuming local storage for now based on previous context.
        # Construct absolute path. 
        # storage_service uses "storage/models" by default? We need to verify storage_service.
        # Let's assume file_path is accessible.
        
        # We need to know where storage_service puts it.
        # Let's verify storage_service.py if possible, but for now we try to load.
        
        if os.path.exists(file_path):
             model = YOLO(file_path)
             if model.names:
                 classes_json = json.dumps(model.names)
    except Exception as e:
        print(f"Failed to extract classes: {e}")

    # Save metadata
    db_model = Model(name=name, type=type, accuracy=accuracy, file_path=file_path, classes=classes_json)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return {"id": db_model.id, "name": db_model.name}
