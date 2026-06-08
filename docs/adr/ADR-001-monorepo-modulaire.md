---
type: ADR
version: 1.0
status: ACCEPTED
owner: CTO
project: YurPass
date: 2026-06-08
---

# ADR-001 — Architecture Monorepo YurPass

## 1. META

| Champ | Valeur |
|-------|--------|
| **ADR ID** | ADR-001 |
| **Title** | Monorepo modulaire |
| **Status** | ACCEPTED |
| **Date** | 2026-06-08 |
| **Deciders** | CTO |
| **Related PRD** | PRD global produit |
| **Supersedes** | — |

## 2. CONTEXT

YurPass = infrastructure d'identité, d'invitation et d'accès aux expériences locales.

Plusieurs interfaces partagent types, design system, règles métier, enums, DTO et conventions : Web public, Admin, Mobile participant, Mobile staff, Backend API.

## 3. DECISION

**Nous avons décidé de développer YurPass en monorepo modulaire unique.**

```
yurpass/
├── backend/          # FastAPI + Python
├── frontend/
│   ├── apps/web/     # Next.js 15
│   ├── apps/admin/   # Next.js 15
│   └── packages/     # ui, types, utils, config
├── infra/docker/
├── docs/             # prd, adr, sprints, architecture
└── scripts/
```

Stack : FastAPI · PostgreSQL · Redis · Next.js 15 · Expo (différé) · Stripe · S3 · Docker VPS.

MVP = Web + Admin + Backend. Mobile reporté.

## 4. RATIONALE

- Réduction duplication types/DTO/design system
- Développement accéléré vibe coding maîtrisé
- CI/CD unifiée
- ADR/PRD/BMAD centralisés

## 5. ALTERNATIVES CONSIDERED

### Multi-repo

Rejeté : duplication, sync types coûteuse, CI fragmentée.

### Monolithe sans packages

Rejeté : pas de partage propre entre web/admin.

## 6. CONSEQUENCES

### Positive

- Types et UI partagés
- Un seul CI/CD
- Documentation centralisée

### Negative

- Repo plus volumineux
- Discipline branching requise

## 7. IMPLEMENTATION IMPACT

Backend : modules `router → service → repository`. Frontend : `packages/ui`. Infra : Docker Compose. Mobile Expo hors Docker au début.

## 8. COMPLIANCE

ADR-001 Monorepo ☑ · Security baseline ☑

## 9. VALIDATION

Sprint 0 Ticket 001 — Monorepo Foundation.

## 10. CTO APPROVAL

Architecture Approved ☑ · Security Approved ☑ · **Status: ACCEPTED** ☑
