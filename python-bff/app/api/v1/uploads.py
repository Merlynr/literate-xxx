from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_tenant_id
from app.services.oss import generate_presigned_download_url, generate_presigned_upload_url, upload_bytes

router = APIRouter()


class PresignedUploadRequest(BaseModel):
    filename: str = Field(..., description="Original filename, e.g. photo.jpg")
    content_type: str = Field(default="image/jpeg", description="MIME type")


class PresignedUploadResponse(BaseModel):
    upload_url: str
    key: str
    expires_in: int = 300


class DirectUploadResponse(BaseModel):
    key: str
    filename: str
    content_type: str
    size_bytes: int


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


@router.post("/uploads/direct", response_model=DirectUploadResponse, status_code=status.HTTP_201_CREATED)
async def direct_upload(
    file: UploadFile = File(...),
    tenant_id=Depends(get_current_tenant_id),
):
    """Upload file bytes through the BFF, then persist them to OSS.

    This is the reliable path for mini-program environments where a raw PUT
    request body may not be transmitted correctly.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    filename = file.filename or "upload.jpg"
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    key = f"uploads/{tenant_id.hex}/{uuid.uuid4().hex}.{ext}"
    content_type = file.content_type or "application/octet-stream"
    try:
        upload_bytes(content, key, content_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to OSS: {e}")
    return DirectUploadResponse(
        key=key,
        filename=filename,
        content_type=content_type,
        size_bytes=len(content),
    )


@router.get("/uploads/{key}/download", response_model=PresignedDownloadResponse)
async def presign_download(key: str):
    """Generate a presigned GET URL for file download."""
    try:
        url = generate_presigned_download_url(key=key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {e}")
    return PresignedDownloadResponse(download_url=url, key=key)
