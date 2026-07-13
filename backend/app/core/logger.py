import sys
from pathlib import Path
from loguru import logger

# 日志目录：backend/logs/
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger(log_level: str = "INFO") -> None:
    """
    初始化 loguru 日志配置。

    策略：
    - 控制台：彩色输出，级别跟随 log_level 配置
    - 文件（info 及以上）：按天切割 + 100 MB 单文件上限，保留 60 天
    - 文件（error 及以上）：独立 error 日志，便于报警监控
    """
    # 移除默认 handler，避免重复输出
    logger.remove()

    # ── 控制台 handler ──────────────────────────────────────────────
    logger.add(
        sys.stdout,
        level=log_level.upper(),
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        enqueue=True,   # 异步写入，不阻塞主线程
    )

    # ── 综合日志文件 handler（INFO+）────────────────────────────────
    logger.add(
        LOG_DIR / "app_{time:YYYY-MM-DD}.log",
        level=log_level.upper(),
        rotation="100 MB",      # 单文件超过 100 MB 立即切割
        retention="60 days",    # 保留最近 60 天的日志文件
        compression="zip",      # 旧日志压缩，节省磁盘
        encoding="utf-8",
        enqueue=True,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{line} - {message}"
        ),
    )

    # ── 错误日志文件 handler（ERROR+）───────────────────────────────
    logger.add(
        LOG_DIR / "error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation="00:00",       # 每天零点切割
        retention="60 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,         # 记录完整堆栈
        diagnose=True,          # 记录变量值，便于排查
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{line} - {message}"
        ),
    )

    logger.info(f"日志系统初始化完成，日志目录：{LOG_DIR}，级别：{log_level.upper()}")
