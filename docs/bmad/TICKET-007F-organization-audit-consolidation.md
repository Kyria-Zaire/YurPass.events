---
type: BMAD
version: 1.0
owner: CTO
project: YurPass
feature: FEATURE-ORGANIZATIONS-V1
ticket: TICKET-007F
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
  - TICKET-007E
blocks:
  - TICKET-007G
---

# BUILD MODE ARCHITECTURE DEVELOPMENT

# TICKET

```
[BMAD] Phase: SPRINT 2 — FEATURE-ORGANIZATIONS-V1
[FEATURE]: FEATURE-ORGANIZATIONS-V1
[TICKET]: TICKET-007F
[SLUG]: organization-audit-consolidation
[ROLE]: Senior Backend Security Engineer + Audit Architecture Reviewer
```

---

## CONTEXTE

TICKET-007A à 007E sont validés et commités :

| Ticket | Commit | Livrable |
|--------|--------|----------|
| 007A | `0466efd` | `organizations` foundation |
| 007B | `da56ffe` | `organization_members` activé |
| 007C | `278e92e` | `require_org_roles()` + matrix |
| 007D | `a5201b6` | CRUD organization (5 endpoints) |
| 007E | `40baa0b` | Members management (4 endpoints) |

**État actuel :**

- Organizations CRUD et Members Management opérationnels
- `audit_logs` existant depuis Auth V1 (006G)
- Actions org **déjà partiellement émises** dans `OrganizationService`, `OrganizationMemberService`, `permissions.py`
- Sanitization basique via `AuditService._sanitize_metadata()`
- **Pas de consolidation formelle** : conventions metadata hétérogènes, champs manquants (`actor_role`, `target_user_id`, status transitions)

Ce ticket **consolide l'audit Organizations** sans ajouter de nouvelle feature métier.

---

## OBJECTIF

Uniformiser, vérifier et durcir **tous** les audit logs liés aux Organizations.

Rendre l'activité Organizations auditable, exploitable et sécurisée avant clôture FEATURE-ORGANIZATIONS-V1 et avant Events / Stripe Connect / Ticketing.

---

## INCLUS

### 1. Audit actions — `AuditAction`

Fichier : `app/modules/audit/constants.py`

Vérifier / compléter :

| Action | État 007E | Action 007F |
|--------|-----------|-------------|
| `organization_created` | ✅ émise | Vérifier shape |
| `organization_updated` | ✅ émise | Vérifier shape + metadata |
| `organization_archived` | ✅ émise | Vérifier shape |
| `organization_suspended` | ❌ absente | **Ajouter constante** — réservée ADR-004, **pas d'émission** en 007F (aucun endpoint suspend) |
| `organization_member_added` | ✅ émise | Uniformiser metadata |
| `organization_member_role_updated` | ✅ émise | Uniformiser metadata |
| `organization_member_removed` | ✅ émise | Uniformiser metadata |
| `organization_rbac_super_admin_bypass` | ✅ émise (007C) | Vérifier shape |

### 2. Resource conventions

**Actions organization** (`created`, `updated`, `archived`, `suspended`*, `rbac_super_admin_bypass`) :

```txt
resource_type = "organization"
resource_id   = str(organization_id)
```

**Actions member** (`member_added`, `member_role_updated`, `member_removed`) :

```txt
resource_type = "organization_member"
resource_id   = str(member_id)
```

**Règle CTO — rattachement obligatoire :**

```txt
metadata_json.organization_id = str(organization_id)  # OBLIGATOIRE
```

Chaque audit member **doit** contenir `organization_id` en metadata — jamais d'audit member orphelin, impossible à rattacher à son organisation.

\* `organization_suspended` : constante uniquement en 007F.

### 3. Metadata minimale — `metadata_json`

