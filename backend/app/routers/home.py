from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DbSession
from app.models.notification import Notification
from app.schemas.common import ApiResponse
from app.schemas.home import HomeMetric, HomeResult, WorkbenchModule, WorkbenchResult
from app.schemas.user import UserView


router = APIRouter(tags=["小程序"])


ROLE_SUMMARIES = {
    "group_leader": "集团审计态势与重大风险概览",
    "regional_manager": "本地区审计态势与整改进度",
    "regional_safety_manager": "本地区安全风险与检查任务",
    "project_leader": "负责项目、成员任务与待复核事项",
    "ordinary_user": "查看我的待办、参与项目和最新通知",
}


WORKBENCH_MODULES = [
    ("personnel_management", "人员管理", "人员", "人员管理", {"group_leader", "regional_manager", "regional_safety_manager", "project_leader", "ordinary_user"}),
    ("heart_to_heart_talk", "谈心谈话", "谈话", "人员管理", {"group_leader", "regional_manager", "regional_safety_manager", "project_leader", "ordinary_user"}),
    ("safety_inspection", "安全检查", "检查", "现场管理", {"regional_safety_manager", "project_leader", "ordinary_user"}),
    ("emergency_drill", "安全应急演练", "演练", "现场管理", {"group_leader", "regional_manager", "regional_safety_manager", "project_leader", "ordinary_user"}),
    ("police_filing", "安全备案", "备案", "人员管理", {"regional_safety_manager", "project_leader", "ordinary_user"}),
    ("consumable_purchase", "耗材采购", "采购", "作业管理", {"regional_safety_manager", "project_leader", "ordinary_user"}),
    ("dispatch", "派工", "派工", "作业管理", {"regional_safety_manager", "project_leader", "ordinary_user"}),
    ("attendance", "工时打卡", "打卡", "现场管理", {"regional_safety_manager", "project_leader", "ordinary_user"}),
    ("audit_project", "审计项目", "项目", "审计业务", {"group_leader", "regional_manager", "regional_safety_manager", "project_leader", "ordinary_user"}),
    ("rectification", "整改跟踪", "整改", "审计业务", {"group_leader", "regional_manager", "regional_safety_manager", "project_leader", "ordinary_user"}),
    ("risk_analysis", "风险分析", "风险", "查询分析", {"group_leader", "regional_manager", "regional_safety_manager", "project_leader"}),
]


ROLE_METRIC_LABELS = {
    "group_leader": (("regions", "覆盖地区"), ("major_risks", "重大风险"), ("rectification", "整改完成率"), ("overdue", "逾期整改")),
    "regional_manager": (("projects", "在审项目"), ("major_risks", "重大风险"), ("rectification", "整改完成率"), ("overdue", "逾期整改")),
    "regional_safety_manager": (("inspections", "待检查"), ("safety_risks", "安全风险"), ("rectification", "待整改"), ("overdue", "逾期整改")),
    "project_leader": (("projects", "负责项目"), ("tasks", "成员任务"), ("review", "待复核"), ("overdue", "逾期事项")),
    "ordinary_user": (("todo", "我的待办"), ("projects", "参与项目"), ("rectification", "待整改"), ("overdue", "逾期事项")),
}


@router.get("/home", response_model=ApiResponse[HomeResult])
def home(current_user: CurrentUser, db: DbSession) -> ApiResponse[HomeResult]:
    hour = datetime.now().hour
    greeting = "早上好" if hour < 12 else "下午好" if hour < 18 else "晚上好"
    unread = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.read_at.is_(None),
        )
    ) or 0
    labels = ROLE_METRIC_LABELS.get(current_user.role_code, ROLE_METRIC_LABELS["ordinary_user"])
    tones = ("blue", "orange", "green", "red")
    metrics = [
        HomeMetric(
            key=key,
            label=label,
            value=0,
            unit="%" if key == "rectification" and "率" in label else "项",
            tone=tones[index],
        )
        for index, (key, label) in enumerate(labels)
    ]
    return ApiResponse(
        data=HomeResult(
            greeting=f"{greeting}，{current_user.real_name}",
            summary=ROLE_SUMMARIES.get(current_user.role_code, ROLE_SUMMARIES["ordinary_user"]),
            user=UserView.model_validate(current_user),
            metrics=metrics,
            unread_count=unread,
        )
    )


@router.get("/workbench", response_model=ApiResponse[WorkbenchResult])
def workbench(current_user: CurrentUser) -> ApiResponse[WorkbenchResult]:
    modules = [
        WorkbenchModule(
            key=key,
            name=name,
            icon=icon,
            group=group,
            enabled=key in {"attendance", "personnel_management", "police_filing", "consumable_purchase", "safety_inspection", "emergency_drill"},
            status_text="进入" if key in {"attendance", "personnel_management", "police_filing", "consumable_purchase", "safety_inspection", "emergency_drill"} else "规划中",
        )
        for key, name, icon, group, roles in WORKBENCH_MODULES
        if current_user.role_code in roles
    ]
    return ApiResponse(data=WorkbenchResult(modules=modules))
