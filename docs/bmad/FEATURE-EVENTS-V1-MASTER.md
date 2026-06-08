---
type: BMAD
kind: MASTER
version: 1.0
owner: CTO
project: YurPass
feature: FEATURE-EVENTS-V1
sprint: 3
status: PROPOSED
date: 2026-06-08
related_prd: docs/prd/yurpass-prd-v3.md
related_adr: docs/adr/ADR-005-events-foundation.md
depends_on:
  - FEATURE-AUTH-V1
  - FEATURE-ORGANIZATIONS-V1
ready_for_bmad: pending
---

# BMAD MASTER — FEATURE-EVENTS-V1

> Document maître de découpage Sprint 3 — Events Foundation.
> Chaque sous-ticket (008A → 008F) sera rédigé en BMAD détaillé **après validation CTO de ce master**.
> Aucun code sans ADR-005 `ACCEPTED` + sous-ticket BMAD validé.

```
[BMAD] Phase: SPRINT 3 — FEATURE-EVENTS-V1
[FEATURE]: FEATURE-EVENTS-V1
[MASTER]: FEATURE-EVENTS-V1-MASTER
[ROLE]: Product Architect + Backend Architect + Security Reviewer
```

---

## 1. CONTEXTE

**Business context :**

FEATURE-AUTH-V1 et FEATURE-ORGANIZATIONS-V1 sont **clôturées**. ADR-005 Events Foundation est **ACCEPTED** (`2e7478f`).

YurPass entre dans son **deuxième sprint métier**. L'événement devient l'**entité produit centrale** — les organisateurs (clubs, festivals, associations) créent et publient des événements sous leur Organization.

**Current architecture :**

- Auth complète + RBAC global (FEATURE-AUTH-V1)
- Organizations CRUD + Members + RBAC org + audit (`require_org_roles`, 9 endpoints)
- Module `events/` en placeholder backend
- Pattern obligatoire : `router → service → repository`
- Migrations head Organizations : `20260608_007`

**Dependencies :**

| Prérequis | Statut |
|-----------|--------|
| FEATURE-AUTH-V1 (006A → 006G) | Clôturée |
| FEATURE-ORGANIZATIONS-V1 (007A → 007G) | Clôturée |
| ADR-004 Organizations | ACCEPTED |
| ADR-005 Events Foundation | ACCEPTED |
| PRD V3.1 | Référence produit |

**Constraints :**

- Chaque Event ∈ **une** Organization (`organization_id` FK)
- RBAC Events via `require_org_roles()` — **pas de nouveau système RBAC**
- `EventStatus` transitions **sans retour arrière** (ADR-005)
- Archive / cancel = logique — **pas de suppression physique**
- Catalogue public = `visibility=public` + `status=published` uniquement
- `super_admin` : bypass support **audité** (pattern Organizations)

**Related PRD :** `docs/prd/yurpass-prd-v3.md` (V3.1)  
**Related ADR :** `docs/adr/ADR-005-events-foundation.md`

---

## 2. OBJECTIF GLOBAL

Découper **FEATURE-EVENTS-V1** en tickets **séquentiels**, **testables** et **validables CTO**, sans big-bang.

À la fin de **008F**, le backend expose les endpoints Events ADR-005, avec publication, catalogue public, audit et QA hardening.

**Chaîne métier officielle (ADR-005) :**

```
Organization → Event → TicketType → Order → Ticket → CheckIn
                  ▲
            Sprint 3 (ce master)
```

Ticketing / Orders / Check-in = **hors scope** Sprint 3.

---

## 3. ORDRE D'EXÉCUTION

```
008A ──► 008B ──► 008C ──► 008D ──► 008E ──► 008F
Events    Event     Event      Public    Event     QA
model     CRUD      publication catalog   audit     closeout
+ mig               status     routes    consolidate hardening
```

| Bloc ADR-005 MVP | Tickets |
|------------------|---------|
| MVP officiel ADR | 008A → 008D |
| Clôture qualité (pattern Organizations 007F/007G) | 008E → 008F |

Chaque ticket doit être **validé CTO** avant le suivant.

---

## 4. DÉCOUPAGE OFFICIEL

### TICKET-008A — Event Foundation

| Champ | Valeur |
|-------|--------|
| **Slug** | `event-foundation` |
| **Rôle** | Backend Architect |
| **Dépend de** | FEATURE-ORGANIZATIONS-V1 |
| **Bloque** | 008B → 008F |

**Objectif :** Poser le modèle de données `events` et la couche repository — sans endpoints HTTP.

**Inclus :**

- Table `events` (champs ADR-005)
- Enums `EventType`, `EventStatus`, `EventVisibility`
- Modèle SQLAlchemy `Event`
- `EventRepository` foundation
- FK `organization_id → organizations.id`
- Migration Alembic (head `20260608_008` ou suivant)
- Slug event — décision unique org vs global documentée en BMAD 008A
- Tests modèle + repository + migration

**Exclusions :**

