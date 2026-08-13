from fastapi import APIRouter

from app.dependencies import CurrentUser, DbSession
from app.schemas.common import ApiResponse
from app.schemas.user import ProfileUpdate, UserView


router = APIRouter(prefix="/profile", tags=["个人中心"])


@router.get("", response_model=ApiResponse[UserView])
def get_profile(current_user: CurrentUser) -> ApiResponse[UserView]:
    return ApiResponse(data=UserView.model_validate(current_user))


@router.patch("", response_model=ApiResponse[UserView])
def update_profile(
    payload: ProfileUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ApiResponse[UserView]:
    values = {key: value for key, value in payload.model_dump(exclude_unset=True).items() if value is not None}
    for field, value in values.items():
        setattr(current_user, field, value)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return ApiResponse(data=UserView.model_validate(current_user))
