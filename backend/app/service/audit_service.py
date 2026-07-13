import json
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogCreate

# 敏感字段，序列化时脱敏
_SENSITIVE_KEYS = {"password", "old_password", "new_password", "access_token", "token"}

# 操作类型中文映射
ACTION_LABELS = {
    "LOGIN": "登录",
    "LOGOUT": "登出",
    "CREATE": "新增",
    "UPDATE": "修改",
    "DELETE": "删除",
    "SUBMIT": "提交审核",
    "APPROVE": "审核通过",
    "CANCEL": "取消",
    "TOGGLE": "切换状态",
    "EXPORT": "导出",
    "SEED": "初始化",
    "CHANGE_PASSWORD": "修改密码",
}

# 模块中文映射
MODULE_LABELS = {
    "auth": "认证",
    "user": "员工账号",
    "settings": "系统设置",
    "product": "商品SKU",
    "partner": "往来单位",
    "inbound": "入库",
    "outbound": "出库",
    "inventory": "库存",
}


def _json_default(obj):
    """JSON 序列化兜底：处理 datetime、Decimal、Enum。"""
    if isinstance(obj, datetime):
        return obj.isoformat(sep=" ", timespec="seconds")
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"不可序列化类型: {type(obj)}")


def _redact(data):
    """递归脱敏敏感字段。"""
    if isinstance(data, dict):
        return {
            k: ("***" if k in _SENSITIVE_KEYS else _redact(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_redact(item) for item in data]
    return data


def to_audit_data(obj, exclude: set[str] | None = None) -> dict | list | None:
    """
    将 ORM 对象、Pydantic 模型或普通 dict 转为可审计的 JSON 友好结构。
    自动脱敏密码等敏感字段。
    """
    if obj is None:
        return None
    exclude = exclude or set()

    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
    elif hasattr(obj, "__table__"):
        data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    elif isinstance(obj, dict):
        data = obj
    elif isinstance(obj, list):
        return [_redact(to_audit_data(item, exclude)) for item in obj]
    else:
        return obj

    for key in exclude:
        data.pop(key, None)
    return _redact(data)


def _serialize_data(data) -> str | None:
    """将审计数据序列化为 JSON 字符串。"""
    if data is None:
        return None
    if isinstance(data, str):
        return data
    return json.dumps(data, ensure_ascii=False, default=_json_default)


def operator_display(user: User | None) -> str:
    """生成操作人展示名：昵称（账号）或 系统。"""
    if not user:
        return "系统"
    name = user.nickname or user.username
    if user.nickname and user.nickname != user.username:
        return f"{user.nickname}（{user.username}）"
    return name


def record(
    db: Session,
    operator: User | None,
    data: AuditLogCreate,
) -> AuditLog:
    """
    写入一条审计日志。

    :param db: 数据库会话（与业务操作同一事务提交）
    :param operator: 当前操作人，登录等场景可为 None
    :param data: 审计内容
    """
    log = AuditLog(
        operator_id=operator.id if operator else None,
        operator_name=operator_display(operator),
        action=data.action,
        module=data.module,
        resource_type=data.resource_type,
        resource_id=str(data.resource_id) if data.resource_id is not None else None,
        resource_name=data.resource_name,
        summary=data.summary,
        before_data=_serialize_data(data.before_data),
        after_data=_serialize_data(data.after_data),
        ip_address=data.ip_address,
        created_at=datetime.now(),
    )
    db.add(log)
    db.commit()
    return log


def get_logs(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    operator_id: int | None = None,
    operator_keyword: str | None = None,
    module: str | None = None,
    action: str | None = None,
    keyword: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> tuple[int, list[AuditLog]]:
    """分页查询审计日志，支持多维度筛选。"""
    query = db.query(AuditLog)

    if operator_id:
        query = query.filter(AuditLog.operator_id == operator_id)
    if operator_keyword:
        query = query.filter(AuditLog.operator_name.like(f"%{operator_keyword}%"))
    if module:
        query = query.filter(AuditLog.module == module)
    if action:
        query = query.filter(AuditLog.action == action)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                AuditLog.summary.like(like),
                AuditLog.resource_name.like(like),
                AuditLog.resource_id.like(like),
            )
        )
    if start_time:
        query = query.filter(AuditLog.created_at >= start_time)
    if end_time:
        query = query.filter(AuditLog.created_at <= end_time)

    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, items


def build_summary(operator: User | None, action: str, target: str, detail: str = "") -> str:
    """生成中文操作摘要。"""
    action_label = ACTION_LABELS.get(action, action)
    name = operator_display(operator)
    base = f"{name} {action_label} {target}"
    return f"{base}：{detail}" if detail else base
