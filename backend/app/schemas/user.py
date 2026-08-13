from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    real_name: str
    avatar_url: Optional[str] = None
    mobile: Optional[str] = None
    org_name: Optional[str] = None
    role_code: str
    role_name: str


class ProfileUpdate(BaseModel):
    real_name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    mobile: Optional[str] = Field(default=None, max_length=32)
