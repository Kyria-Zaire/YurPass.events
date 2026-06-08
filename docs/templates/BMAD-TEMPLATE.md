---
type: BMAD
version: 1.0
owner: CTO
project: YurPass
---

# BUILD MODE ARCHITECTURE DEVELOPMENT

> Le PRD dit **QUOI** et **POURQUOI**.
> Le BMAD dit **COMMENT**.
> C'est lui qui pilote Cursor et Claude Code.

## Philosophy

No code without:

- PRD (Ready For BMAD: YES)
- Scope défini
- Acceptance Criteria mesurables
- Security Review

---

## WORKFLOW

```
PRD
 ↓
ADR (si décision architecture)
 ↓
BMAD (ce document)
 ↓
Implementation
 ↓
Review (/code-review + /reviewer-securite-code)
 ↓
Validation
 ↓
Merge (CTO Gate)
```

---

# TICKET

```
[BMAD] Phase: Sprint N
[FEATURE]: Nom feature
[TICKET]: TICKET-XXX
[ROLE]: seniordev | architecte-api | constructeur-ui | ingenieur | reviewer-securite-code
```

---

## CONTEXTE

**Business context :**

**Current architecture :**

**Dependencies :**

**Constraints :**

**Related PRD :** PRD-XXX
**Related ADR :** ADR-XXX

---

## OBJECTIF

Décrire le résultat attendu à la fin de ce ticket.

---

## IMPORTANT

**Rules to follow :**

- `.claude/rules/seniordev.md` / `seniordev.mdc`
- ADR-001 monorepo
- `router → service → repository`

**Architecture constraints :**

**Security constraints :**

**Performance constraints :**

---

## INCLUS

Liste explicite du travail inclus :

1.
2.
3.
4.

---

## EXCLUSIONS STRICTES

Liste explicite du travail interdit dans ce ticket :

1.
2.
3.
4.

---

## DATA IMPACT

| | |
|---|---|
| **Tables** | |
| **Migrations** | alembic/versions/xxx |
| **Entities** | |
| **Relationships** | |

---

## API IMPACT

| Endpoint | Method | Permission | Schema |
|----------|--------|------------|--------|
| | | | |

**Schemas :** `modules/{domain}/schemas.py`

---

## UI IMPACT

| Page | App | Route |
|------|-----|-------|
| | web / admin | |

**Components :** `packages/ui/...`

**States :** Loading · Error · Empty · Success

---

## SECURITY NOTES

| Domaine | Action |
|---------|--------|
| **RBAC** | permissions requises |
| **Validation** | Pydantic / Zod |
| **Rate limiting** | endpoints concernés |
| **Audit logs** | actions admin |
| **Webhook protection** | signature + idempotence |
| **Threat analysis** | menaces spécifiques |

---

## TESTS REQUIRED

- [ ] **Unit** — service layer
- [ ] **Integration** — router + DB
- [ ] **E2E** — flow critique (si applicable)
- [ ] **Manual** — checklist QA

---

## ACCEPTANCE CRITERIA

- [ ] Critère 1 — mesurable
- [ ] Critère 2 — mesurable
- [ ] Critère 3 — mesurable
- [ ] Critère 4 — mesurable

---

## OUTPUT ATTENDU

**Files created :**

```
-
```

**Files modified :**

```
-
```

**Commands executed :**

```
-
```

**Validation proof :**

```
pytest / pnpm lint / pnpm typecheck / docker compose up
```

---

## REVIEW CHECKLIST

- [ ] Architecture — respect ADR, modules, découplage
- [ ] Security — `/reviewer-securite-code`
- [ ] Code Quality — `/code-review`, lint, types
- [ ] Performance — pas de N+1, pagination
- [ ] Accessibility — WCAG AA si UI
- [ ] Maintainability — pas de duplication, nommage clair

---

## COMMIT RULE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

---

## CTO GATE

Before merge on `main` or `develop` :

| Review | Required | Done |
|--------|----------|------|
| Architecture Review | YES | ☐ |
| Security Review | YES | ☐ |
| QA Review | YES | ☐ |
| CTO Approval | YES | ☐ |

**Branch :** `feature/sprint-N-ticket-XXX-slug`
