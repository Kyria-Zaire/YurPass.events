# YurPass Backend

API FastAPI pour YurPass — identité, invitation, billetterie, check-in et accès aux expériences locales.

> **FEATURE-AUTH-V1** — clôturée (006A → 006G). **FEATURE-ORGANIZATIONS-V1** — clôturée (007A → 007G).

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
└── modules/             # Domaines métier
    ├── auth/            # ✅ FEATURE-AUTH-V1
    ├── audit/           # ✅ audit_logs (006G)
    ├── admin/           # ✅ diagnostic RBAC (006G)
    ├── users/
    ├── organizations/   # ✅ FEATURE-ORGANIZATIONS-V1
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

## Endpoints opérationnels

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Healthcheck applicatif |

L'ancien `/health` est supprimé — utiliser `/api/health` uniquement.

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

## Auth (FEATURE-AUTH-V1 — 006A → 006G)

| Endpoint | Auth | Description |
|----------|------|-------------|
| `POST /api/auth/register` | Public | Inscription email/mot de passe (Argon2id) |
| `POST /api/auth/login` | Public | Connexion — JWT access + cookie refresh HttpOnly |
| `POST /api/auth/refresh` | Cookie refresh | Rotation refresh token + nouvel access token |
| `POST /api/auth/logout` | Cookie refresh | Révocation refresh + suppression cookie |
| `GET /api/auth/me` | Bearer JWT | Profil utilisateur (`global_role`, pas d'org) |
| `POST /api/auth/request-email-verification` | Bearer JWT | Demande token vérification email |
| `POST /api/auth/verify-email` | Public (token) | Valider email via token opaque |
| `POST /api/auth/request-password-reset` | Public | Demande reset mot de passe |
| `POST /api/auth/reset-password` | Public (token) | Nouveau mot de passe via token |
| `POST /api/auth/request-magic-link` | Public | Demande lien magique passwordless |
| `POST /api/auth/verify-magic-link` | Public (token) | Connexion via magic link |
| `POST /api/auth/request-otp` | Public | Demande code OTP email (6 chiffres, 5 min) |
| `POST /api/auth/verify-otp` | Public | Connexion via code OTP email |
| `GET /api/auth/google` | Public | Démarre Google OAuth (redirect + cookie state) |
| `GET /api/auth/google/callback` | Public | Callback Google OAuth → session JWT |

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!","full_name":"User"}'
```

### Sécurité & RBAC (006G)

Couche transverse livrée avec ADR-003 (ACCEPTED) :

| Composant | Détail |
|-----------|--------|
| RBAC global | `require_global_roles(GlobalRole)`, `require_super_admin`, `require_active_user` |
| Audit logs | Table `audit_logs` — actions auth, aucun secret loggé |
| Rate limiting | Par IP + email sur flux sensibles (désactivable en test) |
| Security headers | `nosniff`, `DENY`, `no-referrer`, `Permissions-Policy` |
| Session hardening | Détection refresh reuse → révocation `session_id` |
| Turnstile | Préparation stub — non actif par défaut |

**Migrations auth head :** `20260608_005` (`audit_logs`)

Tables : `users`, `refresh_tokens`, `auth_tokens`, `audit_logs`.

### Admin — diagnostic RBAC

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/admin/rbac/diagnostic` | Bearer JWT + `super_admin` | Rôle global et permissions plateforme |

Réponse exemple :

```json
{
  "global_role": "super_admin",
  "permissions": ["admin.access", "admin.rbac.diagnostic", "admin.users.manage"]
}
```

Layering obligatoire : `admin/router.py` → `admin/service.py` → `admin/repository.py`.

```bash
curl http://localhost:8000/api/admin/rbac/diagnostic \
  -H "Authorization: Bearer <access_token_super_admin>"
```

### Variables d'environnement — sécurité

| Variable | Défaut | Description |
|----------|--------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Active le rate limiting backend (mettre `false` en tests locaux) |
| `TURNSTILE_ENABLED` | `false` | Active la vérification Cloudflare Turnstile (pré-bêta) |
| `TURNSTILE_SECRET_KEY` | `""` | Clé secrète Turnstile (requis si `TURNSTILE_ENABLED=true`) |
| `TURNSTILE_SITE_KEY` | `""` | Clé site Turnstile (frontend futur) |
| `JWT_SECRET` | `""` | **Obligatoire en production** — secret signature access token |

```bash
# Tests locaux — désactiver rate limit
RATE_LIMIT_ENABLED=false uv run pytest

# Dev — Turnstile désactivé (défaut)
TURNSTILE_ENABLED=false
```

Emails transactionnels : `dev_outbox` actif si `APP_ENV` ∈ `{dev, local}` (pas de provider SMTP en Auth V1).

## Organizations (FEATURE-ORGANIZATIONS-V1 — 007A → 007G)

Référence : `../docs/adr/ADR-004-organizations-foundation.md`

**Migrations head :** `20260608_007` (`organizations`, `organization_members` activée)

Tables : `organizations`, `organization_members` (FK `users` + `organizations`, UNIQUE `(user_id, organization_id)`, slug UNIQUE).

### Endpoints organization (007D)

| Method | Path | RBAC org |
|--------|------|----------|
| `POST` | `/api/organizations` | Utilisateur authentifié (devient `owner`) |
| `GET` | `/api/organizations` | Membre actif (liste ses orgs non archivées) |
| `GET` | `/api/organizations/{organization_id}` | `owner`, `admin`, `staff`, `viewer` |
| `PATCH` | `/api/organizations/{organization_id}` | `owner`, `admin` |
| `DELETE` | `/api/organizations/{organization_id}` | `owner` — archive logique (`status=archived`) |

### Endpoints members (007E)

| Method | Path | RBAC org |
|--------|------|----------|
| `GET` | `/api/organizations/{organization_id}/members` | `owner`, `admin`, `staff` — actifs par défaut ; `?include_inactive=true` **owner only** |
| `POST` | `/api/organizations/{organization_id}/members` | `owner`, `admin` — user existant uniquement |
| `PATCH` | `/api/organizations/{organization_id}/members/{member_id}` | `owner` — rôles `admin`/`staff`/`viewer` |
| `DELETE` | `/api/organizations/{organization_id}/members/{member_id}` | `owner` retire un autre membre ; `admin`/`staff`/`viewer` self-leave — **owner self-leave interdit** |

### Rôles organisationnels

| Rôle | Permissions clés |
|------|------------------|
| `owner` | CRUD org, archive, gestion membres, changement rôles |
| `admin` | Lecture/update org, liste/ajout membres |
| `staff` | Lecture org + membres |
| `viewer` | Lecture org uniquement |

RBAC via `require_org_roles(*OrganizationRole)` — jamais de `str` libre.

### Owner protection

- Créateur = `owner` actif automatiquement à la création
- `count_active_owners() >= 1` toujours
- Dernier owner : PATCH rôle et DELETE refusés (`last_owner_protected`)
- Owner **ne peut pas** self-leave (même multi-owner)
- Rôle `owner` : **pas** via POST/PATCH members API (futur transfert ownership)

### Archive logique

- `DELETE /api/organizations/{id}` → `status=archived` (pas de suppression physique)
- Orgs archivées exclues de `GET /api/organizations` pour les membres
- Les lignes `organization_members` sont **préservées**

### Audit (007F)

Actions : `organization_created`, `organization_updated`, `organization_archived`, `organization_member_added`, `organization_member_role_updated`, `organization_member_removed`, `organization_rbac_super_admin_bypass`.

Conventions : `resource_type=organization` ou `organization_member` ; metadata inclut `organization_id` (obligatoire sur actions member), `actor_role`, `target_user_id` si applicable.

### Exemple

```bash
curl -X POST http://localhost:8000/api/organizations \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Club Paris","type":"nightclub","city":"Paris","country":"FR"}'
```

## Roadmap modules

S1 Auth ✅ → S2 Organizations ✅ → S3 Events → S4 Invitations → S5 Ticketing/Stripe → ...

## Documentation projet

- ADR-001 Monorepo : `../docs/adr/ADR-001-monorepo-modulaire.md`
- ADR-002 Auth Foundation : `../docs/adr/ADR-002-auth-foundation.md`
- ADR-003 Security & RBAC : `../docs/adr/ADR-003-security-rbac-foundation.md`
- ADR-004 Organizations : `../docs/adr/ADR-004-organizations-foundation.md`
- Sécurité : `../docs/security/SECURITY_BASELINE.md`
- Gouvernance IA : `../docs/architecture/AI_WORKFLOW.md`
