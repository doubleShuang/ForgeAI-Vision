from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    type = Column(String(50))
    accuracy = Column(Float)
    file_path = Column(String(500))
    description = Column(Text)
    classes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TrainingTask(Base):
    __tablename__ = "training_tasks"
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(255), index=True)
    project_id = Column(Integer, index=True)
    epochs = Column(Integer, default=10)
    batch_size = Column(Integer, default=16)
    status = Column(String(50), default="pending")
    config = Column(Text)
    current_epoch = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    log = Column(Text)
    result_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AnnotationProject(Base):
    __tablename__ = "annotation_projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text)
    workspace_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class InferenceRecord(Base):
    __tablename__ = "inference_records"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    file_type = Column(String(50))
    input_path = Column(String(500))
    output_path = Column(String(500))
    model_name = Column(String(255))
    detections_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
