from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from loguru import logger
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogCreate
from app.schemas.common import R
from app.schemas.settings import BrandingResponse, BrandingUpdate
from app.service import audit_service, settings_service
from app.utils.request_ip import get_client_ip

router = APIRouter(prefix="/settings", tags=["系统设置"])


@router.get("/branding", response_model=R[BrandingResponse], summary="获取品牌配置（公开）")
def get_branding(db: Session = Depends(get_db)):
    """登录页与侧栏使用，无需鉴权。"""
    data = settings_service.get_branding(db)
    return R.ok(data=BrandingResponse(**data))


@router.put("/branding", response_model=R[BrandingResponse], summary="更新品牌文案")
def update_branding(
    body: BrandingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """管理员更新项目名称与登录页副标题。"""
    before = settings_service.get_branding(db)
    data = settings_service.update_branding(db, body.app_name, body.app_subtitle)
    logger.info(f"品牌文案已更新：name={data['app_name']}")
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="UPDATE",
            module="settings",
            resource_type="branding",
            resource_id="branding",
            resource_name=data["app_name"],
            summary=audit_service.build_summary(current_user, "UPDATE", "品牌文案"),
            before_data=before,
            after_data=data,
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=BrandingResponse(**data), msg="品牌配置已保存")


@router.post("/branding/logo", response_model=R[BrandingResponse], summary="上传项目 Logo")
async def upload_logo(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """管理员上传 Logo（PNG/JPG/WEBP/SVG/ICO）。"""
    before = settings_service.get_branding(db)
    try:
        data = await settings_service.upload_logo(db, file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    logger.info(f"Logo 已上传：{data.get('logo_url')}")
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="UPDATE",
            module="settings",
            resource_type="branding",
            resource_id="logo",
            resource_name="logo",
            summary=audit_service.build_summary(current_user, "UPDATE", "项目 Logo"),
            before_data={"logo_url": before.get("logo_url")},
            after_data={"logo_url": data.get("logo_url")},
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=BrandingResponse(**data), msg="Logo 上传成功")


@router.delete("/branding/logo", response_model=R[BrandingResponse], summary="清除项目 Logo")
def clear_logo(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """管理员清除已上传的 Logo，前端将回退为文字标题。"""
    before = settings_service.get_branding(db)
    data = settings_service.clear_logo(db)
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="DELETE",
            module="settings",
            resource_type="branding",
            resource_id="logo",
            resource_name="logo",
            summary=audit_service.build_summary(current_user, "DELETE", "项目 Logo"),
            before_data={"logo_url": before.get("logo_url")},
            after_data={"logo_url": None},
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=BrandingResponse(**data), msg="Logo 已清除")
