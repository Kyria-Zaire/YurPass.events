---
type: BMAD
kind: MASTER
version: 1.0
owner: CTO
project: YurPass
feature: FEATURE-AUTH-V1
sprint: 1
status: PROPOSED
date: 2026-06-08
related_prd: docs/prd/yurpass-prd-v3.md
related_adr: docs/adr/ADR-002-auth-foundation.md
ready_for_bmad: pending
---

# BMAD MASTER — FEATURE-AUTH-V1

> Document maître de découpage Sprint 1 — Auth Foundation.
> Chaque sous-ticket (006A → 006G) sera rédigé en BMAD détaillé **après validation CTO de ce master**.
> Aucun code sans PRD `Ready For BMAD: YES` + ADR-002 `ACCEPTED` + sous-ticket BMAD validé.

```
[BMAD] Phase: SPRINT 1 — AUTH FOUNDATION
[FEATURE]: FEATURE-AUTH-V1
[MASTER]: FEATURE-AUTH-V1-MASTER
[ROLE]: architecte-api + reviewer-securite-code
```

---

## 1. CONTEXTE

**Business context :**

YurPass entre en Sprint 1. L'authentification est la couche d'identité qui supportera participants, organisateurs, staff check-in et admins YurPass, ainsi que les futurs modules Organizations, Events, Ticketing, Passport et Stripe Connect.

**Current architecture :**

* Monorepo validé (ADR-001)
* Backend FastAPI modulaire (`backend/app/modules/auth/` en placeholder)
* PostgreSQL + Redis via Docker Compose
* Aucune auth implémentée à ce jour

**Dependencies :**

| Prérequis | Statut |
|-----------|--------|
| Sprint 0 (TICKET-001 → 005) | Validé |
| PRD V3.1 | En validation finale |
| ADR-002 Auth Foundation | Accepté |

**Constraints :**

* `router → service → repository`
* RBAC global uniquement dans Sprint 1 (pas de permissions organisationnelles actives)
* `OrganizationMember` préparé en schéma, pas de CRUD Organizations
* Aucun secret en clair dans Git
* Rate limiting + audit logs obligatoires sur les flux auth

**Related PRD :** `docs/prd/yurpass-prd-v3.md` (V3.1)  
**Related ADR :** `docs/adr/ADR-002-auth-foundation.md`

---

## 2. OBJECTIF GLOBAL

Livrer une **Auth Foundation** complète, sécurisée et testée, découpée en 7 sous-tickets indépendants et séquentiels, sans big-bang.

À la fin de **006G**, le backend expose tous les endpoints ADR-002 (sauf OAuth Google si reporté explicitement dans 006F), avec sessions JWT + refresh, RBAC global, audit et rate limiting.

---

## 3. ORDRE D'EXÉCUTION

```
006A ──► 006B ──► 006C ──► 006D ──► 006E ──► 006F ──► 006G
 User      JWT/      Email     Magic     OTP       OAuth     RBAC +
 model     refresh   verify    Link                Google    security
 + pwd               + reset
```

Chaque ticket doit être **validé CTO** avant le suivant.

---

## 4. DÉCOUPAGE SOUS-TICKETS

### TICKET-006A — User Model & Password Auth Core

| Champ | Valeur |
|-------|--------|
| **Slug** | `user-model-password-auth` |
| **Rôle** | architecte-api |
| **Dépend de** | Sprint 0 |
| **Bloque** | 006B, 006C |

**Objectif :** Poser le modèle de données User, migrations Alembic, hashage mot de passe (Argon2id ou bcrypt), inscription et connexion email/mot de passe.

**Inclus :**

* Table `users` (champs ADR-002 : id, email, email_verified_at, password_hash, full_name, avatar_url, status, global_role, timestamps, last_login_at)
* Enums `UserStatus`, `GlobalRole`
* Table `organization_members` **placeholder** (schéma minimal, sans logique métier)
* Migration Alembic initiale auth
* `POST /api/auth/register`
* `POST /api/auth/login` (retourne tokens — voir 006B pour implémentation refresh complète, ou stub session minimale documenté)
* Repository + service + router auth
* Tests unitaires hash + register/login

**Exclusions :**

* Magic Link, OTP, OAuth
* Email réel (provider peut être stub/log en dev)
* Turnstile actif
* Frontend

**Endpoints :**

* `POST /api/auth/register`
* `POST /api/auth/login`

---

### TICKET-006B — JWT Access & Refresh Sessions

| Champ | Valeur |
|-------|--------|
| **Slug** | `jwt-refresh-sessions` |
| **Rôle** | architecte-api + reviewer-securite-code |
| **Dépend de** | 006A |
| **Bloque** | 006C → 006G |

**Objectif :** Sessions sécurisées JWT court + refresh token opaque rotatif.

