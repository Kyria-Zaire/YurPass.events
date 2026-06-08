# Architecte API — YurPass

> Backend FastAPI · Modules métier · API REST
> Path-scoped : `.claude/rules/architecte-api.md` · Skill : `/architecte-api`

## Gouvernance

- Scope : `backend/**` uniquement sauf ticket explicite
- Pas de logique métier dans `router.py` — **jamais**
- Pas d'endpoint sans permission RBAC
- Pas de migration sans ticket data impact documenté

## Module obligatoire

```
backend/app/modules/{domain}/
├── router.py       # HTTP uniquement
├── service.py      # Business logic
├── models.py       # SQLAlchemy
├── schemas.py      # Pydantic in/out
├── repository.py   # DB access
└── permissions.py  # RBAC
```

## Conventions API

- Prefix `/api/v1/{resource}`
- UUID v4 · Dates ISO 8601 UTC
- Pagination `{ items, total, page }`
- Erreurs `{ error, message, details }`

## Stripe / Webhooks

Module `payments` isolé. Signature obligatoire. Idempotence via `event.id`. Scope tenant strict.
**Webhook hors scope → ABANDONNER le code.**

## Interdit

- SQL brut non paramétré
- Permissions en dur dans router
- Cross-module coupling direct (orchestrer via service)
- Init framework hors ticket dédié

## Checklist

- [ ] Service contient la logique métier
- [ ] Permissions vérifiées
- [ ] Schemas Pydantic pour in/out
- [ ] Tests service + router si applicable
