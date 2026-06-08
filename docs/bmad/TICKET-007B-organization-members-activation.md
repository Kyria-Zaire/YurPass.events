---
type: BMAD
version: 1.0
owner: CTO
project: YurPass
feature: FEATURE-ORGANIZATIONS-V1
ticket: TICKET-007B
status: APPROVED
date: 2026-06-08
related_prd: docs/prd/yurpass-prd-v3.md
related_adr: docs/adr/ADR-004-organizations-foundation.md
related_master: docs/bmad/FEATURE-ORGANIZATIONS-V1-MASTER.md
depends_on:
  - TICKET-007A
blocks:
  - TICKET-007C
  - TICKET-007D
  - TICKET-007E
---

# BUILD MODE ARCHITECTURE DEVELOPMENT

# TICKET

```
[BMAD] Phase: SPRINT 2 — FEATURE-ORGANIZATIONS-V1
[FEATURE]: FEATURE-ORGANIZATIONS-V1
[TICKET]: TICKET-007B
[SLUG]: organization-members-activation
[ROLE]: Senior Backend Architect + Database Engineer + Security Reviewer
```

---

## CONTEXTE

TICKET-007A est validé et commité (`0466efd`).

- La table `organizations` existe (migration `20260608_006`)
- La table `organization_members` existe encore en **placeholder** depuis 006A
- ADR-004 impose l'activation réelle de `organization_members`
- Aucun endpoint members ni RBAC org n'est encore livré

**État placeholder actuel (006A) :**

| Colonne | Type | Notes |
|---------|------|-------|
| id | UUID PK | |
| user_id | UUID FK users | |
| organization_id | UUID | **sans FK** |
| role | VARCHAR(50) | **pas enum** |
| created_at | TIMESTAMPTZ | |

**Manquant vs ADR-004 :** `status`, `updated_at`, FK `organizations`, enum `role`, UNIQUE constraint.

---

## OBJECTIF

Transformer `organization_members` de placeholder en table métier exploitable, sans créer d'endpoints ni RBAC org complet.

Ce ticket active uniquement la couche **data + repository** — fondation pour la relation `User → OrganizationMember → Organization`.

---

## INCLUS

### 1. Enums

Créer dans `app/modules/organizations/constants.py` (compléter 007A) :

**OrganizationRole**

```txt
owner
admin
staff
viewer
```

**MemberStatus**

```txt
active
suspended
left
```

Typage `StrEnum` — même convention que `OrganizationType` / `OrganizationStatus`.

---

### 2. Migration Alembic

Fichier : `20260608_007_activate_organization_members.py`  
Revises : `20260608_006`

**Modifications `organization_members` :**

| Action | Détail |
|--------|--------|
| FK | `organization_id → organizations.id` |
| role | `VARCHAR(50)` → enum PostgreSQL `organization_role` |
| status | `member_status NOT NULL DEFAULT 'active'` |
| updated_at | `TIMESTAMPTZ NOT NULL DEFAULT now()` |
| UNIQUE | `(user_id, organization_id)` |
| Indexes | `user_id`, `organization_id`, `role`, `status` |
| Index composite | `ix_org_members_org_role` sur `(organization_id, role)` |
| Conserver | `created_at`, `id`, `user_id` |

**Index composite CTO :**

```txt
ix_org_members_org_role (organization_id, role)
```

Requête cible préparée :

```sql
SELECT *
FROM organization_members
WHERE organization_id = ?
AND role = 'owner'
```

**Stratégie migration role :**

- Table considérée **vide en dev** (aucune donnée placeholder en production)
- Si données existantes : `ALTER COLUMN role TYPE organization_role USING role::organization_role` uniquement si valeurs compatibles ; sinon documenter migration manuelle
- **Pas de suppression physique** de table — `ALTER` uniquement

**Enums PostgreSQL à créer :**

```txt
organization_role
member_status
```

---

### 3. SQLAlchemy Model

Mettre à jour `app/modules/organizations/models.py` — `OrganizationMember` :

```python
role: Mapped[OrganizationRole]       # enum organization_role
status: Mapped[MemberStatus]         # enum member_status, default ACTIVE
updated_at: Mapped[datetime]         # onupdate=func.now()
organization_id: Mapped[uuid.UUID]  # FK organizations.id
```

- Ne **pas** casser le modèle `Organization`
- Ne **pas** ajouter de relationship ORM complexe (optionnel minimal OK)

---

### 4. Schemas Pydantic foundation

Fichier : `app/modules/organizations/schemas.py`

| Schema | Usage |
|--------|-------|
| `OrganizationMemberPublic` | Réponse publique membre |
| `OrganizationMemberCreate` | Ajout membre (user_id, role) — usage interne 007E |
| `OrganizationMemberUpdate` | Mise à jour role / status partielle |

