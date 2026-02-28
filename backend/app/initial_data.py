import os
import shutil
import requests
import json
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models.model import Base, Model # Import Base to create tables

def init_db(db: Session):
    # Create tables
    Base.metadata.create_all(bind=engine)

    # 1. Official YOLOv8 Models (General Purpose)
    # COCO 80 classes subset for "shrunk" list: Person, Vehicle
    coco_subset = {
        "0": "Person (人)",
        "1": "Bicycle (自行车)",
        "2": "Car (汽车)",
        "3": "Motorcycle (摩托车)",
        "5": "Bus (公交车)",
        "7": "Truck (卡车)"
    }
    coco_subset_json = json.dumps(coco_subset)

    official_models = [
        {"name": "YOLOv8n (Nano)", "type": "detector", "accuracy": 0.37, "file_path": "yolov8n.pt", "desc": "Fastest, lightweight", "classes": coco_subset_json},
        {"name": "YOLOv8s (Small)", "type": "detector", "accuracy": 0.44, "file_path": "yolov8s.pt", "desc": "Balanced speed/accuracy", "classes": coco_subset_json},
        {"name": "YOLOv8m (Medium)", "type": "detector", "accuracy": 0.50, "file_path": "yolov8m.pt", "desc": "Higher accuracy", "classes": coco_subset_json},
    ]

    for m_data in official_models:
        existing = db.query(Model).filter(Model.name == m_data["name"]).first()
        if not existing:
            print(f"Registering official model: {m_data['name']}")
            model = Model(
                name=m_data["name"],
                type=m_data["type"],
                accuracy=m_data["accuracy"],
                file_path=m_data["file_path"],
                description=m_data["desc"],
                classes=m_data["classes"]
            )
            db.add(model)
        else:
            # Update classes if exists
            existing.classes = m_data["classes"]
            
        # Ensure file exists
        if not os.path.exists(m_data["file_path"]):
            print(f"Note: {m_data['file_path']} will be downloaded by Ultralytics on first use.")

    # 2. Safety Helmet Models (Correct Configuration)
    # The user specifies these are independent pre-trained models, not YOLOv8.
    # We update the configuration to point to the correct files.
    # Note: 'classes' for these models are typically 'hat' and 'person'.
    helmet_classes = {
        "0": "hat (安全帽)",
        "1": "person (人)"
    }
    helmet_classes_json = json.dumps(helmet_classes)
    
    # Path relative to backend root or absolute
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "safety_helmet"))
    
    helmet_models = [
        {"name": "Safety Helmet (MobileNet 0.25)", "type": "mxnet", "accuracy": 0.75, "file_path": os.path.join(base_path, "mobile0.25.params"), "desc": "MXNet MobileNet0.25-SSD (Requires MXNet Env)", "classes": helmet_classes_json},
        {"name": "Safety Helmet (MobileNet 1.0)", "type": "mxnet", "accuracy": 0.86, "file_path": os.path.join(base_path, "mobilenet1.0.params"), "desc": "MXNet MobileNet1.0-SSD (Requires MXNet Env)", "classes": helmet_classes_json},
        {"name": "Safety Helmet (Darknet53)", "type": "mxnet", "accuracy": 0.88, "file_path": os.path.join(base_path, "darknet.params"), "desc": "MXNet Darknet53-YOLOv3 (Requires MXNet Env)", "classes": helmet_classes_json},
    ]

    for m_data in helmet_models:
        # Check if we need to update existing entries or create new ones
        # We will search by name. If the previous "YOLOv8 Port" entries exist, we update them to be "Real" configuration.
        # But names are slightly different. Let's try to match by similarity or just add new ones and delete old ones?
        # User said "Update configuration... from YOLOv8n to correct...".
        # So we should find the ones pointing to 'yolov8n.pt' with 'Safety Helmet' in name and update them.
        
        # Strategy:
        # 1. Update "Safety Helmet (MobileNet 0.25 - YOLOv8 Port)" -> "Safety Helmet (MobileNet 0.25)"
        # 2. Update "Safety Helmet (MobileNet 1.0 - YOLOv8 Port)" -> "Safety Helmet (MobileNet 1.0)"
        # 3. Update "Safety Helmet (Darknet Pre-trained)" -> "Safety Helmet (Darknet53)"
        
        # To avoid duplicates, we first delete the old "YOLOv8 Port" ones if we are going to create new clean ones, OR we update them.
        # Let's update them to preserve IDs if possible, but names change.
        
        # Mapping old names to new names
        if "MobileNet 0.25" in m_data["name"]:
            old_name_pattern = "%MobileNet 0.25%"
        elif "MobileNet 1.0" in m_data["name"]:
            old_name_pattern = "%MobileNet 1.0%"
        else:
            old_name_pattern = "%Darknet%"

        target = db.query(Model).filter(Model.name.like(old_name_pattern)).first()
        
        if target:
            print(f"Updating model: {target.name} -> {m_data['name']}")
            target.name = m_data["name"]
            target.type = m_data["type"]
            target.accuracy = m_data["accuracy"]
            target.file_path = m_data["file_path"]
            target.description = m_data["desc"]
            target.classes = m_data["classes"]
        else:
            print(f"Registering new model: {m_data['name']}")
            model = Model(
                name=m_data["name"],
                type=m_data["type"],
                accuracy=m_data["accuracy"],
                file_path=m_data["file_path"],
                description=m_data["desc"],
                classes=m_data["classes"]
            )
            db.add(model)

    db.commit()

if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
    print("Database initialization completed.")
