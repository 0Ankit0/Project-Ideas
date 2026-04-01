# C4 Code-Level Diagram - InventoryService

This document provides a detailed code-level architecture diagram (C4 Level 4) for the InventoryService microservice, including class diagrams, component interactions, and key design patterns.

---

## InventoryService Architecture

The InventoryService manages ticket availability, holds (reservations), and dynamic pricing. It's the most critical service during high-demand onsale events.

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        InventoryService                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────────────┐   │
│  │ TicketInventory      │  │ PricingService               │   │
│  │ Controller           │  │ (Dynamic Pricing Engine)     │   │
│  │                      │  │                              │   │
│  │ - POST /holds        │  │ - getCurrentPrice()          │   │
│  │ - GET /holds/:id     │  │ - calculateDynamicPrice()    │   │
│  │ - DELETE /holds/:id  │  │ - applyPromotionCode()       │   │
│  │ - POST /holds/convert│  │ - getHistoricalPricing()     │   │
│  │ - GET /seats         │  │                              │   │
│  └──────────┬───────────┘  └──────────────┬───────────────┘   │
│             │                             │                   │
│             ├─────────────────────────────┤                   │
│             │                             │                   │
│  ┌──────────▼──────────────────┐ ┌────────▼─────────────────┐ │
│  │ TicketHoldService           │ │ SeatMapService          │ │
│  │ (Reservation Logic)         │ │ (Seat Availability)     │ │
│  │                             │ │                         │ │
│  │ - createHold()              │ │ - getSeatMap()          │ │
│  │ - releaseHold()             │ │ - reserveSeats()        │ │
│  │ - convertHoldToOrder()      │ │ - releaseSeats()        │ │
│  │ - getHoldStatus()           │ │ - getAvailableSeats()   │ │
│  │ - getHoldsByCustomer()      │ │ - updateSeatStatus()    │ │
│  │ - expireOldHolds()          │ │                         │ │
│  └──────────┬────────────────┬─┘ └────────┬────────────────┘ │
│             │                │            │                  │
│  ┌──────────▼──────┐  ┌──────▼──────┐  ┌──▼──────────────┐  │
│  │ RedisHold       │  │ EventPublish│  │ OrderService    │  │
│  │ Repository      │  │ er          │  │ (Integration)   │  │
│  │ (Fast Cache)    │  │             │  │                 │  │
│  │                 │  │ - publish() │  │ - convertHold() │  │
│  │ - save()        │  │             │  │                 │  │
│  │ - get()         │  │ Events:     │  └─────────────────┘  │
│  │ - delete()      │  │ - hold.*    │                       │
│  │ - expire()      │  │             │                       │
│  └────────┬────────┘  └─────────────┘                       │
│           │                                                  │
│  ┌────────▼────────────────────────────────────────────┐   │
│  │ Redis Cluster                                       │   │
│  │ (Low-latency ticket hold storage)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Class Diagram - Core Domain Models

### TicketHold Class

```typescript
class TicketHold {
  // Identifiers
  holdId: string;           // UUID, generated at creation
  customerId: string;       // Reference to customer
  eventId: string;          // Reference to event
  
  // Reservation Details
  quantity: number;         // Number of tickets reserved
  selectedSeats?: string[]; // Seat IDs if reserved seating
  ticketType: TicketType;   // GA, VIP, reserved, etc.
  
  // Pricing
  unitPrice: number;        // Price per ticket at time of hold
  subtotal: number;         // quantity × unitPrice
  promotionCode?: string;   // Applied discount code
  discount: number;         // Discount amount
  totalPrice: number;       // subtotal - discount
  
  // Status
  status: HoldStatus;       // pending, reserved, converted, expired, released
  createdAt: Date;
  expiresAt: Date;          // 10 minutes from creation
  convertedAt?: Date;       // When converted to order
  releasedAt?: Date;        // When manually released
  
  // Version Control (optimistic locking)
  version: number;
  
  // Methods
  isExpired(): boolean {
    return new Date() > this.expiresAt;
  }
  
  canConvert(): boolean {
    return this.status === 'reserved' && !this.isExpired();
  }
  
  release(): void {
    this.status = 'released';
    this.releasedAt = new Date();
  }
}

enum HoldStatus {
  PENDING = 'pending',       // Just created, awaiting confirmation
  RESERVED = 'reserved',     // Confirmed by customer (payment authorized)
  CONVERTED = 'converted',   // Converted to order
  EXPIRED = 'expired',       // TTL exceeded
  RELEASED = 'released'      // Manually released by customer
}

enum TicketType {
  GENERAL_ADMISSION = 'GA',
  RESERVED_SEATING = 'reserved',
  VIP = 'vip',
  EARLY_BIRD = 'early_bird'
}
```

