from datetime import datetime

from sqlalchemy.orm import Session

from app.models.sequence import SequenceCounter


def _next_seq(db: Session, seq_type: str) -> int:
    """获取并递增当日序列号（事务内调用）。"""
    today = datetime.now().strftime("%Y%m%d")
    counter = (
        db.query(SequenceCounter)
        .filter(SequenceCounter.seq_type == seq_type, SequenceCounter.seq_date == today)
        .with_for_update()
        .first()
    )
    if counter is None:
        counter = SequenceCounter(seq_type=seq_type, seq_date=today, current_value=0)
        db.add(counter)
        db.flush()
    counter.current_value += 1
    db.flush()
    return counter.current_value


def generate_inbound_no(db: Session) -> str:
    """生成入库单号：JIN-{YYYYMMDD}-{序号4位}。"""
    seq = _next_seq(db, "JIN")
    today = datetime.now().strftime("%Y%m%d")
    return f"JIN-{today}-{seq:04d}"


def generate_outbound_no(db: Session) -> str:
    """生成出库单号：JOUT-{YYYYMMDD}-{序号4位}。"""
    seq = _next_seq(db, "JOUT")
    today = datetime.now().strftime("%Y%m%d")
    return f"JOUT-{today}-{seq:04d}"
