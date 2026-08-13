from typing import List, Union

from pydantic import BaseModel

from app.schemas.user import UserView


class HomeMetric(BaseModel):
    key: str
    label: str
    value: Union[int, float]
    unit: str = ""
    tone: str = "blue"


class HomeResult(BaseModel):
    greeting: str
    summary: str
    user: UserView
    metrics: List[HomeMetric]
    unread_count: int


class WorkbenchModule(BaseModel):
    key: str
    name: str
    icon: str
    group: str
    enabled: bool = False
    status_text: str = "规划中"


class WorkbenchResult(BaseModel):
    modules: List[WorkbenchModule]
