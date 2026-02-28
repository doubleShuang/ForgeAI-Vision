from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.project_service import project_service
from typing import List
from pydantic import BaseModel

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: str = ""

class AnnotationSave(BaseModel):
    image_name: str
    content: str

class ClassesSave(BaseModel):
    classes: str

@router.post("/")
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    return project_service.create_project(db, project.name, project.description)

@router.get("/")
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return project_service.list_projects(db, skip, limit)

@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    return project_service.delete_project(db, project_id)

@router.post("/{project_id}/images")
def upload_images(project_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    result = project_service.upload_images(db, project_id, files)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"uploaded": result}

@router.post("/{project_id}/voc")
def upload_voc(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    count = project_service.upload_voc_dataset(db, project_id, file)
    if count is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"processed": count}

@router.get("/{project_id}/images")
def get_project_images(project_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return project_service.get_project_images(db, project_id, skip, limit)

@router.get("/{project_id}/annotations")
def get_annotation(project_id: int, image_name: str, db: Session = Depends(get_db)):
    content = project_service.get_annotation(db, project_id, image_name)
    if content is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"content": content}

@router.post("/{project_id}/annotations")
def save_annotation(project_id: int, annotation: AnnotationSave, db: Session = Depends(get_db)):
    result = project_service.save_annotation(db, project_id, annotation.image_name, annotation.content)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"path": result}

@router.get("/{project_id}/classes")
def get_classes(project_id: int, db: Session = Depends(get_db)):
    return project_service.get_classes(db, project_id)

@router.post("/{project_id}/classes")
def save_classes(project_id: int, data: ClassesSave, db: Session = Depends(get_db)):
    class_list = [c.strip() for c in data.classes.split(",") if c.strip()]
    project_service.save_classes(db, project_id, class_list)
    return {"classes": class_list}
