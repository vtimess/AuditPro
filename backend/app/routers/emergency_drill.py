from io import BytesIO
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.core.config import settings
from app.dependencies import CurrentUser, DbSession
from app.models.business import BusinessAttachment
from app.models.user import User
from app.schemas.common import ApiResponse


router = APIRouter(prefix="/emergency-drills", tags=["安全应急演练"])
MANAGER_ROLES = {"group_leader", "regional_manager", "regional_safety_manager", "project_leader"}
ALLOWED_FILES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 30 * 1024 * 1024


class EmergencyDrillDocumentView(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_size: int
    uploaded_by_name: str
    created_at: str
    preview_url: str
    export_url: str


def safe_original_name(value: str | None) -> str:
    name = Path(value or "").name.strip()
    if not name or len(name) > 255:
        raise HTTPException(status_code=400, detail="文件名称不正确")
    return name


def validate_document(content: bytes, extension: str) -> None:
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="PDF文件内容无效")
    if extension == ".doc" and not content.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        raise HTTPException(status_code=400, detail="Word .doc文件内容无效")
    if extension == ".docx":
        try:
            with ZipFile(BytesIO(content)) as archive:
                names = set(archive.namelist())
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise HTTPException(status_code=400, detail="Word .docx文件内容无效")
        except BadZipFile as exc:
            raise HTTPException(status_code=400, detail="Word .docx文件内容无效") from exc


def document_target(record: BusinessAttachment) -> Path:
    root = Path(settings.file_root).resolve()
    target = (root / record.storage_path).resolve()
    if root not in target.parents or not target.is_file():
        raise HTTPException(status_code=404, detail="应急演练方案文件不存在")
    return target


def get_document(file_id: int, current_user: CurrentUser, db: DbSession) -> BusinessAttachment:
    record = db.scalar(select(BusinessAttachment).where(
        BusinessAttachment.id == file_id,
        BusinessAttachment.business_type == "emergency_drill",
    ))
    if not record:
        raise HTTPException(status_code=404, detail="应急演练方案不存在")
    if current_user.role_code not in MANAGER_ROLES and record.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看该应急演练方案")
    return record


def to_view(record: BusinessAttachment, uploader_name: str) -> EmergencyDrillDocumentView:
    extension = Path(record.file_name).suffix.lower()
    return EmergencyDrillDocumentView(
        id=record.id, file_name=record.file_name, file_type=extension.lstrip(".").upper(),
        file_size=record.file_size, uploaded_by_name=uploader_name,
        created_at=record.created_at.isoformat(timespec="seconds"),
        preview_url=f"/api/v1/emergency-drills/{record.id}/preview",
        export_url=f"/api/v1/emergency-drills/{record.id}/export",
    )


@router.get("", response_model=ApiResponse[list[EmergencyDrillDocumentView]])
def list_documents(
    current_user: CurrentUser,
    db: DbSession,
    keyword: str = Query(default="", max_length=120),
):
    query = (
        select(BusinessAttachment, User.real_name)
        .join(User, User.id == BusinessAttachment.uploaded_by)
        .where(BusinessAttachment.business_type == "emergency_drill")
    )
    if current_user.role_code not in MANAGER_ROLES:
        query = query.where(BusinessAttachment.uploaded_by == current_user.id)
    if keyword:
        query = query.where(BusinessAttachment.file_name.contains(keyword))
    rows = db.execute(query.order_by(BusinessAttachment.id.desc()).limit(1000)).all()
    return ApiResponse(data=[to_view(record, uploader_name) for record, uploader_name in rows])


@router.post("/import", response_model=ApiResponse[EmergencyDrillDocumentView])
async def import_document(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
    original_name: str | None = Form(default=None),
):
    original_name = safe_original_name(original_name or file.filename)
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_FILES:
        raise HTTPException(status_code=400, detail="仅支持 .doc、.docx、.pdf 格式的应急演练方案")
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="单个方案文件不能超过30MB")
    if not content:
        raise HTTPException(status_code=400, detail="不能上传空文件")
    validate_document(content, extension)

    root = Path(settings.file_root)
    folder = root / "emergency_drill"
    folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{extension}"
    target = folder / stored_name
    target.write_bytes(content)
    record = BusinessAttachment(
        business_type="emergency_drill", business_id=0, usage_type="drill_plan",
        file_name=original_name, storage_path=str(target.relative_to(root)),
        content_type=ALLOWED_FILES[extension], file_size=len(content), uploaded_by=current_user.id,
    )
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        target.unlink(missing_ok=True)
        raise
    return ApiResponse(message="应急演练方案导入成功", data=to_view(record, current_user.real_name))


@router.get("/{file_id}/preview")
def preview_document(file_id: int, current_user: CurrentUser, db: DbSession):
    record = get_document(file_id, current_user, db)
    return FileResponse(
        document_target(record), media_type=record.content_type,
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(record.file_name)}"},
    )


@router.get("/{file_id}/export")
def export_document(file_id: int, current_user: CurrentUser, db: DbSession):
    record = get_document(file_id, current_user, db)
    return FileResponse(document_target(record), media_type=record.content_type, filename=record.file_name)
