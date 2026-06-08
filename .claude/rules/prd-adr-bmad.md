# PRD → ADR → BMAD — Workflow obligatoire YurPass

## Le trio

| Doc | Question | Template |
|-----|----------|----------|
| **PRD** | QUOI + POURQUOI | `docs/templates/PRD-TEMPLATE.md` |
| **ADR** | Décision architecture | `docs/templates/ADR-TEMPLATE.md` |
| **BMAD** | COMMENT exécuter | `docs/templates/BMAD-TEMPLATE.md` |

## Workflow

```
PRD (Ready For BMAD: YES)
 ↓
ADR (ACCEPTED — si décision architecture)
 ↓
BMAD (ticket sprint)
 ↓
Implementation
 ↓
Review (/code-review + /reviewer-securite-code)
 ↓
Validation → Merge (CTO Gate)
```

## Règles agents

1. **Ne pas coder** sans PRD validé
2. **Ne pas implémenter** décision archi sans ADR ACCEPTED
3. Chaque ticket = BMAD dans `docs/sprints/`
4. `/createur-workflow` pour rédiger tickets
5. **DO NOT COMMIT** sans validation humaine

## Gates

- PRD → Ready For BMAD: YES
- ADR → ACCEPTED
- BMAD → CTO Gate (Archi + Security + QA + CTO)

Index complet : `docs/templates/README.md`
