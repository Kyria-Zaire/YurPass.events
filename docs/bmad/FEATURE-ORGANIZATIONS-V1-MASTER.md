---
type: BMAD
kind: MASTER
version: 1.0
owner: CTO
project: YurPass
feature: FEATURE-ORGANIZATIONS-V1
sprint: 2
status: PROPOSED
date: 2026-06-08
related_prd: docs/prd/yurpass-prd-v3.md
related_adr: docs/adr/ADR-004-organizations-foundation.md
depends_on:
  - FEATURE-AUTH-V1
ready_for_bmad: pending
---

# BMAD MASTER — FEATURE-ORGANIZATIONS-V1

> Document maître de découpage Sprint 2 — Organizations Foundation.
> Chaque sous-ticket (007A → 007G) sera rédigé en BMAD détaillé **après validation CTO de ce master**.
> Aucun code sans ADR-004 `ACCEPTED` + sous-ticket BMAD validé.

```
[BMAD] Phase: SPRINT 2 — FEATURE-ORGANIZATIONS-V1
[FEATURE]: FEATURE-ORGANIZATIONS-V1
[MASTER]: FEATURE-ORGANIZATIONS-V1-MASTER
[ROLE]: Product Architect + Backend Architect + Security Reviewer
```

---

## 1. CONTEXTE

**Business context :**

FEATURE-AUTH-V1 est clôturée. ADR-004 Organizations Foundation est **ACCEPTED**.

YurPass entre dans son **premier sprint métier B2B**. Le client principal est **Organization**. Le canal d'acquisition initial est **Achraf / nightlife** — le type prioritaire MVP est `nightclub`.

**Current architecture :**

- Monorepo validé (ADR-001)
- Auth complète : register, login, sessions JWT+refresh, OAuth Google, RBAC global, audit logs (FEATURE-AUTH-V1)
- Table `organization_members` **placeholder** (006A) — sans FK `organizations`, sans logique métier
- Module `organizations/` en placeholder backend
- Pattern obligatoire : `router → service → repository`

**Dependencies :**

| Prérequis | Statut |
|-----------|--------|
| FEATURE-AUTH-V1 (006A → 006G) | Clôturée |
| ADR-003 Security & RBAC | ACCEPTED |
| ADR-004 Organizations Foundation | ACCEPTED |
| PRD V3.1 | Référence produit |

**Constraints :**

