---
type: BMAD
version: 1.0
owner: CTO
project: YurPass
feature: FEATURE-ORGANIZATIONS-V1
ticket: TICKET-007C
status: PROPOSED
date: 2026-06-08
related_prd: docs/prd/yurpass-prd-v3.md
related_adr: docs/adr/ADR-004-organizations-foundation.md
related_master: docs/bmad/FEATURE-ORGANIZATIONS-V1-MASTER.md
depends_on:
  - TICKET-007A
  - TICKET-007B
blocks:
  - TICKET-007D
  - TICKET-007E
---

# BUILD MODE ARCHITECTURE DEVELOPMENT

# TICKET

```
[BMAD] Phase: SPRINT 2 — FEATURE-ORGANIZATIONS-V1
[FEATURE]: FEATURE-ORGANIZATIONS-V1
[TICKET]: TICKET-007C
[SLUG]: organization-rbac
[ROLE]: Senior Backend Security Engineer + FastAPI Authorization Architect
```

---

## CONTEXTE

TICKET-007A est validé et commité (`0466efd`).  
TICKET-007B est validé et commité (`da56ffe`).

**État actuel :**

- Table `organizations` opérationnelle (migration `20260608_006`)
- `organization_members` activée (migration `20260608_007`) avec :
  - enum `organization_role`
  - enum `member_status`
  - FK `organization_id → organizations.id`
  - `UNIQUE(user_id, organization_id)`
  - `count_active_owners()` (role=owner, status=active)
  - index composite `ix_org_members_org_role`

ADR-004 impose un **RBAC organisationnel strict**, séparé du `global_role`.

**Principe fondamental :**

```txt
global_role ≠ organization_role
```

---

## OBJECTIF

Créer la couche d'autorisation organisationnelle **réutilisable** pour les futurs endpoints Organizations, Members, Events, Ticketing et Check-in.

**Aucun endpoint CRUD** ne doit être créé dans ce ticket.

---

## INCLUS

### 1. Permissions module

Fichier : `backend/app/modules/organizations/permissions.py`

**Dépendances obligatoires :**

| Dépendance | Rôle |
|------------|------|
| `require_org_member()` | Membre actif de l'organisation |
| `require_org_roles(*allowed_roles: OrganizationRole)` | Membre actif + rôle autorisé |

**Doivent utiliser :**

- `get_current_user()` (`app/modules/auth/dependencies.py`)
- `OrganizationMemberRepository`
- `OrganizationRole` (`constants.py`)
- `MemberStatus` (`constants.py`)
- `PermissionDeniedError` (`app/shared/exceptions.py`)

**Paramètre organisation :** `organization_id: UUID` — extrait du path FastAPI (`Path(...)`) ou injecté par la route appelante.

---

### 2. Règles `require_org_member()`

**Autorise uniquement :**

- membre existant pour `(user_id, organization_id)`
- `status = active`

**Refuse (403 `PermissionDeniedError`) :**

- non membre
- `member.status = suspended`
- `member.status = left`
- user `suspended` / `deleted` — déjà géré par `get_current_user()`

**Retourne :** `OrganizationMember` actif

**Ne fait pas :**

- création de membership
- transformation `super_admin` en membre (voir bypass §4)

---

### 3. Règles `require_org_roles()`

**Factory pattern** (aligné `require_global_roles` 006G) :

```python
def require_org_roles(*allowed_roles: OrganizationRole):
    ...
```

**Autorise :**

- membre actif avec `role in allowed_roles`

**Refuse :**

- non membre
- membre `suspended` / `left`
- rôle non autorisé

**Typage strict CTO :**

```python
# Interdit
require_org_roles("owner")

# Attendu
require_org_roles(OrganizationRole.OWNER)
```

---

### 4. Super admin bypass

`global_role = super_admin` peut bypass l'appartenance organisationnelle pour **support**.

**Contraintes :**

| Règle | Détail |
|-------|--------|
| Bypass explicite | Code path dédié, pas implicite |
| Audit obligatoire | `audit_logs` via `AuditService` |
| Pas de faux membre | Ne retourne **pas** `OrganizationMember` synthétique |
| Pas de ligne DB | Ne crée **pas** de ligne `organization_members` |

**Audit action :**

```txt
organization_rbac_super_admin_bypass
```

**Metadata audit minimale :**

- `organization_id`
- `requested_roles` ou `permission_context`
- **aucun secret**

**Usage futur :** routes support 007D+ — en 007C, tests unitaires/integration des deps suffisent.

---

### 5. Permission matrix foundation

Fichier : `permissions.py` ou `organization_permissions.py` (même module)

**Structure :**

```python
ORGANIZATION_ROLE_PERMISSIONS: dict[OrganizationRole, list[str]]
```

