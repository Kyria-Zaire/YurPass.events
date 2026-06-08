# YurPass Backend

API FastAPI pour YurPass — identité, invitation, billetterie, check-in et accès aux expériences locales.

> **TICKET-003** — Backend Foundation Layer. Aucune logique métier à ce stade.

## Stack

| Outil | Version |
|-------|---------|
| Python | 3.13+ |
| FastAPI | 0.115+ |
| Uvicorn | 0.32+ |
| SQLAlchemy | 2.x |
| Alembic | 1.14+ |
| Pydantic Settings | 2.6+ |
| PostgreSQL | via psycopg 3 |
| Redis | client préparé |
| uv | gestionnaire de paquets |
| Ruff | lint |
| Pytest | tests |

## Architecture

```
app/
├── main.py              # Point d'entrée FastAPI
├── core/                # Config, logging, constants
├── db/                  # SQLAlchemy base, session, health
├── shared/              # Exceptions, responses
└── modules/             # Domaines métier (placeholders)
    ├── auth/
    ├── users/
    ├── organizations/
    ├── events/
    ├── invitations/
    ├── tickets/
    ├── payments/
    ├── checkins/
    ├── passports/
    └── admin/
```

## Règle d'or : router → service → repository

```
router.py       → HTTP uniquement (validation entrée, appel service, réponse)
service.py      → Logique métier
repository.py   → Accès base de données
schemas.py      → Pydantic request/response
models.py       → SQLAlchemy models
permissions.py  → RBAC guards
```

**INTERDIT :** appeler la base de données directement depuis `router.py`.

```
router → service → repository → database   ✅
router → database                          ❌
```

## Endpoint actuel

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Healthcheck applicatif complet |

Exemple (local sans Postgres/Redis) :

```json
{
  "status": "ok",
  "service": "yurpass-backend",
  "version": "0.1.0",
  "environment": "dev",
  "database": "not_configured",
  "redis": "not_configured"
}
```

Avec Postgres/Redis disponibles : `database` et `redis` passent à `"connected"`.

Aucun secret (URL, credentials) n'est exposé dans la réponse.

L'ancien `/health` est supprimé — utiliser `/api/health` uniquement.

Aucun autre endpoint à ce stade.

## Développement local

```bash
# Installer les dépendances
uv sync

# Copier la config
cp .env.example .env.local

# Lancer le serveur
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/api/health
```

## Qualité

```bash
# Lint
uv run ruff check app tests

# Tests
uv run pytest
```

## Migrations (Alembic)

```bash
# Créer une migration (futurs tickets métier)
uv run alembic revision --autogenerate -m "description"

# Appliquer
uv run alembic upgrade head
```

## Auth (TICKET-006A / 006B)

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | Inscription email/mot de passe (Argon2id) |
| `POST /api/auth/login` | Connexion — JWT access + cookie refresh HttpOnly |
| `POST /api/auth/refresh` | Rotation refresh token + nouvel access token |
| `POST /api/auth/logout` | Révocation refresh + suppression cookie |
| `GET /api/auth/me` | Profil utilisateur (Bearer token) |
| `POST /api/auth/request-email-verification` | Demande token vérification email (Bearer) |
| `POST /api/auth/verify-email` | Valider email via token opaque |
| `POST /api/auth/request-password-reset` | Demande reset mot de passe |
| `POST /api/auth/reset-password` | Nouveau mot de passe via token |
| `POST /api/auth/request-magic-link` | Demande lien magique passwordless |
| `POST /api/auth/verify-magic-link` | Connexion via token magic link |
| `POST /api/auth/request-otp` | Demande code OTP email (6 chiffres) |
| `POST /api/auth/verify-otp` | Connexion via code OTP email |

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!","full_name":"User"}'
```

## Modules futurs

Les dossiers modules existent en placeholder. L'implémentation métier arrive sprint par sprint :

S1 Auth → S2 Organizations → S3 Events → S4 Invitations → S5 Ticketing/Stripe → ...

## Documentation projet

- ADR-001 Monorepo : `../docs/adr/ADR-001-monorepo-modulaire.md`
- Sécurité : `../docs/security/SECURITY_BASELINE.md`
- Gouvernance IA : `../docs/architecture/AI_WORKFLOW.md`
