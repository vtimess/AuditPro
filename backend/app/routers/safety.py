from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.models.business import BusinessAttachment, SafetyHazard, SafetyInspection
from app.schemas.business import (
    AttachmentView,
    HazardReviewInput,
    RectificationInput,
    SafetyHazardView,
    SafetyInspectionInput,
    SafetyInspectionView,
)
from app.schemas.common import ApiResponse


router = APIRouter(prefix="/safety-inspections", tags=["安全检查"])
MANAGER_ROLES = {"group_leader", "regional_manager", "regional_safety_manager", "project_leader"}
REVIEW_ROLES = {"regional_safety_manager", "project_leader"}
RISK_ORDER = {"general": 1, "high": 2, "major": 3}


def attachment_views(db: DbSession, business_type: str, business_id: int) -> list[AttachmentView]:
    records = db.scalars(select(BusinessAttachment).where(
        BusinessAttachment.business_type == business_type,
        BusinessAttachment.business_id == business_id,
    )).all()
    return [AttachmentView(
        id=item.id, usage_type=item.usage_type, file_name=item.file_name, file_size=item.file_size,
        created_at=item.created_at, download_url=f"/api/v1/files/{item.id}",
    ) for item in records]


def hazard_view(db: DbSession, item: SafetyHazard) -> SafetyHazardView:
    return SafetyHazardView(
        id=item.id, hazard_name=item.hazard_name, category=item.category, risk_level=item.risk_level,
        description=item.description, responsible_person=item.responsible_person,
        rectification_deadline=item.rectification_deadline,
        rectification_requirement=item.rectification_requirement, immediate_stop=item.immediate_stop,
        status=item.status, is_overdue=item.status != "completed" and item.rectification_deadline < date.today(),
        rectification_description=item.rectification_description, rectified_at=item.rectified_at,
        review_result=item.review_result, review_comment=item.review_comment,
        attachments=attachment_views(db, "safety_hazard", item.id),
    )


def inspection_view(db: DbSession, record: SafetyInspection) -> SafetyInspectionView:
    hazards = db.scalars(select(SafetyHazard).where(SafetyHazard.inspection_id == record.id).order_by(SafetyHazard.id)).all()
    views = [hazard_view(db, item) for item in hazards]
    completed = sum(item.status == "completed" for item in hazards)
    highest = max((item.risk_level for item in hazards), key=lambda value: RISK_ORDER[value], default=None)
    return SafetyInspectionView(
        id=record.id, inspection_project=record.inspection_project, region=record.region,
        inspection_area=record.inspection_area, inspected_at=record.inspected_at, inspectors=record.inspectors,
        location_text=record.location_text, weather=record.weather, site_readiness=record.site_readiness,
        environment_status=record.environment_status, equipment_status=record.equipment_status,
        fire_status=record.fire_status, ppe_status=record.ppe_status, work_order_status=record.work_order_status,
        description=record.description, hazard_count=len(hazards), highest_risk_level=highest,
        rectification_progress=round(completed / len(hazards) * 100) if hazards else 100,
        has_overdue=any(item.is_overdue for item in views), hazards=views,
        attachments=attachment_views(db, "safety_inspection", record.id), created_at=record.created_at,
    )


def scoped_query(current_user: CurrentUser):
    query = select(SafetyInspection).where(SafetyInspection.record_status == "active")
    if current_user.role_code not in MANAGER_ROLES:
        query = query.where(SafetyInspection.created_by == current_user.id)
    return query


@router.post("", response_model=ApiResponse[SafetyInspectionView])
def create_inspection(payload: SafetyInspectionInput, current_user: CurrentUser, db: DbSession):
    record = SafetyInspection(
        created_by=current_user.id, inspection_project=payload.inspection_project.strip(), region=payload.region.strip(),
        inspection_area=payload.inspection_area.strip(), inspected_at=payload.inspected_at,
        inspectors=payload.inspectors.strip(), location_text=payload.location_text, weather=payload.weather,
        site_readiness=payload.site_readiness, environment_status=payload.environment_status,
        equipment_status=payload.equipment_status, fire_status=payload.fire_status,
        ppe_status=payload.ppe_status, work_order_status=payload.work_order_status, description=payload.description,
    )
    db.add(record)
    db.flush()
    for item in payload.hazards:
        db.add(SafetyHazard(inspection_id=record.id, **item.model_dump()))
    db.commit()
    db.refresh(record)
    return ApiResponse(message="安全检查保存成功", data=inspection_view(db, record))


@router.get("", response_model=ApiResponse[list[SafetyInspectionView]])
def list_inspections(
    current_user: CurrentUser,
    db: DbSession,
    keyword: str = Query(default="", max_length=160),
    region: str = Query(default="", max_length=64),
):
    query = scoped_query(current_user)
    if keyword:
        query = query.where(SafetyInspection.inspection_project.contains(keyword) | SafetyInspection.inspection_area.contains(keyword))
    if region:
        query = query.where(SafetyInspection.region == region)
    records = db.scalars(query.order_by(SafetyInspection.inspected_at.desc()).limit(300)).all()
    return ApiResponse(data=[inspection_view(db, item) for item in records])


@router.get("/rectifications", response_model=ApiResponse[list[SafetyHazardView]])
def list_rectifications(current_user: CurrentUser, db: DbSession, status: str = Query(default="")):
    query = select(SafetyHazard).join(SafetyInspection, SafetyInspection.id == SafetyHazard.inspection_id)
    if current_user.role_code not in MANAGER_ROLES:
        query = query.where(
            (SafetyInspection.created_by == current_user.id)
            | (SafetyHazard.responsible_person == current_user.real_name)
        )
    if status:
        query = query.where(SafetyHazard.status == status)
    records = db.scalars(query.order_by(SafetyHazard.rectification_deadline.asc()).limit(500)).all()
    return ApiResponse(data=[hazard_view(db, item) for item in records])


@router.post("/hazards/{hazard_id}/rectify", response_model=ApiResponse[SafetyHazardView])
def submit_rectification(hazard_id: int, payload: RectificationInput, current_user: CurrentUser, db: DbSession):
    hazard = db.get(SafetyHazard, hazard_id)
    if not hazard:
        raise HTTPException(status_code=404, detail="危险点不存在")
    hazard.rectification_description = payload.description
    hazard.rectified_at = datetime.now()
    hazard.status = "pending_review"
    hazard.review_result = None
    db.commit()
    db.refresh(hazard)
    return ApiResponse(message="整改已提交复查", data=hazard_view(db, hazard))


@router.post("/hazards/{hazard_id}/review", response_model=ApiResponse[SafetyHazardView])
def review_hazard(hazard_id: int, payload: HazardReviewInput, current_user: CurrentUser, db: DbSession):
    if current_user.role_code not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="当前角色无复查权限")
    hazard = db.get(SafetyHazard, hazard_id)
    if not hazard:
        raise HTTPException(status_code=404, detail="危险点不存在")
    if hazard.status != "pending_review":
        raise HTTPException(status_code=409, detail="该危险点当前不处于待复查状态")
    hazard.review_result = payload.result
    hazard.review_comment = payload.comment
    hazard.reviewed_by = current_user.id
    hazard.reviewed_at = datetime.now()
    hazard.status = "completed" if payload.result == "approved" else "pending"
    db.commit()
    db.refresh(hazard)
    return ApiResponse(message="复查已完成", data=hazard_view(db, hazard))
