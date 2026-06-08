---
type: BMAD
version: 1.0
owner: CTO
project: YurPass
feature: FEATURE-AUTH-V1
ticket: TICKET-006A
status: PROPOSED
date: 2026-06-08
related_prd: docs/prd/yurpass-prd-v3.md
related_adr: docs/adr/ADR-002-auth-foundation.md
related_master: docs/bmad/FEATURE-AUTH-V1-MASTER.md
blocks:
  - TICKET-006B
  - TICKET-006C
---

# BUILD MODE ARCHITECTURE DEVELOPMENT

> Le PRD dit **QUOI** et **POURQUOI**.
> Le BMAD dit **COMMENT**.
> Premier sous-ticket exécutable de FEATURE-AUTH-V1.

---

# TICKET

```
[BMAD] Phase: SPRINT 1 — AUTH FOUNDATION
[FEATURE]: FEATURE-AUTH-V1
[TICKET]: TICKET-006A
[SLUG]: user-model-password-auth
[ROLE]: architecte-api
```

---

## CONTEXTE

**Business context :**

YurPass démarre le Sprint 1 Auth. Avant Magic Link, OTP, OAuth ou sessions JWT complètes, il faut poser la **couche identité** : modèle `User`, hashage sécurisé des mots de passe, inscription et connexion email/mot de passe. C'est la fondation pour participants, organisateurs, staff et admins.

**Current architecture :**

* Monorepo validé (ADR-001)
* Backend FastAPI modulaire avec `backend/app/modules/auth/` en placeholder
* PostgreSQL + Redis opérationnels via Docker Compose
* Alembic configuré, aucune migration métier auth
* `GET /api/health` seul endpoint actif
* Module auth : `router.py` vide, `models.py` vide

**Dependencies :**

| Prérequis | Statut |
|-----------|--------|
| Sprint 0 (TICKET-001 → 005) | Validé |
| PRD V3.1 | Validé (sections 15–20) |
| ADR-002 Auth Foundation | Accepté |
| FEATURE-AUTH-V1 MASTER | Versionné |

**Constraints :**

* Pattern obligatoire : `router → service → repository`
* Aucun rôle organisationnel dans `User`
* `OrganizationMember` : schéma placeholder uniquement
* Aucun secret en clair dans Git ou logs
* Compatible Docker DEV (`postgres`, `redis` hostnames)
* Python 3.13, uv, Ruff, Pytest

**Related PRD :** `docs/prd/yurpass-prd-v3.md` (V3.1)  
**Related ADR :** `docs/adr/ADR-002-auth-foundation.md`  
**Related MASTER :** `docs/bmad/FEATURE-AUTH-V1-MASTER.md`

---

## OBJECTIF

À la fin de ce ticket, le backend possède :

1. Le modèle de données `users` et `organization_members` (placeholder) avec migration Alembic appliquée.
2. Le hashage mot de passe **Argon2id** (fallback bcrypt documenté si contrainte technique).
3. `POST /api/auth/register` — création compte email/mot de passe.
4. `POST /api/auth/login` — validation credentials, mise à jour `last_login_at`.
5. Couche `service` + `repository` testée (unit + intégration).

Les **tokens JWT et refresh** sont explicitement reportés au **TICKET-006B**. Le login 006A retourne un DTO utilisateur public sans secrets ; la réponse prévoit une structure extensible pour les tokens (champs absents ou `null`, documentés).

---

## IMPORTANT

**Rules to follow :**

* `.claude/rules/architecte-api.md` / `.cursor/rules/architecte-api.mdc`
* `.claude/rules/seniordev.md` / `.cursor/rules/seniordev.mdc`
* ADR-001 monorepo modulaire
* `router → service → repository` — pas de logique métier dans le router
* Pas de commit sans validation humaine explicite

**Architecture constraints :**

