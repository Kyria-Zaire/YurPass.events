---
type: ADR
version: 1.0
status: ACCEPTED
owner: CTO
project: YurPass
date: 2026-06-08
related_prd: PRD V3.1
---

# ADR-002 — Auth Foundation

## Statut

Accepté

## Date

Juin 2026

## Contexte

YurPass entre dans le Sprint 1 après validation du Sprint 0 et du PRD V3.1.

Le produit est une plateforme SaaS destinée principalement aux organisations événementielles : clubs, boîtes de nuit, concerts, festivals, associations, BDE et organisateurs indépendants.

Le système d'authentification doit supporter :

* participants
* organisateurs
* membres d'organisation
* staff check-in
* admins YurPass

L'authentification doit être sécurisée dès le départ car YurPass manipulera progressivement :

* comptes utilisateurs
* organisations
* billets
* paiements
* QR codes
* accès événementiels
* Stripe Connect
* KYC/KYB

---

## Décision

YurPass adopte une stratégie d'authentification hybride :

1. Email + mot de passe
2. Magic Link
3. OTP email
4. OAuth Google
5. JWT access token court
6. Refresh token sécurisé

La V1 doit préparer RBAC et Organizations sans implémenter encore toute la logique organisationnelle.

---

## Stratégie Auth

### Email + Password

Utilisé pour :

* inscription classique
* connexion classique
* admins internes
* organisateurs

Exigences :

* mot de passe hashé avec Argon2id ou bcrypt
* aucun mot de passe en clair
* validation email obligatoire
* rate limiting sur login/register/reset

---

### Magic Link

Utilisé pour :

* connexion passwordless
* expérience participant simplifiée
* récupération d'accès

Règles :

* token unique
* token hashé en base
* expiration courte
* usage unique
* invalidation après consommation
* rate limiting par email/IP

---

### OTP Email

Utilisé pour :

* vérification ponctuelle
* confirmation d'action sensible
* fallback passwordless

Règles :

* code court
* expiration courte
* stockage hashé
* nombre d'essais limité
* rate limiting

---

### OAuth Google

Utilisé pour :

* connexion rapide
* onboarding participant
* onboarding organisateur

Règles :

* redirect URI allowlist obligatoire
* aucun redirect dynamique non validé
* vérification email Google obligatoire
* création ou liaison de compte contrôlée
* audit des connexions OAuth

---

## Sessions

### Access Token

Format :

* JWT signé
* durée courte

Contenu minimal :

* user_id
* email
* role global
* token_type
* exp
* iat

Ne pas inclure :

* secrets
* données sensibles
* permissions détaillées volumineuses
* informations Stripe

---

### Refresh Token

Stratégie :

* token opaque recommandé
* stocké hashé en base
* rotation à chaque refresh
* révocation possible
* expiration longue mais limitée
* lié à un device/session

Stockage client :

* cookie HttpOnly
* Secure en production
* SameSite=Lax ou Strict selon contexte

---

## Modèle User

Champs minimum :

* id
* email
* email_verified_at
* password_hash
* full_name
* avatar_url
* status
* global_role
* created_at
* updated_at
* last_login_at

Statuts :

* active
* pending_verification
* suspended
* deleted

Rôles globaux :

* user
* admin
* super_admin

---

## OrganizationMember préparé

Même si Organizations sera implémenté dans un sprint dédié, Auth doit prévoir le lien futur :

* User peut appartenir à plusieurs Organizations
* OrganizationMember portera les rôles métier
* Les permissions organisationnelles ne doivent pas être hardcodées dans User

Rôles organisationnels prévus :

* owner
* admin
* manager
* checkin_staff
* marketing

Décision :

Le modèle User ne doit pas contenir de rôle organization-specific.

---

## RBAC

YurPass utilise deux niveaux de rôles :

### Global RBAC

Porté par User :

* user
* admin
* super_admin

### Organization RBAC

Porté par OrganizationMember :

* owner
* admin
* manager
* checkin_staff
* marketing

Règle :

Une route admin globale ne doit jamais dépendre d'un rôle organisationnel.

Une route organisationnelle ne doit jamais dépendre uniquement du global_role.

---

## Sécurité obligatoire

### Rate limiting

Obligatoire sur :

* register
* login
* magic link
* OTP
* password reset
* OAuth callback si applicable

### Cloudflare Turnstile

À prévoir pour :

* register
* login
* magic link request
* password reset request

Peut être activé progressivement par environnement.

### Honeypot

À prévoir sur les formulaires publics exposés aux bots.

### Audit logs

Obligatoires pour :

* login success/failure
* logout
* password reset
* magic link consumed
* OTP attempts
* OAuth login
* admin auth actions
* account suspension

---

## Endpoints prévus Sprint 1

Endpoints backend prévus :

* POST /api/auth/register
* POST /api/auth/login
* POST /api/auth/logout
* POST /api/auth/refresh
* POST /api/auth/request-magic-link
* POST /api/auth/verify-magic-link
* POST /api/auth/request-otp
* POST /api/auth/verify-otp
* GET /api/auth/me

`GET /api/auth/me` retourne uniquement les informations du User authentifié et son `global_role`, sans projection sur `OrganizationMember`.

OAuth Google peut être préparé mais pas forcément livré complet au premier ticket si trop large.

---

## Exclusions Sprint 1

Ne pas implémenter :

* Stripe Connect
* Organizations CRUD complet
* Events
* Tickets
* Check-in
* Passport
* KYC/KYB complet
* Admin dashboard
* Permissions fines par organisation
* Mobile Expo

---

## Conséquences

Avantages :

* auth solide dès le départ
* compatible SaaS B2B/B2C
* compatible Organizations
* compatible Stripe Connect futur
* compatible Staff Check-in
* compatible Admin YurPass

Coûts :

* plus long qu'un login basique
* nécessite tests sécurité
* nécessite gestion propre des tokens
* nécessite rate limiting

Risques :

* complexité prématurée si tout est livré en un seul ticket
* confusion entre global_role et organization role
* mauvaise gestion des refresh tokens
* OAuth mal sécurisé

Mitigations :

* découper Sprint 1 en plusieurs tickets
* commencer par modèle User + password auth
* ajouter Magic Link / OTP progressivement
* tester chaque flux séparément
* ne jamais mélanger OrganizationMember dans User

---

## Décision finale

Le Sprint 1 construira une Auth Foundation robuste, compatible avec le modèle Organization-first validé dans le PRD V3.1.

L'objectif n'est pas seulement de connecter un utilisateur.

L'objectif est de créer la couche d'identité qui supportera :

* participants
* organisateurs
* staff
* admins
* Organizations
* Stripe Connect
* Passport
