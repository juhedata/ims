from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """根据主键查询用户，不存在返回 None。"""
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    """根据用户名查询用户，不存在返回 None。"""
    return db.query(User).filter(User.username == username).first()


def get_users(db: Session, page: int = 1, page_size: int = 20) -> tuple[int, list[User]]:
    """
    分页查询用户列表。

    :param db: 数据库会话
    :param page: 页码（从 1 开始）
    :param page_size: 每页条数
    :return: (总记录数, 当前页数据列表)
    """
    query = db.query(User)
    total = query.count()
    items = query.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    创建新用户，密码自动哈希后存储。

    :raises ValueError: 用户名已存在
    """
    if get_user_by_username(db, user_in.username):
        raise ValueError(f"用户名已存在：{user_in.username}")

    user = User(
        username=user_in.username,
        password=hash_password(user_in.password),
        nickname=user_in.nickname,
        email=user_in.email,
        phone=user_in.phone,
        remark=user_in.remark,
        role=user_in.role.value,
        status=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    """
    更新用户信息（仅更新非 None 字段）。

    :param db: 数据库会话
    :param user: 已查询到的用户 ORM 对象
    :param user_in: 更新请求体
    """
    update_data = user_in.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value.value if hasattr(value, "value") else value)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
    """
    修改密码：先验证旧密码，再写入新密码哈希。

    :return: True=修改成功，False=旧密码错误
    """
    if not verify_password(old_password, user.password):
        return False
    user.password = hash_password(new_password)
    db.commit()
    return True


def toggle_user_status(db: Session, user: User) -> User:
    """
    切换用户状态：1（正常）↔ 0（禁用）。

    :return: 更新后的用户对象
    """
    user.status = 0 if user.status == 1 else 1
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """
    删除用户（物理删除）。
    生产环境建议改为软删除（is_deleted 标志位）。
    """
    db.delete(user)
    db.commit()