* Modèles SQLAlchemy dans `app/modules/auth/models.py` (User) et `app/modules/organizations/models.py` (OrganizationMember placeholder) — ou sous-module auth si préféré, mais **OrganizationMember ne doit pas porter de logique métier**
* Enums partagés : `app/modules/auth/constants.py` ou `app/core/constants.py` (choix unique, documenté)
* Schémas Pydantic dans `app/modules/auth/schemas.py`
* Router monté sous `/api/auth` dans `app/main.py`
* Session DB via dépendance FastAPI existante ou à créer dans `app/db/session.py`

**Security constraints :**

* Argon2id avec paramètres sécurisés (time_cost ≥ 2, memory_cost ≥ 65536 KB recommandé)
* Jamais de `password` ou `password_hash` dans les réponses API
* Message d'erreur login **générique** : `"Invalid email or password"` (anti-énumération)
* Email normalisé en lowercase + trim avant persistance
* Contrainte UNIQUE sur `users.email`
* Register : statut initial `pending_verification`, `global_role = user`
* Pas de log du mot de passe en clair

**Performance constraints :**

* Index unique sur `users.email`
* Pas de N+1 sur register/login (requête unique par opération)

---

## INCLUS

1. **Enums** `UserStatus` et `GlobalRole` (valeurs ADR-002).
2. **Modèle SQLAlchemy `User`** avec tous les champs ADR-002.
3. **Modèle SQLAlchemy `OrganizationMember`** placeholder (sans endpoints, sans service).
4. **Migration Alembic** initiale auth (`alembic/versions/xxxx_auth_users.py`).
5. **Service password** : `hash_password()`, `verify_password()` (Argon2id).
6. **Repository** : `create_user()`, `get_by_email()`, `update_last_login()`.
7. **Service auth** : `register()`, `login()`.
8. **Endpoints** :
   * `POST /api/auth/register`
   * `POST /api/auth/login`
9. **Validation Pydantic** des payloads (email, password strength minimale).
10. **Tests** unitaires (hash) + intégration (register, login, doublon email, mauvais mot de passe).
11. **Dépendance** `argon2-cffi` (ou équivalent documenté) ajoutée via `uv add`.
12. **Documentation** courte dans `backend/README.md` — section Auth 006A.

---

## EXCLUSIONS STRICTES

