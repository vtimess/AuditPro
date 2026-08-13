from __future__ import annotations

import os
from datetime import date, timedelta

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("AUTO_CREATE_TABLES", "false")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.routers import auth as auth_router  # noqa: E402


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def login() -> tuple[str, dict]:
    response = client.post(
        "/api/v1/auth/wechat-login",
        json={"code": "test-code", "nickname": "测试用户", "avatar_url": ""},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["code"] == 0
    return body["data"]["access_token"], body["data"]["user"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_home_workbench_and_profile(monkeypatch):
    monkeypatch.setattr(
        auth_router,
        "exchange_code",
        lambda _: {"openid": "test_openid", "unionid": None},
    )
    token, user = login()
    headers = {"Authorization": f"Bearer {token}"}
    assert user["role_code"] == "ordinary_user"

    home = client.get("/api/v1/home", headers=headers)
    assert home.status_code == 200
    assert home.json()["data"]["user"]["real_name"] == "测试用户"
    assert len(home.json()["data"]["metrics"]) == 4

    workbench = client.get("/api/v1/workbench", headers=headers)
    assert workbench.status_code == 200
    assert len(workbench.json()["data"]["modules"]) >= 5

    profile = client.get("/api/v1/profile", headers=headers)
    assert profile.status_code == 200

    updated = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"real_name": "张三", "mobile": "13800000000"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["real_name"] == "张三"
    assert updated.json()["data"]["mobile"] == "13800000000"


def test_protected_endpoint_requires_token():
    response = client.get("/api/v1/profile")
    assert response.status_code == 401


def test_attendance_punch_calendar_and_supplement(monkeypatch):
    monkeypatch.setattr(
        auth_router,
        "exchange_code",
        lambda _: {"openid": "attendance_openid", "unionid": None},
    )
    token, _ = login()
    headers = {"Authorization": f"Bearer {token}"}

    today = client.get("/api/v1/attendance/today", headers=headers)
    assert today.status_code == 200
    assert today.json()["data"]["current_action"] == "check_in"

    payload = {"latitude": 31.2304, "longitude": 121.4737, "accuracy": 10, "location_text": "测试位置"}
    check_in = client.post("/api/v1/attendance/punch", headers=headers, json=payload)
    assert check_in.status_code == 200
    assert check_in.json()["data"]["punch_type"] == "check_in"

    check_out = client.post("/api/v1/attendance/punch", headers=headers, json=payload)
    assert check_out.status_code == 200
    assert check_out.json()["data"]["punch_type"] == "check_out"

    month = date.today().strftime("%Y-%m")
    calendar_response = client.get(f"/api/v1/attendance/month?month={month}", headers=headers)
    assert calendar_response.status_code == 200
    today_item = next(item for item in calendar_response.json()["data"]["days"] if item["date"] == date.today().isoformat())
    assert today_item["status"] == "complete"

    supplement_day = date.today() - timedelta(days=1)
    supplement = client.post(
        "/api/v1/attendance/supplements",
        headers=headers,
        json={
            "work_date": supplement_day.isoformat(),
            "punch_type": "check_in",
            "punch_time": "09:00:00",
            "reason": "外出作业忘记打卡",
        },
    )
    assert supplement.status_code == 200
    assert supplement.json()["data"]["review_status"] == "pending"


def test_police_purchase_and_safety_modules(monkeypatch):
    monkeypatch.setattr(
        auth_router,
        "exchange_code",
        lambda _: {"openid": "business_openid", "unionid": None},
    )
    token, _ = login()
    headers = {"Authorization": f"Bearer {token}"}

    filing = client.post(
        "/api/v1/police-filings",
        headers=headers,
        json={
            "person_name": "李四", "gender": "男", "id_card": "11010519491231002X",
            "company_name": "镇江港务有限公司", "region": "镇江", "mobile": "13800000000",
            "filing_status": "pending",
        },
    )
    assert filing.status_code == 200, filing.text
    assert "*" in filing.json()["data"]["id_card"]
    export = client.get("/api/v1/police-filings/export", headers=headers)
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("application/vnd.openxmlformats")

    rejected_purchase = client.post(
        "/api/v1/consumable-purchases",
        headers=headers,
        json={
            "category": "劳保用品", "item_name": "安全帽", "quantity": "10", "unit": "个",
            "unit_price": "20.00", "total_amount": "180.00", "purchase_date": date.today().isoformat(),
            "region": "镇江",
        },
    )
    assert rejected_purchase.status_code == 422
    purchase = client.post(
        "/api/v1/consumable-purchases",
        headers=headers,
        json={
            "category": "劳保用品", "item_name": "安全帽", "quantity": "10", "unit": "个",
            "unit_price": "20.00", "total_amount": "180.00", "total_adjustment_reason": "供应商优惠",
            "purchase_date": date.today().isoformat(), "region": "镇江",
        },
    )
    assert purchase.status_code == 200, purchase.text
    assert purchase.json()["data"]["is_manual_total"] is True
    assert purchase.json()["data"]["calculated_total"] == "200.00"
    purchase_id = purchase.json()["data"]["id"]
    selected_export = client.get(f"/api/v1/consumable-purchases/export?ids={purchase_id}", headers=headers)
    assert selected_export.status_code == 200
    assert selected_export.headers["content-type"].startswith("application/vnd.openxmlformats")

    inspection = client.post(
        "/api/v1/safety-inspections",
        headers=headers,
        json={
            "inspection_project": "一号码头", "region": "镇江", "inspection_area": "装卸区",
            "inspected_at": "2026-08-13T09:30:00", "inspectors": "测试用户",
            "site_readiness": "rectification", "hazards": [{
                "hazard_name": "临边防护缺失", "category": "作业环境", "risk_level": "major",
                "description": "临边区域未设置防护栏", "responsible_person": "测试用户",
                "rectification_deadline": "2026-08-20", "rectification_requirement": "设置防护栏和警示标志",
                "immediate_stop": True,
            }],
        },
    )
    assert inspection.status_code == 200, inspection.text
    hazard = inspection.json()["data"]["hazards"][0]
    assert hazard["risk_level"] == "major"
    rectified = client.post(
        f"/api/v1/safety-inspections/hazards/{hazard['id']}/rectify",
        headers=headers,
        json={"description": "已安装防护栏和警示标志"},
    )
    assert rectified.status_code == 200
    assert rectified.json()["data"]["status"] == "pending_review"
