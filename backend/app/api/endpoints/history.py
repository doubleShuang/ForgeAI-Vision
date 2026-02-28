from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import SessionLocal
from app.models.model import InferenceRecord
from fastapi.responses import FileResponse
import os
from app.core.config import settings

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[dict])
def list_history(db: Session = Depends(get_db)):
    records = db.query(InferenceRecord).order_by(InferenceRecord.created_at.desc()).all()
    return [{
        "id": r.id,
        "name": r.name,
        "file_type": r.file_type,
        "input_path": r.input_path,
        "output_path": r.output_path,
        "model_name": r.model_name,
        "detections_summary": r.detections_summary,
        "created_at": r.created_at
    } for r in records]

@router.delete("/{id}")
def delete_history(id: int, db: Session = Depends(get_db)):
    record = db.query(InferenceRecord).filter(InferenceRecord.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Optional: Delete files from disk?
    # For now, let's keep files or implement basic cleanup
    if record.input_path and os.path.exists(record.input_path):
        try: os.remove(record.input_path)
        except: pass
    if record.output_path and os.path.exists(record.output_path):
        try: os.remove(record.output_path)
        except: pass

    db.delete(record)
    db.commit()
    return {"message": "Record deleted"}

@router.put("/{id}")
def update_history(id: int, name: str = Body(..., embed=True), db: Session = Depends(get_db)):
    record = db.query(InferenceRecord).filter(InferenceRecord.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    record.name = name
    db.commit()
    return {"message": "Record updated"}

@router.get("/file/{filename}")
def get_history_file(filename: str):
    # This endpoint is strictly to serve files that might be in different directories
    # But for security, we should check if they are in UPLOAD_DIR
    # A simplified approach for demo:
    # We will search in UPLOAD_DIR recursively or just check specific folders
    
    # Try to find in temp_inference
    path1 = os.path.join(settings.UPLOAD_DIR, "temp_inference", filename)
    if os.path.exists(path1):
        return FileResponse(path1)
        
    # Try temp_video_output
    path2 = os.path.join(settings.UPLOAD_DIR, "temp_video_output", filename)
    if os.path.exists(path2):
        return FileResponse(path2)
        
    # Try temp_video_input
    path3 = os.path.join(settings.UPLOAD_DIR, "temp_video_input", filename)
    if os.path.exists(path3):
        return FileResponse(path3)

    raise HTTPException(status_code=404, detail="File not found")
