from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Profile, RoleEnum
from app.schemas.auth import (
    RegisterRequest, LoginRequest, RefreshRequest,
    UserResponse, AuthResponse, RefreshResponse,
    DataWrapper, DataWrapperRefresh, DataWrapperLogout,
)
from app.services.auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, verify_refresh_token, revoke_refresh_token,
)
from app.middleware.auth import get_current_user
from app.middleware.exceptions import AppException

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=DataWrapper)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Profile).filter(Profile.email == request.email).first()
    if existing:
        raise AppException(
            status_code=409,
            code="EMAIL_TAKEN",
            message="Email already registered",
        )

    user = Profile(
        email=request.email,
        name=request.name,
        role=request.role,
        hashed_password=hash_password(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id), user.role.value)

    return DataWrapper(data=AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            created_at=user.created_at,
        ),
        access_token=access_token,
        refresh_token=refresh_token,
    ))


@router.post("/login", response_model=DataWrapper)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Profile).filter(Profile.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise AppException(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
        )
    if not user.is_active:
        raise AppException(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="Account is deactivated",
        )

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id), user.role.value)

    return DataWrapper(data=AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            created_at=user.created_at,
        ),
        access_token=access_token,
        refresh_token=refresh_token,
    ))


@router.post("/refresh", response_model=DataWrapperRefresh)
async def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    payload = verify_refresh_token(request.refresh_token)
    user_id = payload.get("sub")

    user = db.query(Profile).filter(Profile.id == user_id).first()
    if not user or not user.is_active:
        revoke_refresh_token(request.refresh_token)
        raise AppException(
            status_code=401,
            code="INVALID_TOKEN",
            message="Refresh token is invalid or expired",
        )

    revoke_refresh_token(request.refresh_token)
    access_token = create_access_token(str(user.id), user.role.value)
    new_refresh_token = create_refresh_token(str(user.id), user.role.value)

    return DataWrapperRefresh(data=RefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    ))


@router.post("/logout", response_model=DataWrapperLogout)
async def logout(
    request: RefreshRequest | None = None,
    current_user: Profile = Depends(get_current_user),
):
    if request and request.refresh_token:
        revoke_refresh_token(request.refresh_token)
    return DataWrapperLogout(data={"message": "Logged out successfully"})