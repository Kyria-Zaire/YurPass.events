---
paths:
  - "backend/**"
---

# Architecte API — YurPass Backend

Stack : FastAPI + Python + PostgreSQL + Redis + Alembic.

## Structure module obligatoire

```
backend/app/modules/{domain}/
├── router.py       # HTTP endpoints uniquement
├── service.py      # Business logic
├── models.py       # SQLAlchemy models
├── schemas.py      # Pydantic request/response
├── repository.py   # DB queries
└── permissions.py  # RBAC guards
```

## Modules MVP (ordre sprints)

`auth` → `users` → `organizations` → `events` → `invitations` → `tickets` → `orders` → `payments` → `checkins` → `passports` → `admin`

## Conventions API

- Prefix : `/api/v1/{resource}`
- Réponses erreur standardisées :
```json
{ "error": "code", "message": "...", "details": {} }
```
- Pagination : `?page=1&limit=20` → `{ "items": [], "total": 0, "page": 1 }`
- IDs : UUID v4
- Dates : ISO 8601 UTC

## Router — exemple correct

```python
@router.post("/events", response_model=EventResponse)
async def create_event(
    body: CreateEventRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("events:write")),
    service: EventService = Depends(),
):
    return await service.create_event(body, current_user)
```

## Service — logique métier

- Valider règles métier ici, pas dans router
- Lever des exceptions domain (`EventNotFound`, `InsufficientPermission`)
- Transaction boundary ici

## Repository — accès DB

- Requêtes SQLAlchemy uniquement
- Pas de logique métier
- Méthodes explicites : `get_by_id`, `list_by_org`, `create`, `update`

## Redis

- Sessions refresh tokens
- Rate limiting counters
- Cache lecture fréquente (events publics) avec TTL

## Stripe

- `payments` module isolé
- Webhook handler dédié avec signature check
- Idempotency via table `processed_webhook_events`

## Tests

- `tests/modules/{domain}/test_service.py` — logique métier
- `tests/modules/{domain}/test_router.py` — endpoints (TestClient)
- Fixtures DB transaction rollback
