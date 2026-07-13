from sqlalchemy.orm import Session

from app.models.product import ProductCategory, ProductSku
from app.schemas.product import CategoryCreate, CategoryUpdate, SkuCreate, SkuUpdate


def get_categories(db: Session) -> list[ProductCategory]:
    return db.query(ProductCategory).order_by(ProductCategory.id).all()


def create_category(db: Session, data: CategoryCreate) -> ProductCategory:
    if db.query(ProductCategory).filter(ProductCategory.name == data.name).first():
        raise ValueError(f"分类名称已存在：{data.name}")
    cat = ProductCategory(name=data.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update_category(db: Session, cat: ProductCategory, data: CategoryUpdate) -> ProductCategory:
    if data.name and data.name != cat.name:
        if db.query(ProductCategory).filter(ProductCategory.name == data.name).first():
            raise ValueError(f"分类名称已存在：{data.name}")
        cat.name = data.name
    db.commit()
    db.refresh(cat)
    return cat


def delete_category(db: Session, cat: ProductCategory) -> None:
    if db.query(ProductSku).filter(ProductSku.category_id == cat.id).first():
        raise ValueError("分类下存在商品，无法删除")
    db.delete(cat)
    db.commit()


def get_skus(db: Session, page: int = 1, page_size: int = 20, category_id: int | None = None, keyword: str | None = None):
    query = db.query(ProductSku)
    if category_id:
        query = query.filter(ProductSku.category_id == category_id)
    if keyword:
        query = query.filter(ProductSku.name.like(f"%{keyword}%") | ProductSku.barcode.like(f"%{keyword}%"))
    total = query.count()
    items = query.order_by(ProductSku.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def get_sku_by_id(db: Session, sku_id: int) -> ProductSku | None:
    return db.get(ProductSku, sku_id)


def create_sku(db: Session, data: SkuCreate) -> ProductSku:
    if db.query(ProductSku).filter(ProductSku.barcode == data.barcode).first():
        raise ValueError(f"条码已存在：{data.barcode}")
    sku = ProductSku(**data.model_dump())
    db.add(sku)
    db.commit()
    db.refresh(sku)
    return sku


def update_sku(db: Session, sku: ProductSku, data: SkuUpdate) -> ProductSku:
    update_data = data.model_dump(exclude_none=True)
    if "barcode" in update_data and update_data["barcode"] != sku.barcode:
        if db.query(ProductSku).filter(ProductSku.barcode == update_data["barcode"]).first():
            raise ValueError(f"条码已存在：{update_data['barcode']}")
    for k, v in update_data.items():
        setattr(sku, k, v)
    db.commit()
    db.refresh(sku)
    return sku


def delete_sku(db: Session, sku: ProductSku) -> None:
    from app.models.inventory import InventoryItem
    if db.query(InventoryItem).filter(InventoryItem.sku_id == sku.id).first():
        raise ValueError("该 SKU 已有库存记录，无法删除")
    db.delete(sku)
    db.commit()
