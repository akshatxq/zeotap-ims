# AI Assistance Documentation

This document records the AI assistance used during development, as required by the submission guidelines.

## Tools Used

- **Primary AI:** Claude (Anthropic) — architecture design, implementation guidance, debugging
- **Editor:** VS Code
- **Version Control:** Git + GitHub

## How AI Was Used

### Architecture Planning
- Designing the backpressure system using asyncio.Queue
- Choosing the dual database strategy (MongoDB + PostgreSQL)
- Selecting State and Strategy design patterns for workflow and alerting

### Implementation Guidance
- FastAPI async endpoint structure
- Redis debounce window implementation
- Pydantic V2 field validators for RCA validation
- Docker Compose health check configuration

### Debugging Assistance
- MongoDB ObjectId JSON serialization
- CORS configuration for frontend-backend communication
- Redis connection pooling
- Pydantic V2 migration from @validator to @field_validator

### Documentation
- README structure and backpressure explanation
- Architecture Decision Records format

## Key Prompts Used

### Initial Architecture
- "Create a mission-critical incident management system with backpressure using asyncio.Queue"
- "Implement debouncing: 100 signals/10 seconds → 1 work item using Redis"
- "Apply State pattern for work item lifecycle and Strategy pattern for alerts"

### Database Design
- "Use MongoDB for raw signals (NoSQL, schema-flexible)"
- "Use PostgreSQL for work items (ACID transactions)"
- "Use Redis for debouncing TTL and dashboard cache"

### Feature Implementation
- "Add SlowAPI rate limiter (1000 requests/minute per IP)"
- "Implement retry logic with exponential backoff (3 attempts, 0.5s → 1s → 2s)"
- "Create simulation script for RDBMS cascade failure"

### Frontend Development
- "Build React dashboard with live feed, incident list, detail view, and RCA form"
- "Add Tailwind CSS for styling"

### Testing and Documentation
- "Write unit tests for RCA validation (14 tests total)"
- "Create README with backpressure section and architecture diagram"

## AI Contribution Breakdown

| Component | AI Assisted | Human Reviewed |
|-----------|-------------|----------------|
| Architecture Design | 90% | 10% |
| Backend Code | 85% | 15% |
| Frontend Code | 80% | 20% |
| Tests | 90% | 10% |
| Documentation | 95% | 5% |
| Debugging | 70% | 30% |

## Lessons Learned

1. **Pydantic V2 migration** required changing `@validator` to `@field_validator` and `class Config` to `model_config`
2. **MongoDB ObjectId** needed explicit string conversion for JSON serialization
3. **CORS configuration** was essential for frontend-backend communication
4. **Docker health checks** prevented race conditions on first run
5. **Redis connection pooling** required careful global variable management

## Transparency Note

This project was completed as an assignment for Zeotap's Infrastructure/SRE Intern position. AI assistance was used to accelerate development while maintaining understanding of all implemented concepts. The candidate reviewed and understood all code before integration.

**Repository:** https://github.com/akshatxq/zeotap-ims
**Candidate:** Akshat Singh
**Date:** May 2026