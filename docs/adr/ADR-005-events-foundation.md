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
  - ADR-004-organizations-foundation.md
blocks:
  - ADR-006-ticketing-foundation
  - ADR-007-payments-stripe-connect-foundation
  - ADR-008-check-in-foundation
---

# ADR-005 — Events Foundation

## Statut

Accepté

## Date

2026-06-08

## Contexte

FEATURE-AUTH-V1 est clôturée.

FEATURE-ORGANIZATIONS-V1 est clôturée.

YurPass dispose désormais :

- Authentification complète (JWT, sessions, OAuth)
- RBAC global et organisationnel (`require_org_roles`)
- `organizations` + `organization_members` opérationnels
- Audit logs consolidés Organizations

YurPass doit maintenant permettre aux organisations de **créer et publier des événements**.

L'événement devient l'**entité métier centrale** de la plateforme — pivot entre Organizations (B2B) et les futurs modules Ticketing, Paiement et Check-in.

---

## Décision

Établir la chaîne métier officielle :

```
Organization
  → Event
    → TicketType
      → Order
        → Ticket
          → CheckIn
```

**Règles d'intégrité :**

| Entité | Dépend de |
|--------|-----------|
| Ticket | Event (obligatoire) |
| Order | TicketType (obligatoire) |
| CheckIn | Ticket valide (obligatoire) |

Sprint 3 (Events V1) couvre **uniquement la fondation Event** — pas Ticketing, Orders, ni Check-in.

---

## Ownership

Chaque Event appartient à **une seule** Organization.

```
Organization (1) → Event (N)
```

| Règle | Détail |
|-------|--------|
| FK | `events.organization_id → organizations.id` |
| Suppression | Logique uniquement — pas de suppression physique |
| Cascade métier | Archiver un Event n'implique pas Ticketing en V1 (hors scope) |

---

## Modèle Event (fondation)

Table cible : `events`

Champs fondamentaux (détail schéma en TICKET-008A) :

| Champ | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| organization_id | UUID FK organizations | Ownership |
| title | VARCHAR | |
| slug | VARCHAR | Unique par organisation ou global — à préciser en 008A |
| type | ENUM | Voir EventType |
| status | ENUM | Voir EventStatus |
| visibility | ENUM | Voir EventVisibility |
| description | TEXT nullable | |
| starts_at | TIMESTAMPTZ | |
| ends_at | TIMESTAMPTZ nullable | |
| venue_name | VARCHAR nullable | |
| city | VARCHAR nullable | |
| country | VARCHAR nullable | |
| created_by_user_id | UUID FK users | |
| published_at | TIMESTAMPTZ nullable | Renseigné à la publication |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Principe :** aucune suppression physique en Events V1.

---

## EventStatus

| Valeur | Description |
|--------|-------------|
| `draft` | Brouillon — non visible publiquement |
| `published` | Publié — visible selon `visibility` |
| `sold_out` | Publié mais capacité épuisée (futur Ticketing) |
| `cancelled` | Annulé |
| `archived` | Archivé logiquement |

### Transitions autorisées

```txt
draft       → published
published   → sold_out
published   → cancelled
published   → archived
sold_out    → archived
cancelled   → archived
```

**Règle :** aucun retour arrière. Une fois `published`, retour à `draft` interdit.

---

## EventVisibility

| Valeur | Description |
|--------|-------------|
| `public` | Visible dans le catalogue public |
| `unlisted` | Accessible par lien direct uniquement |
| `private` | Accès restreint (membres org / invitations futures) |

---

## EventType

| Valeur |
|--------|
| `nightclub` |
| `festival` |
| `concert` |
| `conference` |
| `association` |
| `sports` |
| `other` |

---

## RBAC

RBAC organisationnel via `require_org_roles()` — réutilisation ADR-004.

| Action | Rôles autorisés |
|--------|-----------------|
| Création Event | `owner`, `admin` |
| Modification Event | `owner`, `admin` |
| Publication (`draft → published`) | `owner`, `admin` |
| Lecture interne (org scope) | `owner`, `admin`, `staff` |
| Catalogue public | `public` uniquement — pas de JWT requis |

**Principes :**

- `staff` : lecture interne, pas d'écriture Event en V1
- `viewer` : pas d'accès Events internes (sauf évolution documentée en 008)
- `super_admin` : bypass support audité (même pattern Organizations)

---

## Endpoints cibles (Sprint 3)

Détail par ticket BMAD — périmètre MVP :

| Ticket | Scope |
|--------|-------|
| **008A** | Event Foundation — modèle, migration, enums |
| **008B** | Event CRUD — création, lecture interne, modification |
| **008C** | Event Publication — transitions status |
| **008D** | Public Catalog — catalogue `public` + `published` |

Routes attendues (indicatif) :

```txt
POST   /api/organizations/{organization_id}/events
GET    /api/organizations/{organization_id}/events
GET    /api/organizations/{organization_id}/events/{event_id}
PATCH  /api/organizations/{organization_id}/events/{event_id}
POST   /api/organizations/{organization_id}/events/{event_id}/publish
GET    /api/events                    # catalogue public (008D)
GET    /api/events/{event_id}         # détail public (008D)
```

Layering obligatoire : `router → service → repository`.

---

## Audit Logs

Événements obligatoires (à intégrer en Sprint 3) :

- `event_created`
- `event_updated`
- `event_published`
- `event_cancelled`
- `event_archived`
- `event_rbac_super_admin_bypass` (si applicable)

Conventions : réutiliser le pattern ADR-004 / TICKET-007F (`resource_type`, `organization_id` en metadata).

---

## MVP Sprint 3 — Découpage tickets

| Ticket | Slug | Livrable |
|--------|------|----------|
| 008A | `event-foundation` | Table `events`, enums, migration Alembic |
| 008B | `event-crud` | CRUD interne sous organisation |
| 008C | `event-publication` | Publication + transitions status |
| 008D | `public-catalog` | Catalogue public (`visibility=public`, `status=published`) |

**Dépendances :**

```txt
008A → 008B → 008C → 008D
```

---

## Exclusions

Hors scope Events V1 (Sprint 3) :

- Ticketing
- TicketType (schéma complet)
- Stripe / Paiements
- Orders
- QR codes
- Check-in
- Analytics
- Invitations tokenisées
- Frontend avancé
- Suppression physique

Ces modules feront l'objet d'ADR et tickets dédiés (ADR-006 → ADR-008).

---

## ADR Futurs

| ADR | Sujet |
|-----|-------|
| ADR-006 | Ticketing Foundation |
| ADR-007 | Payments & Stripe Connect Foundation |
| ADR-008 | Check-in Foundation |

---

## Conséquences

Le prochain domaine métier prioritaire est **Events**.

Tous les futurs modules Ticketing, Paiement et Check-in **dépendent** de cette fondation.

Chaîne métier complète :

```
User → OrganizationMember → Organization → Event → TicketType → Order → Ticket → CheckIn → Revenue
                                              ▲
                                         Sprint 3 (ce ADR)
```

Organizations V1 reste la couche B2B stable ; Events V1 en devient la couche produit centrale visible par les utilisateurs finaux.

---

## Références

- ADR-004 Organizations Foundation
- FEATURE-ORGANIZATIONS-V1 — CLOSED (`007A` → `007G`)
- PRD V3.1
