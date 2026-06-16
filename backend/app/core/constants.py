from enum import Enum

SHOP_LATITUDE = 21.006237
SHOP_LONGITUDE = 105.843127


class UserRole(str, Enum):
    ADMIN = "admin"
    INVENTORY_MANAGER = "inventory_manager"
    DELIVERY_MANAGER = "delivery_manager"
    CASHIER = "cashier"
    SHIPPER = "shipper"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class StaffStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


def enum_values(enum_class: type[Enum]) -> list[str]:
    return [item.value for item in enum_class]
