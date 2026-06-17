from app.schemas.delivery import (
    DeliveryLocationLogRead,
    DeliveryLocationUpdate,
    DeliveryOrderDelivered,
    DeliveryOrderFailed,
    ShipperPerformanceRead as DeliveryShipperPerformanceRead,
    DeliveryTripDetailRead,
    DeliveryTripRead,
)

ShipperTripRead = DeliveryTripRead
ShipperTripDetailRead = DeliveryTripDetailRead
ShipperLocationUpdate = DeliveryLocationUpdate
ShipperLocationLogRead = DeliveryLocationLogRead
ShipperOrderDelivered = DeliveryOrderDelivered
ShipperOrderFailed = DeliveryOrderFailed
ShipperPerformanceRead = DeliveryShipperPerformanceRead
