---
type: BMAD
version: 1.0
owner: CTO
project: YurPass
feature: FEATURE-ORGANIZATIONS-V1
ticket: TICKET-007E
status: APPROVED
date: 2026-06-08
related_prd: docs/prd/yurpass-prd-v3.md
related_adr: docs/adr/ADR-004-organizations-foundation.md
related_master: docs/bmad/FEATURE-ORGANIZATIONS-V1-MASTER.md
depends_on:
  - TICKET-007A
  - TICKET-007B
  - TICKET-007C
  - TICKET-007D
blocks:
  - TICKET-007F
---

# BUILD MODE ARCHITECTURE DEVELOPMENT

# TICKET

```
[BMAD] Phase: SPRINT 2 — FEATURE-ORGANIZATIONS-V1
[FEATURE]: FEATURE-ORGANIZATIONS-V1
[TICKET]: TICKET-007E
[SLUG]: members-management
[ROLE]: Senior Backend Engineer + Authorization Architect + Security Reviewer
```

---

## CONTEXTE

TICKET-007A à 007D sont validés et commités :

| Ticket | Commit | Livrable |
|--------|--------|----------|
| 007A | `0466efd` | `organizations` foundation |
| 007B | `da56ffe` | `organization_members` activé |
| 007C | `278e92e` | `require_org_roles()` + matrix |
| 007D | `a5201b6` | CRUD organization (5 endpoints) |

**État actuel :**

- CRUD organization opérationnel
- `organization_members` avec enums, FK, UNIQUE, `count_active_owners()`
- RBAC org via `require_org_roles(*OrganizationRole)`
- Owner automatique à la création org (007D)
- **Aucun endpoint members**

ADR-004 impose la gestion des membres avec **protection du dernier owner**.

---

## OBJECTIF

Créer les **4 endpoints** de gestion des membres d'une organisation.

Ajout direct d'utilisateurs **existants** uniquement — pas d'invitation tokenisée.

---

## ENDPOINTS

| Méthode | Route |
|---------|-------|
| GET | `/api/organizations/{organization_id}/members` |
| POST | `/api/organizations/{organization_id}/members` |
| PATCH | `/api/organizations/{organization_id}/members/{member_id}` |
| DELETE | `/api/organizations/{organization_id}/members/{member_id}` |

Layering obligatoire : `router → service → repository`.

---

## RÈGLES MÉTIER

### GET members

