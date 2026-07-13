from datetime import date, datetime, time, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.db.database import SessionLocal
from app.service import snapshot_service

scheduler = BackgroundScheduler()

# 接近日末触发，留足执行缓冲；业务时间戳仍锚定在当日 23:59:59
SNAPSHOT_SCHEDULE_HOUR = 23
SNAPSHOT_SCHEDULE_MINUTE = 50
SNAPSHOT_BUSINESS_END = time(23, 59, 59)


def _resolve_snapshot_business_date(now: datetime | None = None) -> date:
    """解析日快照业务日期：晚间执行为当天；凌晨 0~1 点补跑仍归属前一日。"""
    now = now or datetime.now()
    if now.time() < time(1, 0):
        return (now - timedelta(days=1)).date()
    return now.date()


def _daily_snapshot_job() -> None:
    """接近日末执行日快照，记录当日期末库存。"""
    db = SessionLocal()
    try:
        business_date = _resolve_snapshot_business_date()
        snapshot_at = datetime.combine(business_date, SNAPSHOT_BUSINESS_END)
        result = snapshot_service.create_daily_snapshot(db, snapshot_at=snapshot_at)
        logger.info(f"日库存快照完成：{result}")
    except Exception as e:
        logger.error(f"日库存快照失败：{e}")
    finally:
        db.close()


def start_scheduler() -> None:
    """启动后台定时任务。"""
    if scheduler.running:
        return
    scheduler.add_job(
        _daily_snapshot_job,
        CronTrigger(
            hour=SNAPSHOT_SCHEDULE_HOUR,
            minute=SNAPSHOT_SCHEDULE_MINUTE,
            second=0,
        ),
        id="daily_inventory_snapshot",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"定时任务调度器已启动（每日 {SNAPSHOT_SCHEDULE_HOUR:02d}:"
        f"{SNAPSHOT_SCHEDULE_MINUTE:02d} 日快照，业务日锚定 23:59:59）"
    )


def stop_scheduler() -> None:
    """关闭调度器。"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已关闭")
