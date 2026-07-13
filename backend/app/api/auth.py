from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import verify_password, create_access_token
from app.db.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogCreate
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import R
from app.schemas.user import UserResponse
from app.service import audit_service
from app.utils.request_ip import get_client_ip

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=R[TokenResponse], summary="用户登录")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    用户名 + 密码登录，登录成功返回 JWT Access Token。

    错误码：
    - 401：用户名不存在或密码错误
    - 403：账号已被禁用
    """
    user: User | None = db.query(User).filter(User.username == req.username).first()

    if not user:
        logger.warning(f"登录失败：用户名不存在 [{req.username}]")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not verify_password(req.password, user.password):
        logger.warning(f"登录失败：密码错误 [{req.username}]")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if user.status != 1:
        logger.warning(f"登录失败：账号已禁用 [{req.username}]")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员",
        )

    token = create_access_token({"user_id": user.id, "username": user.username})
    logger.info(f"用户登录成功 [{req.username}]")
    audit_service.record(
        db,
        user,
        AuditLogCreate(
            action="LOGIN",
            module="auth",
            resource_type="user",
            resource_id=str(user.id),
            resource_name=user.username,
            summary=audit_service.build_summary(user, "LOGIN", "系统"),
            ip_address=get_client_ip(request),
        ),
    )

    return R.ok(
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        )
    )


@router.get("/me", response_model=R[UserResponse], summary="获取当前登录用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    """
    返回当前 Token 对应的用户信息（不含密码）。
    需要在请求头携带：Authorization: Bearer <token>
    """
    return R.ok(data=UserResponse.model_validate(current_user))
