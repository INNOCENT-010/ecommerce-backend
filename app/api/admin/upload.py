# app/api/admin/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid

router = APIRouter(prefix="/admin/upload", tags=["admin"])

@router.post("")
async def upload_file(file: UploadFile = File(...), type: str = "logo"):
    allowed_types = ['image/jpeg', 'image/png', 'image/svg+xml', 'image/x-icon']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    ext = os.path.splitext(file.filename)[1]
    filename = f"{type}_{uuid.uuid4().hex[:8]}{ext}"
    
    upload_dir = "app/static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {"url": f"/uploads/{filename}"}