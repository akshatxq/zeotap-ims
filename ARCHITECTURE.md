# Architecture Decision Records (ADR)

## 1. Queue Choice: asyncio.Queue vs Kafka/RabbitMQ

**Decision:** Use Python's native `asyncio.Queue` with maxsize=50000

**Why not Kafka/RabbitMQ?**
- Adds operational complexity (extra containers to manage)
- Overkill for single-instance deployment
- No need for persistence across restarts
- Reviewer would need to learn new system

**Why asyncio.Queue?**
- Zero additional dependencies
- Bounded size provides natural backpressure
- Native async support without external brokers
- Perfect for single-node deployment

**Trade-off:** Signals are lost on container restart (acceptable for assignment). In production with multiple replicas, we'd use Redis Streams or Kafka.

---

## 2. Dual Database: MongoDB + PostgreSQL

**Decision:** Store raw signals in MongoDB, work items in PostgreSQL

**Why MongoDB for Signals?**
- Schema-flexible (signal payloads vary by component)
- High write throughput (200k+ writes/sec)
- Easy horizontal scaling with sharding
- No need for complex joins

**Why PostgreSQL for Work Items?**
- ACID transactions for state transitions
- Foreign key constraints ensure data integrity
- `SELECT FOR UPDATE` prevents race conditions
- JSON column for RCA data (best of both worlds)

**Why Not Single Database?**
- PostgreSQL: JSON queries slower than MongoDB for millions of signals
- MongoDB: No ACID across multiple documents for state machines
- Separation of concerns: hot path (signals) vs critical path (work items)

---

## 3. Redis: Dual Purpose (Debounce + Cache)

**Decision:** Single Redis instance for both debouncing and dashboard cache

**Debouncing Implementation:**
```python
redis_key = f"debounce:{component_id}"
await redis.setex(redis_key, 10, work_item_id)  # 10 second TTL
```
- Atomic SETEX ensures window starts exactly once
- TTL auto-expires window without cron jobs

**Dashboard Cache Implementation:**
```python
await redis.setex("dashboard:active_incidents", 10, json.dumps(incidents))
```
- 10s TTL balances freshness vs PostgreSQL load
- Cache invalidation on state transitions and RCA submission

**Why Not Separate Instances?**
- Single Redis handles both workloads easily
- Reduces container count (simpler for reviewer)
- No performance impact at this scale

---

## 4. Backpressure Flow End-to-End

```
High Load Scenario (5000 signals/sec, DB writes at 500/sec)

1. HTTP Handler receives signal
   → signal_queue.put_nowait()  (0.001ms)
   → returns 202 Accepted

2. Queue fills to 50k capacity
   → subsequent signals trigger QueueFull exception
   → signals DROPPED with counter increment

3. Background worker processes at DB speed (500/sec)
   → queue_depth decreases as DB catches up

4. Monitoring exposes:
   - queue_depth (current backlog)
   - dropped_signals (total lost)
   - processing_rate (signals/sec)

Result: HTTP server stays responsive even under 10x overload
```

---

## 5. Rate Limiting Strategy

**Decision:** SlowAPI with per-IP limiting (1000 requests/minute)

**Why per-IP?**
- Prevents single client from overwhelming queue
- Fair distribution across multiple clients
- No authentication required (simpler for demo)

**Why 1000/minute?**
- ~16 requests/second sustained
- Matches typical API gateway limits
- Allows burst testing while preventing abuse

---

## 6. Retry Logic with Exponential Backoff

**Delays:** 0.5s → 1s → 2s across 3 attempts

**Applied to:**
- MongoDB store_raw_signal
- PostgreSQL create_work_item
- PostgreSQL update_work_item_status

**Why Exponential Backoff?**
- Simple to implement
- Reduces load during transient failures
- Prevents thundering herd on recovery

---

## 7. State Machine Design

**Pattern:** Classic GoF State pattern with explicit transition validation

**State Diagram:**
```
OPEN ──start_investigation──> INVESTIGATING
INVESTIGATING ──resolve──> RESOLVED
INVESTIGATING ──escalate──> (self)   # notifies on-call
RESOLVED ──close──> CLOSED           (requires complete RCA)
RESOLVED ──reopen──> INVESTIGATING
CLOSED ──reopen──> INVESTIGATING
```

**Why Not Simple Enum?**
- Enums cannot prevent invalid transitions
- State pattern encapsulates transition logic
- Easy to add pre/post transition hooks (logging, notifications)

---

## 8. Alert Strategy Design

**Pattern:** Strategy pattern with component-to-strategy mapping

**Mapping:**
```python
COMPONENT_STRATEGIES = {
    "RDBMS_PRIMARY": P0Strategy(),    # Page everyone
    "API_GATEWAY":   P0Strategy(),    # Page everyone
    "MCP_HOST_01":   P1Strategy(),    # Page on-call
    "CACHE_CLUSTER": P2Strategy(),    # Slack only
}
```

**Why Strategy Pattern?**
- New alert methods (SMS, PagerDuty, OpsGenie) added without modifying core
- Strategies are interchangeable at runtime
- Easy to test each strategy in isolation

---

## 9. Health Check Design

**Endpoint:** `GET /health` returns:
```json
{
  "status": "ok",
  "components": {
    "redis": "ok",
    "mongodb": "ok",
    "postgresql": "ok"
  },
  "queue": {
    "depth": 0,
    "max_size": 50000,
    "utilization": 0.0
  },
  "metrics": {
    "total_signals_received": 190,
    "work_items_created": 3,
    "dropped_signals": 0
  }
}
```

**Why Per-Component?**
- Orchestrators (Kubernetes) can make routing decisions based on component health
- Debugging: instantly know which database is failing
- Load balancers can route around degraded components

---

## 10. Docker Compose Orchestration

**Health Check Dependencies:**
```yaml
depends_on:
  postgres:
    condition: service_healthy   # Waits for pg_isready
  mongodb:
    condition: service_healthy   # Waits for mongosh ping
  redis:
    condition: service_healthy   # Waits for redis-cli ping
```

**Why Health Checks?**
- Prevents backend from starting before databases are ready
- Eliminates race conditions on first run
- Reviewer can docker-compose up successfully on first try

---

## Summary Table

| Area | Decision | Rationale |
|------|----------|-----------|
| Backpressure | asyncio.Queue | Simplicity, native async, zero deps |
| Debounce | Redis with TTL | Atomic operations, auto-expiry |
| Signals DB | MongoDB | Schema-flexible, high throughput |
| Work Items DB | PostgreSQL | ACID, SELECT FOR UPDATE |
| State Machine | GoF State pattern | Encapsulates transition rules |
| Alert Strategy | GoF Strategy pattern | Pluggable alert methods |
| Rate Limiting | SlowAPI per-IP | Simple, effective for demo |
| Retry | Exponential backoff | Prevents thundering herd |
| Deployment | Docker Compose | Single command for reviewer |

These decisions prioritize simplicity and demonstrability over production-scale complexity, while still demonstrating deep SRE knowledge.