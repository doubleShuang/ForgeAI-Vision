import os
import shutil
import glob
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from app.models.model import AnnotationProject
from fastapi import UploadFile
import json

class ProjectService:
    def __init__(self, workspace_root="workspaces"):
        self.workspace_root = workspace_root
        os.makedirs(self.workspace_root, exist_ok=True)

    def create_project(self, db: Session, name: str, description: str):
        # Create folder
        project_dir = os.path.join(self.workspace_root, name)
        os.makedirs(os.path.join(project_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "labels"), exist_ok=True)
        
        # Create default classes.txt
        with open(os.path.join(project_dir, "classes.txt"), "w") as f:
            f.write("object\n")

        # DB entry
        project = AnnotationProject(
            name=name,
            description=description,
            workspace_path=os.path.abspath(project_dir)
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def list_projects(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(AnnotationProject).offset(skip).limit(limit).all()

    def get_project(self, db: Session, project_id: int):
        return db.query(AnnotationProject).filter(AnnotationProject.id == project_id).first()

    def delete_project(self, db: Session, project_id: int):
        project = self.get_project(db, project_id)
        if project:
            # Delete files
            if os.path.exists(project.workspace_path):
                shutil.rmtree(project.workspace_path)
            # Delete DB
            db.delete(project)
            db.commit()
        return project

    def upload_images(self, db: Session, project_id: int, files: list[UploadFile]):
        project = self.get_project(db, project_id)
        if not project:
            return None
        
        image_dir = os.path.join(project.workspace_path, "images")
        saved_files = []
        for file in files:
            file_path = os.path.join(image_dir, file.filename)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            saved_files.append(file.filename)
        return saved_files

    def upload_voc_dataset(self, db: Session, project_id: int, file: UploadFile):
        project = self.get_project(db, project_id)
        if not project:
            return None
        
        # Ensure workspace exists
        if not os.path.exists(project.workspace_path):
            os.makedirs(project.workspace_path, exist_ok=True)

        # Paths
        temp_zip = os.path.join(project.workspace_path, "temp_voc.zip")
        extract_path = os.path.join(project.workspace_path, "temp_voc")
        
        # Cleanup previous failed attempts
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)

        try:
            # Save zip temporarily
            with open(temp_zip, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            # Extract
            import zipfile
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Search for XMLs and Images
            xml_files = glob.glob(os.path.join(extract_path, "**", "*.xml"), recursive=True)
            
            # Get existing classes
            classes = self.get_classes(db, project_id)
            class_map = {c: i for i, c in enumerate(classes)}
            
            processed_count = 0
            
            for xml_file in xml_files:
                try:
                    with open(xml_file, "r", encoding="utf-8") as f:
                        tree = ET.parse(f)
                    root = tree.getroot()
                    
                    # Image
                    filename = root.find('filename').text
                    # Find image file
                    xml_dir = os.path.dirname(xml_file)
                    # Try relative paths
                    possible_paths = [
                        os.path.join(xml_dir, filename),
                        os.path.join(xml_dir, "..", "JPEGImages", filename),
                        os.path.join(xml_dir, "..", "images", filename),
                    ]
                    src_img = None
                    for p in possible_paths:
                        if os.path.exists(p):
                            src_img = p
                            break
                    
                    if src_img:
                        # Copy Image
                        shutil.copy2(src_img, os.path.join(project.workspace_path, "images", filename))
                        
                        # Convert Annotation
                        txt_path = os.path.join(project.workspace_path, "labels", os.path.splitext(filename)[0] + ".txt")
                        
                        size = root.find('size')
                        w = int(size.find('width').text)
                        h = int(size.find('height').text)
                        
                        lines = []
                        for obj in root.iter('object'):
                            cls = obj.find('name').text
                            if cls not in class_map:
                                # Add new class
                                classes.append(cls)
                                class_map[cls] = len(classes) - 1
                            
                            cls_id = class_map[cls]
                            xmlbox = obj.find('bndbox')
                            b = (float(xmlbox.find('xmin').text), float(xmlbox.find('xmax').text), float(xmlbox.find('ymin').text), float(xmlbox.find('ymax').text))
                            bb = ((b[0] + b[1]) / 2.0 / w, (b[2] + b[3]) / 2.0 / h, (b[1] - b[0]) / w, (b[3] - b[2]) / h)
                            lines.append(f"{cls_id} {bb[0]:.6f} {bb[1]:.6f} {bb[2]:.6f} {bb[3]:.6f}")
                        
                        with open(txt_path, "w") as f:
                            f.write("\n".join(lines))
                        
                        processed_count += 1
                except Exception as e:
                    print(f"Error processing {xml_file}: {e}")
            
            # Save updated classes
            self.save_classes(db, project_id, classes)
            
            return processed_count
            
        except OSError as e:
            if e.errno == 28:
                raise Exception("Server disk is full. Please free up space.")
            raise e
        except Exception as e:
            raise e
        finally:
            # Cleanup
            try:
                if os.path.exists(temp_zip):
                    os.remove(temp_zip)
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
            except Exception as e:
                print(f"Warning: Failed to cleanup temp files: {e}")

    def get_project_images(self, db: Session, project_id: int, skip: int = 0, limit: int = 50):
        project = self.get_project(db, project_id)
        if not project:
            return []
        
        image_dir = os.path.join(project.workspace_path, "images")
        # List all images
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
        images = []
        for ext in extensions:
            images.extend(glob.glob(os.path.join(image_dir, ext)))
        names = [os.path.basename(img) for img in images]
        names.sort()
        return names[skip: skip + limit]

    def get_annotation(self, db: Session, project_id: int, image_name: str):
        project = self.get_project(db, project_id)
        if not project:
            return None
        
        label_name = os.path.splitext(image_name)[0] + ".txt"
        label_path = os.path.join(project.workspace_path, "labels", label_name)
        
        if os.path.exists(label_path):
            with open(label_path, "r") as f:
                return f.read()
        return ""

    def save_annotation(self, db: Session, project_id: int, image_name: str, annotation_content: str):
        project = self.get_project(db, project_id)
        if not project:
            return None
        
        # YOLO format txt file
        label_name = os.path.splitext(image_name)[0] + ".txt"
        label_path = os.path.join(project.workspace_path, "labels", label_name)
        
        with open(label_path, "w") as f:
            f.write(annotation_content)
        return label_path

    def get_classes(self, db: Session, project_id: int):
        project = self.get_project(db, project_id)
        if not project:
            return []
        
        classes_path = os.path.join(project.workspace_path, "classes.txt")
        if os.path.exists(classes_path):
            with open(classes_path, "r") as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        return ["object"]

    def save_classes(self, db: Session, project_id: int, classes: list):
        project = self.get_project(db, project_id)
        if not project:
            return
        
        classes_path = os.path.join(project.workspace_path, "classes.txt")
        with open(classes_path, "w") as f:
            f.write("\n".join(classes))

project_service = ProjectService()
