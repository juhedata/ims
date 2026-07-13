from sqlalchemy.orm import Session

from app.models.customer import Customer


def get_customers(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
) -> tuple[int, list[Customer]]:
    query = db.query(Customer)
    if keyword and keyword.strip():
        query = query.filter(Customer.name.like(f"%{keyword.strip()}%"))
    total = query.count()
    items = (
        query.order_by(Customer.weight.desc(), Customer.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, items


def increment_weight(db: Session, name: str) -> None:
    """出库提交时提升客户权重。"""
    customer = get_or_create(db, name)
    customer.weight += 1


def get_or_create(db: Session, name: str) -> Customer:
    """按名称查找客户，不存在则新建。"""
    normalized = name.strip()
    if not normalized:
        raise ValueError("客户名称不能为空")
    existing = db.query(Customer).filter(Customer.name == normalized).first()
    if existing:
        return existing
    customer = Customer(name=normalized)
    db.add(customer)
    db.flush()
    return customer
