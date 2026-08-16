from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def bigint_pk():
    return BigInteger().with_variant(Integer, "sqlite")


class PoliceRegistration(Base):
    __tablename__ = "ops_police_registration"

    id: Mapped[int] = mapped_column(bigint_pk(), primary_key=True, autoincrement=True)
    created_by: Mapped[int] = mapped_column(bigint_pk(), ForeignKey("sys_user.id"), index=True)
    person_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    id_card_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    id_card_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    id_card_last4: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(64), nullable=False, default="镇江", index=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    filing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    filing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    record_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Personnel(Base):
    __tablename__ = "ops_personnel"

    id: Mapped[int] = mapped_column(bigint_pk(), primary_key=True, autoincrement=True)
    staff_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True, index=True)
    unit_name: Mapped[str] = mapped_column(String(64), nullable=False, default="泗阳队")
    department_name: Mapped[str] = mapped_column(String(64), nullable=False, default="泗阳劳务")
    position: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    employment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="在职", index=True)
    person_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    id_card_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    id_card_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    id_card_last4: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    nationality: Mapped[str] = mapped_column(String(32), nullable=False, default="汉族")
    education: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    chronic_disease: Mapped[str] = mapped_column(String(32), nullable=False, default="否")
    has_chronic_disease: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    smokes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    drinks_alcohol: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    native_place: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    political_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    joined_party_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    served_in_military: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    military_service_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    port_entry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    mobile: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    home_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    emergency_mobile: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    insurance_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    accident_insurance_limit: Mapped[str] = mapped_column(String(20), nullable=False, default="150+")
    created_by: Mapped[int] = mapped_column(bigint_pk(), ForeignKey("sys_user.id"), index=True)
    record_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class ConsumablePurchase(Base):
    __tablename__ = "ops_consumable_purchase"

    id: Mapped[int] = mapped_column(bigint_pk(), primary_key=True, autoincrement=True)
    created_by: Mapped[int] = mapped_column(bigint_pk(), ForeignKey("sys_user.id"), index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_manual_total: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    total_adjustment_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    supplier_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    region: Mapped[str] = mapped_column(String(64), nullable=False, default="镇江", index=True)
    operator_name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    record_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class BusinessAttachment(Base):
    __tablename__ = "ops_business_attachment"

    id: Mapped[int] = mapped_column(bigint_pk(), primary_key=True, autoincrement=True)
    business_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    business_id: Mapped[int] = mapped_column(bigint_pk(), nullable=False, index=True)
    usage_type: Mapped[str] = mapped_column(String(32), nullable=False, default="general")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by: Mapped[int] = mapped_column(bigint_pk(), ForeignKey("sys_user.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class SafetyInspection(Base):
    __tablename__ = "ops_safety_inspection"

    id: Mapped[int] = mapped_column(bigint_pk(), primary_key=True, autoincrement=True)
    created_by: Mapped[int] = mapped_column(bigint_pk(), ForeignKey("sys_user.id"), index=True)
    inspection_project: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(64), nullable=False, default="镇江", index=True)
    inspection_area: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    inspected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    inspectors: Mapped[str] = mapped_column(String(255), nullable=False)
    location_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    weather: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    site_readiness: Mapped[str] = mapped_column(String(20), nullable=False)
    environment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    equipment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    fire_status: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    ppe_status: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    work_order_status: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    record_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class SafetyHazard(Base):
    __tablename__ = "ops_safety_hazard"

    id: Mapped[int] = mapped_column(bigint_pk(), primary_key=True, autoincrement=True)
    inspection_id: Mapped[int] = mapped_column(bigint_pk(), ForeignKey("ops_safety_inspection.id"), index=True)
    hazard_name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    responsible_person: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rectification_deadline: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    rectification_requirement: Mapped[str] = mapped_column(Text, nullable=False)
    immediate_stop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    rectification_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rectified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[int]] = mapped_column(bigint_pk(), ForeignKey("sys_user.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
