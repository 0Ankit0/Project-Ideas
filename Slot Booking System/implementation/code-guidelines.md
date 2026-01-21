# Code Guidelines - Slot Booking System

> **Platform Independence**: Guidelines applicable to any programming language and framework.

---

## Project Structure

```
slot-booking-system/
├── apps/
│   ├── api/                    # Backend API
│   │   ├── src/
│   │   │   ├── controllers/    # HTTP request handlers
│   │   │   ├── services/       # Business logic
│   │   │   ├── repositories/   # Data access
│   │   │   ├── domain/         # Domain models
│   │   │   ├── middleware/     # Request middleware
│   │   │   ├── validators/     # Input validation
│   │   │   ├── utils/          # Helper functions
│   │   │   └── config/         # Configuration
│   │   └── tests/
│   ├── web/                    # Web frontend
│   └── mobile/                 # Mobile app
├── packages/
│   └── shared/                 # Shared code
├── docker/
├── scripts/
└── docs/
```

---

## Coding Conventions

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | kebab-case | `booking-service.ts` |
| Classes | PascalCase | `BookingService` |
| Functions | camelCase | `createBooking()` |
| Constants | UPPER_SNAKE | `MAX_SLOTS_PER_BOOKING` |
| Database tables | snake_case | `booking_slots` |
| API endpoints | kebab-case | `/api/v1/booking-slots` |

### Code Organization

```typescript
// 1. Imports (external, internal, relative)
import { Injectable } from '@nestjs/common';
import { BookingRepository } from '../repositories';
import { CreateBookingDto } from './dto';

// 2. Constants
const MAX_BOOKING_SLOTS = 5;

// 3. Interfaces/Types
interface BookingResult { /* ... */ }

// 4. Main class/function
@Injectable()
export class BookingService {
  constructor(private readonly repo: BookingRepository) {}
  
  async createBooking(dto: CreateBookingDto): Promise<BookingResult> {
    // Implementation
  }
}
```

---

## Architecture Patterns

### Service Layer Pattern
```
Controller → Service → Repository → Database
    ↓           ↓
 Validator   Domain Logic
```

### Dependency Injection
```typescript
// ✅ Good: Inject dependencies
class BookingService {
  constructor(
    private slotService: ISlotService,
    private paymentService: IPaymentService
  ) {}
}

// ❌ Bad: Direct instantiation
class BookingService {
  private slotService = new SlotService();
}
```

### Repository Pattern
```typescript
interface IBookingRepository {
  findById(id: string): Promise<Booking | null>;
  findByUser(userId: string): Promise<Booking[]>;
  save(booking: Booking): Promise<Booking>;
  update(id: string, data: Partial<Booking>): Promise<Booking>;
}
```

---

## Error Handling

```typescript
// Custom error classes
class BookingError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 400
  ) {
    super(message);
  }
}

class SlotUnavailableError extends BookingError {
  constructor(slotId: string) {
    super(`Slot ${slotId} is not available`, 'SLOT_UNAVAILABLE', 409);
  }
}

// Usage
async function bookSlot(slotId: string) {
  const slot = await slotRepo.findById(slotId);
  if (!slot || slot.status !== 'available') {
    throw new SlotUnavailableError(slotId);
  }
}
```

---

## API Response Format

### Success Response
```json
{
  "success": true,
  "data": { /* response data */ },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      { "field": "email", "message": "Invalid format" }
    ]
  }
}
```

---

## Testing Standards

### Unit Tests
```typescript
describe('BookingService', () => {
  describe('createBooking', () => {
    it('should create booking when slots are available', async () => {
      // Arrange
      const mockSlotService = { lockSlots: jest.fn().mockResolvedValue(true) };
      const service = new BookingService(mockSlotService);
      
      // Act
      const result = await service.createBooking(validDto);
      
      // Assert
      expect(result.status).toBe('pending');
      expect(mockSlotService.lockSlots).toHaveBeenCalled();
    });
  });
});
```

### Test Coverage Targets
| Type | Minimum Coverage |
|------|------------------|
| Unit Tests | 80% |
| Integration Tests | 60% |
| E2E Tests | Critical paths |

---

## Security Guidelines

1. **Input Validation**: Validate all inputs at API boundary
2. **SQL Injection**: Use parameterized queries/ORM
3. **XSS**: Sanitize outputs, use CSP headers
4. **Authentication**: JWT with short expiry, refresh tokens
5. **Authorization**: Check permissions at service layer
6. **Secrets**: Use environment variables, never commit secrets

```typescript
// ✅ Good: Parameterized query
const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);

// ❌ Bad: String interpolation
const user = await db.query(`SELECT * FROM users WHERE id = '${userId}'`);
```

---

## Git Workflow

### Branch Naming
```
feature/add-booking-cancellation
bugfix/fix-payment-timeout
hotfix/critical-security-patch
```

### Commit Messages
```
feat(booking): add cancellation with refund
fix(payment): handle gateway timeout gracefully
docs(api): update booking endpoint documentation
```

---

## Environment Variables

```bash
# .env.example
NODE_ENV=development
PORT=3000
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
STRIPE_API_KEY=sk_test_xxx
```

---

## Domain-Specific Adaptations

When adapting this system for different domains:

| Domain | Resource | Slot Duration | Special Fields |
|--------|----------|---------------|----------------|
| Futsal | Court | 60-90 min | teamSize, matchType |
| Events | Venue | Variable | attendeeLimit, eventType |
| Medical | Doctor | 15-30 min | specialization, insuranceAccepted |
| Coworking | Desk/Room | Hourly/Daily | amenities, floor |

Add domain-specific fields as JSON metadata rather than changing core schema.
