from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.id_card import decrypt_id_card, encrypt_id_card, hash_id_card, mask_id_card
from app.dependencies import CurrentUser, DbSession
from app.models.business import PoliceRegistration
from app.schemas.business import PoliceRegistrationInput, PoliceRegistrationView
from app.schemas.common import ApiResponse


router = APIRouter(prefix="/police-filings", tags=["安全备案"])
MANAGER_ROLES = {"group_leader", "regional_manager", "regional_safety_manager", "project_leader"}


def scoped_query(current_user: CurrentUser):
    query = select(PoliceRegistration).where(PoliceRegistration.record_status == "active")
    if current_user.role_code not in MANAGER_ROLES:
        query = query.where(PoliceRegistration.created_by == current_user.id)
    return query


def to_view(record: PoliceRegistration, reveal: bool = False) -> PoliceRegistrationView:
    id_card = decrypt_id_card(record.id_card_ciphertext)
    return PoliceRegistrationView(
        id=record.id,
        person_name=record.person_name,
        gender=record.gender,
        id_card=id_card if reveal else mask_id_card(id_card),
        company_name=record.company_name,
        region=record.region,
        mobile=record.mobile,
        filing_status=record.filing_status,
        filing_date=record.filing_date,
        remarks=record.remarks,
        created_at=record.created_at,
    )


@router.post("", response_model=ApiResponse[PoliceRegistrationView])
def create_filing(payload: PoliceRegistrationInput, current_user: CurrentUser, db: DbSession):
    record = PoliceRegistration(
        created_by=current_user.id,
        person_name=payload.person_name.strip(),
        gender=payload.gender,
        id_card_ciphertext=encrypt_id_card(payload.id_card),
        id_card_hash=hash_id_card(payload.id_card),
        id_card_last4=payload.id_card[-4:],
        company_name=payload.company_name.strip(),
        region=payload.region.strip(),
        mobile=payload.mobile,
        filing_status=payload.filing_status,
        filing_date=payload.filing_date,
        remarks=payload.remarks,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="该身份证号已登记") from exc
    db.refresh(record)
    return ApiResponse(message="备案人员保存成功", data=to_view(record))


@router.get("", response_model=ApiResponse[list[PoliceRegistrationView]])
def list_filings(
    current_user: CurrentUser,
    db: DbSession,
    keyword: str = Query(default="", max_length=64),
    region: str = Query(default="", max_length=64),
    filing_status: str = Query(default="", max_length=20),
):
    query = scoped_query(current_user)
    if keyword:
        query = query.where(
            PoliceRegistration.person_name.contains(keyword)
            | PoliceRegistration.company_name.contains(keyword)
            | PoliceRegistration.id_card_last4.contains(keyword)
        )
    if region:
        query = query.where(PoliceRegistration.region == region)
    if filing_status:
        query = query.where(PoliceRegistration.filing_status == filing_status)
    records = db.scalars(query.order_by(PoliceRegistration.created_at.desc()).limit(500)).all()
    return ApiResponse(data=[to_view(item) for item in records])


@router.get("/export")
def export_filings(
    current_user: CurrentUser,
    db: DbSession,
    keyword: str = Query(default="", max_length=64),
    region: str = Query(default="", max_length=64),
    filing_status: str = Query(default="", max_length=20),
):
    query = scoped_query(current_user)
    if keyword:
        query = query.where(
            PoliceRegistration.person_name.contains(keyword)
            | PoliceRegistration.company_name.contains(keyword)
            | PoliceRegistration.id_card_last4.contains(keyword)
        )
    if region:
        query = query.where(PoliceRegistration.region == region)
    if filing_status:
        query = query.where(PoliceRegistration.filing_status == filing_status)
    records = db.scalars(query.order_by(PoliceRegistration.created_at.desc())).all()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "安全备案人员"
    sheet.append(["序号", "姓名", "性别", "身份证号", "联系电话", "公司名称", "所属地区", "备案状态", "备案日期", "备注"])
    status_names = {"pending": "待备案", "filed": "已备案", "not_required": "无需备案"}
    for index, record in enumerate(records, 1):
        sheet.append([
            index, record.person_name, record.gender, decrypt_id_card(record.id_card_ciphertext),
            record.mobile or "", record.company_name, record.region,
            status_names.get(record.filing_status, record.filing_status),
            record.filing_date.isoformat() if record.filing_date else "", record.remarks or "",
        ])
    widths = (8, 14, 8, 24, 16, 28, 14, 14, 14, 32)
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[chr(64 + index)].width = width
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    filename = quote(f"安全备案人员_{region or '全部地区'}.xlsx")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/{filing_id}", response_model=ApiResponse[PoliceRegistrationView])
def get_filing(filing_id: int, current_user: CurrentUser, db: DbSession):
    record = db.get(PoliceRegistration, filing_id)
    if not record or record.record_status != "active":
        raise HTTPException(status_code=404, detail="备案人员不存在")
    if current_user.role_code not in MANAGER_ROLES and record.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看该记录")
    return ApiResponse(data=to_view(record, reveal=True))


@router.put("/{filing_id}", response_model=ApiResponse[PoliceRegistrationView])
def update_filing(filing_id: int, payload: PoliceRegistrationInput, current_user: CurrentUser, db: DbSession):
    record = db.get(PoliceRegistration, filing_id)
    if not record or record.record_status != "active":
        raise HTTPException(status_code=404, detail="备案人员不存在")
    if current_user.role_code not in MANAGER_ROLES and record.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改该记录")
    for key in ("person_name", "gender", "company_name", "region", "mobile", "filing_status", "filing_date", "remarks"):
        setattr(record, key, getattr(payload, key))
    record.id_card_ciphertext = encrypt_id_card(payload.id_card)
    record.id_card_hash = hash_id_card(payload.id_card)
    record.id_card_last4 = payload.id_card[-4:]
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="该身份证号已登记") from exc
    db.refresh(record)
    return ApiResponse(message="备案信息修改成功", data=to_view(record))


@router.delete("/{filing_id}", response_model=ApiResponse[bool])
def delete_filing(filing_id: int, current_user: CurrentUser, db: DbSession):
    record = db.get(PoliceRegistration, filing_id)
    if not record or record.record_status != "active":
        raise HTTPException(status_code=404, detail="备案人员不存在")
    if current_user.role_code not in MANAGER_ROLES and record.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除该记录")
    record.record_status = "deleted"
    db.commit()
    return ApiResponse(message="备案信息已删除", data=True)