- `global_role` ≠ `organization_role` — jamais mélangés
- `require_org_roles(*allowed_roles: OrganizationRole)` = référence unique routes org
- Archive logique uniquement — pas de suppression physique
- Ownership : min. 1 `owner` par organisation
- Super admin : bypass support global **audité**
- Ajout membre = utilisateur existant uniquement (pas d'invitations tokenisées)

**Related PRD :** `docs/prd/yurpass-prd-v3.md` (V3.1)  
**Related ADR :** `docs/adr/ADR-004-organizations-foundation.md`

---

## 2. OBJECTIF GLOBAL

Découper **FEATURE-ORGANIZATIONS-V1** en tickets **séquentiels**, **testables** et **validables CTO**, sans big-bang.

À la fin de **007G**, le backend expose tous les endpoints ADR-004, avec RBAC organisationnel, ownership, audit et archive logique.

---

## 3. ORDRE D'EXÉCUTION

```
007A ──► 007B ──► 007C ──► 007D ──► 007E ──► 007F ──► 007G
 Orgs      Members    Org       CRUD      Members    Audit     QA
 model     activation RBAC      org       mgmt       logs      hardening
 + mig                deps       endpoints endpoints
```

Chaque ticket doit être **validé CTO** avant le suivant.

---

## 4. DÉCOUPAGE OFFICIEL

### TICKET-007A — Organizations Foundation

| Champ | Valeur |
|-------|--------|
| **Slug** | `organizations-foundation` |
| **Rôle** | Backend Architect |
| **Dépend de** | FEATURE-AUTH-V1 |
| **Bloque** | 007B → 007G |

**Objectif :** Poser le modèle de données `organizations` et la couche repository — sans endpoints publics complets.

**Inclus :**

- Table `organizations` (champs ADR-004)
- Enums `OrganizationType`, `OrganizationStatus`
- Modèle SQLAlchemy `Organization`
- `OrganizationRepository` foundation (CRUD interne, pas exposé HTTP)
- Migration Alembic `organizations`
- Tests modèle + repository (unitaires)

**Exclusions :**

- Endpoints HTTP publics complets
- `organization_members` activation (007B)
- RBAC organisationnel (007C)

---

### TICKET-007B — Organization Members Activation

| Champ | Valeur |
|-------|--------|
| **Slug** | `organization-members-activation` |
| **Rôle** | Backend Architect |
| **Dépend de** | 007A |
| **Bloque** | 007C → 007G |

**Objectif :** Activer officiellement `organization_members` — refactor du placeholder 006A.

**Inclus :**

- Refactor `organization_members` placeholder → schéma cible ADR-004
- FK `organization_id → organizations.id`
- Enums `OrganizationRole`, `MemberStatus`
- Contrainte `UNIQUE(user_id, organization_id)`
- Indexes performance (`organization_id`, `user_id`)
- Colonnes `status`, `updated_at`
- Migration Alembic (alter/create selon état placeholder)
- `OrganizationMemberRepository` foundation
- Tests contraintes + FK

**Exclusions :**

- Endpoints HTTP members complets (007E)
- RBAC deps (007C)

---

### TICKET-007C — Organization RBAC

| Champ | Valeur |
|-------|--------|
| **Slug** | `organization-rbac` |
| **Rôle** | Backend Architect + Security Reviewer |
| **Dépend de** | 007A, 007B |
| **Bloque** | 007D, 007E |

**Objectif :** Couche permissions organisationnelles — référence unique pour toutes les routes org.

**Inclus :**

- `require_org_roles(*allowed_roles: OrganizationRole)` — typage enum, pas `str`
- Matrice permissions V1 : `owner`, `admin`, `staff`, `viewer`
- `super_admin` support bypass audité (global_role, pas organization_role implicite)
- `OrganizationPermissions` / constants module
- Résolution membership : user authentifié + `organization_id` → membre actif
- `PermissionDeniedError` sur accès refusé
- Tests permissions exhaustifs (par rôle, super_admin, non-membre, suspended)

**Exclusions :**

- Endpoints CRUD (007D/007E)
- Modification module `auth/` sauf import deps si nécessaire

**Règle critique :**

```python
# Interdit
require_org_roles("owner")

# Attendu
require_org_roles(OrganizationRole.OWNER)
```

---

### TICKET-007D — Organizations CRUD

| Champ | Valeur |
|-------|--------|
| **Slug** | `organizations-crud` |
| **Rôle** | Backend Architect |
| **Dépend de** | 007A, 007B, 007C |
| **Bloque** | 007E, 007F |

**Objectif :** Exposer le CRUD organisation avec ownership automatique à la création.

**Inclus :**

- `POST /api/organizations` — création + `created_by_user_id` + membre `owner` auto
- `GET /api/organizations` — liste filtrée (membres actifs + super_admin all)
- `GET /api/organizations/{organization_id}` — détail
- `PATCH /api/organizations/{organization_id}` — modification (owner/admin selon matrice)
- `DELETE /api/organizations/{organization_id}` — **archive logique** (`status=archived`)
- Génération slug unique avec suffixe collision (`club-xyz`, `club-xyz-2`, …)
- `OrganizationService` + `organizations/router.py`
- Layering `router → service → repository`
- Tests intégration CRUD + ownership création

**Exclusions :**

- Members endpoints (007E)
- Audit events (007F) — hooks préparés OK, intégration complète en 007F
- Suspension super_admin (peut être 007D ou 007F — documenter dans BMAD 007D)

**Endpoints :**

| Méthode | Route |
|---------|-------|
| POST | `/api/organizations` |
| GET | `/api/organizations` |
| GET | `/api/organizations/{organization_id}` |
| PATCH | `/api/organizations/{organization_id}` |
| DELETE | `/api/organizations/{organization_id}` |

---

### TICKET-007E — Members Management

| Champ | Valeur |
|-------|--------|
| **Slug** | `organization-members-management` |
| **Rôle** | Backend Architect |
| **Dépend de** | 007B, 007C, 007D |
| **Bloque** | 007F, 007G |

**Objectif :** Gestion des membres — ajout direct utilisateur existant, protection ownership.

**Inclus :**

- `GET /api/organizations/{organization_id}/members`
- `POST /api/organizations/{organization_id}/members` — ajout user existant par email ou user_id
- `PATCH /api/organizations/{organization_id}/members/{member_id}` — rôle / statut
- `DELETE /api/organizations/{organization_id}/members/{member_id}` — retrait logique (`status=left`)
- **Interdiction** de retirer le dernier `owner` sans transfert préalable
- Transfert ownership documenté (PATCH role owner → autre membre avant DELETE owner)
- Permissions selon matrice 007C
- Tests : dernier owner, multi-org, suspended member

**Exclusions :**

- Invitations tokenisées
- Recherche utilisateurs publique non authentifiée

**Endpoints :**

| Méthode | Route |
|---------|-------|
| GET | `/api/organizations/{organization_id}/members` |
| POST | `/api/organizations/{organization_id}/members` |
| PATCH | `/api/organizations/{organization_id}/members/{member_id}` |
| DELETE | `/api/organizations/{organization_id}/members/{member_id}` |

---

### TICKET-007F — Organization Audit

| Champ | Valeur |
|-------|--------|
| **Slug** | `organization-audit` |
| **Rôle** | Backend Architect + Security Reviewer |
| **Dépend de** | 007D, 007E |
| **Bloque** | 007G |

**Objectif :** Traçabilité complète des actions organisationnelles via `audit_logs` existant.

**Inclus :**

- Extension `AuditAction` (ou module audit org) — événements ADR-004 :
  - `organization_created`
  - `organization_updated`
  - `organization_archived`
  - `organization_suspended`
  - `organization_member_added`
  - `organization_member_role_updated`
  - `organization_member_removed`
- Intégration `AuditService` dans `OrganizationService` / `MemberService`
- `resource_id` VARCHAR(100) — IDs org/member/externes
- Aucun secret en metadata
- Actions `super_admin` auditées distinctement
- Tests : audit créé sur create org, archive, member add/remove

**Exclusions :**

- Nouvelle table audit (réutiliser `audit_logs` 006G)

---

### TICKET-007G — QA Hardening

| Champ | Valeur |
|-------|--------|
| **Slug** | `organizations-qa-hardening` |
| **Rôle** | Backend Architect + Security Reviewer |
| **Dépend de** | 007A → 007F |
| **Bloque** | Sprint 2 clôture Organizations |

**Objectif :** Validation finale, documentation, cohérence — clôture FEATURE-ORGANIZATIONS-V1.

**Inclus :**

- Matrice RBAC complète testée (tous rôles × toutes routes)
- Ownership protection (dernier owner, multi-owner, transfert)
- Slug collisions (`name` identique → suffixes)
- Archive behavior (org archived → accès refusé, members préservés)
- Audit consistency (chaque action critique = 1 log)
- Migration check Alembic head documenté
- `backend/README.md` section Organizations
- Ruff OK + pytest vert module organizations
- Rapport clôture FEATURE-ORGANIZATIONS-V1

**Exclusions :**

- Nouvelles features hors ADR-004

---

## 5. MATRICE ENDPOINTS → TICKETS

| Endpoint | Ticket |
|----------|--------|
| `POST /api/organizations` | 007D |
| `GET /api/organizations` | 007D |
| `GET /api/organizations/{organization_id}` | 007D |
| `PATCH /api/organizations/{organization_id}` | 007D |
| `DELETE /api/organizations/{organization_id}` | 007D |
| `GET /api/organizations/{organization_id}/members` | 007E |
| `POST /api/organizations/{organization_id}/members` | 007E |
| `PATCH /api/organizations/{organization_id}/members/{member_id}` | 007E |
| `DELETE /api/organizations/{organization_id}/members/{member_id}` | 007E |

---

## 6. RÈGLES STRICTES (FEATURE-ORGANIZATIONS-V1)

**Interdit dans tous les sous-tickets 007A → 007G :**

- Implémenter Stripe Connect
- Implémenter KYC/KYB
- Implémenter Events
- Implémenter Ticketing
- Implémenter Check-in
- Créer du frontend
- Créer des invitations tokenisées
- Modifier Auth sauf dépendances nécessaires (deps RBAC, audit)
- Mélanger `global_role` et `organization_role`

---

## 7. MODÈLE DE DONNÉES CIBLE (VUE MASTER)

| Table / Enum | Ticket | Rôle |
|--------------|--------|------|
| `organizations` | 007A | Entité métier centrale B2B |
| `OrganizationType` | 007A | Typologie (nightclub MVP) |
| `OrganizationStatus` | 007A | Lifecycle (draft → archived) |
| `organization_members` (activation) | 007B | Appartenance user ↔ org |
| `OrganizationRole` | 007B | owner, admin, staff, viewer |
| `MemberStatus` | 007B | active, suspended, left |
| Audit events org | 007F | Traçabilité via `audit_logs` |

---

## 8. ACCEPTANCE FEATURE — CRITÈRES DE CLÔTURE

**FEATURE-ORGANIZATIONS-V1** est clôturée **uniquement si** :

- [ ] `organizations` existe et est migrée
- [ ] `organization_members` est activée proprement (FK, enums, UNIQUE)
- [ ] RBAC organisationnel fonctionne (`require_org_roles`)
- [ ] CRUD organization fonctionne (5 endpoints)
- [ ] Members management fonctionne (4 endpoints)
- [ ] Audit logs organisationnels fonctionnent (7 événements)
- [ ] Tests permissions verts
- [ ] Ruff OK
- [ ] Migrations Alembic OK (head documenté)
- [ ] `backend/README.md` mis à jour
- [ ] Les 7 sous-tickets 007A → 007G validés CTO

---

## 9. CHAÎNE MÉTIER CIBLE

```
User → OrganizationMember → Organization → Event → Ticket → Check-in → Revenue
                              ▲
                         Sprint 2 (ce master)
```

---

## 10. BRANCHING (RECOMMANDÉ)

```
feature/sprint-2-ticket-007a-organizations-foundation
feature/sprint-2-ticket-007b-organization-members-activation
feature/sprint-2-ticket-007c-organization-rbac
feature/sprint-2-ticket-007d-organizations-crud
feature/sprint-2-ticket-007e-members-management
feature/sprint-2-ticket-007f-organization-audit
feature/sprint-2-ticket-007g-organizations-qa-hardening
```

---

## 11. PROCHAINES ÉTAPES

1. Validation CTO de ce **BMAD MASTER**
2. Rédiger **TICKET-007A** en BMAD détaillé (premier ticket exécutable)
3. Exécution 007A → validation CTO → 007B → …
4. Clôture FEATURE-ORGANIZATIONS-V1 → ouverture ADR-005 Events

---

## COMMIT RULE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

---

## CTO GATE (MASTER)

| Review | Required | Done |
|--------|----------|------|
| Découpage tickets cohérent (007A → 007G) | YES | ☐ |
| Alignement ADR-004 | YES | ☐ |
| Séparation global_role / organization_role | YES | ☐ |
| Pas de big-bang (fondation avant endpoints) | YES | ☐ |
| Exclusions respectées (Stripe, Events, etc.) | YES | ☐ |
| CTO Approval MASTER | YES | ☐ |