### SeatMap Class

```typescript
class SeatMap {
  seatMapId: string;
  eventId: string;
  venueId: string;
  
  // Seat Structure
  sections: Section[];      // Different sections (Mezzanine, Orchestra, etc.)
  totalSeats: number;
  totalAvailable: number;
  
  // Pricing by Seat
  pricingBySection: Map<string, number>; // Section → price
  
  // Status Tracking
  updatedAt: Date;
  version: number;
  
  // Methods
  getAvailableSeats(): Seat[] {
    return this.sections
      .flatMap(s => s.seats)
      .filter(s => s.status === 'available');
  }
  
  reserveSeats(seatIds: string[]): boolean {
    // Atomic operation: all seats reserved or none
    const seats = this.findSeats(seatIds);
    if (!seats.every(s => s.status === 'available')) {
      return false;
    }
    seats.forEach(s => s.status = 'reserved');
    this.totalAvailable -= seats.length;
    return true;
  }
  
  releaseSeats(seatIds: string[]): void {
    const seats = this.findSeats(seatIds);
    seats.forEach(s => s.status = 'available');
    this.totalAvailable += seats.length;
  }
}

class Section {
  sectionId: string;
  name: string;              // "Mezzanine", "Orchestra", etc.
  rows: Row[];
  totalSeats: number;
  pricePerSeat: number;      // Section-specific pricing
}

class Row {
  rowId: string;
  rowNumber: number;         // Row A, B, C
  seats: Seat[];
}

class Seat {
  seatId: string;
  seatNumber: number;        // Seat 1, 2, 3
  status: SeatStatus;        // available, reserved, sold, blocked
  holdId?: string;           // Which hold owns this seat
  
  // Accessibility
  isAccessible: boolean;
  hasArmrestOnLeft?: boolean;
  hasArmrestOnRight?: boolean;
}

enum SeatStatus {
  AVAILABLE = 'available',
  RESERVED = 'reserved',     // Temporarily held
  SOLD = 'sold',             // Converted to order
  BLOCKED = 'blocked'        // Cannot sell (damaged, obstructed view)
}
```

### PriceVariant Class

```typescript
class PriceVariant {
  variantId: string;
  eventId: string;
  
  // Base Configuration
  ticketType: TicketType;
  basePrice: number;
  
  // Dynamic Pricing
  peakPrice?: number;        // Price when demand high (>80% sold)
  offPeakPrice?: number;     // Price when demand low (<20% sold)
  currentPrice: number;      // Calculated based on demand
  
  // Promotional
  promotionCodes: PromoCode[];
  seasonalDiscounts: SeasonalDiscount[];
  
  // Constraints
  maxQuantityPerCustomer: number;
  minimumQuantityPerOrder: number;
  
  // Timing
  salesStartDate: Date;
  salesEndDate: Date;
  lastUpdatedAt: Date;
  
  // Methods
  isOnSale(): boolean {
    const now = new Date();
    return now >= this.salesStartDate && now <= this.salesEndDate;
  }
  
  calculateCurrentPrice(soldPercentage: number): number {
    if (soldPercentage > 80 && this.peakPrice) {
      return this.peakPrice;
    } else if (soldPercentage < 20 && this.offPeakPrice) {
      return this.offPeakPrice;
    }
    return this.basePrice;
  }
  
  applyPromoCode(code: string): number {
    const promo = this.promotionCodes.find(p => p.code === code);
    if (promo && promo.isValid()) {
      return this.currentPrice * (1 - promo.discountRate);
    }
    return this.currentPrice;
  }
}

class PromoCode {
  code: string;
  discountRate: number;      // 0.1 = 10% off
  maxUsages: number;
  currentUsages: number;
  validFrom: Date;
  validUntil: Date;
  
  isValid(): boolean {
    const now = new Date();
    return now >= this.validFrom &&
           now <= this.validUntil &&
           this.currentUsages < this.maxUsages;
  }
}

class SeasonalDiscount {
  seasonId: string;
  season: Season;            // summer, fall, winter, spring
  discountRate: number;
  applicableTicketTypes: TicketType[];
}

enum Season {
  SUMMER = 'summer',
  FALL = 'fall',
  WINTER = 'winter',
  SPRING = 'spring'
}
```

