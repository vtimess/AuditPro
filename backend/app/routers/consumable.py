from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.models.business import BusinessAttachment, ConsumablePurchase
from app.schemas.business import AttachmentView, ConsumablePurchaseInput, ConsumablePurchaseView
from app.schemas.common import ApiResponse


router = APIRouter(prefix="/consumable-purchases", tags=["耗材采购"])
MANAGER_ROLES = {"group_leader", "regional_manager", "regional_safety_manager", "project_leader"}


def scoped_query(current_user: CurrentUser):
    query = select(ConsumablePurchase).where(ConsumablePurchase.record_status == "active")
    if current_user.role_code not in MANAGER_ROLES:
        query = query.where(ConsumablePurchase.created_by == current_user.id)
    return query


def attachment_views(db: DbSession, purchase_id: int) -> list[AttachmentView]:
    records = db.scalars(
        select(BusinessAttachment).where(
            BusinessAttachment.business_type == "consumable_purchase",
            BusinessAttachment.business_id == purchase_id,
        )
    ).all()
    return [
        AttachmentView(
            id=item.id, usage_type=item.usage_type, file_name=item.file_name,
            file_size=item.file_size, created_at=item.created_at,
            download_url=f"/api/v1/files/{item.id}",
        ) for item in records
    ]


def to_view(db: DbSession, record: ConsumablePurchase) -> ConsumablePurchaseView:
    calculated = (record.quantity * record.unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return ConsumablePurchaseView(
        id=record.id, category=record.category, item_name=record.item_name,
        quantity=record.quantity, unit=record.unit, unit_price=record.unit_price,
        total_amount=record.total_amount, calculated_total=calculated,
        is_manual_total=record.is_manual_total,
        total_adjustment_reason=record.total_adjustment_reason,
        purchase_date=record.purchase_date, supplier_name=record.supplier_name,
        invoice_number=record.invoice_number, region=record.region,
        operator_name=record.operator_name, description=record.description,
        attachments=attachment_views(db, record.id), created_at=record.created_at,
    )


@router.post("", response_model=ApiResponse[ConsumablePurchaseView])
def create_purchase(payload: ConsumablePurchaseInput, current_user: CurrentUser, db: DbSession):
    manual = payload.total_amount != payload.calculated_total
    record = ConsumablePurchase(
        created_by=current_user.id, category=payload.category.strip(), item_name=payload.item_name.strip(),
        quantity=payload.quantity, unit=payload.unit.strip(), unit_price=payload.unit_price,
        total_amount=payload.total_amount, is_manual_total=manual,
        total_adjustment_reason=payload.total_adjustment_reason.strip() if manual else None,
        purchase_date=payload.purchase_date, supplier_name=payload.supplier_name,
        invoice_number=payload.invoice_number, region=payload.region.strip(),
        operator_name=current_user.real_name, description=payload.description,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ApiResponse(message="采购记录保存成功", data=to_view(db, record))


@router.get("", response_model=ApiResponse[list[ConsumablePurchaseView]])
def list_purchases(
    current_user: CurrentUser,
    db: DbSession,
    keyword: str = Query(default="", max_length=120),
    category: str = Query(default="", max_length=64),
    region: str = Query(default="", max_length=64),
):
    query = scoped_query(current_user)
    if keyword:
        query = query.where(ConsumablePurchase.item_name.contains(keyword) | ConsumablePurchase.operator_name.contains(keyword))
    if category:
        query = query.where(ConsumablePurchase.category == category)
    if region:
        query = query.where(ConsumablePurchase.region == region)
    records = db.scalars(query.order_by(ConsumablePurchase.purchase_date.desc(), ConsumablePurchase.id.desc()).limit(500)).all()
    return ApiResponse(data=[to_view(db, item) for item in records])


@router.get("/export")
def export_purchases(
    current_user: CurrentUser,
    db: DbSession,
    keyword: str = Query(default="", max_length=120),
    category: str = Query(default="", max_length=64),
    region: str = Query(default="", max_length=64),
):
    query = scoped_query(current_user)
    if keyword:
        query = query.where(ConsumablePurchase.item_name.contains(keyword) | ConsumablePurchase.operator_name.contains(keyword))
    if category:
        query = query.where(ConsumablePurchase.category == category)
    if region:
        query = query.where(ConsumablePurchase.region == region)
    records = db.scalars(query.order_by(ConsumablePurchase.purchase_date.desc(), ConsumablePurchase.id.desc())).all()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "采购台账"
    sheet.append(["序号", "采购日期", "耗材类别", "耗材名称", "数量", "单位", "单价", "总价", "是否手工调整", "调整原因", "供应商名称", "发票号码", "发票状态", "所属地区", "经办人", "采购说明"])
    for index, record in enumerate(records, 1):
        invoice_count = len(attachment_views(db, record.id))
        sheet.append([
            index, record.purchase_date.isoformat(), record.category, record.item_name, float(record.quantity),
            record.unit, float(record.unit_price), float(record.total_amount), "是" if record.is_manual_total else "否",
            record.total_adjustment_reason or "", record.supplier_name or "", record.invoice_number or "",
            "已上传" if invoice_count else "未上传", record.region, record.operator_name, record.description or "",
        ])
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    filename = quote(f"耗材采购台账_{region or '全部地区'}.xlsx")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/{purchase_id}", response_model=ApiResponse[ConsumablePurchaseView])
def get_purchase(purchase_id: int, current_user: CurrentUser, db: DbSession):
    record = db.get(ConsumablePurchase, purchase_id)
    if not record or record.record_status != "active":
        raise HTTPException(status_code=404, detail="采购记录不存在")
    if current_user.role_code not in MANAGER_ROLES and record.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看该记录")
    return ApiResponse(data=to_view(db, record))


@router.put("/{purchase_id}", response_model=ApiResponse[ConsumablePurchaseView])
def update_purchase(purchase_id: int, payload: ConsumablePurchaseInput, current_user: CurrentUser, db: DbSession):
    record = db.get(ConsumablePurchase, purchase_id)
    if not record or record.record_status != "active":
        raise HTTPException(status_code=404, detail="采购记录不存在")
    if current_user.role_code not in MANAGER_ROLES and record.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改该记录")
    manual = payload.total_amount != payload.calculated_total
    values = payload.model_dump(exclude={"total_adjustment_reason"})
    for key, value in values.items():
        setattr(record, key, value)
    record.is_manual_total = manual
    record.total_adjustment_reason = payload.total_adjustment_reason.strip() if manual else None
    db.commit()
    db.refresh(record)
    return ApiResponse(message="采购记录修改成功", data=to_view(db, record))


@router.delete("/{purchase_id}", response_model=ApiResponse[bool])
def delete_purchase(purchase_id: int, current_user: CurrentUser, db: DbSession):
    record = db.get(ConsumablePurchase, purchase_id)
    if not record or record.record_status != "active":
        raise HTTPException(status_code=404, detail="采购记录不存在")
    if current_user.role_code not in MANAGER_ROLES and record.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除该记录")
    record.record_status = "deleted"
    db.commit()
    return ApiResponse(message="采购记录已删除", data=True)