**Inclus :**

* Table `refresh_tokens` (hashé, device/session, révocation, expiration)
* JWT access signé (user_id, email, global_role, token_type, exp, iat)
* `POST /api/auth/refresh` (rotation obligatoire)
* `POST /api/auth/logout` (révocation refresh)
* Cookie HttpOnly pour refresh (configurable dev/prod)
* Dependency `get_current_user` pour routes protégées
* Tests rotation + révocation + expiration

**Exclusions :**

* Permissions organisationnelles
* OAuth
* Données sensibles dans le JWT (Stripe, etc.)

**Endpoints :**

* `POST /api/auth/refresh`
* `POST /api/auth/logout`

---

### TICKET-006C — Email Verification & Password Reset

| Champ | Valeur |
|-------|--------|
| **Slug** | `email-verification-password-reset` |
| **Rôle** | architecte-api |
| **Dépend de** | 006A, 006B |
| **Bloque** | 006D (optionnel) |

**Objectif :** Validation email obligatoire et réinitialisation mot de passe sécurisée.

**Inclus :**

* Table `email_verification_tokens` (hashé, expiration, usage unique)
* Table `password_reset_tokens` (hashé, expiration, usage unique)
* `POST /api/auth/verify-email` (ou flow intégré register)
* `POST /api/auth/request-password-reset`
* `POST /api/auth/reset-password`
* Rate limiting sur request-reset
* Mise à jour `email_verified_at` et `UserStatus`
* Audit logs : password reset request/success
* Service email abstrait (interface + impl dev log)

**Exclusions :**

* Magic Link (006D)
* Frontend formulaires

**Endpoints :**

* `POST /api/auth/request-password-reset`
* `POST /api/auth/reset-password`
* `POST /api/auth/verify-email` (si distinct du register)

---

### TICKET-006D — Magic Link

| Champ | Valeur |
|-------|--------|
| **Slug** | `magic-link-auth` |
| **Rôle** | architecte-api |
| **Dépend de** | 006B |
| **Bloque** | — |

**Objectif :** Connexion passwordless par Magic Link.

**Inclus :**

* Table `magic_link_tokens` (hashé, expiration courte, usage unique)
* `POST /api/auth/request-magic-link`
* `POST /api/auth/verify-magic-link`
* Rate limiting email/IP
* Invalidation après consommation
* Audit : magic link consumed
* Création compte ou connexion compte existant (règle documentée)

**Exclusions :**

* OTP (006E)
* OAuth (006F)

**Endpoints :**

* `POST /api/auth/request-magic-link`
* `POST /api/auth/verify-magic-link`

---

### TICKET-006E — OTP Email

| Champ | Valeur |
|-------|--------|
| **Slug** | `otp-email-auth` |
| **Rôle** | architecte-api |
| **Dépend de** | 006B |
| **Bloque** | — |

**Objectif :** Vérification ponctuelle et fallback passwordless par OTP email.

**Inclus :**

* Table `otp_codes` (hashé, expiration courte, max attempts)
* `POST /api/auth/request-otp`
* `POST /api/auth/verify-otp`
* Rate limiting + lockout après N échecs
* Audit : OTP attempts

**Exclusions :**

* SMS OTP
* 2FA TOTP (hors scope V1)

**Endpoints :**

* `POST /api/auth/request-otp`
* `POST /api/auth/verify-otp`

---

### TICKET-006F — OAuth Google

| Champ | Valeur |
|-------|--------|
| **Slug** | `oauth-google` |
| **Rôle** | architecte-api + reviewer-securite-code |
| **Dépend de** | 006B |
| **Bloque** | — |

**Objectif :** Connexion Google sécurisée avec liaison/création de compte contrôlée.

**Inclus :**

* Table `oauth_accounts` (provider, provider_user_id, user_id)
* `GET /api/auth/google` (redirect)
* `GET /api/auth/google/callback`
* State CSRF + redirect URI allowlist
* Vérification `email_verified` Google
* Liaison compte existant ou création
* Audit : OAuth login

**Exclusions (report possible avec accord CTO) :**

* Autres providers OAuth
* Frontend callback UI (peut être ticket séparé frontend)

**Note ADR-002 :** Peut être préparé mais pas forcément livré complet si trop large — documenter le périmètre exact dans le BMAD détaillé 006F.

---

### TICKET-006G — RBAC Global, /me & Security Hardening

| Champ | Valeur |
|-------|--------|
| **Slug** | `rbac-me-security-hardening` |
| **Rôle** | architecte-api + reviewer-securite-code |
| **Dépend de** | 006A → 006F (selon périmètre OAuth) |
| **Bloque** | Sprint 1 clôture Auth |

**Objectif :** Finaliser la couche identité : endpoint `/me`, RBAC global, rate limiting unifié, audit logs, hooks Turnstile/honeypot.

