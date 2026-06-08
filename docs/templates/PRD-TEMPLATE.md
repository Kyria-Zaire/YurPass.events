---
type: PRD
version: 1.0
status: DRAFT
owner: CTO
project: YurPass
---

# PRODUCT REQUIREMENTS DOCUMENT

> Le PRD n'est pas un cahier des charges.
> Le PRD est : **Pourquoi** le produit existe + **Qui** il sert + **Comment** il fonctionne + **Comment** il gagne de l'argent + **Comment** mesurer son succès.
>
> Chaque feature YurPass doit avoir son PRD avant toute exécution BMAD.
>
> Exemples : PRD-001 Authentication · PRD-002 Events · PRD-003 Organizations · PRD-004 Invitations · PRD-005 Ticketing · PRD-006 Passport

---

## 1. META

| Champ | Valeur |
|-------|--------|
| **PRD ID** | PRD-XXX |
| **Feature Name** | |
| **Owner** | |
| **Date** | YYYY-MM-DD |
| **Status** | DISCOVERY · READY · IN_PROGRESS · DONE · ARCHIVED |
| **Related ADR** | ADR-XXX |
| **Related BMAD** | Sprint N — TICKET-XXX |

---

## 2. EXECUTIVE SUMMARY

Décrire en 5-10 lignes :

- Quel problème est résolu
- Qui en bénéficie
- Pourquoi cette feature existe dans YurPass

---

## 3. BUSINESS CONTEXT

### Problem

Quel problème existe actuellement ?

### Impact

Que se passe-t-il si on ne fait rien ?

### Opportunity

Pourquoi vaut-il la peine de construire cette feature ?

---

## 4. GOALS

### Business Goals

- Goal 1
- Goal 2
- Goal 3

### User Goals

- Goal 1
- Goal 2
- Goal 3

---

## 5. NON GOALS

Lister explicitement ce qui n'est **PAS** inclus.

Exemples YurPass :

- Pas de chat
- Pas de notifications push (MVP)
- Pas de mobile natif (MVP)
- Pas d'IA embarquée
- Pas de multi-devise (MVP)

---

## 6. PERSONAS

### Persona 1

| | |
|---|---|
| **Name** | |
| **Role** | organisateur · participant · admin · staff |
| **Goals** | |
| **Pain Points** | |
| **Success Criteria** | |

### Persona 2

| | |
|---|---|
| **Name** | |
| **Role** | |
| **Goals** | |
| **Pain Points** | |
| **Success Criteria** | |

---

## 7. USER STORIES

### US-001

**As a** [User]
**I want** [action]
**So that** [benefit]

**Acceptance Criteria :**

- [ ] Critère 1
- [ ] Critère 2

### US-002

**As a** [User]
**I want** [action]
**So that** [benefit]

**Acceptance Criteria :**

- [ ] Critère 1
- [ ] Critère 2

---

## 8. FUNCTIONAL REQUIREMENTS

### FR-001

**Description :**

**Acceptance Criteria :**

- [ ]

### FR-002

**Description :**

**Acceptance Criteria :**

- [ ]

### FR-003

**Description :**

**Acceptance Criteria :**

- [ ]

---

## 9. NON FUNCTIONAL REQUIREMENTS

| Catégorie | Exigence |
|-----------|----------|
| **Performance** | ex. API < 200ms p95, page load < 2s |
| **Security** | ex. RBAC, rate limiting, audit logs |
| **Availability** | ex. 99.9% prod |
| **Accessibility** | ex. WCAG AA |
| **Scalability** | ex. 10k events simultanés |
| **Compliance** | ex. RGPD, conservation données |

---

## 10. DATA MODEL IMPACT

| | |
|---|---|
| **Entities involved** | User, Organization, Event... |
| **Tables involved** | |
| **New tables** | |
| **Modified tables** | |
| **Relationships** | |

Référence schéma MVP : `users`, `organizations`, `events`, `ticket_types`, `orders`, `payments`, `invitations`, `checkins`, `passports`, `badges`.

---

## 11. API IMPACT

| Endpoint | Method | Permission | Description |
|----------|--------|------------|-------------|
| `/api/v1/...` | GET/POST/PATCH/DELETE | `resource:action` | |

**Payloads :** référencer schemas Pydantic (`schemas.py`)

---

## 12. UI IMPACT

| Screen | App | Description |
|--------|-----|-------------|
| | web / admin | |

**Components :** packages/ui

**States obligatoires :** Loading · Error · Empty · Success

---

## 13. SECURITY

| Domaine | Exigence |
|---------|----------|
| **Authentication** | JWT, refresh, magic link, OTP, OAuth Google |
| **Authorization** | RBAC via `permissions.py` |
| **Rate limiting** | Login, API publiques |
| **Audit logs** | Actions admin |
| **Data protection** | Chiffrement, PII minimale |
| **Abuse prevention** | Honeypot, Turnstile |
| **Threats** | STRIDE ou liste menaces spécifiques |

---

## 14. ANALYTICS

| Event tracked | Description |
|---------------|-------------|
| | |

**KPIs :**

- KPI 1
- KPI 2

**Success metrics :**

- Metric 1
- Metric 2

---

## 15. RISKS

| Risk | Impact | Mitigation |
|------|--------|------------|
| | High/Med/Low | |

---

## 16. ROLLOUT PLAN

### Phase 1

Scope minimal livrable.

### Phase 2

Extensions.

### Phase 3

Optimisations / scale.

---

## 17. ACCEPTANCE CRITERIA

Checklist validation globale feature :

- [ ] Tous les FR validés
- [ ] NFR respectés
- [ ] Sécurité review passée
- [ ] Tests passent
- [ ] UI states complets
- [ ] Documentation à jour

---

## 18. CTO APPROVAL

| Gate | Approved | Date | Notes |
|------|----------|------|-------|
| Architecture Approved | ☐ | | |
| Security Approved | ☐ | | |
| Product Approved | ☐ | | |
| **Ready For BMAD** | **YES / NO** | | |

> Aucun ticket BMAD ne démarre sans **Ready For BMAD: YES**.
