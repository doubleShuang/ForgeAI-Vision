import os
import yaml
import torch
from ultralytics import YOLO
import threading
import shutil
import glob
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from app.models.model import TrainingTask, AnnotationProject
from app.db.session import SessionLocal

import json

class TrainingService:
    def __init__(self):
        self.active_tasks = {} # task_id -> {"thread": Thread, "stop_event": Event}
        # self.training_status = {} # task_id -> status dict (Now using DB)

    def stop_training(self, task_id: int, db: Session):
        if task_id in self.active_tasks:
            # Signal stop
            # Note: YOLOv8 doesn't have a direct "stop" method easily accessible from outside without patching callbacks or raising exceptions.
            # We can use a custom callback to check for a stop flag.
            self.active_tasks[task_id]['stop_event'].set()
            return True
        return False

    def get_status(self, task_id: int, db: Session):
        task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
        if not task:
            return {"status": "unknown", "progress": 0}
        
        # Calculate progress
        progress = 0
        if task.epochs > 0:
            progress = int((task.current_epoch / task.epochs) * 100)
        
        return {
            "status": task.status,
            "progress": progress,
            "log": task.log.split("\n") if task.log else [],
            "result_path": task.result_path,
            "config": json.loads(task.config) if task.config else {},
            "error": None # Ideally stored in DB too
        }

    def create_task(self, db: Session, model_name: str, project_id: int, epochs: int, batch_size: int, config: dict = None):
        task = TrainingTask(
            model_name=model_name,
            project_id=project_id,
            epochs=epochs,
            batch_size=batch_size,
            status="pending",
            config=json.dumps(config) if config else "{}"
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def start_training(self, task_id: int, db: Session):
        task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
        if not task:
            return
        
        # Get project info
        project = db.query(AnnotationProject).filter(AnnotationProject.id == task.project_id).first()
        data_path = project.workspace_path if project else "coco128.yaml" # Fallback
        
        task.status = "starting"
        db.commit()
        
        # Run in a separate thread
        stop_event = threading.Event()
        thread = threading.Thread(
            target=self._train_task,
            args=(task_id, task.model_name, project.workspace_path if project else None, task.epochs, task.batch_size, stop_event)
        )
        self.active_tasks[task_id] = {"thread": thread, "stop_event": stop_event}
        thread.start()

    def _train_task(self, task_id, model_name, data_path, epochs, batch_size, stop_event):
        # Create a new session for the thread
        db = SessionLocal()
        task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
        
        print(f"Starting training task {task_id}...")
        task.status = "running"
        self._append_log(task, f"Starting training task {task_id}...")
        db.commit()
        
        try:
            config = json.loads(task.config) if task.config else {}
            device = config.get('device', 'cpu')
            
            # Debug CUDA
            try:
                self._append_log(task, f"DEBUG: torch.cuda.is_available() = {torch.cuda.is_available()}")
                self._append_log(task, f"DEBUG: torch.cuda.device_count() = {torch.cuda.device_count()}")
                if torch.cuda.is_available():
                    self._append_log(task, f"DEBUG: Device Name = {torch.cuda.get_device_name(0)}")
            except Exception as e:
                self._append_log(task, f"DEBUG: Error checking CUDA: {e}")

            # Check CUDA availability
            if device != 'cpu':
                if not torch.cuda.is_available():
                    self._append_log(task, f"Warning: CUDA not available. Fallback to CPU. (Requested: {device})")
                    device = 'cpu'
                else:
                    # Validate device index if specified
                    try:
                        # If device is "0,1", check if we have enough GPUs
                        requested_indices = [int(x) for x in str(device).split(',') if x.strip().isdigit()]
                        available_count = torch.cuda.device_count()
                        for idx in requested_indices:
                            if idx >= available_count:
                                self._append_log(task, f"Warning: Requested GPU {idx} not available (Count: {available_count}). Fallback to CPU.")
                                device = 'cpu'
                                break
                    except:
                        # Fallback if parsing fails but keep original if valid string like "0"
                        pass

            imgsz = int(config.get('imgsz', 640))
            optimizer = config.get('optimizer', 'auto')
            
            self._append_log(task, f"Training Config: Device={device}, ImgSz={imgsz}, Optimizer={optimizer}")

            if not data_path:
                 raise ValueError("Invalid project workspace path")

            # 1. Prepare Dataset
            final_data_path = data_path
            
            # Check if it's a directory (Project Workspace or Raw Path)
            if os.path.isdir(data_path):
                self._append_log(task, f"Processing dataset at {data_path}...")
                
                # Check for VOC XMLs
                xml_files = glob.glob(os.path.join(data_path, "**", "*.xml"), recursive=True)
                
                if xml_files:
                    self._append_log(task, f"Detected {len(xml_files)} XML files. Converting VOC to YOLO format...")
                    final_data_path = self._convert_voc_to_yolo(task, model_name, data_path, xml_files)
                else:
                    # Assume YOLO format (images/ and labels/ folders exist or simple flat structure)
                    # We create a data.yaml wrapper
                    work_dir = os.path.join("runs", "datasets", model_name)
                    os.makedirs(work_dir, exist_ok=True)
                    yaml_path = os.path.join(work_dir, "data.yaml")
                    
                    # YOLO expects relative paths to be relative to the yaml file location OR absolute paths.
                    # Safe bet: Use absolute paths for train/val
                    
                    # Check structure:
                    # if images/ exists inside data_path, use that.
                    images_dir = os.path.join(data_path, "images")
                    if not os.path.exists(images_dir):
                        # Maybe flat structure? Or directly inside data_path?
                        # Let's assume images are in data_path if 'images' subdir doesn't exist, 
                        # but standard is 'images' folder.
                        # If the user just uploaded images to project root/images, we are good.
                        images_dir = data_path # Fallback
                        
                    dataset_config = {
                        'path': os.path.abspath(data_path), # Root
                        'train': 'images', # relative to path
                        'val': 'images',   # relative to path
                        'names': {0: 'object'} # Default class
                    }
                    
                    # Try to find classes.txt
                    classes_file = os.path.join(data_path, "classes.txt")
                    if os.path.exists(classes_file):
                         with open(classes_file, 'r') as f:
                             names = {i: n.strip() for i, n in enumerate(f.readlines()) if n.strip()}
                             if names:
                                 dataset_config['names'] = names

                    with open(yaml_path, 'w') as f:
                        yaml.dump(dataset_config, f)
                    
                    final_data_path = yaml_path

            self._append_log(task, f"Using dataset config: {final_data_path}")
            db.commit()

            # 2. Load model
            base_model = config.get('base_model', 'yolov8n.pt')
            self._append_log(task, f"Loading base model: {base_model}")
            
            # If base_model is a file path, ensure it exists
            if base_model.endswith('.pt') and os.path.sep in base_model and not os.path.exists(base_model):
                 self._append_log(task, f"Warning: Base model path {base_model} not found. Fallback to yolov8n.pt")
                 base_model = "yolov8n.pt"
                 
            model = YOLO(base_model) 
            
            # 3. Add a callback to update progress and check for stop
            def on_train_epoch_end(trainer):
                if stop_event.is_set():
                    self._append_log(task, "Training stopped by user.")
                    db.commit()
                    trainer.stop = True # Signal YOLO to stop
                    raise InterruptedError("Training stopped by user")

                try:
                    # Re-query task to avoid stale object
                    # Use a new session to avoid threading issues with shared session state if any (though we use local)
                    # But here we are inside the thread, so `db` is local.
                    # However, to be safe and see updates, we might need to expire/refresh.
                    db.expire_all()
                    t = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
                    if t:
                        t.current_epoch = trainer.epoch + 1
                        t.accuracy = float(trainer.metrics.get('metrics/mAP50-95(B)', 0))
                        self._append_log(t, f"Epoch {t.current_epoch}/{epochs} completed. mAP: {t.accuracy:.4f}")
                        db.commit()
                except Exception as ex:
                    print(f"Callback error: {ex}")

            model.add_callback("on_train_epoch_end", on_train_epoch_end)

            # 4. Train
            self._append_log(task, "Starting YOLOv8 training...")
            db.commit()
            
            # Use absolute path for project save dir to avoid confusion
            save_dir = os.path.abspath(os.path.join("runs", "train"))
            
            results = model.train(
                data=final_data_path, 
                epochs=epochs, 
                batch=batch_size, 
                project=save_dir, 
                name=model_name,
                device=device,
                imgsz=imgsz,
                optimizer=optimizer
            )
            
            # Re-query
            t = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
            t.status = "completed"
            t.current_epoch = epochs
            t.result_path = str(results.save_dir)
            self._append_log(t, f"Training completed. Model saved to {results.save_dir}")
            db.commit()
            
        except Exception as e:
            print(f"Training task {task_id} failed: {e}")
            t = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
            t.status = "failed"
            self._append_log(t, f"Error: {str(e)}")
            # traceback
            import traceback
            self._append_log(t, traceback.format_exc())
            db.commit()
        finally:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            db.close()

    def _convert_voc_to_yolo(self, task, model_name, source_path, xml_files):
        # Create a processed dataset folder
        processed_dir = os.path.join("runs", "datasets", f"{model_name}_processed")
        if os.path.exists(processed_dir):
            shutil.rmtree(processed_dir)
        os.makedirs(os.path.join(processed_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(processed_dir, "labels"), exist_ok=True)
        
        classes = set()
        
        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Image info
                filename = root.find('filename').text
                size = root.find('size')
                w = int(size.find('width').text)
                h = int(size.find('height').text)
                
                # Find corresponding image file
                # Try same directory as xml or ../JPEGImages or ../image or ../images
                xml_dir = os.path.dirname(xml_file)
                possible_img_paths = [
                    os.path.join(xml_dir, filename),
                    os.path.join(xml_dir, "..", "JPEGImages", filename),
                    os.path.join(xml_dir, "..", "images", filename),
                    os.path.join(xml_dir, "..", "image", filename),
                    # Fallback: search recursively in source_path (slow but robust)
                ]
                
                src_img_path = None
                for p in possible_img_paths:
                    if os.path.exists(p):
                        src_img_path = p
                        break
                
                if not src_img_path:
                    # Try finding by name in source_path
                    found_imgs = glob.glob(os.path.join(source_path, "**", filename), recursive=True)
                    if found_imgs:
                        src_img_path = found_imgs[0]
                
                if not src_img_path:
                    self._append_log(task, f"Warning: Image {filename} not found for {xml_file}")
                    continue
                
                # Copy image
                dst_img_path = os.path.join(processed_dir, "images", filename)
                shutil.copy2(src_img_path, dst_img_path)
                
                # Convert labels
                txt_filename = os.path.splitext(filename)[0] + ".txt"
                txt_path = os.path.join(processed_dir, "labels", txt_filename)
                
                with open(txt_path, "w") as f:
                    for obj in root.iter('object'):
                        cls_name = obj.find('name').text
                        classes.add(cls_name)
                        # We need to map class name to ID. 
                        # For now, we will collect all classes and assign IDs later? 
                        # Or we assume a fixed class map?
                        # Dynamic mapping requires two passes. 
                        # Let's do a simple mapping on the fly but we need to know the ID.
                        # We'll store class names in the txt for a moment and rewrite? No, YOLO needs ID.
                        # We need a consistent class map.
                        pass 
            except Exception as e:
                self._append_log(task, f"Error parsing {xml_file}: {e}")

        # Second pass: Generate class map and write files
        # Wait, avoiding two passes is better. 
        # Let's collect all data first.
        
        # Reset and do it properly
        dataset_data = [] # List of (txt_path, objects)
        all_classes = sorted(list(classes)) # This won't work if we populate classes inside the loop
        
        # We need to scan classes first? Or just append to a list and process.
        # Let's scan first.
        self._append_log(task, "Scanning classes...")
        detected_classes = set()
        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                for obj in tree.getroot().iter('object'):
                    detected_classes.add(obj.find('name').text)
            except: pass
            
        class_list = sorted(list(detected_classes))
        class_map = {name: i for i, name in enumerate(class_list)}
        self._append_log(task, f"Detected classes: {class_map}")
        
        # Processing loop
        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                filename = root.find('filename').text
                size = root.find('size')
                w = int(size.find('width').text)
                h = int(size.find('height').text)
                
                # Find image (Reuse logic)
                xml_dir = os.path.dirname(xml_file)
                src_img_path = None
                # ... (Same search logic as above)
                possible_img_paths = [
                    os.path.join(xml_dir, filename),
                    os.path.join(xml_dir, "..", "JPEGImages", filename),
                    os.path.join(xml_dir, "..", "images", filename),
                    os.path.join(xml_dir, "..", "image", filename)
                ]
                for p in possible_img_paths:
                    if os.path.exists(p):
                        src_img_path = p
                        break
                if not src_img_path:
                    found_imgs = glob.glob(os.path.join(source_path, "**", filename), recursive=True)
                    if found_imgs: src_img_path = found_imgs[0]
                
                if src_img_path:
                    shutil.copy2(src_img_path, os.path.join(processed_dir, "images", filename))
                    
                    txt_path = os.path.join(processed_dir, "labels", os.path.splitext(filename)[0] + ".txt")
                    with open(txt_path, "w") as f:
                        for obj in root.iter('object'):
                            cls = obj.find('name').text
                            if cls not in class_map: continue
                            cls_id = class_map[cls]
                            
                            xmlbox = obj.find('bndbox')
                            b = (float(xmlbox.find('xmin').text), float(xmlbox.find('xmax').text), float(xmlbox.find('ymin').text), float(xmlbox.find('ymax').text))
                            
                            # Convert to YOLO (x_center, y_center, w, h) normalized
                            bb = ((b[0] + b[1]) / 2.0 / w, (b[2] + b[3]) / 2.0 / h, (b[1] - b[0]) / w, (b[3] - b[2]) / h)
                            
                            f.write(f"{cls_id} {bb[0]:.6f} {bb[1]:.6f} {bb[2]:.6f} {bb[3]:.6f}\n")
            except Exception as e:
                pass

        # Create data.yaml
        yaml_path = os.path.join(processed_dir, "data.yaml")
        dataset_config = {
            'path': os.path.abspath(processed_dir),
            'train': 'images',
            'val': 'images',
            'names': {i: name for i, name in enumerate(class_list)}
        }
        with open(yaml_path, 'w') as f:
            yaml.dump(dataset_config, f)
            
        return yaml_path

    def _append_log(self, task, message):
        if not task.log:
            task.log = ""
        task.log += message + "\n"

training_service = TrainingService()