**Inclus :**

* `GET /api/auth/me` — User authentifié + `global_role` **uniquement** (pas de projection OrganizationMember)
* Decorators/deps RBAC global (`user`, `admin`, `super_admin`)
* Middleware ou utilitaire rate limiting Redis (register, login, magic, OTP, reset, OAuth)
* Table `audit_logs` auth (login success/failure, logout, reset, magic, OTP, OAuth, suspension)
* Hooks Turnstile (vérif optionnelle par env, désactivé en dev)
* Champ honeypot documenté pour futurs formulaires
* Tests intégration RBAC + `/me`
* Revue sécurité `/reviewer-securite-code`

**Exclusions :**

* Organization RBAC actif
* Admin dashboard
* Suspension UI admin (API prep only si minimal)

**Endpoints :**

* `GET /api/auth/me`

---

## 5. MATRICE ENDPOINTS → TICKETS

| Endpoint | Ticket |
|----------|--------|
| `POST /api/auth/register` | 006A |
| `POST /api/auth/login` | 006A (+ sessions 006B) |
| `POST /api/auth/logout` | 006B |
| `POST /api/auth/refresh` | 006B |
| `POST /api/auth/request-password-reset` | 006C |
| `POST /api/auth/reset-password` | 006C |
| `POST /api/auth/verify-email` | 006C |
| `POST /api/auth/request-magic-link` | 006D |
| `POST /api/auth/verify-magic-link` | 006D |
| `POST /api/auth/request-otp` | 006E |
| `POST /api/auth/verify-otp` | 006E |
| `GET /api/auth/google` | 006F |
| `GET /api/auth/google/callback` | 006F |
| `GET /api/auth/me` | 006G |

---

## 6. EXCLUSIONS GLOBALES (FEATURE-AUTH-V1)

Conformes ADR-002 — **interdits dans tous les sous-tickets 006A-G** :

* Stripe Connect
* Organizations CRUD complet
* Events, Tickets, Check-in, Passport
* KYC/KYB complet
* Admin dashboard
* Permissions fines par organisation (Organization RBAC actif)
* Mobile Expo
* Frontend auth UI (sauf mention explicite dans un ticket futur)

---

## 7. MODÈLE DE DONNÉES CIBLE (VUE MASTER)

| Table | Ticket création | Rôle |
|-------|-----------------|------|
| `users` | 006A | Identité principale |
| `organization_members` | 006A | Placeholder futur Organizations |
| `refresh_tokens` | 006B | Sessions refresh |
| `email_verification_tokens` | 006C | Vérification email |
| `password_reset_tokens` | 006C | Reset mot de passe |
| `magic_link_tokens` | 006D | Magic Link |
| `otp_codes` | 006E | OTP email |
| `oauth_accounts` | 006F | Liaison Google |
| `audit_logs` | 006G | Traçabilité auth |

---

## 8. CRITÈRES DE CLÔTURE FEATURE-AUTH-V1

- [ ] Les 7 sous-tickets 006A → 006G validés CTO
- [ ] Tous les endpoints ADR-002 opérationnels (OAuth selon périmètre 006F)
- [ ] `GET /api/auth/me` sans projection OrganizationMember
- [ ] Rate limiting actif sur tous les flux sensibles
- [ ] Audit logs auth en place
- [ ] `pytest` backend vert sur module auth
- [ ] Revue sécurité passée sur 006B, 006F, 006G
- [ ] Aucun secret commité
- [ ] Documentation `backend/README.md` section auth à jour

---

## 9. BRANCHING

```
feature/sprint-1-ticket-006a-user-model-password-auth
feature/sprint-1-ticket-006b-jwt-refresh-sessions
feature/sprint-1-ticket-006c-email-verification-password-reset
feature/sprint-1-ticket-006d-magic-link-auth
feature/sprint-1-ticket-006e-otp-email-auth
feature/sprint-1-ticket-006f-oauth-google
feature/sprint-1-ticket-006g-rbac-me-security-hardening
```

---

## 10. PROCHAINES ÉTAPES

1. Validation CTO de ce **BMAD MASTER**
2. Marquer PRD V3.1 `Ready For BMAD: YES`
3. Rédiger **TICKET-006A** en BMAD détaillé (premier ticket exécutable)
4. Exécution 006A → validation → 006B → …

---

## COMMIT RULE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

---

## CTO GATE (MASTER)

| Review | Required | Done |
|--------|----------|------|
| Découpage tickets cohérent | YES | ☐ |
| Alignement ADR-002 | YES | ☐ |
| Alignement PRD V3.1 | YES | ☐ |
| Sécurité (pas de big-bang) | YES | ☐ |
| CTO Approval MASTER | YES | ☐ |
