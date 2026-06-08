# Improve Codebase Architecture — YurPass

Posture tech lead : architecture claire, découplée, évolutive.

## Principes monorepo

1. **Apps consomment packages, jamais l'inverse**
2. **Backend et frontend communiquent via API REST**, pas d'import cross-stack
3. **Types partagés** : `packages/types` (frontend) ↔ schemas Pydantic (backend) — synchroniser manuellement ou via OpenAPI codegen
4. **Un module = un domaine métier**

## Dépendances autorisées

```
apps/web      → packages/ui, types, utils, config
apps/admin    → packages/ui, types, utils, config
packages/ui   → packages/utils, config
packages/types → (aucune dépendance app)
backend/modules/X → backend/shared, backend/core
```

## Anti-patterns architecture

- App qui importe une autre app
- Logique métier dans `packages/ui`
- Types dupliqués entre frontend et backend sans doc
- Module backend qui importe un autre module sans passer par service
- God module qui fait tout

## Évolution

- Nouveau domaine → nouveau module backend + types frontend
- Feature cross-module → orchestration dans un service dédié, pas couplage direct
- Breaking API → version `/api/v2/`

## Documentation architecture

- ADR dans `docs/adr/`
- Diagrammes dans `docs/architecture/`
- OpenAPI auto-généré par FastAPI → `docs/api/openapi.json`

## Avant refactor architecture

1. Documenter la décision (ADR)
2. Scope minimal (un module à la fois)
3. Tests de non-régression
4. Pas de big-bang rewrite

## Checklist santé codebase

- [ ] Pas de dépendance circulaire
- [ ] Modules < 10 fichiers ou bien découpés
- [ ] Chaque endpoint a un test
- [ ] Types frontend alignés avec schemas backend
- [ ] Pas de code mort
