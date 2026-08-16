from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.id_card import is_valid_id_card, normalize_id_card


FIXED_FILING_COMPANY = "泗阳星光装卸有限公司"
FILING_REGIONS = {"镇江", "南京"}


class PoliceRegistrationInput(BaseModel):
    person_name: str = Field(min_length=2, max_length=64)
    gender: str
    id_card: str
    company_name: str = Field(default=FIXED_FILING_COMPANY, min_length=1, max_length=160)
    region: str = Field(default="镇江", min_length=1, max_length=64)
    mobile: str = Field(min_length=7, max_length=32)
    filing_status: str = "pending"
    filing_date: Optional[date] = None
    remarks: Optional[str] = Field(default=None, max_length=500)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str) -> str:
        if value not in {"男", "女"}:
            raise ValueError("性别必须为男或女")
        return value

    @field_validator("id_card")
    @classmethod
    def validate_id_card(cls, value: str) -> str:
        value = normalize_id_card(value)
        if not is_valid_id_card(value):
            raise ValueError("身份证号格式或校验码不正确")
        return value

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"[0-9+\-\s]{7,20}", value):
            raise ValueError("联系电话格式不正确")
        return value

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, value: str) -> str:
        if value != FIXED_FILING_COMPANY:
            raise ValueError(f"公司名称固定为{FIXED_FILING_COMPANY}")
        return value

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        if value not in FILING_REGIONS:
            raise ValueError("所属地区只能选择镇江或南京")
        return value

    @field_validator("filing_status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {"pending", "filed", "not_required"}:
            raise ValueError("备案状态不正确")
        return value

    @model_validator(mode="after")
    def validate_filing_date(self):
        if self.filing_status == "filed" and not self.filing_date:
            raise ValueError("已备案时必须填写备案日期")
        return self


class PoliceRegistrationView(BaseModel):
    id: int
    person_name: str
    gender: str
    id_card: str
    age: int
    company_name: str
    region: str
    mobile: Optional[str] = None
    filing_status: str
    filing_date: Optional[date] = None
    remarks: Optional[str] = None
    created_at: datetime


class ConsumablePurchaseInput(BaseModel):
    category: str = Field(min_length=1, max_length=64)
    item_name: str = Field(min_length=1, max_length=120)
    quantity: Decimal = Field(gt=0, decimal_places=3)
    unit: str = Field(min_length=1, max_length=32)
    unit_price: Decimal = Field(ge=0, decimal_places=2)
    total_amount: Decimal = Field(ge=0, decimal_places=2)
    total_adjustment_reason: Optional[str] = Field(default=None, max_length=500)
    purchase_date: date
    supplier_name: Optional[str] = Field(default=None, max_length=160)
    invoice_number: Optional[str] = Field(default=None, max_length=80)
    region: str = Field(default="镇江", min_length=1, max_length=64)
    description: Optional[str] = Field(default=None, max_length=500)

    @property
    def calculated_total(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @model_validator(mode="after")
    def validate_manual_total(self):
        if self.total_amount != self.calculated_total and not (self.total_adjustment_reason or "").strip():
            raise ValueError("手工总价与数量×单价不一致时，必须填写调整原因")
        return self


class AttachmentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usage_type: str
    file_name: str
    file_size: int
    created_at: datetime
    download_url: str


class ConsumablePurchaseView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: str
    item_name: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    total_amount: Decimal
    calculated_total: Decimal
    is_manual_total: bool
    total_adjustment_reason: Optional[str] = None
    purchase_date: date
    supplier_name: Optional[str] = None
    invoice_number: Optional[str] = None
    region: str
    operator_name: str
    description: Optional[str] = None
    attachments: List[AttachmentView] = Field(default_factory=list)
    created_at: datetime


class SafetyHazardInput(BaseModel):
    hazard_name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=32)
    risk_level: str
    description: str = Field(min_length=2, max_length=1000)
    responsible_person: str = Field(min_length=1, max_length=64)
    rectification_deadline: date
    rectification_requirement: str = Field(min_length=2, max_length=1000)
    immediate_stop: bool = False

    @field_validator("risk_level")
    @classmethod
    def validate_risk(cls, value: str) -> str:
        if value not in {"general", "high", "major"}:
            raise ValueError("风险等级不正确")
        return value


class SafetyInspectionInput(BaseModel):
    inspection_project: str = Field(min_length=1, max_length=160)
    region: str = Field(default="镇江", min_length=1, max_length=64)
    inspection_area: str = Field(min_length=1, max_length=160)
    inspected_at: datetime
    inspectors: str = Field(min_length=1, max_length=255)
    location_text: Optional[str] = Field(default=None, max_length=255)
    weather: Optional[str] = Field(default=None, max_length=64)
    site_readiness: str
    environment_status: str = "normal"
    equipment_status: str = "normal"
    fire_status: str = "normal"
    ppe_status: str = "normal"
    work_order_status: str = "normal"
    description: Optional[str] = Field(default=None, max_length=1000)
    hazards: List[SafetyHazardInput] = Field(default_factory=list, max_length=20)

    @field_validator("site_readiness")
    @classmethod
    def validate_readiness(cls, value: str) -> str:
        if value not in {"normal", "basic", "rectification"}:
            raise ValueError("现场整备情况不正确")
        return value

    @field_validator("environment_status", "equipment_status", "fire_status", "ppe_status", "work_order_status")
    @classmethod
    def validate_check_status(cls, value: str) -> str:
        if value not in {"normal", "abnormal", "not_applicable"}:
            raise ValueError("检查项状态不正确")
        return value


class SafetyHazardView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hazard_name: str
    category: str
    risk_level: str
    description: str
    responsible_person: str
    rectification_deadline: date
    rectification_requirement: str
    immediate_stop: bool
    status: str
    is_overdue: bool
    rectification_description: Optional[str] = None
    rectified_at: Optional[datetime] = None
    review_result: Optional[str] = None
    review_comment: Optional[str] = None
    attachments: List[AttachmentView] = Field(default_factory=list)


class SafetyInspectionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inspection_project: str
    region: str
    inspection_area: str
    inspected_at: datetime
    inspectors: str
    location_text: Optional[str] = None
    weather: Optional[str] = None
    site_readiness: str
    environment_status: str
    equipment_status: str
    fire_status: str
    ppe_status: str
    work_order_status: str
    description: Optional[str] = None
    hazard_count: int
    highest_risk_level: Optional[str] = None
    rectification_progress: int
    has_overdue: bool
    hazards: List[SafetyHazardView] = Field(default_factory=list)
    attachments: List[AttachmentView] = Field(default_factory=list)
    created_at: datetime


class RectificationInput(BaseModel):
    description: str = Field(min_length=2, max_length=1000)


class HazardReviewInput(BaseModel):
    result: str
    comment: str = Field(min_length=2, max_length=1000)

    @field_validator("result")
    @classmethod
    def validate_result(cls, value: str) -> str:
        if value not in {"approved", "rejected"}:
            raise ValueError("复查结果不正确")
        return value
