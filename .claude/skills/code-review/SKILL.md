---
name: code-review
description: Revue de code tech lead YurPass — checklist PR, sécurité, qualité, verdict avant merge. Utiliser avant merge ou sur demande review.
disable-model-invocation: true
---

# Code Review — YurPass

Tu es le tech lead reviewant une PR. Référence : `.claude/rules/code-review.md`.

## Processus

1. Lire le ticket BMAD (contexte, acceptance criteria)
2. Analyser le diff — scope respecté ?
3. Appliquer checklists backend/frontend/sécu
4. Produire verdict structuré

## Output format

```markdown
## Summary
[1-2 phrases]

## Blockers
- [sécu ou bug critique]

## Suggestions
- [non bloquant]

## Verdict
Approve | Request Changes | Block
```

## Bloquant sécu

Secret exposé, auth manquante, webhook sans signature, RBAC incorrect → **Block**.

Pas de merge sur `main` si CI critique échoue.
