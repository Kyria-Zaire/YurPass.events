# YurPass — Documentation Templates

> Colonne vertébrale du projet. Pilote humains, Cursor, Claude Code, futurs devs et associés.

## Le trio PRD → ADR → BMAD

```
┌─────────────────────────────────────────────────────────────┐
│  PRD          Pourquoi le produit / feature existe          │
│  (Product)    Qui · Comment · Revenue · Métriques           │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌──────────────────────────┴──────────────────────────────────┐
│  ADR          Décision d'architecture structurante          │
│  (Decision)   Contexte · Alternatives · Conséquences        │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌──────────────────────────┴──────────────────────────────────┐
│  BMAD         Exécution technique (tickets)                 │
│  (Build)      Scope · Inclus/Exclus · Tests · Review        │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
                    Implementation
                           ↓
              Review → Validation → Merge
```

## Fichiers templates

| Template | Claude (.md) | Cursor (.mdc) | Destination |
|----------|---------------|---------------|-------------|
| PRD | `PRD-TEMPLATE.md` | `PRD-TEMPLATE.mdc` | `docs/prd/PRD-XXX-slug.md` |
| ADR | `ADR-TEMPLATE.md` | `ADR-TEMPLATE.mdc` | `docs/adr/ADR-XXX-slug.md` |
| BMAD | `BMAD-TEMPLATE.md` | `BMAD-TEMPLATE.mdc` | `docs/sprints/sprint-N/TICKET-XXX.md` |

## PRD roadmap MVP

| ID | Feature | Sprint |
|----|---------|--------|
| PRD-001 | Authentication | S1 |
| PRD-002 | Events | S3 |
| PRD-003 | Organizations | S2 |
| PRD-004 | Invitations | S4 |
| PRD-005 | Ticketing | S5 |
| PRD-006 | Passport | S6 |

## Règles d'or

1. **Pas de code sans PRD** (Ready For BMAD: YES)
2. **Pas de décision archi sans ADR** (Status: ACCEPTED)
3. **Pas de merge sans BMAD complet** + CTO Gate
4. **DO NOT COMMIT** sans validation humaine explicite

## Gates CTO

| Document | Gate | Condition |
|----------|------|-----------|
| PRD | Ready For BMAD | Architecture + Security + Product approved |
| ADR | ACCEPTED | Architecture + Security approved |
| BMAD | CTO Gate | Archi + Security + QA + CTO approval |

## Pour les agents IA

- Claude Code : lire `docs/templates/*.md` + invoquer `/createur-workflow`
- Cursor : rules `prd-adr-bmad.mdc` + `/createur-workflow`
- Skills sécu : `/reviewer-securite-code` avant tout merge auth/paiements/webhooks

## ADR existants

| ID | Title | Status |
|----|-------|--------|
| ADR-001 | Monorepo modulaire | ACCEPTED |