Aucun endpoint HTTP dans ce ticket.

---

### 5. Repository foundation

Fichier : `app/modules/organizations/repository.py`

Créer `OrganizationMemberRepository` (distinct de `OrganizationRepository`) :

| Méthode | Description |
|---------|-------------|
| `get_member_by_id(member_id)` | Par PK |
| `get_member(user_id, organization_id)` | Par couple unique |
| `list_members(organization_id)` | Liste membres d'une org |
| `add_member(...)` | Créer membre actif |
| `update_member_role(member, role)` | Changer rôle |
| `update_member_status(member, status)` | Changer statut |
| `count_active_owners(organization_id)` | Compte owners actifs |

**Règle métier de données (CTO) :**

- Il peut exister **plusieurs** `owner`
- `count_active_owners()` doit compter uniquement : `role = owner` **ET** `status = active`
- Aucune validation métier dans 007B
- La protection « impossible de supprimer le dernier owner » sera implémentée en **007E**

**Interdit dans ce ticket :**

- RBAC dependency
- Règle « dernier owner » (007E)
- Owner automatique à la création org (007D)

---

### 6. Tests

Fichier : `tests/modules/organizations/test_organization_members_007b.py`

| Test | Vérification |
|------|--------------|
| migration activated | Table + colonnes + enums en DB |
| OrganizationRole enum values | 4 valeurs |
| MemberStatus enum values | 3 valeurs |
| unique(user_id, organization_id) | IntegrityError sur doublon |
| FK organization_id enforced | IntegrityError org inexistante |
| repository add/get/list | CRUD foundation |
| update role | `update_member_role` |
| update status | `update_member_status` |
| count active owners | `count_active_owners` |
| Organization model non cassé | Régression 007A |
| aucun endpoint exposé | `main.py` sans router org |

Mettre à jour `tests/conftest.py` si nécessaire pour `create_all`.

---

## EXCLUSIONS STRICTES

Ne **pas** faire dans ce ticket :

- Aucun endpoint members
- Aucun endpoint organizations
- Aucun `require_org_roles`
- Aucun owner automatique
- Aucun audit organization
- Aucun CRUD organization (007D)
- Aucun Stripe / Event / Ticketing / frontend

---

## QUALITÉ

Architecture cible :

```txt
router → service → repository → database
```

Ce ticket reste **repository / data foundation** — router et service restent placeholders.

Le repository ne contient pas de règle métier complexe (ownership, RBAC).

---

## ACCEPTANCE CRITERIA

1. Migration `20260608_007` créée
2. `alembic upgrade head` passe sur DB propre
3. `organization_members` a FK `organizations.id`
4. `role` est enum `organization_role`
5. `status` est enum `member_status`
6. `UNIQUE(user_id, organization_id)` existe
7. Indexes `user_id`, `organization_id`, `role`, `status` existent
8. SQLAlchemy `OrganizationMember` aligné ADR-004
9. Schemas foundation existent
10. Repository foundation fonctionne
11. Aucun endpoint exposé
12. Pytest OK
13. Ruff OK
14. **Aucun commit avant review CTO**

---

## OUTPUT ATTENDU (EXÉCUTION)

À la fin de l'implémentation, fournir :

1. Fichiers créés/modifiés
2. Migration 007
3. Preuve FK `organization_id`
4. Preuve `UNIQUE(user_id, organization_id)`
5. Preuve enums `role` / `status`
6. Tests ajoutés
7. Résultat pytest
8. Résultat ruff
9. Confirmation aucune dérive hors scope
10. Confirmation aucun commit

---

## IMPORTANT

- **Ne pas** passer au TICKET-007C
- **Ne pas** créer RBAC org (`require_org_roles` = 007C)
- Ce ticket **active seulement** `organization_members`

---

## INTENTION PRODUIT / TECHNIQUE

Ce ticket rend exploitable la relation :

```txt
User → OrganizationMember → Organization
```

Fondation indispensable pour les futurs :

- owners, admins, staff, viewers
- Events, Ticketing, Check-in
- Stripe Connect (via org ownership)

---

## COMMIT RULE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

Message attendu après validation CTO :

```txt
feat(organizations): TICKET-007B organization members activation
```

---

## CTO GATE

| Review | Required | Done |
|--------|----------|------|
| Alignement ADR-004 | YES | ☐ |
| FK + UNIQUE + enums | YES | ☐ |
| Pas d'endpoint / pas de RBAC | YES | ☐ |
| Organization 007A non cassé | YES | ☐ |
| CTO Approval TICKET-007B | YES | ☐ |