---

## Service Layer Classes

### TicketHoldService

```typescript
class TicketHoldService {
  constructor(
    private holdRepository: RedisHoldRepository,
    private seatMapService: SeatMapService,
    private pricingService: PricingService,
    private eventPublisher: EventPublisher,
    private orderService: OrderService
  ) {}
  
  // Create Hold (Reserve Tickets)
  async createHold(request: CreateHoldRequest): Promise<TicketHold> {
    const { eventId, customerId, quantity, ticketType } = request;
    
    // 1. Get current pricing
    const pricing = await this.pricingService.getPricing(eventId, ticketType);
    if (!pricing.isOnSale()) {
      throw new Error('Tickets not on sale');
    }
    
    // 2. Reserve seats (if reserved seating)
    let selectedSeats: string[] = [];
    if (ticketType === TicketType.RESERVED_SEATING) {
      selectedSeats = await this.seatMapService.reserveSeats(
        eventId,
        quantity,
        request.sectionPreference
      );
      if (!selectedSeats) {
        throw new Error('No seats available');
      }
    }
    
    // 3. Create hold record
    const hold = new TicketHold();
    hold.holdId = generateUUID();
    hold.customerId = customerId;
    hold.eventId = eventId;
    hold.quantity = quantity;
    hold.ticketType = ticketType;
    hold.selectedSeats = selectedSeats;
    hold.unitPrice = pricing.currentPrice;
    hold.subtotal = quantity * pricing.currentPrice;
    hold.promotionCode = request.promotionCode;
    hold.discount = await this.calculateDiscount(request.promotionCode, hold.subtotal);
    hold.totalPrice = hold.subtotal - hold.discount;
    hold.status = HoldStatus.PENDING;
    hold.createdAt = new Date();
    hold.expiresAt = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes
    hold.version = 1;
    
    // 4. Save to Redis (fast, expires automatically)
    await this.holdRepository.save(hold);
    
    // 5. Publish event
    await this.eventPublisher.publish('hold.created', {
      holdId: hold.holdId,
      customerId: hold.customerId,
      eventId: hold.eventId,
      quantity: hold.quantity,
      totalPrice: hold.totalPrice,
      expiresAt: hold.expiresAt
    });
    
    return hold;
  }
  
  // Get Hold Status
  async getHold(holdId: string): Promise<TicketHold> {
    const hold = await this.holdRepository.get(holdId);
    if (!hold) {
      throw new Error('Hold not found');
    }
    if (hold.isExpired()) {
      await this.expireHold(holdId);
      throw new Error('Hold has expired');
    }
    return hold;
  }
  
  // Release Hold (Customer cancels before checkout)
  async releaseHold(holdId: string): Promise<void> {
    const hold = await this.holdRepository.get(holdId);
    if (!hold) {
      throw new Error('Hold not found');
    }
    
    // Release reserved seats
    if (hold.selectedSeats && hold.selectedSeats.length > 0) {
      await this.seatMapService.releaseSeats(hold.eventId, hold.selectedSeats);
    }
    
    // Release hold record
    hold.release();
    await this.holdRepository.save(hold);
    
    // Publish event
    await this.eventPublisher.publish('hold.released', {
      holdId: hold.holdId,
      eventId: hold.eventId,
      seatsReleased: hold.selectedSeats?.length || 0
    });
  }
  
  // Convert Hold to Order (Payment completed)
  async convertHoldToOrder(holdId: string, orderId: string): Promise<void> {
    const hold = await this.holdRepository.get(holdId);
    if (!hold) {
      throw new Error('Hold not found');
    }
    if (hold.status !== HoldStatus.PENDING && hold.status !== HoldStatus.RESERVED) {
      throw new Error('Hold cannot be converted');
    }
    if (hold.isExpired()) {
      throw new Error('Hold has expired');
    }
    
    // Atomically update hold status (optimistic locking)
    hold.status = HoldStatus.CONVERTED;
    hold.convertedAt = new Date();
    hold.version += 1;
    
    const success = await this.holdRepository.updateWithVersion(hold);
    if (!success) {
      throw new Error('Optimistic lock failed - hold was modified');
    }
    
    // Notify order service
    await this.orderService.recordOrderFromHold(holdId, orderId);
    
    // Publish event
    await this.eventPublisher.publish('hold.converted', {
      holdId: hold.holdId,
      orderId: orderId,
      eventId: hold.eventId
    });
  }
  
  // Expire Old Holds (Scheduled job, runs every 5 minutes)
  async expireOldHolds(): Promise<number> {
    const expiredHolds = await this.holdRepository.getExpiredHolds();
    let count = 0;
    
    for (const hold of expiredHolds) {
      // Release reserved seats
      if (hold.selectedSeats && hold.selectedSeats.length > 0) {
        await this.seatMapService.releaseSeats(hold.eventId, hold.selectedSeats);
      }
      
      // Mark as expired
      hold.status = HoldStatus.EXPIRED;
      await this.holdRepository.delete(holdId); // Delete from Redis (expired)
      
      count++;
      
      // Publish event
      await this.eventPublisher.publish('hold.expired', {
        holdId: hold.holdId,
        eventId: hold.eventId
      });
    }
    
    return count;
  }
  
  // Helper: Calculate Discount
  private async calculateDiscount(promoCode?: string, subtotal?: number): Promise<number> {
    if (!promoCode) return 0;
    return await this.pricingService.validateAndCalculateDiscount(promoCode, subtotal);
  }
}
```

