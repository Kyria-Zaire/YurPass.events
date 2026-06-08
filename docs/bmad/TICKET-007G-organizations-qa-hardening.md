---
type: BMAD
version: 1.0
owner: CTO
project: YurPass
feature: FEATURE-ORGANIZATIONS-V1
ticket: TICKET-007G
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
  - TICKET-007F
closes:
  - FEATURE-ORGANIZATIONS-V1
---

# BUILD MODE ARCHITECTURE DEVELOPMENT

# TICKET

```
[BMAD] Phase: SPRINT 2 — FEATURE-ORGANIZATIONS-V1
[FEATURE]: FEATURE-ORGANIZATIONS-V1
[TICKET]: TICKET-007G
[SLUG]: organizations-qa-hardening
[ROLE]: Senior QA Engineer + Backend Security Reviewer + CTO Reviewer
```

---

## CONTEXTE

TICKET-007A à 007F sont validés et commités :

| Ticket | Commit | Livrable |
|--------|--------|----------|
| 007A | `0466efd` | `organizations` foundation |
| 007B | `da56ffe` | `organization_members` activé |
| 007C | `278e92e` | `require_org_roles()` + matrix |
| 007D | `a5201b6` | CRUD organization (5 endpoints) |
| 007E | `40baa0b` | Members management (4 endpoints) |
| 007F | `5e912f7` | Audit consolidation |

**État actuel :**

- Organizations CRUD opérationnel (5 endpoints)
- Members Management opérationnel (4 endpoints)
- RBAC org via `require_org_roles()`
- Audit org consolidé (`organizations/audit.py`)
- Tests unitaires/intégration par ticket (007A→007F)
- `backend/README.md` **non mis à jour** (placeholder Sprint 2)

Ce ticket **clôture FEATURE-ORGANIZATIONS-V1** — passe finale QA/hardening sans nouvelle feature métier.

---

## OBJECTIF

Faire une passe finale **QA / hardening** sur Organizations V1 :

- Couvrir par tests les cas limites non encore explicitement verrouillés
- Valider schéma DB / migrations sur DB propre
- Documenter le module dans `backend/README.md`
- Produire un rapport de clôture feature

---

## INCLUS

### 1. RBAC matrix hardening

Fichier recommandé : `tests/modules/organizations/test_organizations_qa_hardening_007g.py`

Matrice à vérifier par tests d'intégration HTTP :

| Acteur | Autorisé | Refusé |
|--------|----------|--------|
| **owner** | CRUD org (sauf contraintes owner), members read/add, role PATCH, member DELETE | self-leave |
| **admin** | GET org, PATCH org, GET members, POST member | DELETE org (archive), PATCH member role, DELETE autre membre |
| **staff** | GET org, GET members | PATCH org, POST member, PATCH/DELETE members |
| **viewer** | GET org | GET members, toute écriture |
| **non-member** | — | toutes routes org/members → 403 |
| **left / suspended** | — | toutes routes → 403 (membership inactive) |
| **super_admin** | bypass audité (GET org, GET members, etc.) | — (audit `organization_rbac_super_admin_bypass`) |

Routes couvertes (9 endpoints) :

```txt
POST   /api/organizations
GET    /api/organizations
GET    /api/organizations/{id}
PATCH  /api/organizations/{id}
DELETE /api/organizations/{id}
GET    /api/organizations/{id}/members
POST   /api/organizations/{id}/members
PATCH  /api/organizations/{id}/members/{member_id}
DELETE /api/organizations/{id}/members/{member_id}
```

### 2. Ownership hardening

| Règle | Test |
|-------|------|
| Owner auto à la création org | `status=active`, `role=owner` |
| Au moins un owner actif toujours | `count_active_owners() >= 1` |
| Dernier owner protégé | PATCH role + DELETE refusés |
| Owner self-leave refusé | toujours, même multi-owner |
| Pas de promotion owner via PATCH | `409 owner_role_not_allowed` |
| Pas d'ajout owner via POST | `409 owner_role_not_allowed` |

Compléter / consolider les tests 007D/007E si redondance acceptable — priorité : fichier 007G lisible comme matrice de clôture.

### 3. Slug hardening

| Cas | Attendu |
|-----|---------|
| Génération depuis `name` | `Club XYZ` → `club-xyz` |
| Collision | `Club` × 3 → `club`, `club-2`, `club-3` |
| Stabilité après PATCH name | slug **inchangé** |
| Unicité DB | contrainte `UNIQUE` sur `organizations.slug` |
| Accents / spéciaux | normalisation (`slugify_name`) — ex. `Café Événement` → slug ASCII |

### 4. Archive hardening