| Action | Champs obligatoires |
|--------|---------------------|
| `organization_created` | `organization_id`, `actor_role` (si membre actif / `super_admin` si bypass) |
| `organization_updated` | `organization_id`, `actor_role`, `updated_fields` |
| `organization_archived` | `organization_id`, `actor_role`, `previous_status`, `new_status` |
| `organization_suspended` | *(réservé — non émis en 007F)* |
| `organization_member_added` | `organization_id`, `actor_role`, `target_user_id`, `role` |
| `organization_member_role_updated` | `organization_id`, `actor_role`, `target_user_id`, `previous_role`, `new_role` |
| `organization_member_removed` | `organization_id`, `actor_role`, `target_user_id`, `previous_status`, `new_status`, `self_leave` |
| `organization_rbac_super_admin_bypass` | `organization_id`, `requested_roles`, `permission_context` (si disponible) |

**Règles :**

- `actor_role` = rôle org actif de l'acteur (`owner` / `admin` / …) ou `"super_admin"` pour bypass global
- `target_user_id` = `str(user_id)` du membre cible (actions member)
- Transitions status : `previous_status` / `new_status` en string enum (`active` → `archived`, `active` → `left`, etc.)
- Pas de duplication redondante : `organization_id` dans metadata même quand `resource_id` = member_id (requis pour requêtes transverses)

### 4. Refactoring autorisé

Centraliser l'émission audit org dans un helper dédié (recommandé) :

```txt
app/modules/organizations/audit.py
  record_organization_audit(...)
  record_member_audit(...)
  resolve_actor_role(user, organization_id, access)
```

Modifier **uniquement** les appels audit existants dans :

- `app/modules/organizations/service.py`
- `app/modules/organizations/member_service.py`
- `app/modules/organizations/permissions.py` (bypass super_admin)

**Pas de changement** de logique métier, RBAC, ou comportement endpoints.

### 5. Sanitization

Fichier : `app/modules/audit/service.py`

Étendre `_FORBIDDEN_METADATA_KEYS` pour couvrir explicitement :

```txt
token
password
password_hash
refresh_token
access_token
jwt
secret
plain_token
otp
code
```

Vérifier que toute metadata org/member passe par `AuditService.record()` (déjà le cas).

Ajouter test : tentative d'injection metadata sensible → clé filtrée.

### 6. Super admin bypass

Chaque bypass `super_admin` sur une route organization **doit** générer :

```json
{
  "action": "organization_rbac_super_admin_bypass",
  "actor_user_id": "<super_admin.id>",
  "resource_type": "organization",
  "resource_id": "<organization_id>",
  "metadata_json": {
    "organization_id": "<organization_id>",
    "requested_roles": ["owner", "admin"],
    "permission_context": "member:remove"
  }
}
```

Vérifier couverture sur toutes les routes protégées par `require_org_roles()` et `require_active_org_member_or_super_admin()`.

---

## EXCLUSIONS STRICTES

Ne **pas** faire dans ce ticket :

- Aucun endpoint nouveau
- Aucun changement RBAC
- Aucun changement métier Organizations / Members Management
- Aucune migration Alembic
- Aucun frontend
- Aucun Stripe / Event / Ticketing / Check-in
- Aucun changement module Auth (sauf lecture `actor_role` via membership existant)
- Émission `organization_suspended` (constante OK, pas de trigger)
- TICKET-007G (QA Hardening)

---

## TESTS

Fichier : `tests/modules/organizations/test_organization_audit_007f.py`

| Test | Vérification |
|------|--------------|
| create organization audit shape | action, resource_type, resource_id, metadata |
| update organization audit shape | `updated_fields`, `actor_role` |
| archive organization audit shape | `previous_status` / `new_status` |
| member add audit shape | `target_user_id`, `role`, `organization_id` |
| member role update audit shape | `previous_role` / `new_role` |
| member remove audit shape | `previous_status`/`new_status`, `self_leave` |
| super_admin bypass audit shape | `requested_roles`, resource conventions |
| audit metadata sanitized | clés sensibles filtrées |
| resource_type / resource_id conventions | org vs member |
| no sensitive metadata leakage | password/token/jwt absents |
| organization_suspended constant exists | enum présent, pas d'émission |

Tests existants 007D/007E : **ne pas casser** — adapter si assertions metadata changent.

---

