# Senior Dev — YurPass

> Gouvernance IA · Posture développeur senior · Scope control
> Path-scoped : `.claude/rules/seniordev.md` · Skill : `/seniordev`

## Gouvernance (obligatoire)

- **Un ticket BMAD = un scope.** Ne pas implémenter au-delà des INCLUS.
- **Diff minimal.** Ne modifier que les fichiers nécessaires au ticket.
- **Pas de refactor opportuniste** hors demande explicite.
- **DO NOT COMMIT** sans validation humaine.
- **Pas de feature inventée** non listée dans le PRD/BMAD.

## Principes

1. Lire le code existant avant d'écrire
2. Une responsabilité par fonction — pas de god functions
3. Typer strictement (TS `strict`, Python hints + Pydantic)
4. Erreurs explicites — jamais `except: pass` ou `catch {}`
5. Tester le comportement, pas les détails d'implémentation
6. Nommer explicitement (`get_user_by_email`, pas `getData`)

## Découpage obligatoire

**Backend :** `router → service → repository` + `schemas.py` + `permissions.py`
**Frontend :** Server Components par défaut · UI dans `packages/ui` · Types dans `packages/types`

## Interdit

- Logique métier dans les routes
- Secrets hardcodés
- `any` sans justification
- Modifications hors scope ticket
- Commits non demandés · Force push sur `main`

## Checklist avant livraison

- [ ] Scope ticket respecté
- [ ] Lint + types OK
- [ ] Pas de secret exposé
- [ ] Diff reviewable en < 5 min
- [ ] Aucun fichier hors scope modifié
