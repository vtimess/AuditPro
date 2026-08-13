import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.config import settings
from app.dependencies import CurrentUser, DbSession
from app.models.business import BusinessAttachment
from app.schemas.business import AttachmentView
from app.schemas.common import ApiResponse


router = APIRouter(prefix="/files", tags=["业务附件"])
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
BUSINESS_TYPES = {"consumable_purchase", "safety_inspection", "safety_hazard"}


def safe_path(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "", value.lower())


@router.post("/upload", response_model=ApiResponse[AttachmentView])
async def upload_file(
    current_user: CurrentUser,
    db: DbSession,
    business_type: str = Form(...),
    business_id: int = Form(..., gt=0),
    usage_type: str = Form(default="general"),
    file: UploadFile = File(...),
):
    if business_type not in BUSINESS_TYPES:
        raise HTTPException(status_code=400, detail="附件业务类型不正确")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG、WebP 图片")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="单张图片不能超过10MB")
    folder = Path(settings.file_root) / safe_path(business_type)
    folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{ALLOWED_TYPES[file.content_type]}"
    target = folder / stored_name
    target.write_bytes(content)
    record = BusinessAttachment(
        business_type=business_type, business_id=business_id, usage_type=safe_path(usage_type) or "general",
        file_name=(file.filename or stored_name)[:255], storage_path=str(target.relative_to(Path(settings.file_root))),
        content_type=file.content_type, file_size=len(content), uploaded_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ApiResponse(data=AttachmentView(
        id=record.id, usage_type=record.usage_type, file_name=record.file_name,
        file_size=record.file_size, created_at=record.created_at,
        download_url=f"/api/v1/files/{record.id}",
    ))


@router.get("/{file_id}")
def download_file(file_id: int, current_user: CurrentUser, db: DbSession):
    record = db.scalar(select(BusinessAttachment).where(BusinessAttachment.id == file_id))
    if not record:
        raise HTTPException(status_code=404, detail="附件不存在")
    target = (Path(settings.file_root) / record.storage_path).resolve()
    root = Path(settings.file_root).resolve()
    if root not in target.parents or not target.is_file():
        raise HTTPException(status_code=404, detail="附件文件不存在")
    return FileResponse(target, media_type=record.content_type, filename=record.file_name)
