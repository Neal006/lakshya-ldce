from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Profile, RoleEnum
from app.middleware.auth import get_current_user, require_roles
from app.middleware.exceptions import AppException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone

router = APIRouter()


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserProfileResponse]
    total: int
    page: int
    limit: int


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


class DataWrapperUserList(BaseModel):
    data: dict


class DataWrapperUser(BaseModel):
    data: dict


@router.get("", response_model=DataWrapperUserList)
def list_users(
    page: int = 1,
    limit: int = 20,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(require_roles("admin")),
):
    from math import ceil

    query = db.query(Profile)

    if role:
        try:
            role_enum = RoleEnum(role)
            query = query.filter(Profile.role == role_enum)
        except ValueError:
            raise AppException(status_code=400, code="VALIDATION_ERROR", message=f"Invalid role: {role}")

    total = query.count()
    total_pages = ceil(total / limit) if total > 0 else 1
    users = query.order_by(Profile.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    user_list = [
        UserProfileResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role.value,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]

    return {
        "data": UserListResponse(
            users=user_list,
            total=total,
            page=page,
            limit=limit,
        ).model_dump(mode="json")
    }


@router.get("/{user_id}", response_model=DataWrapperUser)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(require_roles("admin")),
):
    user = db.query(Profile).filter(Profile.id == user_id).first()
    if not user:
        raise AppException(status_code=404, code="NOT_FOUND", message="User not found")

    return {
        "data": UserProfileResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
        ).model_dump(mode="json")
    }


@router.patch("/{user_id}", response_model=DataWrapperUser)
def update_user(
    user_id: str,
    request: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(require_roles("admin")),
):
    user = db.query(Profile).filter(Profile.id == user_id).first()
    if not user:
        raise AppException(status_code=404, code="NOT_FOUND", message="User not found")

    if not any([request.name, request.role is not None, request.is_active is not None]):
        raise AppException(status_code=400, code="VALIDATION_ERROR", message="No fields to update")

    if current_user.id == user_id and request.is_active is False:
        raise AppException(status_code=400, code="VALIDATION_ERROR", message="Cannot deactivate your own account")

    if request.name:
        user.name = request.name
    if request.role is not None:
        user.role = request.role
    if request.is_active is not None:
        user.is_active = request.is_active

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return {
        "data": UserProfileResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
        ).model_dump(mode="json")
    }


@router.delete("/{user_id}")
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(require_roles("admin")),
):
    user = db.query(Profile).filter(Profile.id == user_id).first()
    if not user:
        raise AppException(status_code=404, code="NOT_FOUND", message="User not found")

    if current_user.id == user_id:
        raise AppException(status_code=400, code="VALIDATION_ERROR", message="Cannot deactivate your own account")

    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"data": {"message": "User deactivated successfully", "user_id": user_id}}