---
type: ADR
version: 1.0
status: ACCEPTED
owner: CTO
project: YurPass
date: 2026-06-08
related_prd: PRD V3.1
depends_on:
  - ADR-002-auth-foundation.md
  - ADR-003-security-rbac-foundation.md
blocks:
  - ADR-005-events-foundation
  - ADR-006-ticketing-foundation
  - ADR-007-payments-stripe-connect-foundation
  - ADR-008-check-in-foundation
---

# ADR-004 — Organizations Foundation

## Statut

Accepté

## Date

2026-06-08

## Contexte

FEATURE-AUTH-V1 est clôturée.

YurPass dispose désormais :

- d'un système d'authentification complet
- d'un RBAC global
- d'audit logs
- d'un système de sessions sécurisé
- d'une table `organization_members` placeholder

Le Sprint 2 introduit la première brique métier B2B de YurPass : **Organization**.

L'objectif est de permettre à des organisateurs, clubs, festivals, associations et structures événementielles de gérer leur présence sur YurPass.

Cette fondation servira ensuite à :

- Events
- Ticketing
- Check-in
- Stripe Connect
- KYC/KYB
- Reporting

---

## Décision

Créer une fondation Organizations V1 composée de :

- `organizations`
- `organization_members`
- RBAC organisationnel
- ownership
- auditabilité
- archive logique

La gestion des paiements est explicitement exclue et fera l'objet d'un ADR séparé.

---

## Modèle Organization

Table : `organizations`

| Champ | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| name | VARCHAR | |
| slug | VARCHAR UNIQUE | Génération automatique avec suffixe en cas de collision |
| type | ENUM | Voir OrganizationType |
| status | ENUM | Voir OrganizationStatus |
| description | TEXT nullable | |
| logo_url | VARCHAR nullable | |
| website_url | VARCHAR nullable | |
| city | VARCHAR nullable | |
| country | VARCHAR nullable | |
| created_by_user_id | UUID FK users | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

## OrganizationType

Valeurs :

- `nightclub`
- `festival`
- `association`
- `bde`
- `venue`
- `business`
- `independent_organizer`
- `other`

Le type prioritaire MVP est **`nightclub`**, car le réseau d'acquisition initial repose principalement sur les établissements nightlife.

---

## OrganizationStatus

Valeurs :

- `draft` — organisation créée mais non finalisée
- `active` — organisation utilisable
- `suspended` — organisation bloquée par YurPass
- `archived` — organisation désactivée sans suppression physique

**Règle :** aucune suppression physique n'est autorisée dans Organizations V1.

---

## OrganizationMember

La table existe déjà sous forme de placeholder. Sprint 2 l'active officiellement.

| Champ | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| user_id | UUID FK users | |
| organization_id | UUID FK organizations | |
| role | ENUM | Voir OrganizationRole |
| status | ENUM | Voir MemberStatus |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Contraintes :**

- `UNIQUE(user_id, organization_id)`
- `FK user_id → users.id`
- `FK organization_id → organizations.id`

---

## OrganizationRole

Valeurs :

- `owner`
- `admin`
- `staff`
- `viewer`

Les rôles métier spécialisés seront introduits plus tard (ex. `checkin_staff`, `marketing`, `event_manager`). Ils ne font **pas** partie de Organizations V1.

---

## MemberStatus

Valeurs :

- `active` — membre actif
- `suspended` — accès temporairement bloqué
- `left` — historique conservé, plus membre actif

---

## RBAC Organisationnel

**Principe fondamental :** `global_role` ≠ `organization_role`

Exemples :

- `global_role = super_admin` **n'implique pas** `organization_role = owner`
- Les permissions organisationnelles sont évaluées indépendamment

**Exception :** `super_admin` dispose d'un accès support global audité.

### Dépendance RBAC

Créer :

```python
require_org_roles(*allowed_roles: OrganizationRole)
```

Cette dépendance devient la **référence unique** pour les routes organisationnelles. Toutes les routes Organizations doivent passer par cette couche.

---

## Ownership

Lors de la création d'une organisation :

1. `created_by_user_id` est renseigné
2. une ligne `organization_members` est créée
3. le créateur devient automatiquement `owner`

**Règles :**

- Une organisation doit toujours posséder au moins un `owner`
- Un `owner` ne peut pas supprimer son propre dernier ownership sans transfert préalable
- Un utilisateur peut être `owner` de plusieurs organisations

---

## Permissions V1

| Rôle | Permissions |
|------|-------------|
| **owner** | Gestion complète, gestion membres, archivage |
| **admin** | Modification organisation, ajout membres, gestion membres limitée |
| **staff** | Lecture, opérations terrain futures |
| **viewer** | Lecture seule |

---

## Endpoints V1

### Organizations

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/organizations` | Créer une organisation |
| GET | `/api/organizations` | Lister les organisations accessibles |
| GET | `/api/organizations/{organization_id}` | Détail organisation |
| PATCH | `/api/organizations/{organization_id}` | Modifier organisation |
| DELETE | `/api/organizations/{organization_id}` | Archive logique |

### Members

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/organizations/{organization_id}/members` | Lister les membres |
| POST | `/api/organizations/{organization_id}/members` | Ajouter un membre (utilisateur existant) |
| PATCH | `/api/organizations/{organization_id}/members/{member_id}` | Modifier rôle ou statut |
| DELETE | `/api/organizations/{organization_id}/members/{member_id}` | Retrait membre (archive logique) |

`DELETE` correspond à une **archive logique**, pas à une suppression physique.

---

## Audit Logs

Événements obligatoires :

- `organization_created`
- `organization_updated`
- `organization_archived`
- `organization_suspended`
- `organization_member_added`
- `organization_member_role_updated`
- `organization_member_removed`

Toutes les actions critiques doivent être auditables.

---

## Super Admin

`global_role = super_admin` peut :

- consulter toutes les organisations
- consulter les membres
- suspendre une organisation
- intervenir en support

Toutes ces actions doivent être **auditées**.

---

## Invitations

Organizations V1 utilise l'**ajout direct d'un utilisateur existant**.

Les invitations tokenisées sont reportées à une version ultérieure.

---

## Slug

Le slug est **unique**.

Exemples en cas de collision :

```
club-xyz
club-xyz-2
club-xyz-3
```

---

## Exclusions

Hors scope Organizations V1 :

- Stripe Connect
- KYC/KYB
- Billing
- Events
- Ticketing
- Check-in
- Dashboard métier
- Passport
- Invitations tokenisées
- Frontend avancé

---

## ADR Futurs

| ADR | Sujet |
|-----|-------|
| ADR-005 | Events Foundation |
| ADR-006 | Ticketing Foundation |
| ADR-007 | Payments & Stripe Connect Foundation |
| ADR-008 | Check-in Foundation |

---

## Conséquences

Organizations devient la première entité métier centrale de YurPass.

Chaîne métier cible :

```
User → OrganizationMember → Organization → Event → Ticket → Check-in → Revenue
```

Toute l'économie de YurPass reposera sur cette relation.

Cette architecture doit rester stable et extensible pour les futures verticales : nightlife, festivals, associations, BDE, sport et business.