1. JWT access token, refresh token, cookies session (**006B**).
2. `POST /api/auth/logout`, `POST /api/auth/refresh` (**006B**).
3. `GET /api/auth/me` (**006G**).
4. Email verification envoyée, `verify-email`, password reset (**006C**).
5. Magic Link, OTP, OAuth Google (**006D, 006E, 006F**).
6. Rate limiting Redis actif (**006G** — hooks/config prep acceptable, pas d'implémentation complète).
7. Turnstile, honeypot actifs (**006G**).
8. Audit logs persistants (**006G**).
9. Frontend web/admin (pages login/register).
10. Organizations CRUD, Events, Stripe, Passport, RBAC enforcement sur routes protégées.
11. Suspension admin, OAuth, envoi email réel (provider stub/log DEV uniquement si nécessaire).

---

## DATA IMPACT

| | |
|---|---|
| **Tables** | `users`, `organization_members` |
| **Migrations** | `alembic/versions/<rev>_auth_users_and_org_members_placeholder.py` |
| **Entities** | `User`, `OrganizationMember` |
| **Relationships** | `OrganizationMember.user_id` → `users.id` (FK). `organization_id` UUID **sans FK** vers table `organizations` (n'existe pas encore). |

### Table `users`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| `id` | UUID | PK, default `uuid4` |
| `email` | VARCHAR(320) | NOT NULL, UNIQUE, index |
| `email_verified_at` | TIMESTAMPTZ | NULLABLE |
| `password_hash` | VARCHAR(255) | NOT NULL |
| `full_name` | VARCHAR(255) | NULLABLE |
| `avatar_url` | VARCHAR(2048) | NULLABLE |
| `status` | ENUM `user_status` | NOT NULL, default `pending_verification` |
| `global_role` | ENUM `global_role` | NOT NULL, default `user` |
| `created_at` | TIMESTAMPTZ | NOT NULL, server default now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, on update |
| `last_login_at` | TIMESTAMPTZ | NULLABLE |

### Enums

**`user_status` :** `active`, `pending_verification`, `suspended`, `deleted`

**`global_role` :** `user`, `admin`, `super_admin`

### Table `organization_members` (placeholder)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| `id` | UUID | PK |
| `user_id` | UUID | FK → `users.id`, NOT NULL |
| `organization_id` | UUID | NOT NULL (pas de FK pour l'instant) |
| `role` | VARCHAR(50) | NOT NULL (valeurs futures ADR-002, non enforced) |
| `created_at` | TIMESTAMPTZ | NOT NULL |

Aucun endpoint ni seed sur cette table dans 006A.

---

## API IMPACT

| Endpoint | Method | Permission | Description |
|----------|--------|------------|-------------|
| `/api/auth/register` | POST | Public | Créer un compte email/mot de passe |
| `/api/auth/login` | POST | Public | Valider credentials |

**Schemas :** `app/modules/auth/schemas.py`

### `POST /api/auth/register`

**Request — `RegisterRequest`**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "Jean Dupont"
}
```

| Champ | Règles |
|-------|--------|
| `email` | EmailStr, normalisé lowercase |
| `password` | min 8 caractères, max 128 |
| `full_name` | optionnel, max 255 |

**Response — `RegisterResponse` (201)**

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "Jean Dupont",
    "status": "pending_verification",
    "global_role": "user",
    "email_verified_at": null,
    "created_at": "2026-06-08T12:00:00Z"
  }
}
```

**Erreurs :**

| Code | Cas |
|------|-----|
| 409 | Email déjà enregistré |
| 422 | Validation Pydantic |

---

### `POST /api/auth/login`

**Request — `LoginRequest`**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response — `LoginResponse` (200)**

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "Jean Dupont",
    "status": "pending_verification",
    "global_role": "user",
    "email_verified_at": null,
    "last_login_at": "2026-06-08T12:05:00Z"
  },
  "tokens": null
}
```

> **`tokens`** : réservé pour **006B**. Valeur `null` en 006A. Ne pas inventer de JWT factice.

**Erreurs :**

| Code | Cas |
|------|-----|
| 401 | Credentials invalides (message générique) |
| 403 | Compte `suspended` ou `deleted` |
| 422 | Validation Pydantic |

**Comportement login :**

* Vérifier email + password
* Refuser `suspended` / `deleted`
* Mettre à jour `last_login_at`
* Ne pas exposer si l'email existe ou non (même message 401)

---

## UI IMPACT

| Page | App | Route |
|------|-----|-------|
| — | — | — |

**Aucun impact UI dans ce ticket.**

Les formulaires login/register frontend seront traités dans un ticket UI dédié (hors scope 006A).

---

## SECURITY NOTES

| Domaine | Action |
|---------|--------|
| **RBAC** | Aucune route protégée dans 006A. `global_role` persisté uniquement. |
| **Validation** | Pydantic v2 — `RegisterRequest`, `LoginRequest`, `UserPublic` |
| **Rate limiting** | Reporté 006G. Prévoir constantes nommées si utile. |
| **Audit logs** | Reporté 006G. |
| **Password storage** | Argon2id via `argon2-cffi`. Jamais en clair. |
| **Anti-énumération** | Login : message unique. Register 409 acceptable (email pris). |
| **Threat analysis** | Timing attacks mitigés par verify Argon2 constant-time ; pas de fuite `password_hash` en API/logs. |

---

## TESTS REQUIRED

- [ ] **Unit** — `hash_password` / `verify_password` (round-trip, mauvais password)
- [ ] **Unit** — `AuthService.register` (mock repository)
- [ ] **Unit** — `AuthService.login` (mock repository)
- [ ] **Integration** — `POST /api/auth/register` → 201 + user en DB
- [ ] **Integration** — register doublon email → 409
- [ ] **Integration** — `POST /api/auth/login` succès → 200 + `last_login_at` mis à jour
- [ ] **Integration** — login mauvais password → 401 message générique
- [ ] **Integration** — login compte suspended → 403
- [ ] **Manual** — `curl` ou Swagger `/docs` en Docker DEV

**Fixtures :** DB de test (pytest + session transaction rollback ou DB dédiée documentée).

---

## ACCEPTANCE CRITERIA

- [ ] Migration Alembic appliquée sans erreur (`uv run alembic upgrade head`) sur PostgreSQL Docker.
- [ ] Tables `users` et `organization_members` créées avec contraintes documentées.
- [ ] `POST /api/auth/register` crée un user `pending_verification` / `global_role=user`.
- [ ] `POST /api/auth/register` refuse email dupliqué (409).
- [ ] `POST /api/auth/login` valide credentials et met à jour `last_login_at`.
- [ ] `POST /api/auth/login` retourne 401 générique si credentials invalides.
- [ ] `POST /api/auth/login` retourne 403 si `suspended` ou `deleted`.
- [ ] Aucun champ `password`, `password_hash` ou secret dans les réponses JSON.
- [ ] `tokens` absent ou `null` dans login (pas de JWT en 006A).
- [ ] `pytest` backend : tous les tests auth 006A passent.
- [ ] `uv run ruff check app tests` sans erreur.
- [ ] Aucune feature hors scope (OAuth, Magic Link, JWT, /me, frontend).
- [ ] Aucun secret commité.

---

## OUTPUT ATTENDU

**Files created :**

```
backend/app/modules/auth/constants.py          # UserStatus, GlobalRole enums
backend/app/modules/auth/password.py         # hash / verify Argon2id
backend/app/modules/organizations/models.py  # OrganizationMember placeholder
backend/alembic/versions/<rev>_auth_users.py
backend/tests/modules/auth/test_password.py
backend/tests/modules/auth/test_auth_api.py
```

**Files modified :**

```
backend/app/modules/auth/models.py
backend/app/modules/auth/schemas.py
backend/app/modules/auth/repository.py
backend/app/modules/auth/service.py
backend/app/modules/auth/router.py
backend/app/main.py                          # include auth router
backend/pyproject.toml                       # argon2-cffi
backend/uv.lock
backend/README.md                            # section Auth 006A
backend/tests/conftest.py                    # fixtures DB si nécessaire
```

**Commands executed :**

```bash
cd backend
uv add argon2-cffi
uv run alembic revision --autogenerate -m "auth users and org members placeholder"
uv run alembic upgrade head
uv run ruff check app tests
uv run pytest -q
```

**Validation proof :**

```bash
# Docker stack
docker compose up -d postgres redis backend

