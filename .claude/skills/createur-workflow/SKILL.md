---
name: createur-workflow
description: Créateur workflow BMAD YurPass — format tickets, sprints, branches, ADR. Utiliser pour planification et rédaction tickets.
disable-model-invocation: true
---

# Créateur Workflow — YurPass

Tu prépares PRD, ADR et tickets BMAD. Références :
- `docs/templates/PRD-TEMPLATE.md`
- `docs/templates/ADR-TEMPLATE.md`
- `docs/templates/BMAD-TEMPLATE.md`
- `docs/templates/README.md`

## Workflow

PRD (Ready YES) → ADR (ACCEPTED) → BMAD → Code → Review → Merge

## Template BMAD

Copier `docs/templates/BMAD-TEMPLATE.md` intégralement. Ne pas raccourcir les sections SECURITY, TESTS, CTO GATE.

## Sprints

S0 Monorepo → S1 Auth → S2 Orgs → S3 Events → S4 Invitations → S5 Stripe → S6 Wallet → S7 Check-in → S8 Host → S9 Admin → S10 Hardening

## Branch

`feature/sprint-N-ticket-XXX-slug`

## Règles

1 ticket = 1 scope fini. Invoquer le skill rôle au début. Review avant merge.
