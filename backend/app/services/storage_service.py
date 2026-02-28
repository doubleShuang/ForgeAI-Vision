import shutil
import os
from minio import Minio
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.use_local = settings.USE_LOCAL_STORAGE
        if not self.use_local:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False
            )

    def save_file(self, file_obj, filename: str, bucket: str) -> str:
        if self.use_local:
            target_dir = os.path.join(settings.UPLOAD_DIR, bucket)
            os.makedirs(target_dir, exist_ok=True)
            base, ext = os.path.splitext(filename)
            candidate = filename
            idx = 1
            while os.path.exists(os.path.join(target_dir, candidate)):
                candidate = f"{base}_{idx}{ext}"
                idx += 1
            file_path = os.path.join(target_dir, candidate)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file_obj.file, buffer)
            return file_path
        else:
            # MinIO implementation
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
            self.client.put_object(
                bucket, filename, file_obj.file, length=-1, part_size=10*1024*1024
            )
            return f"{bucket}/{filename}"

    def get_file_path(self, file_path_or_key: str) -> str:
        """Returns a local accessible path. If remote, might need to download."""
        if self.use_local:
            return file_path_or_key
        else:
            # For simplicity in this demo, we assume we download it to a temp path for inference
            # or return a presigned URL. For backend inference, we need a local path.
            bucket, key = file_path_or_key.split("/", 1)
            local_path = os.path.join(settings.UPLOAD_DIR, "temp", key)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.client.fget_object(bucket, key, local_path)
            return local_path

storage_service = StorageService()