## ACCEPTANCE CRITERIA

1. Toutes les actions `AuditAction` org listées existent dans l'enum
2. Conventions `resource_type` / `resource_id` respectées partout
3. Metadata minimale présente sur chaque action émise
4. Sensitive keys filtrées (liste étendue + test)
5. Super_admin bypass audité correctement sur toutes les routes concernées
6. Tests audit dédiés ajoutés
7. Pytest OK
8. Ruff OK
9. Aucun endpoint / migration ajouté
10. **Aucun commit avant review CTO**

---

## OUTPUT ATTENDU (EXÉCUTION)

1. Fichiers modifiés
2. Liste actions `AuditAction` finales
3. Exemples audit logs (JSON)
4. Preuve `resource_type` / `resource_id`
5. Preuve `metadata_json` conforme
6. Preuve sanitization
7. Tests ajoutés
8. Résultat pytest
9. Résultat ruff
10. Confirmation hors scope
11. Confirmation aucun commit

---

## EXEMPLES AUDIT LOGS ATTENDUS

### organization_created

```json
{
  "action": "organization_created",
  "actor_user_id": "uuid",
  "resource_type": "organization",
  "resource_id": "org-uuid",
  "metadata_json": {
    "organization_id": "org-uuid",
    "actor_role": "owner"
  }
}
```

### organization_member_role_updated

```json
{
  "action": "organization_member_role_updated",
  "actor_user_id": "uuid",
  "resource_type": "organization_member",
  "resource_id": "member-uuid",
  "metadata_json": {
    "organization_id": "org-uuid",
    "actor_role": "owner",
    "target_user_id": "user-uuid",
    "previous_role": "staff",
    "new_role": "admin"
  }
}
```

### organization_rbac_super_admin_bypass

```json
{
  "action": "organization_rbac_super_admin_bypass",
  "actor_user_id": "super-admin-uuid",
  "resource_type": "organization",
  "resource_id": "org-uuid",
  "metadata_json": {
    "organization_id": "org-uuid",
    "requested_roles": ["owner", "admin", "staff"],
    "permission_context": null
  }
}
```

---

## ÉCARTS CONNUS (007E → 007F)

À corriger en exécution :

| Écart | Fichier actuel |
|-------|----------------|
| `actor_role` absent | `service.py`, `member_service.py` |
| `user_id` au lieu de `target_user_id` | `member_service.py` |
| `previous_status` / `new_status` absents sur remove/archive | `service.py`, `member_service.py` |
| `organization_suspended` absent de l'enum | `audit/constants.py` |
| `jwt`, `password_hash` absents de sanitization | `audit/service.py` |
| Helper audit non centralisé | duplication `_record_audit` × 2 |

---

## IMPORTANT

- **Ne pas** passer au TICKET-007G
- Ce ticket **consolide uniquement l'audit Organizations**
- Aucune nouvelle capacité produit

---

## INTENTION PRODUIT / TECHNIQUE

```txt
Auth V1 audit_logs  →  Organizations audit consolidé  →  007G QA  →  Events / Stripe / Ticketing
```

Traçabilité uniforme = conformité sécurité, support ops, et fondation pour investigations incident.

---

## COMMIT RULE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

Message attendu après validation CTO (BMAD) :

```txt
docs: BMAD TICKET-007F organization audit consolidation
```

Message attendu après validation CTO (code) :

```txt
feat(organizations): TICKET-007F organization audit consolidation
```

---

## CTO GATE

| Review | Required | Done |
|--------|----------|------|
| AuditAction enum complet | YES | ☐ |
| Resource conventions org/member | YES | ☐ |
| Metadata minimale uniformisée | YES | ☐ |
| Sanitization étendue + testée | YES | ☐ |
| Super_admin bypass vérifié | YES | ☐ |
| Aucun endpoint / migration / RBAC change | YES | ☐ |
| Pas d'émission organization_suspended | YES | ☐ |
| metadata_json.organization_id obligatoire (member) | YES | ☑ |
| CTO Approval TICKET-007F | YES | ☑ |