| Rôle | Permissions |
|------|-------------|
| **owner** | `organization:read`, `organization:update`, `organization:archive`, `member:read`, `member:add`, `member:update_role`, `member:remove` |
| **admin** | `organization:read`, `organization:update`, `member:read`, `member:add` |
| **staff** | `organization:read`, `member:read` |
| **viewer** | `organization:read` |

**Helper obligatoire :**

```python
def role_has_permission(role: OrganizationRole, permission: str) -> bool
```

Utilisé par les futurs services 007D/007E — pas d'endpoint dans 007C.

---

### 6. Repository (si nécessaire)

Pas de migration.

Si `OrganizationMemberRepository` manque une méthode utile aux deps :

- ajouter **uniquement** la méthode nécessaire (ex. `get_active_member(user_id, organization_id)`)
- pas de logique RBAC dans le repository

**Interdit :** requêtes SQL directes dans `permissions.py` si une méthode repository existe.

---

### 7. Tests

Fichier : `tests/modules/organizations/test_organization_rbac_007c.py`

| Test | Vérification |
|------|--------------|
| owner matrix | permissions owner complètes |
| admin matrix | update org + member read/add |
| staff matrix | read org + member read uniquement |
| viewer matrix | read org uniquement |
| non membre | `PermissionDeniedError` |
| suspended member | refusé |
| left member | refusé |
| rôle non autorisé | refusé via `require_org_roles` |
| super_admin bypass | autorisé sans membership |
| super_admin bypass audité | log `organization_rbac_super_admin_bypass` |
| super_admin no member row | aucune création `organization_members` |
| require_org_roles typing | signature `OrganizationRole`, pas `str` |
| role_has_permission | true/false par rôle |

Mettre à jour `AuditAction` dans `app/modules/audit/constants.py` si nécessaire.

---

## EXCLUSIONS STRICTES

Ne **pas** faire dans ce ticket :

- Aucun endpoint `/api/organizations`
- Aucun CRUD organization (007D)
- Aucun endpoint members (007E)
- Aucun ajout owner automatique (007D)
- Aucune protection dernier owner (007E)
- Aucun audit `organization_created` / `updated` / `archived` (007F)
- Aucune migration
- Stripe, Event, Ticketing, Check-in, frontend

---

## QUALITÉ

Architecture cible :

```txt
router → service → repository → database
```

Ce ticket **ne crée pas de router**.

- Pas de logique DB directe dans `permissions.py` si repository suffit
- Dépendances FastAPI testables via `Depends` override
- `permissions.py` exempté `B008` (convention 006G)

---

## ACCEPTANCE CRITERIA

1. `require_org_member` existe
2. `require_org_roles` existe
3. Les deux utilisent `OrganizationRole` / `MemberStatus`
4. Aucun `str` libre pour les rôles
5. Matrix `ORGANIZATION_ROLE_PERMISSIONS` existe
6. `role_has_permission` fonctionne
7. Non membre refusé
8. `suspended` / `left` refusés
9. `super_admin` bypass fonctionne
10. `super_admin` bypass audité
11. Aucun endpoint exposé
12. Aucune migration
13. Pytest OK
14. Ruff OK
15. **Aucun commit avant review CTO**

---

## OUTPUT ATTENDU (EXÉCUTION)

À la fin de l'implémentation, fournir :

1. Fichiers créés/modifiés
2. Détail `require_org_member`
3. Détail `require_org_roles`
4. Matrix permissions
5. Preuve `super_admin` bypass
6. Preuve audit bypass
7. Tests ajoutés
8. Résultat pytest
9. Résultat ruff
10. Confirmation aucune dérive hors scope
11. Confirmation aucun commit

---

## IMPORTANT

- **Ne pas** passer au TICKET-007D
- **Ne pas** créer les endpoints Organizations
- Ce ticket crée la **couche d'autorisation B2B centrale** de YurPass

---

## INTENTION PRODUIT / TECHNIQUE

Garantir que les futures actions sur Organizations, Members, Events, Ticketing et Check-in pourront être protégées **sans mélanger** `global_role` et `organization_role`.

Chaîne cible :

```txt
get_current_user() → require_org_member() → require_org_roles(OrganizationRole.OWNER)
```

---

## COMMIT RULE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

Message attendu après validation CTO :

```txt
feat(organizations): TICKET-007C organization RBAC
```

---

## CTO GATE

| Review | Required | Done |
|--------|----------|------|
| Typage `OrganizationRole` strict | YES | ☐ |
| Séparation global_role / org_role | YES | ☐ |
| Super admin bypass audité sans faux membre | YES | ☐ |
| Pas d'endpoint / pas de migration | YES | ☐ |
| Matrix permissions ADR-004 | YES | ☐ |
| CTO Approval TICKET-007C | YES | ☐ |
