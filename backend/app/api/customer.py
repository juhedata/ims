from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import R, PageResult
from app.schemas.customer import CustomerResponse
from app.service import customer_service

router = APIRouter(prefix="/customers", tags=["客户"])


@router.get("", response_model=R[PageResult[CustomerResponse]], summary="客户列表")
def list_customers(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total, items = customer_service.get_customers(db, page, page_size, keyword)
    return R.ok(
        data=PageResult(
            total=total,
            page=page,
            page_size=page_size,
            items=[CustomerResponse.model_validate(c) for c in items],
        )
    )
