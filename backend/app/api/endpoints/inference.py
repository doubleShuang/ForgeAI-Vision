from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.model import InferenceRecord
from app.services.inference_service import inference_service
from app.services.storage_service import storage_service
from app.core.config import settings
import os
import json
from typing import List, Optional

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/image")
def predict_image(
    model_path: str = Form("yolov8n.pt"), 
    file: UploadFile = File(...),
    classes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Save temp image
    file_path = storage_service.save_file(file, file.filename, "temp_inference")
    
    # Parse classes
    class_list = None
    if classes:
        try:
            class_list = json.loads(classes)
        except:
            pass 
            
    # Run inference
    try:
        results = inference_service.predict_image(model_path, file_path, classes=class_list)
        
        # Save Record
        # Calculate summary e.g. {"Person": 2, "Car": 1}
        summary_dict = {}
        # Make sure detections are JSON serializable
        detections_to_save = []
        
        for det in results:
            cls = det["class"]
            summary_dict[cls] = summary_dict.get(cls, 0) + 1
            detections_to_save.append(det)
        
        # IMPORTANT: For history replay, we need to save the full detections JSON
        # We'll store it in detections_summary for now (abusing the field slightly, or should have added a new field)
        # But given the schema, detections_summary is Text, so it fits.
        # Ideally, we should have a separate column for 'raw_results', but 'detections_summary' is Text so we can put full JSON.
        
        record = InferenceRecord(
            name=f"Image Inference {file.filename}",
            file_type="image",
            input_path=file_path,
            output_path=None, 
            model_name=model_path,
            detections_summary=json.dumps(detections_to_save) # Saving FULL detections for replay
        )
        db.add(record)
        db.commit()

        return {"code": 200, "data": results}
    except Exception as e:
        return {"code": 500, "message": str(e)}

@router.post("/video")
def predict_video(
    model_path: str = Form("yolov8n.pt"),
    file: UploadFile = File(...),
    classes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Save temp video
    file_path = storage_service.save_file(file, file.filename, "temp_video_input")
    
    # Define output path
    output_filename = f"processed_{file.filename}"
    output_path = os.path.join(settings.UPLOAD_DIR, "temp_video_output", output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Parse classes
    class_list = None
    if classes:
        try:
            class_list = json.loads(classes)
        except:
            pass

    try:
        # Process video
        processed_path = inference_service.process_video(model_path, file_path, output_path, classes=class_list)
        
        # Save Record
        record = InferenceRecord(
            name=f"Video Inference {file.filename}",
            file_type="video",
            input_path=file_path,
            output_path=processed_path,
            model_name=model_path,
            detections_summary="Video processed"
        )
        db.add(record)
        db.commit()

        return {"code": 200, "data": {"video_url": f"/api/v1/predict/video/download/{output_filename}"}}
    except Exception as e:
        return {"code": 500, "message": str(e)}

@router.get("/video/download/{filename}")
def download_video(filename: str):
    file_path = os.path.join(settings.UPLOAD_DIR, "temp_video_output", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4")
    else:
        raise HTTPException(status_code=404, detail="Video not found")
