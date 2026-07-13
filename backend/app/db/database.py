from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# 创建数据库引擎
# pool_pre_ping=True：每次获取连接前发送 SELECT 1，防止使用已断开的连接
# pool_recycle=3600：连接池中的连接超过 1 小时后回收，避免 MySQL wait_timeout 问题
# pool_size=10：连接池大小；max_overflow=20：超出 pool_size 时最多额外创建 20 个连接
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,    # DEBUG 模式下打印 SQL 语句
)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 依赖项：提供数据库 Session，请求结束后自动关闭。

    用法：
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    检测数据库连接是否正常，用于启动健康检查。

    :return: 连接成功返回 True，否则返回 False
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
