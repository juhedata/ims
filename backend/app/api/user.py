from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogCreate
from app.schemas.common import R, PageResult
from app.schemas.user import UserCreate, UserUpdate, UserResponse, ChangePasswordRequest
from app.service import audit_service, user_service
from app.utils.request_ip import get_client_ip

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=R[PageResult[UserResponse]], summary="用户列表（分页）")
def list_users(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """分页获取用户列表，需要登录。"""
    total, items = user_service.get_users(db, page=page, page_size=page_size)
    return R.ok(
        data=PageResult(
            total=total,
            page=page,
            page_size=page_size,
            items=[UserResponse.model_validate(u) for u in items],
        )
    )


@router.post("", response_model=R[UserResponse], status_code=status.HTTP_201_CREATED, summary="创建用户")
def create_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """创建新用户，需要登录。用户名不可重复。"""
    try:
        user = user_service.create_user(db, user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    logger.info(f"新用户创建成功：{user.username} (id={user.id})")
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="CREATE",
            module="user",
            resource_type="user",
            resource_id=str(user.id),
            resource_name=user.username,
            summary=audit_service.build_summary(current_user, "CREATE", f"员工账号「{user.username}」"),
            after_data=audit_service.to_audit_data(UserResponse.model_validate(user)),
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=UserResponse.model_validate(user), msg="用户创建成功")


@router.get("/{user_id}", response_model=R[UserResponse], summary="用户详情")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """根据 ID 获取用户详情，需要登录。"""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return R.ok(data=UserResponse.model_validate(user))


@router.put("/{user_id}", response_model=R[UserResponse], summary="更新用户信息")
def update_user(
    user_id: int,
    user_in: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """更新用户基本信息，需要登录。"""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    before = audit_service.to_audit_data(UserResponse.model_validate(user))
    user = user_service.update_user(db, user, user_in)
    logger.info(f"用户信息更新：id={user_id}")
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="UPDATE",
            module="user",
            resource_type="user",
            resource_id=str(user.id),
            resource_name=user.username,
            summary=audit_service.build_summary(current_user, "UPDATE", f"员工账号「{user.username}」"),
            before_data=before,
            after_data=audit_service.to_audit_data(UserResponse.model_validate(user)),
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=UserResponse.model_validate(user), msg="更新成功")


@router.post("/change-password", response_model=R, summary="修改当前用户密码")
def change_password(
    req: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改当前登录用户的密码，需要提供旧密码验证。"""
    success = user_service.change_password(db, current_user, req.old_password, req.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误")
    logger.info(f"用户修改密码：{current_user.username}")
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="CHANGE_PASSWORD",
            module="user",
            resource_type="user",
            resource_id=str(current_user.id),
            resource_name=current_user.username,
            summary=audit_service.build_summary(current_user, "CHANGE_PASSWORD", "自己的登录密码"),
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(msg="密码修改成功")


@router.patch("/{user_id}/status", response_model=R[UserResponse], summary="启用/禁用用户")
def toggle_status(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """切换用户状态（启用↔禁用），需要登录。"""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    before_status = user.status
    user = user_service.toggle_user_status(db, user)
    action = "启用" if user.status == 1 else "禁用"
    logger.info(f"用户状态变更：id={user_id}，操作={action}")
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="TOGGLE",
            module="user",
            resource_type="user",
            resource_id=str(user.id),
            resource_name=user.username,
            summary=audit_service.build_summary(
                current_user, "TOGGLE", f"员工账号「{user.username}」", f"状态 {before_status} → {user.status}"
            ),
            before_data={"status": before_status},
            after_data={"status": user.status},
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=UserResponse.model_validate(user), msg=f"已{action}")


@router.delete("/{user_id}", response_model=R, summary="删除用户")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """删除指定用户（物理删除），需要管理员权限。不可删除自身。"""
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不可删除当前登录账号")
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    before = audit_service.to_audit_data(UserResponse.model_validate(user))
    username = user.username
    user_service.delete_user(db, user)
    logger.info(f"用户已删除：id={user_id}")
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="DELETE",
            module="user",
            resource_type="user",
            resource_id=str(user_id),
            resource_name=username,
            summary=audit_service.build_summary(current_user, "DELETE", f"员工账号「{username}」"),
            before_data=before,
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(msg="删除成功")
