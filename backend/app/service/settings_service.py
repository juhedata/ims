import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.system_config import SystemConfig

KEY_APP_NAME = "app_name"
KEY_APP_SUBTITLE = "app_subtitle"
KEY_LOGO_PATH = "logo_path"

DEFAULT_APP_NAME = "IMS"
DEFAULT_APP_SUBTITLE = "一物一码库存管理系统"

ALLOWED_LOGO_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
}


def _get_value(db: Session, key: str) -> str | None:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row is None or row.value is None:
        return None
    value = row.value.strip()
    return value or None


def _set_value(db: Session, key: str, value: str | None) -> None:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row is None:
        row = SystemConfig(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    db.flush()


def _logo_url(logo_path: str | None) -> str | None:
    if not logo_path:
        return None
    return f"{settings.UPLOAD_URL_PREFIX}/{logo_path.lstrip('/')}"


def get_branding(db: Session) -> dict:
    """读取品牌配置，缺失时回退到默认值。"""
    app_name = _get_value(db, KEY_APP_NAME) or DEFAULT_APP_NAME
    app_subtitle = _get_value(db, KEY_APP_SUBTITLE) or DEFAULT_APP_SUBTITLE
    logo_path = _get_value(db, KEY_LOGO_PATH)
    return {
        "app_name": app_name,
        "app_subtitle": app_subtitle,
        "logo_url": _logo_url(logo_path),
    }


def update_branding(db: Session, app_name: str, app_subtitle: str) -> dict:
    """更新项目名称与副标题。"""
    _set_value(db, KEY_APP_NAME, app_name.strip())
    _set_value(db, KEY_APP_SUBTITLE, app_subtitle.strip())
    db.commit()
    return get_branding(db)


def _ensure_branding_dir() -> Path:
    directory = Path(settings.UPLOAD_DIR) / "branding"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _delete_logo_file(logo_path: str | None) -> None:
    if not logo_path:
        return
    file_path = Path(settings.UPLOAD_DIR) / logo_path
    if file_path.is_file():
        file_path.unlink()


async def upload_logo(db: Session, file: UploadFile) -> dict:
    """上传 Logo，替换旧文件。"""
    content_type = (file.content_type or "").lower()
    ext = ALLOWED_LOGO_CONTENT_TYPES.get(content_type)
    if not ext:
        raise ValueError("仅支持 PNG / JPG / WEBP / SVG / ICO 格式的 Logo")

    data = await file.read()
    if not data:
        raise ValueError("上传文件为空")
    if len(data) > settings.MAX_LOGO_SIZE:
        raise ValueError(f"Logo 大小不能超过 {settings.MAX_LOGO_SIZE // (1024 * 1024)}MB")

    old_path = _get_value(db, KEY_LOGO_PATH)
    branding_dir = _ensure_branding_dir()
    filename = f"logo-{uuid.uuid4().hex[:8]}{ext}"
    relative_path = f"branding/{filename}"
    target = branding_dir / filename
    target.write_bytes(data)

    _set_value(db, KEY_LOGO_PATH, relative_path)
    db.commit()
    _delete_logo_file(old_path)
    return get_branding(db)


def clear_logo(db: Session) -> dict:
    """清除已上传的 Logo。"""
    old_path = _get_value(db, KEY_LOGO_PATH)
    _set_value(db, KEY_LOGO_PATH, None)
    db.commit()
    _delete_logo_file(old_path)
    return get_branding(db)
