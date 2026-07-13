import enum


class StockStatus(str, enum.Enum):
    """库存状态（单品维度）。"""
    IN_STOCK = "IN_STOCK"
    SOLD = "SOLD"
    BORROWED = "BORROWED"
    GIFTED = "GIFTED"
    SCRAPPED = "SCRAPPED"
    RND = "RND"           # 研发出库
    SAMPLE = "SAMPLE"     # 样机出库
    TRIAL = "TRIAL"       # 试用出库
    REPAIR = "REPAIR"     # 维修出库
    DEPT_PROCUREMENT = "DEPT_PROCUREMENT"  # 部门采购出库
    PRESOLD = "PRESOLD"               # 准售出
    SOLD_OFFLINE = "SOLD_OFFLINE"     # 售出-线下（已完成）


class StockCondition(str, enum.Enum):
    """库存属性（在库时的成色/来源）。"""
    NEW = "NEW"
    RETURNED_FROM_SALE = "RETURNED_FROM_SALE"
    RETURNED_FROM_SOLD_OFFLINE = "RETURNED_FROM_SOLD_OFFLINE"
    RETURNED_FROM_PRESOLD = "RETURNED_FROM_PRESOLD"
    RETURNED_FROM_BORROW = "RETURNED_FROM_BORROW"
    RETURNED_FROM_GIFT = "RETURNED_FROM_GIFT"
    RETURNED_FROM_SCRAPPED = "RETURNED_FROM_SCRAPPED"
    RETURNED_FROM_RND = "RETURNED_FROM_RND"
    RETURNED_FROM_SAMPLE = "RETURNED_FROM_SAMPLE"
    RETURNED_FROM_TRIAL = "RETURNED_FROM_TRIAL"
    RETURNED_FROM_REPAIR = "RETURNED_FROM_REPAIR"
    RETURNED_FROM_DEPT_PROCUREMENT = "RETURNED_FROM_DEPT_PROCUREMENT"


class OperationStatus(str, enum.Enum):
    """操作状态（单据 + 单品）。"""
    INITIATED = "INITIATED"
    PICKING = "PICKING"
    CHECKING = "CHECKING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class OutboundType(str, enum.Enum):
    """出库类型（顺序见 OUTBOUND_TYPE_ORDER）。"""
    SOLD = "SOLD"                     # 售出-线上
    SOLD_OFFLINE = "SOLD_OFFLINE"     # 售出-线下
    PRESOLD = "PRESOLD"               # 准售出
    GIFTED = "GIFTED"
    SCRAPPED = "SCRAPPED"
    RND = "RND"
    SAMPLE = "SAMPLE"
    TRIAL = "TRIAL"
    REPAIR = "REPAIR"
    DEPT_PROCUREMENT = "DEPT_PROCUREMENT"  # 部门采购
    BORROWED = "BORROWED"


OUTBOUND_TYPE_ORDER = [
    OutboundType.SOLD,
    OutboundType.SOLD_OFFLINE,
    OutboundType.PRESOLD,
    OutboundType.GIFTED,
    OutboundType.SCRAPPED,
    OutboundType.RND,
    OutboundType.SAMPLE,
    OutboundType.TRIAL,
    OutboundType.REPAIR,
    OutboundType.DEPT_PROCUREMENT,
]

RETURN_CONDITION_ORDER = [
    StockCondition.RETURNED_FROM_SALE,
    StockCondition.RETURNED_FROM_SOLD_OFFLINE,
    StockCondition.RETURNED_FROM_PRESOLD,
    StockCondition.RETURNED_FROM_GIFT,
    StockCondition.RETURNED_FROM_SCRAPPED,
    StockCondition.RETURNED_FROM_RND,
    StockCondition.RETURNED_FROM_SAMPLE,
    StockCondition.RETURNED_FROM_TRIAL,
    StockCondition.RETURNED_FROM_REPAIR,
    StockCondition.RETURNED_FROM_DEPT_PROCUREMENT,
]


class InboundMode(str, enum.Enum):
    """入库方式。"""
    PROCUREMENT = "PROCUREMENT"
    NON_PROCUREMENT = "NON_PROCUREMENT"


class SnSource(str, enum.Enum):
    """SN 来源。"""
    MANUAL = "MANUAL"
    AUTO = "AUTO"


class PartnerType(int, enum.Enum):
    """往来单位类型。"""
    BOTH = 0       # 供应商 & 客户
    CUSTOMER = 1   # 客户
    SUPPLIER = 2   # 供应商


class SnMode(str, enum.Enum):
    """SKU 的 SN 录入模式。"""
    MANUAL = "MANUAL"
    AUTO = "AUTO"
    BOTH = "BOTH"


class UserRole(str, enum.Enum):
    """系统用户角色。"""
    ADMIN = "ADMIN"   # 管理员
    STAFF = "STAFF"   # 普通员工