- Endpoints HTTP
- Publication / transitions status (008C)
- Catalogue public (008D)
- Ticketing / Stripe / Check-in

---

### TICKET-008B — Event CRUD

| Champ | Valeur |
|-------|--------|
| **Slug** | `event-crud` |
| **Rôle** | Backend Architect |
| **Dépend de** | 008A |
| **Bloque** | 008C, 008E |

**Objectif :** CRUD interne Events sous organisation — statut initial `draft`.

**Inclus :**

- `POST /api/organizations/{organization_id}/events`
- `GET /api/organizations/{organization_id}/events`
- `GET /api/organizations/{organization_id}/events/{event_id}`
- `PATCH /api/organizations/{organization_id}/events/{event_id}`
- RBAC : création/modification `owner`, `admin` ; lecture `owner`, `admin`, `staff`
- `created_by_user_id` renseigné à la création
- `EventService` + router nested sous organizations
- Layering `router → service → repository`
- Tests intégration CRUD + RBAC

**Exclusions :**

- Publication (`draft → published`) — 008C
- Routes publiques `/api/events` — 008D
- Transitions `sold_out`, `cancelled`, `archived` — 008C
- Audit consolidation — 008E

**Endpoints :**

| Méthode | Route |
|---------|-------|
| POST | `/api/organizations/{organization_id}/events` |
| GET | `/api/organizations/{organization_id}/events` |
| GET | `/api/organizations/{organization_id}/events/{event_id}` |
| PATCH | `/api/organizations/{organization_id}/events/{event_id}` |

---

### TICKET-008C — Event Publication

| Champ | Valeur |
|-------|--------|
| **Slug** | `event-publication` |
| **Rôle** | Backend Architect + Security Reviewer |
| **Dépend de** | 008B |
| **Bloque** | 008D, 008E |

**Objectif :** Gérer les transitions `EventStatus` conformes ADR-005.

**Inclus :**

- `POST /api/organizations/{organization_id}/events/{event_id}/publish` (ou action dédiée documentée)
- Transitions autorisées :
  - `draft → published`
  - `published → sold_out` (stub / manuel V1 — pas de Ticketing)
  - `published → cancelled`
  - `published → archived`
  - `sold_out → archived`
  - `cancelled → archived`
- **Aucun retour arrière** (`published → draft` interdit)
- `published_at` renseigné à la publication
- RBAC : `owner`, `admin` uniquement
- Validation métier (champs requis avant publish — documenter en BMAD 008C)
- Tests transitions valides / invalides

**Exclusions :**

- Catalogue public (008D)
- Ticketing auto `sold_out`
- Suppression physique

---

### TICKET-008D — Public Catalog

| Champ | Valeur |
|-------|--------|
| **Slug** | `public-catalog` |
| **Rôle** | Backend Architect |
| **Dépend de** | 008C |
| **Bloque** | 008E, 008F |

**Objectif :** Exposer le catalogue public — sans authentification.

**Inclus :**

- `GET /api/events` — liste paginée/filtrée
- `GET /api/events/{event_id}` — détail public
- Filtre strict : `status=published` AND `visibility=public`
- `unlisted` / `private` : **non listés** ; accès direct `unlisted` — décision BMAD 008D
- Pas de JWT requis sur routes publiques
- Tests catalogue + exclusion draft/archived/cancelled/private

**Exclusions :**

- Réservation / achat billet
- Analytics
- Frontend

**Endpoints :**

| Méthode | Route |
|---------|-------|
| GET | `/api/events` |
| GET | `/api/events/{event_id}` |

---

### TICKET-008E — Event Audit Consolidation

| Champ | Valeur |
|-------|--------|
| **Slug** | `event-audit-consolidation` |
| **Rôle** | Backend Security Engineer + Audit Architecture Reviewer |
| **Dépend de** | 008B, 008C |
| **Bloque** | 008F |

**Objectif :** Uniformiser audit Events — pattern TICKET-007F.

**Inclus :**

- `AuditAction` : `event_created`, `event_updated`, `event_published`, `event_cancelled`, `event_archived`, `event_rbac_super_admin_bypass`
- Conventions `resource_type` / `resource_id` / `metadata_json`
- `organization_id` obligatoire en metadata
- Helper `events/audit.py` (recommandé)
- Sanitization — réutiliser `AuditService`
- Tests shape audit

**Exclusions :**

- Nouvelle table audit
- Changement métier Events

---

### TICKET-008F — Events QA Hardening

| Champ | Valeur |
|-------|--------|
| **Slug** | `events-qa-hardening` |
| **Rôle** | Senior QA Engineer + Backend Security Reviewer + CTO Reviewer |
| **Dépend de** | 008A → 008E |
| **Bloque** | Sprint 3 clôture Events |

**Objectif :** Validation finale — clôture FEATURE-EVENTS-V1.

**Inclus :**

