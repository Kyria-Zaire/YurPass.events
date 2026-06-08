---
name: createur-workflow
description: Workflow BMAD YurPass — format tickets, sprints, branches.
disable-model-invocation: true
---

# Créateur Workflow — YurPass

Rule : `createur-workflow.mdc`.

## Template

`[BMAD] Sprint N | [FEATURE] | [TICKET] | [ROLE]` + CONTEXTE → OBJECTIF → INCLUS → EXCLUSIONS → CRITERIA → OUTPUT

## Sprints

S0-S10 : Monorepo → Auth → Orgs → Events → Invitations → Stripe → Wallet → Check-in → Host → Admin → Hardening

Branch : `feature/sprint-N-ticket-XXX-slug`