# 出库类型 → 审核后单品库存状态
OUTBOUND_TO_STOCK_STATUS = {
    OutboundType.SOLD: StockStatus.SOLD,
    OutboundType.SOLD_OFFLINE: StockStatus.SOLD_OFFLINE,
    OutboundType.PRESOLD: StockStatus.PRESOLD,
    OutboundType.GIFTED: StockStatus.GIFTED,
    OutboundType.SCRAPPED: StockStatus.SCRAPPED,
    OutboundType.RND: StockStatus.RND,
    OutboundType.SAMPLE: StockStatus.SAMPLE,
    OutboundType.TRIAL: StockStatus.TRIAL,
    OutboundType.REPAIR: StockStatus.REPAIR,
    OutboundType.DEPT_PROCUREMENT: StockStatus.DEPT_PROCUREMENT,
    OutboundType.BORROWED: StockStatus.BORROWED,
}

# 历史出库类型 code 兼容
OUTBOUND_TYPE_ALIASES: dict[str, OutboundType] = {
    "OFFLINE_SOLD": OutboundType.SOLD_OFFLINE,
}


def parse_outbound_type(code: str) -> OutboundType:
    """解析出库类型 code，兼容历史别名。"""
    if code in OUTBOUND_TYPE_ALIASES:
        return OUTBOUND_TYPE_ALIASES[code]
    return OutboundType(code)


# 非采购入库类型 → 默认关联的出库类型
RETURN_CONDITION_TO_OUTBOUND = {
    StockCondition.RETURNED_FROM_SALE: OutboundType.SOLD,
    StockCondition.RETURNED_FROM_SOLD_OFFLINE: OutboundType.SOLD_OFFLINE,
    StockCondition.RETURNED_FROM_PRESOLD: OutboundType.PRESOLD,
    StockCondition.RETURNED_FROM_BORROW: OutboundType.BORROWED,
    StockCondition.RETURNED_FROM_GIFT: OutboundType.GIFTED,
    StockCondition.RETURNED_FROM_SCRAPPED: OutboundType.SCRAPPED,
    StockCondition.RETURNED_FROM_RND: OutboundType.RND,
    StockCondition.RETURNED_FROM_SAMPLE: OutboundType.SAMPLE,
    StockCondition.RETURNED_FROM_TRIAL: OutboundType.TRIAL,
    StockCondition.RETURNED_FROM_REPAIR: OutboundType.REPAIR,
    StockCondition.RETURNED_FROM_DEPT_PROCUREMENT: OutboundType.DEPT_PROCUREMENT,
}

# 非采购入库类型 → 允许的关联出库类型
RETURN_CONDITION_ALLOWED_OUTBOUND: dict[StockCondition, list[OutboundType]] = {
    StockCondition.RETURNED_FROM_SALE: [OutboundType.SOLD],
    StockCondition.RETURNED_FROM_SOLD_OFFLINE: [OutboundType.SOLD_OFFLINE],
    StockCondition.RETURNED_FROM_PRESOLD: [OutboundType.PRESOLD],
    StockCondition.RETURNED_FROM_BORROW: [OutboundType.BORROWED],
    StockCondition.RETURNED_FROM_GIFT: [OutboundType.GIFTED],
    StockCondition.RETURNED_FROM_SCRAPPED: [OutboundType.SCRAPPED],
    StockCondition.RETURNED_FROM_RND: [OutboundType.RND],
    StockCondition.RETURNED_FROM_SAMPLE: [OutboundType.SAMPLE],
    StockCondition.RETURNED_FROM_TRIAL: [OutboundType.TRIAL],
    StockCondition.RETURNED_FROM_REPAIR: [OutboundType.REPAIR],
    StockCondition.RETURNED_FROM_DEPT_PROCUREMENT: [OutboundType.DEPT_PROCUREMENT],
}

# 非采购入库类型 → 单品当前应处的库存状态
RETURN_CONDITION_EXPECTED_STOCK: dict[StockCondition, list[StockStatus]] = {
    StockCondition.RETURNED_FROM_SALE: [StockStatus.SOLD],
    StockCondition.RETURNED_FROM_SOLD_OFFLINE: [StockStatus.SOLD_OFFLINE],
    StockCondition.RETURNED_FROM_PRESOLD: [StockStatus.PRESOLD],
    StockCondition.RETURNED_FROM_BORROW: [StockStatus.BORROWED],
    StockCondition.RETURNED_FROM_GIFT: [StockStatus.GIFTED],
    StockCondition.RETURNED_FROM_SCRAPPED: [StockStatus.SCRAPPED],
    StockCondition.RETURNED_FROM_RND: [StockStatus.RND],
    StockCondition.RETURNED_FROM_SAMPLE: [StockStatus.SAMPLE],
    StockCondition.RETURNED_FROM_TRIAL: [StockStatus.TRIAL],
    StockCondition.RETURNED_FROM_REPAIR: [StockStatus.REPAIR],
    StockCondition.RETURNED_FROM_DEPT_PROCUREMENT: [StockStatus.DEPT_PROCUREMENT],
}
