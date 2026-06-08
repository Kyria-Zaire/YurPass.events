# Code Review — YurPass

Posture : tech lead reviewant une PR avant merge sur `develop` ou `main`.

## Processus

1. Lire le ticket BMAD associé (contexte, critères d'acceptation)
2. Vérifier le diff — scope respecté ?
3. Appliquer les checklists ci-dessous
4. Classer : **Approve** | **Request Changes** | **Block** (sécu)

## Checklist générale

- [ ] Répond au ticket, rien de plus
- [ ] Pas de code mort ou commenté
- [ ] Nommage clair et cohérent
- [ ] Pas de duplication évitable
- [ ] Tests ajoutés pour logique nouvelle
- [ ] Pas de régression lint/typecheck

## Checklist backend

- [ ] Logique dans service, pas router
- [ ] Schemas Pydantic pour in/out
- [ ] Permissions vérifiées
- [ ] Migrations Alembic si schema change
- [ ] Pas de N+1 queries

## Checklist frontend

- [ ] Composant dans `packages/ui` si réutilisable
- [ ] Types depuis `packages/types`
- [ ] Pas de `any`
- [ ] Loading/error states gérés
- [ ] Responsive testé

## Checklist sécurité (bloquant)

- [ ] Pas de secret exposé
- [ ] Auth sur routes sensibles
- [ ] Webhook signature si applicable
- [ ] Input validation serveur
- [ ] RBAC correct

## Format feedback

```
## Summary
[1-2 phrases]

## Blockers
- [sécu ou bug critique]

## Suggestions
- [amélioration non bloquante]

## Verdict
Approve | Request Changes | Block
```

## Règle merge

Pas de merge sur `main` si checks CI critiques échouent.
