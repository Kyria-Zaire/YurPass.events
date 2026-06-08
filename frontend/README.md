# YurPass Frontend

Workspace monorepo pour les applications et packages partagés YurPass.

> **TICKET-004** — Frontend Workspace Foundation. Aucune feature métier à ce stade.

## Stack

| Outil | Usage |
|-------|-------|
| pnpm | Gestionnaire de paquets + workspaces |
| Turborepo | Orchestration build/lint/typecheck |
| Next.js 15 | Apps web et admin |
| React 19 | UI |
| TypeScript | Typage strict |
| Tailwind CSS 3 | Styles |
| ESLint | Lint |

## Structure

```
frontend/
├── apps/
│   ├── web/          # Site public (port 3000)
│   └── admin/        # Cockpit organisateur (port 3001)
└── packages/
    ├── ui/           # Design system (Button placeholder)
    ├── types/        # Types partagés (AppEnvironment)
    ├── utils/        # Utilitaires (cn)
    └── config/       # TS, ESLint, Tailwind partagés
```

## Règles

```
apps     = produits exécutables (web, admin)
packages = code partagé réutilisable
```

**INTERDIT :** logique métier complexe dans `packages/ui`. Les packages restent génériques.

**Apps** consomment **packages**, jamais l'inverse.

```
apps/web, apps/admin → packages/ui, types, utils, config
packages/ui → packages/utils
```

## Scripts racine (depuis `yurpass/`)

```bash
pnpm install
pnpm dev          # Démarre web + admin (turbo)
pnpm build        # Build toutes les apps
pnpm lint         # Lint workspace
pnpm typecheck    # Typecheck workspace
```

## Développement par app

```bash
# Web seul
pnpm --filter @yurpass/web dev

# Admin seul
pnpm --filter @yurpass/admin dev
```

## Packages

| Package | Export foundation |
|---------|-------------------|
| `@yurpass/types` | `AppEnvironment` |
| `@yurpass/utils` | `cn()` |
| `@yurpass/ui` | `Button` (placeholder) |
| `@yurpass/config` | tsconfig, eslint, tailwind preset |

## Pages actuelles

| App | Route | Contenu |
|-----|-------|---------|
| web | `/` | YurPass Web |
| admin | `/` | YurPass Admin |

Aucune page métier, auth, ou appel API.

## Mobile

`frontend/apps/mobile` (Expo) — **différé** post-MVP.

## Documentation projet

- Backend : `../backend/README.md`
- ADR-001 : `../docs/adr/ADR-001-monorepo-modulaire.md`
- Gouvernance IA : `../docs/architecture/AI_WORKFLOW.md`
