from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 应用基础（Swagger / 健康检查用；前端展示名以 sys_config 为准）
    APP_NAME: str = "IMS"
    DEBUG: bool = False
    PORT: int = 8000

    # MySQL 数据库
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DB: str

    # JWT 鉴权
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 默认 24 小时

    # Alembic 自动迁移（开发环境可开启）
    AUTO_MIGRATE: bool = False

    # 日志级别
    LOG_LEVEL: str = "INFO"

    # 上传文件目录（Logo 等），相对路径基于进程工作目录
    UPLOAD_DIR: str = "uploads"
    UPLOAD_URL_PREFIX: str = "/uploads"
    MAX_LOGO_SIZE: int = 2 * 1024 * 1024  # 2MB

    # 跨域白名单，.env 中用逗号分隔，此处自动解析为列表
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """将逗号分隔的 CORS_ORIGINS 字符串解析为列表。"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def database_url(self) -> str:
        """拼接 SQLAlchemy 连接字符串。"""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
            f"?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# 全局单例，其他模块统一从此导入
settings = Settings()
