# Data Dictionary - E-Commerce

## Core Entities

### User
- **id**: UUID
- **role**: customer | vendor | admin
- **email**: string
- **status**: active | suspended

### Product
- **id**: UUID
- **vendorId**: UUID
- **name**: string
- **price**: decimal
- **currency**: string
- **status**: active | out_of_stock | archived

### Inventory
- **id**: UUID
- **productId**: UUID
- **warehouseId**: UUID
- **quantity**: int

### Cart
- **id**: UUID
- **userId**: UUID
- **items**: array

### Order
- **id**: UUID
- **userId**: UUID
- **status**: created | paid | packed | shipped | delivered | cancelled | returned
- **totalAmount**: decimal
- **createdAt**: ISO 8601

### Payment
- **id**: UUID
- **orderId**: UUID
- **provider**: string
- **status**: authorized | captured | failed | refunded
- **amount**: decimal

### Shipment
- **id**: UUID
- **orderId**: UUID
- **status**: created | in_transit | delivered | failed
- **carrier**: string

### ReturnRequest
- **id**: UUID
- **orderId**: UUID
- **status**: requested | approved | rejected | refunded