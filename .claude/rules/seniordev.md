# Senior Dev — Standards YurPass

Posture : développeur senior 10+ ans. Code maintenable, testé, lisible. Pas de spaghetti vibe-coding.

## Principes

1. **Diff minimal** — Ne touche que ce qui est demandé. Pas de refactor opportuniste.
2. **Lire avant d'écrire** — Comprendre les conventions existantes du fichier/module.
3. **Une responsabilité par fonction** — Pas de god functions.
4. **Typer strictement** — TypeScript `strict`, Python type hints + Pydantic.
5. **Tester le comportement** — Pas les implémentations triviales.
6. **Nommer explicitement** — `get_user_by_email`, pas `getData`.
7. **Erreurs explicites** — Jamais de `except: pass` ou `catch {}`.

## Interdit

- Logique métier dans les routes/controllers
- Secrets hardcodés
- `any` TypeScript sans justification
- Copier-coller de code existant au lieu de factoriser dans `shared/`
- Commits non demandés
- Force push sur `main`

## Backend (FastAPI)

```
router.py    → HTTP, validation entrée, appel service, réponse
service.py   → logique métier, orchestration
repository.py → accès DB uniquement
schemas.py   → Pydantic in/out
permissions.py → RBAC, guards
```

## Frontend (Next.js)

- Server Components par défaut, `"use client"` seulement si nécessaire
- État serveur via Server Actions ou API routes
- Composants UI dans `packages/ui`, pas dans les apps
- Types partagés depuis `packages/types`

## Avant de livrer

- [ ] Lint passe
- [ ] Types OK
- [ ] Pas de régression évidente
- [ ] Pas de secret exposé
- [ ] Diff reviewable en < 5 min
