from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.models.attendance import AttendanceRecord
from app.schemas.attendance import (
    CalendarDay,
    LocationInput,
    MonthAttendance,
    PunchResult,
    SupplementRequest,
    TodayAttendance,
)
from app.schemas.common import ApiResponse


router = APIRouter(prefix="/attendance", tags=["考勤打卡"])
SHANGHAI = ZoneInfo("Asia/Shanghai")


def now_local() -> datetime:
    return datetime.now(SHANGHAI).replace(tzinfo=None)


def to_result(record: AttendanceRecord) -> PunchResult:
    return PunchResult.model_validate(record, from_attributes=True)


def day_records(db: DbSession, user_id: int, work_date: date) -> list[AttendanceRecord]:
    return list(
        db.scalars(
            select(AttendanceRecord)
            .where(
                AttendanceRecord.user_id == user_id,
                AttendanceRecord.work_date == work_date,
                AttendanceRecord.review_status.in_(["approved", "pending"]),
            )
            .order_by(AttendanceRecord.punched_at.asc())
        )
    )


@router.get("/today", response_model=ApiResponse[TodayAttendance])
def get_today(current_user: CurrentUser, db: DbSession) -> ApiResponse[TodayAttendance]:
    today = now_local().date()
    records = day_records(db, current_user.id, today)
    check_in = records[0] if records else None
    check_out = records[-1] if len(records) >= 2 else None
    current_action = "check_in" if not records else "check_out"
    return ApiResponse(
        data=TodayAttendance(
            work_date=today,
            current_action=current_action,
            check_in=to_result(check_in) if check_in else None,
            check_out=to_result(check_out) if check_out else None,
            punch_count=len(records),
        )
    )


@router.post("/punch", response_model=ApiResponse[PunchResult])
def punch(
    payload: LocationInput,
    current_user: CurrentUser,
    db: DbSession,
) -> ApiResponse[PunchResult]:
    punched_at = now_local()
    records = day_records(db, current_user.id, punched_at.date())
    punch_type = "check_in" if not records else "check_out"
    record = AttendanceRecord(
        user_id=current_user.id,
        work_date=punched_at.date(),
        punch_type=punch_type,
        punched_at=punched_at,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        location_text=payload.location_text,
        source="normal",
        review_status="approved",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ApiResponse(
        message="上班打卡成功" if punch_type == "check_in" else "下班打卡成功",
        data=to_result(record),
    )


@router.get("/month", response_model=ApiResponse[MonthAttendance])
def get_month(
    current_user: CurrentUser,
    db: DbSession,
    month: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
) -> ApiResponse[MonthAttendance]:
    year, month_number = (int(part) for part in month.split("-"))
    first_day = date(year, month_number, 1)
    last_day = date(year, month_number, calendar.monthrange(year, month_number)[1])
    records = list(
        db.scalars(
            select(AttendanceRecord)
            .where(
                AttendanceRecord.user_id == current_user.id,
                AttendanceRecord.work_date.between(first_day, last_day),
                AttendanceRecord.review_status.in_(["approved", "pending"]),
            )
            .order_by(AttendanceRecord.punched_at.asc())
        )
    )
    grouped: dict[date, list[AttendanceRecord]] = defaultdict(list)
    for record in records:
        grouped[record.work_date].append(record)

    today = now_local().date()
    days: list[CalendarDay] = []
    summary = {"complete": 0, "partial": 0, "missing": 0, "pending": 0}
    for day_number in range(1, last_day.day + 1):
        current_date = date(year, month_number, day_number)
        items = grouped.get(current_date, [])
        pending = any(item.review_status == "pending" for item in items)
        approved = [item for item in items if item.review_status == "approved"]
        types = {item.punch_type for item in items}
        missing_types = [kind for kind in ("check_in", "check_out") if kind not in types]
        check_in = next((item for item in items if item.punch_type == "check_in"), None)
        check_out_candidates = [item for item in items if item.punch_type == "check_out"]
        check_out = check_out_candidates[-1] if check_out_candidates else None

        if current_date > today:
            status, status_text = "future", "未到"
        elif pending:
            status, status_text = "pending", "补卡待审核"
            summary["pending"] += 1
        elif {"check_in", "check_out"} <= {item.punch_type for item in approved}:
            status, status_text = "complete", "正常"
            summary["complete"] += 1
        elif approved:
            status, status_text = "partial", "缺卡"
            summary["partial"] += 1
        else:
            status, status_text = "missing", "缺卡"
            summary["missing"] += 1

        days.append(
            CalendarDay(
                date=current_date,
                day=day_number,
                is_today=current_date == today,
                status=status,
                status_text=status_text,
                check_in_time=check_in.punched_at.strftime("%H:%M") if check_in else None,
                check_out_time=check_out.punched_at.strftime("%H:%M") if check_out else None,
                missing_types=missing_types if current_date <= today else [],
                has_pending_supplement=pending,
            )
        )
    return ApiResponse(data=MonthAttendance(month=month, summary=summary, days=days))


@router.post("/supplements", response_model=ApiResponse[PunchResult])
def supplement(
    payload: SupplementRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ApiResponse[PunchResult]:
    today = now_local().date()
    if payload.work_date > today:
        raise HTTPException(status_code=400, detail="不能补未来日期的打卡")
    existing = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.user_id == current_user.id,
            AttendanceRecord.work_date == payload.work_date,
            AttendanceRecord.punch_type == payload.punch_type,
            AttendanceRecord.review_status.in_(["approved", "pending"]),
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="该时段已有打卡或待审核补卡")

    record = AttendanceRecord(
        user_id=current_user.id,
        work_date=payload.work_date,
        punch_type=payload.punch_type,
        punched_at=datetime.combine(payload.work_date, payload.punch_time),
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_text=payload.location_text,
        source="supplement",
        supplement_reason=payload.reason,
        review_status="pending",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ApiResponse(message="补卡申请已提交", data=to_result(record))