| Règle | Détail |
|-------|--------|
| RBAC lecture | `owner`, `admin`, `staff` autorisés |
| Refus | `viewer` → 403 |
| super_admin | bypass audité (`organization_rbac_super_admin_bypass`) |
| Filtre défaut | `status = active` uniquement |
| Inactifs | `?include_inactive=true` — **owner uniquement** (prépare audits / historique sans casser l'API) |

### POST member

| Règle | Détail |
|-------|--------|
| RBAC ajout | `owner`, `admin` uniquement |
| User cible | doit **exister** (`users.email` ou `user_id`) |
| Rôles POST | `admin`, `staff`, `viewer` — **pas `owner`** |
| Owner via POST | **interdit** — owner = création org (007D) ou futur transfert |
| Membre existant | si `active` → **409** `member_already_exists` |
| Réactivation | `left` / `suspended` → **409** `member_inactive_requires_manual_reactivation` (pas de réactivation en 007E) |
| Création user | **interdit** |
| Invitation | **interdit** |
| Audit | `organization_member_added` |

**Payload POST minimal :**

```json
{
  "user_id": "uuid",
  "role": "staff"
}
```

ou lookup par email (décision implémentation — un seul mode documenté dans exécution).

### PATCH member (rôle)

| Règle | Détail |
|-------|--------|
| RBAC | `owner` **uniquement** |
| admin PATCH rôle | **refusé** |
| Rôles cibles | `admin`, `staff`, `viewer` |
| Promotion owner | **interdit** en 007E |
| Dernier owner | modification du dernier owner actif → **refusé** |
| Audit | `organization_member_role_updated` |

### DELETE member (retrait logique)

| Règle | Détail |
|-------|--------|
| RBAC retrait | `owner` peut retirer un autre membre |
| admin DELETE | **refusé** |
| Effet | `status = left` — **pas de suppression physique** |
| Dernier owner | retrait du dernier owner actif → **refusé** |
| Self-leave | `admin`, `staff`, `viewer` peuvent se retirer (`status=left`) |
| Self-leave owner | **toujours refusé** — un owner ne peut jamais utiliser self-leave tant qu'il est owner, même s'il existe plusieurs owners (évite contournement futur transfert ownership) |
| Audit | `organization_member_removed` |

**Protection owner — règle centrale :**

```txt
count_active_owners() >= 1 TOUJOURS
```

Utiliser `OrganizationMemberRepository.count_active_owners()` (007B).

---

## INCLUS

### 1. Schemas

Fichier : `app/modules/organizations/schemas.py`

| Schema | Usage |
|--------|-------|
| `OrganizationMemberPublic` | Réponse membre (existe) |
| `OrganizationMemberCreateRequest` | POST — user_id + role |
| `OrganizationMemberUpdateRequest` | PATCH — role |
| `OrganizationMemberListResponse` | Liste membres actifs |

### 2. Service

Fichier : `app/modules/organizations/member_service.py` ou méthodes dans `service.py`

| Méthode | Description |
|---------|-------------|
| `list_members()` | Membres actifs |
| `add_member()` | Ajout user existant |
| `update_member_role()` | Changement rôle |
| `remove_member()` | status=left + owner protection |

### 3. Router

Étendre `app/modules/organizations/router.py` — sous-routes `/members`.

RBAC via `require_org_roles()` :

| Endpoint | Rôles autorisés |
|----------|-----------------|
| GET | OWNER, ADMIN, STAFF |
| POST | OWNER, ADMIN |
| PATCH | OWNER |
| DELETE | OWNER (+ self-leave exception dans service) |

### 4. Exceptions métier

| Cas | Code HTTP |
|-----|-----------|
| User inexistant | 404 |
| Membre active duplicate | 409 `member_already_exists` |
| Membre left / suspended | 409 `member_inactive_requires_manual_reactivation` |
| Dernier owner protection | 409 ou 403 (documenter choix — recommandé 409 `last_owner_protected`) |
| Rôle owner via POST/PATCH | 400 ou 403 |
| RBAC refusé | 403 |

### 5. Audit

Étendre `AuditAction` :

```txt
organization_member_added
organization_member_role_updated
organization_member_removed
```

Intégration via `AuditService` dans le service layer.

### 6. Repository (si nécessaire)

Méthodes additionnelles autorisées :

- `list_active_members(organization_id)`
- `get_member_by_id_and_org(member_id, organization_id)`

Pas de migration.

---

## EXCLUSIONS STRICTES

Ne **pas** faire dans ce ticket :

- Invitation email / tokenisée
- Création user
- Promotion owner / transfert ownership
- Stripe, Event, Ticketing, Check-in
- Migration Alembic
- Frontend
- Modification module Auth
- Suppression physique `organization_members`
- TICKET-007F (audit consolidation)
- Réactivation membre `left` / `suspended`

---

## TESTS

Fichier : `tests/modules/organizations/test_organization_members_api_007e.py`

| Test | Vérification |
|------|--------------|
| GET owner/admin/staff OK | liste membres actifs |
| GET viewer refused | 403 |
| POST owner/admin OK | membre ajouté |
| POST viewer/staff refused | 403 |
| POST unknown user | 404 |
| POST duplicate active | 409 |
| POST owner role | refusé |
| PATCH role owner OK | rôle changé |
| PATCH role admin refused | 403 |
| PATCH role to owner refused | refusé |
| DELETE owner OK | status=left |
| DELETE admin refused | 403 |
| self-leave admin/staff/viewer OK | status=left |
| self-leave owner refused | 409/403 (toujours, même multi-owner) |
| remove last owner refused | 409/403 |
| audit add/update/remove | 3 logs |
| super_admin bypass | OK + audité |
| no physical delete | row conservée status=left |
| no user creation | users count stable |
| no extra endpoints | 4 members routes only |

---

## ACCEPTANCE CRITERIA

1. 4 member endpoints exposés
2. RBAC conforme ADR-004
3. Owner protection fonctionne (`count_active_owners`)
4. Ajout membre — user existant uniquement
5. Pas d'ajout owner via API members
6. Retrait = `status=left`
7. Pas de suppression physique
8. Audits add / update / remove
9. Pytest OK
10. Ruff OK
11. **Aucun commit avant review CTO**

---

## OUTPUT ATTENDU (EXÉCUTION)

1. Fichiers modifiés
2. Endpoints livrés
3. Exemples curl
4. Preuve owner protection
5. Preuve `status=left`
6. Preuve audits
7. Tests ajoutés
8. Résultat pytest
9. Résultat ruff
10. Confirmation aucune dérive hors scope
11. Confirmation aucun commit

---

## IMPORTANT

- **Ne pas** passer au TICKET-007F
- **Ne pas** créer d'invitation tokenisée
- Ce ticket gère **uniquement les membres existants**

---

## INTENTION PRODUIT / TECHNIQUE

Compléter la relation B2B :

```txt
User → OrganizationMember → Organization
```

avec gestion d'équipe sécurisée (owners, admins, staff, viewers) — fondation pour Events, Ticketing et Check-in.

---

## COMMIT RULE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

Message attendu après validation CTO :

```txt
feat(organizations): TICKET-007E members management
```

---

## CTO GATE

| Review | Required | Done |
|--------|----------|------|
| 4 endpoints members | YES | ☐ |
| Owner protection dernier owner | YES | ☐ |
| Pas owner via POST/PATCH | YES | ☐ |
| Pas invitation / pas création user | YES | ☐ |
| Retrait status=left uniquement | YES | ☐ |
| Audits member add/update/remove | YES | ☐ |
| GET ?include_inactive=true owner only | YES | ☑ |
| POST 409 codes explicites | YES | ☑ |
| Owner self-leave toujours refusé | YES | ☑ |
| CTO Approval TICKET-007E | YES | ☑ |