| Cas | Attendu |
|-----|---------|
| DELETE org | `status=archived` (pas de suppression physique) |
| GET list normal | org archived **exclue** pour membres |
| Accès archived | membres standards : GET detail → 403 si archived |
| Super_admin + archived | **Décision CTO** : `super_admin` peut lister non-archived via `list_all_non_archived` ; archived **exclu** de la list publique actuelle — **pas de nouvel endpoint** support archived en 007G |
| Members préservés | archive org ne supprime pas `organization_members` |

### 5. Audit hardening

Vérifier (compléter tests 007F si lacunes) :

| Action | Vérification |
|--------|--------------|
| `organization_created` | shape + `actor_role` |
| `organization_updated` | `updated_fields` |
| `organization_archived` | `previous_status` / `new_status` |
| `organization_member_added` | `target_user_id` + **`organization_id` obligatoire** |
| `organization_member_role_updated` | `previous_role` / `new_role` |
| `organization_member_removed` | `previous_status` / `new_status` |
| `organization_rbac_super_admin_bypass` | `requested_roles` |
| Sanitization | `password`, `token`, `jwt`, etc. filtrés |
| `actor_user_id` | présent sur toutes les actions émises |

### 6. Migration / schema check

Sur **DB propre** (PostgreSQL, `alembic upgrade head`) :

```bash
alembic upgrade head
```

Vérifier :

| Élément | Attendu |
|---------|---------|
| Tables | `organizations`, `organization_members` |
| Enums PG | `organization_type`, `organization_status`, `organization_role`, `member_status` |
| Contraintes | `uq_organization_members_user_org`, FK `users` / `organizations` |
| Indexes | `ix_org_members_org_role`, indexes slug/status |
| Head documenté | `20260608_007` (ou head courant au moment exécution) |

Downgrade : non requis en 007G, mais ne doit pas être cassé si existant.

Test automatisé autorisé : réutiliser pattern `test_migration_organization_members_activated` (007B) + check `organizations` table.

**Précision CTO — contraintes DB explicites :**

Vérifier par tests ou inspection schema que les protections applicatives sont **également garanties côté base** :

```txt
uq_organization_members_user_org
uq_organizations_slug          # UNIQUE sur organizations.slug
fk_organization_members_organization_id
fk_organization_members_user_id
```

Fichier recommandé : section dédiée dans `test_organizations_qa_hardening_007g.py` ou extension `test_organizations_007a.py` / `test_organization_members_007b.py`.

### 7. Documentation backend

Mettre à jour `backend/README.md` :

- Section **Organizations module** (remplacer placeholder Sprint 2)
- Liste des **9 endpoints** (5 org + 4 members)
- Rôles `owner` / `admin` / `staff` / `viewer` + matrice permissions résumée
- Règles **owner protection** (dernier owner, no self-leave, no owner via API)
- **Archive logique** (`DELETE` → `status=archived`)
- Référence ADR-004 + tickets 007A→007G
- Head migration Alembic

---

## EXCLUSIONS STRICTES

Ne **pas** faire dans ce ticket :

- Nouvelle feature métier
- Nouveaux endpoints
- Nouvelle migration (sauf correction critique bloquante — improbable)
- Stripe / Events / Ticketing / Check-in
- Invitations tokenisées
- Frontend
- Changement module Auth
- Refactor massif
- Sprint 3
- ADR-005 Events
- Transfert ownership
- Réactivation membre `left` / `suspended`

---

## TESTS

### Fichier principal

`tests/modules/organizations/test_organizations_qa_hardening_007g.py`

### Cas minimum

```txt
RBAC
- test_owner_full_access_matrix
- test_admin_allowed_and_denied
- test_staff_allowed_and_denied
- test_viewer_allowed_and_denied
- test_non_member_denied_all_routes
- test_suspended_member_denied
- test_left_member_denied
- test_super_admin_bypass_audited_on_protected_routes

Ownership
- test_owner_auto_on_create
- test_last_owner_protected_patch_and_delete
- test_owner_self_leave_always_denied
- test_no_owner_via_member_post_or_patch

Slug
- test_slug_collision_club_club_2_club_3
- test_slug_stable_after_name_patch
- test_slug_special_chars_normalized

Archive
- test_delete_sets_archived_not_physical_delete
- test_archived_excluded_from_member_list
- test_archived_org_inaccessible_to_members
- test_archive_preserves_member_rows

Audit (smoke consolidation)
- test_all_org_audit_actions_emitted_on_happy_paths
- test_member_audit_has_organization_id

Migration
- test_alembic_head_schema_organizations (ou script documenté + preuve manuelle)

DB constraints (CTO)
- test_uq_organization_members_user_org_enforced
- test_uq_organizations_slug_enforced
- test_fk_organization_members_organization_id_enforced
- test_fk_organization_members_user_id_enforced
```