- Matrice RBAC Events (owner/admin/staff/viewer × routes)
- Transitions status exhaustives testées
- Catalogue public hardening
- Contraintes DB (`fk events.organization_id`, slug unique si applicable)
- Non-régression Auth + Organizations (rapport pytest séparé)
- `alembic upgrade head` DB vierge
- `backend/README.md` section Events
- Rapport clôture FEATURE-EVENTS-V1

**Exclusions :**

- Nouvelles features hors ADR-005

---

## 5. MATRICE ENDPOINTS → TICKETS

| Endpoint | Ticket |
|----------|--------|
| `POST /api/organizations/{organization_id}/events` | 008B |
| `GET /api/organizations/{organization_id}/events` | 008B |
| `GET /api/organizations/{organization_id}/events/{event_id}` | 008B |
| `PATCH /api/organizations/{organization_id}/events/{event_id}` | 008B |
| `POST /api/organizations/{organization_id}/events/{event_id}/publish` | 008C |
| `POST .../cancel` ou transition dédiée | 008C |
| `POST .../archive` ou transition dédiée | 008C |
| `GET /api/events` | 008D |
| `GET /api/events/{event_id}` | 008D |

---

## 6. RBAC EVENTS (RAPPEL ADR-005)

| Action | Rôles |
|--------|-------|
| Création Event | owner, admin |
| Modification Event | owner, admin |
| Publication / transitions | owner, admin |
| Lecture interne (org scope) | owner, admin, staff |
| Catalogue public | public (sans JWT) |

**Interdit :** `viewer` sur routes Events internes en V1 (sauf décision contraire documentée en 008B).

---

## 7. EVENT STATUS (RAPPEL)

```txt
draft → published
published → sold_out | cancelled | archived
sold_out → archived
cancelled → archived
```

Aucun retour arrière.

---

## 8. RÈGLES STRICTES (FEATURE-EVENTS-V1)

**Interdit dans tous les sous-tickets 008A → 008F :**

- Ticketing / TicketType (schéma complet)
- Stripe / Paiements / Orders
- QR codes
- Check-in
- Analytics
- Invitations tokenisées
- Frontend avancé
- Suppression physique `events`
- Modifier Auth / Organizations RBAC sauf deps nécessaires
- Mélanger `global_role` et `organization_role`

---

## 9. MODÈLE DE DONNÉES CIBLE (VUE MASTER)

| Table / Enum | Ticket | Rôle |
|--------------|--------|------|
| `events` | 008A | Entité produit centrale |
| `EventType` | 008A | nightclub, festival, concert, … |
| `EventStatus` | 008A | draft → archived |
| `EventVisibility` | 008A | public, unlisted, private |
| Audit events | 008E | Traçabilité via `audit_logs` |

---

## 10. ACCEPTANCE FEATURE — CRITÈRES DE CLÔTURE

**FEATURE-EVENTS-V1** est clôturée **uniquement si** :

- [ ] `events` existe et est migrée
- [ ] CRUD interne Events fonctionne (4 endpoints org-scoped)
- [ ] Publication + transitions status conformes ADR-005
- [ ] Catalogue public fonctionne (2 endpoints)
- [ ] RBAC org appliqué sur routes internes
- [ ] Audit events consolidé
- [ ] Tests permissions + hardening verts
- [ ] Ruff OK
- [ ] Migrations Alembic OK (head documenté)
- [ ] `backend/README.md` mis à jour
- [ ] Non-régression Auth + Organizations
- [ ] Les 6 sous-tickets 008A → 008F validés CTO

---

## 11. CHAÎNE MÉTIER CIBLE

```
User → OrganizationMember → Organization → Event → TicketType → Order → Ticket → CheckIn
                                              ▲
                                         Sprint 3 (ce master)
```

---

## 12. BRANCHING (RECOMMANDÉ)

```
feature/sprint-3-ticket-008a-event-foundation
feature/sprint-3-ticket-008b-event-crud
feature/sprint-3-ticket-008c-event-publication
feature/sprint-3-ticket-008d-public-catalog
feature/sprint-3-ticket-008e-event-audit
feature/sprint-3-ticket-008f-events-qa-hardening
```

---

## 13. PROCHAINES ÉTAPES

1. Validation CTO de ce **BMAD MASTER**
2. Commit : `docs: BMAD FEATURE-EVENTS-V1 master`
3. Rédiger **TICKET-008A** en BMAD détaillé (premier ticket exécutable)
4. Exécution 008A → validation CTO → 008B → …
5. Clôture FEATURE-EVENTS-V1 → ouverture ADR-006 Ticketing

---

## COMMIT RULE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

---

## CTO GATE (MASTER)

| Review | Required | Done |
|--------|----------|------|
| Découpage tickets cohérent (008A → 008F) | YES | ☐ |
| Alignement ADR-005 | YES | ☐ |
| Réutilisation RBAC org (`require_org_roles`) | YES | ☐ |
| Pas de big-bang (fondation avant endpoints) | YES | ☐ |
| Exclusions respectées (Ticketing, Stripe, etc.) | YES | ☐ |
| Transitions status sans retour arrière | YES | ☐ |
| CTO Approval MASTER | YES | ☐ |
