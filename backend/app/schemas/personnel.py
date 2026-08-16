import re
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator

from app.core.id_card import age_from_birth_date, birth_date_from_id_card, normalize_id_card


POSITIONS = {"经理", "安全员", "会计", "带班长", "一班班组长", "二班班组长", "装卸工"}
EMPLOYMENT_STATUSES = {"在职", "离职"}
INSURANCE_TYPES = {"大港+工伤险", "大港+雇主责任险"}
CHRONIC_DISEASES = {"否", "高血压", "糖尿病"}


def china_today() -> date:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


class PersonnelInput(BaseModel):
    position: str
    employment_status: str = "在职"
    person_name: str = Field(min_length=2, max_length=64)
    gender: str
    id_card: str
    nationality: str = Field(default="汉族", min_length=1, max_length=32)
    education: str = Field(default="小学", min_length=1, max_length=32)
    chronic_disease: str = Field(default="否", min_length=1, max_length=32)
    smokes: bool = False
    drinks_alcohol: bool = False
    native_place: Optional[str] = Field(default=None, max_length=160)
    political_status: str = Field(default="群众", min_length=1, max_length=32)
    joined_party_at: Optional[date] = None
    served_in_military: bool = False
    military_service_time: Optional[str] = Field(default=None, max_length=64)
    port_entry_date: date = Field(default_factory=china_today)
    mobile: str = Field(min_length=11, max_length=11)
    home_address: Optional[str] = Field(default=None, max_length=500)
    emergency_contact: Optional[str] = Field(default=None, max_length=64)
    emergency_mobile: Optional[str] = Field(default=None, max_length=32)
    insurance_type: str

    @field_validator("position")
    @classmethod
    def validate_position(cls, value: str) -> str:
        if value not in POSITIONS:
            raise ValueError("职务岗位不正确")
        return value

    @field_validator("employment_status")
    @classmethod
    def validate_employment_status(cls, value: str) -> str:
        if value not in EMPLOYMENT_STATUSES:
            raise ValueError("在职状态不正确")
        return value

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
        birth_date_from_id_card(value)
        return value

    @field_validator("chronic_disease")
    @classmethod
    def validate_chronic_disease(cls, value: str) -> str:
        if value not in CHRONIC_DISEASES:
            raise ValueError("基础病必须为否、高血压或糖尿病")
        return value

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"1[3-9]\d{9}", value):
            raise ValueError("联系电话必须为11位手机号码")
        return value

    @field_validator("emergency_mobile")
    @classmethod
    def validate_emergency_mobile(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None
        value = value.strip()
        if not re.fullmatch(r"[0-9+\-\s]{7,20}", value):
            raise ValueError("紧急联系人电话格式不正确")
        return value

    @field_validator("insurance_type")
    @classmethod
    def validate_insurance_type(cls, value: str) -> str:
        if value not in INSURANCE_TYPES:
            raise ValueError("保险种类不正确")
        return value


class PersonnelView(BaseModel):
    id: int
    staff_no: str
    unit_name: str
    department_name: str
    position: str
    employment_status: str
    person_name: str
    gender: str
    id_card: str
    birth_date: date
    age: int
    nationality: str
    education: str
    chronic_disease: str
    has_chronic_disease: bool
    smokes: bool
    drinks_alcohol: bool
    native_place: Optional[str] = None
    political_status: Optional[str] = None
    joined_party_at: Optional[date] = None
    served_in_military: bool
    military_service_time: Optional[str] = None
    port_entry_date: Optional[date] = None
    mobile: str
    home_address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_mobile: Optional[str] = None
    insurance_type: str
    accident_insurance_limit: str
    created_at: datetime


class PersonnelImportResult(BaseModel):
    success_count: int
    failure_count: int
    errors: list[str] = Field(default_factory=list)


def calculate_age(birth_date: date) -> int:
    return age_from_birth_date(birth_date)