### SeatMapService

```typescript
class SeatMapService {
  constructor(
    private seatMapRepository: SeatMapRepository,
    private redisCache: Redis
  ) {}
  
  async getSeatMap(eventId: string): Promise<SeatMap> {
    // Try cache first
    const cached = await this.redisCache.get(`seatmap:${eventId}`);
    if (cached) {
      return JSON.parse(cached);
    }
    
    // Fetch from database
    const seatMap = await this.seatMapRepository.getByEventId(eventId);
    if (!seatMap) {
      throw new Error('Seat map not found');
    }
    
    // Cache for 30 seconds (frequent queries, eventual consistency acceptable)
    await this.redisCache.setex(`seatmap:${eventId}`, 30, JSON.stringify(seatMap));
    
    return seatMap;
  }
  
  async reserveSeats(
    eventId: string,
    quantity: number,
    sectionPreference?: string
  ): Promise<string[]> {
    const seatMap = await this.getSeatMap(eventId);
    
    // Find available seats (matching section preference if provided)
    const availableSeats = seatMap.getAvailableSeats()
      .filter(s => !sectionPreference || s.section === sectionPreference)
      .slice(0, quantity);
    
    if (availableSeats.length < quantity) {
      return null; // Not enough seats available
    }
    
    // Reserve seats atomically
    const seatIds = availableSeats.map(s => s.seatId);
    const success = seatMap.reserveSeats(seatIds);
    
    if (!success) {
      return null; // Race condition: seats already reserved
    }
    
    // Persist to database
    await this.seatMapRepository.update(seatMap);
    
    // Invalidate cache
    await this.redisCache.del(`seatmap:${eventId}`);
    
    return seatIds;
  }
  
  async releaseSeats(eventId: string, seatIds: string[]): Promise<void> {
    const seatMap = await this.getSeatMap(eventId);
    seatMap.releaseSeats(seatIds);
    
    await this.seatMapRepository.update(seatMap);
    await this.redisCache.del(`seatmap:${eventId}`);
  }
  
  async getAvailableSeats(eventId: string): Promise<number> {
    const seatMap = await this.getSeatMap(eventId);
    return seatMap.totalAvailable;
  }
}
```

### PricingService

```typescript
class PricingService {
  constructor(
    private priceRepository: PriceRepository,
    private redisCache: Redis
  ) {}
  
  async getPricing(eventId: string, ticketType: TicketType): Promise<PriceVariant> {
    const cacheKey = `pricing:${eventId}:${ticketType}`;
    
    // Try cache first
    const cached = await this.redisCache.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }
    
    // Fetch from database
    const pricing = await this.priceRepository.getByEventAndType(eventId, ticketType);
    
    // Calculate current price based on demand
    const seatMap = new SeatMapService().getSeatMap(eventId);
    const soldPercentage = ((seatMap.totalSeats - seatMap.totalAvailable) / seatMap.totalSeats) * 100;
    pricing.currentPrice = pricing.calculateCurrentPrice(soldPercentage);
    
    // Cache for 1 minute (balance between freshness and performance)
    await this.redisCache.setex(cacheKey, 60, JSON.stringify(pricing));
    
    return pricing;
  }
  
  async calculateDynamicPrice(eventId: string, soldPercentage: number): Promise<number> {
    const pricing = await this.priceRepository.getByEventAndType(eventId, TicketType.GENERAL_ADMISSION);
    return pricing.calculateCurrentPrice(soldPercentage);
  }
}
```

