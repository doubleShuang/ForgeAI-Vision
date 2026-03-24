import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.model import Model, AnnotationProject, InferenceRecord, TrainingTask

# Initialize DB connection
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def to_relative(path):
    if not path:
        return path
    if os.path.isabs(path):
        try:
            # Try to make it relative to current working directory (backend/)
            rel = os.path.relpath(path, start=os.getcwd())
            # Simple check to avoid creating paths that go completely outside if not intended
            if not rel.startswith("..\\.."):
                # Clean up backwards slashes for consistency if desired, or keep os specific
                return rel.replace("\\", "/") 
            return path # keep as absolute if it's completely out of bounds
        except ValueError:
            # Happens on Windows if paths are on different drives
            return path
    return path.replace("\\", "/")

def migrate():
    db = SessionLocal()
    try:
        # Migrate Models
        models = db.query(Model).all()
        models_count = 0
        for m in models:
            if m.file_path and os.path.isabs(m.file_path):
                m.file_path = to_relative(m.file_path)
                models_count += 1
                
        # Migrate AnnotationProjects
        projects = db.query(AnnotationProject).all()
        projects_count = 0
        for p in projects:
            if p.workspace_path and os.path.isabs(p.workspace_path):
                p.workspace_path = to_relative(p.workspace_path)
                projects_count += 1
                
        # Migrate InferenceRecords
        records = db.query(InferenceRecord).all()
        records_count = 0
        for r in records:
            updated = False
            if r.input_path and os.path.isabs(r.input_path):
                r.input_path = to_relative(r.input_path)
                updated = True
            if r.output_path and os.path.isabs(r.output_path):
                r.output_path = to_relative(r.output_path)
                updated = True
            if r.model_name and os.path.isabs(r.model_name):
                r.model_name = to_relative(r.model_name)
                updated = True
            if updated:
                records_count += 1
                
        # Migrate TrainingTasks
        tasks = db.query(TrainingTask).all()
        tasks_count = 0
        for t in tasks:
            if t.result_path and os.path.isabs(t.result_path):
                t.result_path = to_relative(t.result_path)
                tasks_count += 1
                
        db.commit()
        print(f"Migration successful!")
        print(f"Updated Models: {models_count}")
        print(f"Updated Projects: {projects_count}")
        print(f"Updated Records: {records_count}")
        print(f"Updated Training Tasks: {tasks_count}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
