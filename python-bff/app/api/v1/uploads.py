from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.oss import generate_presigned_upload_url, generate_presigned_download_url

router = APIRouter()


class PresignedUploadRequest(BaseModel):
    filename: str = Field(..., description="Original filename, e.g. photo.jpg")
    content_type: str = Field(default="image/jpeg", description="MIME type")


class PresignedUploadResponse(BaseModel):
    upload_url: str
    key: str
    expires_in: int = 300


class PresignedDownloadResponse(BaseModel):
    download_url: str
    key: str
    expires_in: int = 3600


@router.post("/uploads/presign", response_model=PresignedUploadResponse)
async def presign_upload(req: PresignedUploadRequest):
    """Generate a presigned PUT URL for client-side file upload."""
    ext = req.filename.rsplit(".", 1)[-1] if "." in req.filename else "jpg"
    key = f"uploads/{uuid.uuid4().hex}.{ext}"
    try:
        url = generate_presigned_upload_url(key=key, content_type=req.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {e}")
    return PresignedUploadResponse(upload_url=url, key=key)


@router.get("/uploads/{key}/download", response_model=PresignedDownloadResponse)
async def presign_download(key: str):
    """Generate a presigned GET URL for file download."""
    try:
        url = generate_presigned_download_url(key=key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {e}")
    return PresignedDownloadResponse(download_url=url, key=key)
