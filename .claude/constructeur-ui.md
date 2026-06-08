# Constructeur UI — YurPass

> Next.js 15 · shadcn/ui · Design system
> Path-scoped : `.claude/rules/constructeur-ui.md` · Skill : `/constructeur-ui`

## Gouvernance

- Scope : `frontend/**` uniquement sauf ticket explicite
- Composants réutilisables → `packages/ui/` — **jamais** dupliqués entre apps
- Pas de page/composant hors scope ticket
- Pas d'init Next.js hors ticket dédié

## Structure

```
frontend/apps/web/      # Public
frontend/apps/admin/    # Cockpit
frontend/packages/ui/   # Design system
frontend/packages/types/
```

## Règles

- Server Components par défaut
- `"use client"` seulement si interactif
- Types depuis `packages/types`
- Accessibilité WCAG AA

## Workflow design

1. `/design-taste-frontend` ou `/image-to-code`
2. Implémentation shadcn + wrappers YurPass
3. `/emil-design-eng` — motion
4. `/impeccable` — audit final

## Interdit

- Copier composants entre apps au lieu de `packages/ui`
- `any` dans props
- Cards imbriquées (anti-slop)
- Fetch client si Server Component suffit

## Checklist

- [ ] Composant dans `packages/ui` si réutilisable
- [ ] States Loading / Error / Empty / Success
- [ ] Scope ticket respecté
