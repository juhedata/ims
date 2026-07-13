from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.partner import PartnerGroup, Partner
from app.models.user import User
from app.schemas.audit import AuditLogCreate
from app.schemas.common import R, PageResult
from app.schemas.partner import *
from app.service import audit_service, partner_service
from app.utils.request_ip import get_client_ip

router = APIRouter(prefix="/partners", tags=["往来单位"])


@router.get("/groups", response_model=R[list[GroupResponse]], summary="分组列表")
def list_groups(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return R.ok(data=[GroupResponse.model_validate(g) for g in partner_service.get_groups(db)])


@router.post("/groups", response_model=R[GroupResponse], status_code=201, summary="新增分组")
def create_group(
    data: GroupCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        group = partner_service.create_group(db, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="CREATE",
            module="partner",
            resource_type="partner_group",
            resource_id=str(group.id),
            resource_name=group.name,
            summary=audit_service.build_summary(current_user, "CREATE", f"往来单位分组「{group.name}」"),
            after_data=audit_service.to_audit_data(group),
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=GroupResponse.model_validate(group))


@router.put("/groups/{group_id}", response_model=R[GroupResponse], summary="修改分组")
def update_group(
    group_id: int,
    data: GroupUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.get(PartnerGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    before = audit_service.to_audit_data(group)
    try:
        group = partner_service.update_group(db, group, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="UPDATE",
            module="partner",
            resource_type="partner_group",
            resource_id=str(group.id),
            resource_name=group.name,
            summary=audit_service.build_summary(current_user, "UPDATE", f"往来单位分组「{group.name}」"),
            before_data=before,
            after_data=audit_service.to_audit_data(group),
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=GroupResponse.model_validate(group))


@router.delete("/groups/{group_id}", response_model=R, summary="删除分组")
def delete_group(
    group_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.get(PartnerGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    before = audit_service.to_audit_data(group)
    name = group.name
    try:
        partner_service.delete_group(db, group)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="DELETE",
            module="partner",
            resource_type="partner_group",
            resource_id=str(group_id),
            resource_name=name,
            summary=audit_service.build_summary(current_user, "DELETE", f"往来单位分组「{name}」"),
            before_data=before,
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(msg="删除成功")


@router.get("", response_model=R[PageResult[PartnerResponse]], summary="往来单位列表")
def list_partners(
    page: int = 1, page_size: int = 20, group_id: int | None = None,
    partner_type: int | None = None, keyword: str | None = None,
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    total, items = partner_service.get_partners(db, page, page_size, group_id, partner_type, keyword)
    return R.ok(data=PageResult(total=total, page=page, page_size=page_size,
                                items=[PartnerResponse.model_validate(p) for p in items]))


@router.post("", response_model=R[PartnerResponse], status_code=201, summary="新增往来单位")
def create_partner(
    data: PartnerCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    partner = partner_service.create_partner(db, data)
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="CREATE",
            module="partner",
            resource_type="partner",
            resource_id=str(partner.id),
            resource_name=partner.name,
            summary=audit_service.build_summary(current_user, "CREATE", f"往来单位「{partner.name}」"),
            after_data=audit_service.to_audit_data(partner),
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=PartnerResponse.model_validate(partner))


@router.get("/{partner_id}", response_model=R[PartnerResponse], summary="单位详情")
def get_partner(partner_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    partner = partner_service.get_partner_by_id(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="单位不存在")
    return R.ok(data=PartnerResponse.model_validate(partner))


@router.put("/{partner_id}", response_model=R[PartnerResponse], summary="修改单位")
def update_partner(
    partner_id: int,
    data: PartnerUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    partner = partner_service.get_partner_by_id(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="单位不存在")
    before = audit_service.to_audit_data(partner)
    partner = partner_service.update_partner(db, partner, data)
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="UPDATE",
            module="partner",
            resource_type="partner",
            resource_id=str(partner.id),
            resource_name=partner.name,
            summary=audit_service.build_summary(current_user, "UPDATE", f"往来单位「{partner.name}」"),
            before_data=before,
            after_data=audit_service.to_audit_data(partner),
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(data=PartnerResponse.model_validate(partner))


@router.delete("/{partner_id}", response_model=R, summary="删除单位")
def delete_partner(
    partner_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    partner = partner_service.get_partner_by_id(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="单位不存在")
    before = audit_service.to_audit_data(partner)
    name = partner.name
    partner_service.delete_partner(db, partner)
    audit_service.record(
        db,
        current_user,
        AuditLogCreate(
            action="DELETE",
            module="partner",
            resource_type="partner",
            resource_id=str(partner_id),
            resource_name=name,
            summary=audit_service.build_summary(current_user, "DELETE", f"往来单位「{name}」"),
            before_data=before,
            ip_address=get_client_ip(request),
        ),
    )
    return R.ok(msg="删除成功")
