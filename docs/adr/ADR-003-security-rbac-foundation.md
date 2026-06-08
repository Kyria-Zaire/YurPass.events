---
type: ADR
version: 1.0
status: PROPOSED
owner: CTO
project: YurPass
date: 2026-06-08
related_prd: PRD V3.1
---

# ADR-003 — Security & RBAC Foundation

## Statut

Proposé

## Contexte

FEATURE-AUTH-V1 possède désormais :

- register / login
- JWT access token
- refresh token rotatif
- logout
- /me
- email verification
- password reset
- Magic Link
- OTP Email
- Google OAuth

Avant de clôturer Auth V1, YurPass doit verrouiller la base sécurité transversale.

YurPass va gérer progressivement :

- utilisateurs
- organisateurs
- staff événementiel
- organisations
- billets
- paiements
- check-in
- Passport

La sécurité doit être traitée comme une couche plateforme, pas comme une feature isolée.

---

## Décision

YurPass introduit une fondation Security & RBAC composée de :

1. Global RBAC
2. dépendances FastAPI de protection
3. audit logs
4. rate limiting
5. sécurité sessions
6. headers HTTP sécurité
7. préparation Turnstile

---

## RBAC

### GlobalRole

Les rôles globaux restent :

- user
- admin
- super_admin

Ils sont portés par `users.global_role`.

### OrganizationRole futur

Les rôles organisationnels seront portés par `organization_members.role`.

Rôles prévus :

- owner
- admin
- staff
- viewer

Ils ne sont pas encore utilisés dans Auth V1.

---

## Règle critique

`global_role` ne doit jamais représenter un rôle dans une organisation.

Exemple :

- un `admin` global est admin YurPass
- un `admin` organisation est admin d'une boîte, d'un festival, d'un BDE

Ces deux notions restent séparées.

---

## Dépendances FastAPI

Créer des dépendances réutilisables :

- `require_authenticated`
- `require_global_roles`
- `require_super_admin`
- `require_active_user`

Elles doivent s'appuyer sur `get_current_user()`.

---

## Audit logs

Créer une table :

```txt
audit_logs
```

Champs minimum :

```txt
id
actor_user_id
action
resource_type
resource_id
ip_address
user_agent
metadata
created_at
```

Actions Auth V1 à logger :

- register_success
- login_success
- login_failed
- refresh_success
- refresh_failed
- logout
- password_reset_requested
- password_reset_success
- email_verification_requested
- email_verified
- magic_link_requested
- magic_link_success
- otp_requested
- otp_success
- google_oauth_success
- google_oauth_failed

Aucun secret ne doit être loggé.

---

## Rate limiting

Rate limiting obligatoire avant bêta sur :

- register
- login
- request-password-reset
- request-email-verification
- request-magic-link
- request-otp
- verify-otp
- verify-magic-link
- google callback
- refresh

Implémentation recommandée :

- SlowAPI ou middleware équivalent
- backend-only
- par IP
- par email quand disponible
- config désactivable en test

---

## Turnstile

Cloudflare Turnstile est préparé mais non activé globalement en Auth V1.

Objectif :

- prévoir config
- prévoir service de vérification
- ne pas bloquer les tests
- activation future par endpoint sensible

---

## Security Headers

Ajouter middleware HTTP pour :

- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: no-referrer
- Permissions-Policy minimal

CORS reste configuré séparément.

---

## Session Security

La rotation refresh existe déjà.

Ajouter durcissements :

- détecter réutilisation refresh token révoqué/rotated
- logger tentative suspecte
- pouvoir révoquer tous les tokens d'une session_id
- ne jamais exposer refresh token dans JSON
- maintenir access JWT court

---

## /me

`GET /api/auth/me` reste centré User.

Il peut évoluer vers :

```json
{
  "user": {},
  "permissions": []
}
```

mais ne doit pas retourner `OrganizationMember` tant que Sprint 2 n'est pas livré.

---

## Exclusions ADR-003

Ne pas implémenter maintenant :

- RBAC organisationnel complet
- permissions fines par organisation
- dashboard admin
- interface frontend
- Stripe security
- check-in roles
- KYC/KYB
- MFA
- SMS
- WebAuthn

---

## Conséquences

Avantages :

- auth prête pour bêta
- base sécurité transverse
- moins de dette sur paiements/check-in
- séparation claire entre global RBAC et organization RBAC
- auditabilité dès les premiers utilisateurs

Coûts :

- ticket 006G plus large
- nécessite plus de tests
- ajoute une table audit_logs
- nécessite choix de rate limiter

---

## Décision finale

Avant de clôturer FEATURE-AUTH-V1, YurPass doit livrer un ticket 006G dédié à :

- RBAC global
- security dependencies
- audit logs
- rate limiting
- session hardening
- security headers
- Turnstile preparation

Le RBAC organisationnel complet est explicitement reporté à FEATURE-ORGANIZATIONS-V1.