Tests existants 007A→007F : **doivent rester verts** — pas de régression.

**Précision CTO — non-régression Auth :**

Le rapport final d'exécution **doit séparer** les résultats pytest :

```txt
Organizations tests  → tests/modules/organizations/
Auth tests           → tests/modules/auth/
Suite complète       → tests/
```

Objectif : prouver explicitement que la baseline (~199 tests pré-007G) n'est pas cassée.

---

## ACCEPTANCE CRITERIA

1. Tests hardening ajoutés (fichier 007G)
2. RBAC matrix couverte
3. Ownership protections couvertes
4. Slug behavior couvert
5. Archive behavior couvert
6. Audit behavior couvert (ou validé via 007F + smoke 007G)
7. `alembic upgrade head` validé sur DB propre
8. `backend/README.md` mis à jour
9. Pytest complet OK
10. Ruff OK
11. Rapport clôture FEATURE-ORGANIZATIONS-V1 produit
12. **Aucun commit avant review CTO**

---

## OUTPUT ATTENDU (EXÉCUTION)

1. Fichiers modifiés
2. Liste tests hardening ajoutés
3. Résultat `alembic upgrade head` DB propre
4. Résultat pytest organizations (nombre)
5. Résultat pytest auth (nombre)
6. Résultat pytest complet (nombre total)
7. Résultat ruff
8. Vérification contraintes DB (4 contraintes)
9. Résumé **risques restants** (ex. suspend org endpoint futur, réactivation membre, transfert ownership)
10. Confirmation aucune dérive hors scope
11. Confirmation aucun commit

---

## RISQUES RESTANTS ATTENDUS (POST-007G)

Documenter explicitement dans le rapport — **hors scope V1** :

| Risque / gap | Ticket futur |
|--------------|--------------|
| Transfert ownership | post-V1 |
| Réactivation membre `left`/`suspended` | 008+ |
| Endpoint `organization_suspended` | post-V1 |
| Invitations tokenisées | post-V1 |
| List archived pour super_admin support | endpoint dédié futur |
| Events / Ticketing / Stripe | Sprint 3+ |

---

## CLÔTURE FEATURE-ORGANIZATIONS-V1

Après validation CTO de 007G, cocher dans `FEATURE-ORGANIZATIONS-V1-MASTER.md` :

```txt
☑ organizations migrée
☑ organization_members activée
☑ RBAC org
☑ CRUD 5 endpoints
☑ Members 4 endpoints
☑ Audit org consolidé
☑ Tests permissions + hardening
☑ README backend
☑ 007A → 007G validés
```

Message de clôture recommandé :

```txt
FEATURE-ORGANIZATIONS-V1 — CLOSED
Prêt pour Sprint 3 (Events / ADR-005)
```

---

## IMPORTANT

- **Ne pas** ouvrir Sprint 3
- **Ne pas** créer ADR-005
- Ce ticket **clôture uniquement Organizations V1**

---

## INTENTION PRODUIT / TECHNIQUE

```txt
Organizations V1 fonctionnel  →  007G QA/hardening  →  Fondation fiable documentée
                                                      →  Events, Ticketing, Stripe Connect, Check-in
```

Transformer un ensemble de tickets livrés en **fondation B2B testée, auditable et documentée**.

---

## COMMIT RULE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

Message attendu après validation CTO (BMAD) :

```txt
docs: BMAD TICKET-007G organizations QA hardening
```

Message attendu après validation CTO (code) :

```txt
test(organizations): TICKET-007G QA hardening and feature closeout
```

Option README seul si tests uniquement :

```txt
feat(organizations): TICKET-007G QA hardening — tests + README closeout
```

---

## CTO GATE

| Review | Required | Done |
|--------|----------|------|
| RBAC matrix tests complets | YES | ☐ |
| Ownership hardening vérifié | YES | ☐ |
| Slug + archive hardening | YES | ☐ |
| Audit smoke validé | YES | ☐ |
| Alembic head DB propre | YES | ☐ |
| README backend mis à jour | YES | ☐ |
| Risques restants documentés | YES | ☐ |
| Aucune nouvelle feature / endpoint | YES | ☐ |
| FEATURE-ORGANIZATIONS-V1 closeout | YES | ☐ |
| Contraintes DB uq/fk vérifiées | YES | ☑ |
| Rapport pytest org/auth/complet séparé | YES | ☑ |
| CTO Approval TICKET-007G | YES | ☑ |