# Register
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@yurpass.local","password":"SecurePass123!","full_name":"Test User"}'

# Login
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@yurpass.local","password":"SecurePass123!"}'

# Tests
cd backend && uv run pytest tests/modules/auth/ -q
```

---

## REVIEW CHECKLIST

- [ ] Architecture — respect ADR-001, modules découplés, pas de logique dans router
- [ ] Security — hash Argon2id, anti-énumération login, pas de fuite password_hash
- [ ] Code Quality — Ruff clean, typage explicite, nommage cohérent
- [ ] Performance — index email, pas de requêtes superflues
- [ ] Accessibility — N/A (pas d'UI)
- [ ] Maintainability — OrganizationMember placeholder sans dette cachée
- [ ] ADR-002 — User sans rôle org-specific ; champs conformes

---

## COMMIT RULE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

Message suggéré après validation :

```
feat(auth): TICKET-006A — user model, register and login
```

---

## CTO GATE

Before merge on `main` or `develop` :

| Review | Required | Done |
|--------|----------|------|
| Architecture Review | YES | ☐ |
| Security Review | YES | ☐ |
| QA Review | YES | ☐ |
| CTO Approval | YES | ☐ |

**Branch :** `feature/sprint-1-ticket-006a-user-model-password-auth`

---

## LIEN TICKETS SUIVANTS

| Ticket | Dépend de 006A |
|--------|----------------|
| **006B** | Modèles User + login validé → JWT + refresh |
| **006C** | User + email → verification + reset |
| **006G** | User + global_role → `/me` + RBAC |
