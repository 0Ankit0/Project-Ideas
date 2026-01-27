# Event Catalog - E-Commerce

| Event | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| product.created | Vendor Portal | Search Index, Catalog | Product listed |
| cart.updated | Web/App | Pricing Service | Cart changed |
| order.created | Checkout | Payment Service, Inventory | Order created |
| payment.captured | Payment Service | Order Service | Payment completed |
| inventory.reserved | Inventory Service | Order Service | Inventory held |
| shipment.created | Fulfillment | Tracking Service | Shipment initiated |
| order.delivered | Carrier | Notification Service | Delivery confirmed |
| return.requested | Customer App | Returns Service | Return initiated |