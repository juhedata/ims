from sqlalchemy.orm import Session

from app.models.partner import Partner, PartnerGroup
from app.schemas.partner import GroupCreate, GroupUpdate, PartnerCreate, PartnerUpdate


def get_groups(db: Session) -> list[PartnerGroup]:
    return db.query(PartnerGroup).order_by(PartnerGroup.id).all()


def create_group(db: Session, data: GroupCreate) -> PartnerGroup:
    if db.query(PartnerGroup).filter(PartnerGroup.name == data.name).first():
        raise ValueError(f"分组名称已存在：{data.name}")
    group = PartnerGroup(name=data.name)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def update_group(db: Session, group: PartnerGroup, data: GroupUpdate) -> PartnerGroup:
    if data.name and data.name != group.name:
        if db.query(PartnerGroup).filter(PartnerGroup.name == data.name).first():
            raise ValueError(f"分组名称已存在：{data.name}")
        group.name = data.name
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, group: PartnerGroup) -> None:
    if db.query(Partner).filter(Partner.group_id == group.id).first():
        raise ValueError("分组下存在往来单位，无法删除")
    db.delete(group)
    db.commit()


def get_partners(db: Session, page: int = 1, page_size: int = 20, group_id: int | None = None, partner_type: int | None = None, keyword: str | None = None):
    query = db.query(Partner)
    if group_id:
        query = query.filter(Partner.group_id == group_id)
    if partner_type is not None:
        query = query.filter(Partner.partner_type == partner_type)
    if keyword:
        query = query.filter(Partner.name.like(f"%{keyword}%"))
    total = query.count()
    items = query.order_by(Partner.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def get_partner_by_id(db: Session, partner_id: int) -> Partner | None:
    return db.get(Partner, partner_id)


def validate_partner(db: Session, partner_id: int | None) -> Partner:
    """校验关联往来单位是否存在且已启用（不限制单位类型）。"""
    if partner_id is None:
        raise ValueError("请选择关联单位")
    partner = db.get(Partner, partner_id)
    if not partner:
        raise ValueError(f"往来单位不存在：{partner_id}")
    if partner.status != 1:
        raise ValueError(f"往来单位 [{partner.name}] 已停用")
    return partner


def create_partner(db: Session, data: PartnerCreate) -> Partner:
    partner = Partner(**data.model_dump())
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def update_partner(db: Session, partner: Partner, data: PartnerUpdate) -> Partner:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(partner, k, v)
    db.commit()
    db.refresh(partner)
    return partner


def delete_partner(db: Session, partner: Partner) -> None:
    db.delete(partner)
    db.commit()
