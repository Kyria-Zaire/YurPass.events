---
type: BMAD
version: 2.0
owner: CTO
project: YurPass
feature: FEATURE-AUTH-V1
ticket: TICKET-006G
status: APPROVED_WITH_CONDITIONS
date: 2026-06-08
related_prd: docs/prd/yurpass-prd-v3.md
related_adr:
  - docs/adr/ADR-002-auth-foundation.md
  - docs/adr/ADR-003-security-rbac-foundation.md
related_master: docs/bmad/FEATURE-AUTH-V1-MASTER.md
depends_on:
  - TICKET-006A
  - TICKET-006B
  - TICKET-006C
  - TICKET-006D
  - TICKET-006E
  - TICKET-006F
blocks: FEATURE-AUTH-V1 closure
---

# BUILD MODE ARCHITECTURE DEVELOPMENT

# TICKET

```
[BMAD] Phase: SPRINT 1 — AUTH FOUNDATION
[FEATURE]: FEATURE-AUTH-V1
[TICKET]: TICKET-006G
[SLUG]: rbac-security-hardening
[ROLE]: architecte-api + reviewer-securite-code
```

---

## CONTEXTE

FEATURE-AUTH-V1 est fonctionnellement complète (006A → 006F).

ADR-003 impose de verrouiller la couche sécurité transverse avant clôture Auth V1 :

- RBAC global
- dépendances FastAPI
- audit logs
- rate limiting
- session hardening
- security headers
- préparation Turnstile

---

## OBJECTIF

Livrer la fondation Security & RBAC plateforme pour clôturer FEATURE-AUTH-V1.

---

## CONDITIONS CTO (v2 — obligatoires)

### 1. RBAC typing

`require_global_roles` doit accepter `GlobalRole`, pas `str`.

**Interdit :**

```python
def require_global_roles(*allowed_roles: str) -> ...
```

**Attendu :**

```python
def require_global_roles(*allowed_roles: GlobalRole) -> ...
```

### 2. Audit resource_id

`audit_logs.resource_id` = `VARCHAR(100)` ou `TEXT`, **pas UUID**.

Raison : audit futur Stripe / OAuth / QR / external IDs.

### 3. Admin diagnostic layering

L'endpoint diagnostic RBAC admin ne doit **pas** appeler `UserRepository` depuis le router.

**Obligatoire :** `router → service → repository`

Créer `app/modules/admin/service.py` minimal si nécessaire.

---

## INCLUS

### 1. Dépendances FastAPI (`app/modules/auth/permissions.py`)

- `require_authenticated` — alias sémantique de `get_current_user()`
- `require_global_roles(*allowed_roles: GlobalRole)`
- `require_super_admin` — raccourci `GlobalRole.SUPER_ADMIN`
- `require_active_user` — refuse `suspended` / `deleted`

Erreur : `PermissionDeniedError` (403).

### 2. Table `audit_logs`

Migration `20260608_005`.

| Colonne | Type |
|---------|------|
| id | UUID PK |
| actor_user_id | UUID FK users nullable |
| action | VARCHAR(50) |
| resource_type | VARCHAR(50) nullable |
| resource_id | VARCHAR(100) nullable |
| ip_address | VARCHAR(64) nullable |
| user_agent | TEXT nullable |
| metadata | JSONB nullable |
| created_at | TIMESTAMPTZ |

Module : `app/modules/audit/` (models, repository, service, constants).

Actions Auth V1 (ADR-003) — aucun secret loggé.

### 3. Rate limiting

- Backend-only, désactivable en test (`RATE_LIMIT_ENABLED=false`)
- Par IP ; par email quand disponible
- Endpoints : register, login, refresh, logout-adjacent flows, request-password-reset, request-email-verification, request-magic-link, request-otp, verify-otp, verify-magic-link, google callback

### 4. Security headers middleware

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy` minimal

### 5. Session hardening

- Détecter réutilisation refresh token révoqué/rotated
- Révoquer tous les tokens de la `session_id` en cas de reuse
- Logger audit `refresh_reuse_detected` / `refresh_failed`

### 6. Turnstile (préparation)

- Settings : `TURNSTILE_ENABLED`, `TURNSTILE_SECRET_KEY`, `TURNSTILE_SITE_KEY`
- Service `app/core/turnstile.py` — vérification no-op si désactivé
- Aucun blocage tests

### 7. Endpoint diagnostic RBAC admin

```
GET /api/admin/rbac/diagnostic
```

- Auth : `require_super_admin`
- Layering : `admin/router.py` → `admin/service.py` → `admin/repository.py`
- Réponse : rôle global + permissions plateforme (pas OrganizationMember)

---

## EXCLUSIONS

- RBAC organisationnel actif
- Dashboard admin UI
- MFA / SMS / WebAuthn
- Stripe security
- KYC/KYB
- Turnstile actif en production (prep only)

---

## TESTS REQUIS

1. `require_global_roles` accepte `GlobalRole` uniquement
2. `require_super_admin` refuse user/admin
3. `require_active_user` refuse suspended
4. audit log créé sur login_success
5. audit log sans secrets
6. `resource_id` accepte string non-UUID
7. rate limit actif quand enabled
8. rate limit désactivé en test
9. security headers présents
10. refresh reuse révoque session_id
11. admin diagnostic via service layer
12. admin diagnostic refuse non-super_admin

---

## ACCEPTANCE CRITERIA

1. Dépendances RBAC avec `GlobalRole` typé
2. Migration `audit_logs` avec `resource_id` VARCHAR(100)
3. Audit intégré aux flux auth
4. Rate limiting configurable
5. Security headers actifs
6. Refresh reuse detection
7. Turnstile prep sans blocage tests
8. Admin diagnostic respecte layering
9. Ruff OK
10. Pytest OK
11. Aucun commit code avant review CTO

---

## COMMIT RULE

- Commit BMAD autorisé après validation CTO conditions
- Commit code **interdit** avant review CTO ticket 006G
