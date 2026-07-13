# 导入所有模型，供 Alembic autogenerate 发现
from app.models.user import User  # noqa: F401
from app.models.sequence import SequenceCounter  # noqa: F401
from app.models.product import ProductCategory, ProductSku  # noqa: F401
from app.models.partner import PartnerGroup, Partner  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.inventory import InventoryItem, InventoryItemHistory, InventoryItemSnapshot, InventoryDailySummary, InventorySkuDailyLedger  # noqa: F401
from app.models.inbound import InboundOrder, InboundOrderLine, InboundOrderItem  # noqa: F401
from app.models.outbound import OutboundOrder, OutboundOrderItem  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.system_config import SystemConfig  # noqa: F401
