# Improve Codebase Architecture — YurPass

> Monorepo · Découplage · Évolutivité
> Path-scoped : `.claude/rules/improve-codebase-architecture.md` · Always apply

## Gouvernance

- Pas de modification architecture hors ADR + ticket
- Apps → packages (jamais l'inverse)
- Backend ↔ Frontend via API REST uniquement

## Dépendances autorisées

```
apps/web, apps/admin → packages/ui, types, utils, config
packages/ui → packages/utils, config
backend/modules/X → backend/shared, backend/core
```

## Anti-patterns

- App importe une autre app
- Logique métier dans `packages/ui`
- God module
- Couplage direct inter-modules
- Big-bang rewrite

## Évolution

Nouveau domaine = nouveau module backend + types frontend
Breaking API = `/api/v2/`
Refactor = ADR + scope minimal

## Checklist santé

Pas de dépendance circulaire · Endpoints testés · Types alignés · Pas de code mort