---

## Data Access Layer (Repository)

### RedisHoldRepository

```typescript
class RedisHoldRepository {
  constructor(private redis: Redis) {}
  
  async save(hold: TicketHold): Promise<void> {
    const ttl = Math.floor((hold.expiresAt.getTime() - Date.now()) / 1000);
    const key = `hold:${hold.holdId}`;
    const value = JSON.stringify(hold);
    
    // SETEX: set with automatic expiration
    await this.redis.setex(key, ttl, value);
  }
  
  async get(holdId: string): Promise<TicketHold | null> {
    const key = `hold:${holdId}`;
    const value = await this.redis.get(key);
    
    if (!value) return null;
    return JSON.parse(value);
  }
  
  async delete(holdId: string): Promise<void> {
    const key = `hold:${holdId}`;
    await this.redis.del(key);
  }
  
  async updateWithVersion(hold: TicketHold): Promise<boolean> {
    // Optimistic locking: only update if version matches
    const key = `hold:${hold.holdId}`;
    
    // Lua script: compare-and-set
    const script = `
      if redis.call('GET', KEYS[1]) == ARGV[1] then
        redis.call('SET', KEYS[1], ARGV[2])
        return 1
      else
        return 0
      end
    `;
    
    const result = await this.redis.eval(script, 1, key, JSON.stringify(hold), JSON.stringify(hold));
    return result === 1;
  }
  
  async getExpiredHolds(): Promise<TicketHold[]> {
    // Scan for all holds
    const keys = await this.redis.keys('hold:*');
    const holds: TicketHold[] = [];
    
    for (const key of keys) {
      const value = await this.redis.get(key);
      const hold = JSON.parse(value);
      
      if (hold.isExpired()) {
        holds.push(hold);
      }
    }
    
    return holds;
  }
}
```

---

## Event Publishing

### EventPublisher

```typescript
class EventPublisher {
  constructor(private kafka: KafkaProducer) {}
  
  async publish(eventType: string, payload: any): Promise<void> {
    const event = {
      type: eventType,
      timestamp: new Date().toISOString(),
      payload: payload
    };
    
    await this.kafka.send({
      topic: 'inventory-events',
      messages: [{
        key: payload.eventId, // Partition by eventId (ensures ordering)
        value: JSON.stringify(event)
      }]
    });
  }
}
```

---

## Integration with Other Services

### OrderService Integration

The TicketHoldService integrates with OrderService:

```typescript
// In TicketHoldService.convertHoldToOrder()
await this.orderService.recordOrderFromHold(holdId, orderId);

// In OrderService
async recordOrderFromHold(holdId: string, orderId: string): Promise<void> {
  // Retrieve hold details
  const hold = await this.inventoryService.getHold(holdId);
  
  // Create order record
  const order = new Order();
  order.orderId = orderId;
  order.customerId = hold.customerId;
  order.eventId = hold.eventId;
  order.quantity = hold.quantity;
  order.selectedSeats = hold.selectedSeats;
  order.totalPrice = hold.totalPrice;
  order.status = OrderStatus.CONFIRMED;
  
  // Save order
  await this.orderRepository.save(order);
  
  // Publish event
  await this.eventPublisher.publish('order.confirmed', {
    orderId: order.orderId,
    holdId: holdId,
    customerId: order.customerId
  });
}
```

---

## Key Design Patterns

1. **Repository Pattern:** Data access abstraction (Redis + PostgreSQL)
2. **Service Layer:** Business logic encapsulation
3. **Event Sourcing:** Audit trail of holds (created, reserved, converted, expired)
4. **Optimistic Locking:** Handle concurrent updates safely
5. **Caching Strategy:** Redis for hot data (holds, seat maps), PostgreSQL for cold
6. **TTL-based Expiration:** Redis auto-expires holds after 10 minutes
7. **Pub/Sub:** Events published for downstream services (OrderService, TicketService, NotificationService)

---

This C4 Level 4 diagram provides implementation details for developers building the InventoryService.
