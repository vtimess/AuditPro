from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class LocationInput(BaseModel):
    latitude: Decimal = Field(ge=-90, le=90)
    longitude: Decimal = Field(ge=-180, le=180)
    accuracy: Optional[Decimal] = Field(default=None, ge=0)
    location_text: Optional[str] = Field(default=None, max_length=255)


class PunchResult(BaseModel):
    id: int
    punch_type: str
    punched_at: datetime
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    location_text: Optional[str] = None
    source: str
    review_status: str


class TodayAttendance(BaseModel):
    work_date: date
    current_action: str
    check_in: Optional[PunchResult] = None
    check_out: Optional[PunchResult] = None
    punch_count: int


class CalendarDay(BaseModel):
    date: date
    day: int
    is_current_month: bool = True
    is_today: bool = False
    status: str
    status_text: str
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    missing_types: List[str] = Field(default_factory=list)
    has_pending_supplement: bool = False


class MonthAttendance(BaseModel):
    month: str
    summary: Dict[str, int]
    days: List[CalendarDay]


class SupplementRequest(BaseModel):
    work_date: date
    punch_type: str
    punch_time: time
    reason: str = Field(min_length=2, max_length=500)
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180)
    location_text: Optional[str] = Field(default=None, max_length=255)

    @field_validator("punch_type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in {"check_in", "check_out"}:
            raise ValueError("补卡类型必须为 check_in 或 check_out")
        return value
