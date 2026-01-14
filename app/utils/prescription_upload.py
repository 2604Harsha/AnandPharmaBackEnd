import os
from fastapi import UploadFile

UPLOAD_DIR = "uploads/prescriptions"

def save_file(file: UploadFile) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path
