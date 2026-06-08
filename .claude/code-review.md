# Code Review — YurPass

> Tech Lead · Revue PR avant merge
> Path-scoped : `.claude/rules/code-review.md` · Skill : `/code-review`

## Gouvernance

- Review **obligatoire** avant merge `develop` ou `main`
- Verdict : **Approve** | **Request Changes** | **Block** (sécu)
- **DO NOT COMMIT** — la review produit un rapport, pas un commit

## Processus

1. Lire ticket BMAD + PRD/ADR liés
2. Vérifier scope du diff
3. Checklists ci-dessous
4. Verdict structuré

## Checklist

**Général :** scope ticket · pas de code mort · tests · lint/types

**Backend :** logique dans service · permissions · migrations si schema

**Frontend :** `packages/ui` · types · loading/error states

**Sécu (bloquant) :** auth · RBAC · webhook signature · pas de secrets

## Format output

```markdown
## Summary
## Blockers
## Suggestions
## Verdict: Approve | Request Changes | Block
```

## Règle merge

Pas de merge si CI critique échoue ou verdict Block.
