# Créateur Workflow — YurPass

## Colonne vertébrale : PRD → ADR → BMAD

```
PRD (QUOI/POURQUOI) → ADR (décision archi) → BMAD (COMMENT) → Code → Review → Merge
```

Templates : `docs/templates/PRD-TEMPLATE.md` · `ADR-TEMPLATE.md` · `BMAD-TEMPLATE.md`

## Template BMAD complet

Copier `docs/templates/BMAD-TEMPLATE.md` → `docs/sprints/sprint-N/TICKET-XXX-slug.md`

Sections obligatoires : CONTEXTE · OBJECTIF · IMPORTANT · INCLUS · EXCLUSIONS STRICTES · DATA IMPACT · API IMPACT · UI IMPACT · SECURITY NOTES · TESTS REQUIRED · ACCEPTANCE CRITERIA · OUTPUT ATTENDU · REVIEW CHECKLIST · CTO GATE

**DO NOT COMMIT WITHOUT EXPLICIT HUMAN VALIDATION**

## Ordre sprints officiel

| Sprint | Focus |
|--------|-------|
| S0 | Monorepo + Docker + CI |
| S1 | Auth + Users + RBAC |
| S2 | Organizations |
| S3 | Events |
| S4 | Invitations |
| S5 | Ticketing + Stripe |
| S6 | Wallet + QR |
| S7 | Check-in |
| S8 | Host Dashboard |
| S9 | Admin |
| S10 | Hardening MVP |

## Règles workflow

1. Un ticket = un scope fini
2. Branch nommée `feature/sprint-N-ticket-XXX-slug`
3. PR vers `develop`, merge `main` après validation
4. Invoquer le skill/rôle correspondant au début du travail
5. Code review avant merge

## ADR

Décisions architecture dans `docs/adr/`. ADR-001 = monorepo validé.

## Documentation

- PRD : `docs/prd/`
- Architecture : `docs/architecture/`
- Sprints : `docs/sprints/`
