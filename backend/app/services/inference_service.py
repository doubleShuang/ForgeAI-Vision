from ultralytics import YOLO
import cv2
import os
import subprocess
from typing import List, Optional

class InferenceService:
    def __init__(self):
        self.models = {} # Cache loaded models

    def load_model(self, model_path: str):
        # Validate model format
        if not model_path.endswith('.pt') and not model_path.endswith('.yaml') and model_path not in ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"]:
            if model_path.endswith('.params') or model_path.endswith('.weights'):
                 # Check if MXNet/GluonCV is available
                 try:
                     import mxnet
                     import gluoncv
                 except ImportError:
                     raise ValueError(f"Missing dependency: MXNet/GluonCV is required to run {os.path.basename(model_path)}. Please install 'mxnet' and 'gluoncv' or use a compatible Python environment (e.g. 3.8).")
                 
                 raise ValueError(f"MXNet model support is currently disabled/incomplete due to missing symbol files for {os.path.basename(model_path)}. Please provide .json symbol files.")
        
        if model_path not in self.models:
            print(f"Loading model from {model_path}")
            self.models[model_path] = YOLO(model_path)
        return self.models[model_path]
    
    # Removed is_mxnet_model check as we are fully YOLO now

    def predict_image(self, model_path: str, image_path: str, classes: Optional[List[int]] = None):
        model = self.load_model(model_path)
        # Pass 'classes' argument to predict method if provided
        results = model.predict(source=image_path, save=False, classes=classes)
        # Parse results for frontend
        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    "class": model.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": box.xyxy[0].tolist() # [x1, y1, x2, y2]
                })
        return detections

    def process_video(self, model_path: str, video_path: str, output_path: str, classes: Optional[List[int]] = None):
        """
        Process video file and save annotated video to output_path.
        Uses OpenCV for processing and FFmpeg for H.264 encoding.
        Returns the path to the annotated video.
        """
        model = self.load_model(model_path)
        cap = cv2.VideoCapture(video_path)
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Intermediate file (using mp4v which OpenCV handles well, but browsers don't)
        temp_output = output_path.replace(".mp4", "_temp.mp4")
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Run tracking/inference
            results = model.track(source=frame, persist=True, verbose=False, classes=classes)
            
            # Visualize results on frame
            annotated_frame = results[0].plot()
            
            # Write frame
            out.write(annotated_frame)
            
        cap.release()
        out.release()
        
        # Use FFmpeg to convert to H.264 (browser compatible)
        # ffmpeg -i input.mp4 -vcodec libx264 -acodec aac output.mp4
        if os.path.exists(temp_output):
            try:
                # Remove existing output if any
                if os.path.exists(output_path):
                    os.remove(output_path)
                    
                command = [
                    "ffmpeg", "-y",
                    "-i", temp_output,
                    "-vcodec", "libx264",
                    "-preset", "fast",
                    "-crf", "23", # Good balance of quality/size
                    output_path
                ]
                subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Clean up temp file
                os.remove(temp_output)
            except Exception as e:
                print(f"FFmpeg conversion failed: {e}")
                # Fallback: rename temp to output (might not play in browser but better than nothing)
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(temp_output, output_path)
        
        return output_path

inference_service = InferenceService()
