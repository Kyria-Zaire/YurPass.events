# Créateur Workflow — YurPass BMAD

> Planification · Tickets · Sprints · Gates CTO
> Path-scoped : `.claude/rules/createur-workflow.md` · Skill : `/createur-workflow`

## Gouvernance

- **Pas de code sans PRD** (`Ready For BMAD: YES`)
- **Pas de décision archi sans ADR** (`ACCEPTED`)
- **Un ticket = un scope fini**
- **DO NOT COMMIT** sans validation humaine

## Workflow

```
PRD → ADR (si archi) → BMAD → Implementation → Review → Validation → Merge
```

Templates : `docs/templates/PRD-TEMPLATE.md` · `ADR-TEMPLATE.md` · `BMAD-TEMPLATE.md`

## Header ticket

```
[BMAD] Phase: Sprint N
[FEATURE]: ...
[TICKET]: TICKET-XXX
[ROLE]: seniordev | architecte-api | constructeur-ui | ingenieur | reviewer-securite-code
```

## Sections obligatoires BMAD

CONTEXTE · OBJECTIF · IMPORTANT · INCLUS · EXCLUSIONS STRICTES · DATA/API/UI IMPACT · SECURITY NOTES · TESTS · ACCEPTANCE CRITERIA · OUTPUT ATTENDU · CTO GATE

## Sprints MVP

S0 Monorepo → S1 Auth → S2 Orgs → S3 Events → S4 Invitations → S5 Stripe → S6 Wallet → S7 Check-in → S8 Host → S9 Admin → S10 Hardening

## Gates CTO

| Doc | Gate |
|-----|------|
| PRD | Ready For BMAD: YES |
| ADR | ACCEPTED |
| BMAD | Archi + Security + QA + CTO |
