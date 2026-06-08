# YurPass — Gouvernance IA Cursor

> **TICKET-002** — AI Governance Files Hardening
> Infrastructure d'identité, d'invitation et d'accès aux expériences locales.
> ADR-001 validé : monorepo modulaire. MVP = Web + Admin + Backend. Mobile différé.

## Lignes rouges absolues

| # | Règle |
|---|-------|
| 1 | Pas de code sans PRD (`Ready For BMAD: YES`) |
| 2 | Pas de décision archi sans ADR (`ACCEPTED`) |
| 3 | Pas de feature hors ticket BMAD actif |
| 4 | Pas de modification hors scope ticket |
| 5 | **DO NOT COMMIT sans validation humaine** |
| 6 | Pas de secret dans le repo |
| 7 | Pas de suppression sans demande explicite |
| 8 | Pas de dépendance installée hors ticket |

Manifeste rules : `.cursor/rules.json` · Workflow : `docs/architecture/AI_WORKFLOW.md` · Sécurité : `docs/security/SECURITY_BASELINE.md`

## Commandes (à compléter au Sprint 0)

```bash
cd backend && uvicorn app.main:app --reload
cd frontend/apps/web && pnpm dev
cd frontend/apps/admin && pnpm dev
docker compose up -d
cd backend && pytest
cd frontend && pnpm lint && pnpm typecheck
```

## Architecture

```
yurpass/
├── backend/          # FastAPI — modules métier
├── frontend/
│   ├── apps/web/     # Next.js 15 — public
│   ├── apps/admin/   # Next.js 15 — cockpit
│   └── packages/     # ui, types, utils, config
├── infra/docker/
├── docs/adr/
└── scripts/
```

**Backend** : `router → service → repository`. Zéro logique métier dans les routes.
**Frontend** : design system dans `packages/ui`, types partagés dans `packages/types`.

## Posture obligatoire

Tu opères comme une **équipe senior** (tech lead + expert sécu + senior dev). Pas de vibe coding spaghetti.

| Rôle | Rule / Skill | Quand |
|------|-------------|-------|
| Senior dev | `seniordev.mdc` | Toujours |
| API | `architecte-api.mdc` | `backend/**` |
| UI | `constructeur-ui.mdc` | `frontend/**` |
| Review | `code-review.mdc` | Avant merge |
| Sécurité | `reviewer-securite-code.mdc` | Auth, webhooks, paiements |
| Infra | `ingenieur.mdc` | Docker, CI, envs |
| Workflow | `createur-workflow.mdc` | Tickets BMAD |

Invoquer via `/seniordev`, `/architecte-api`, etc. ou laisser les rules `globs` s'appliquer.

## Skills design installés (`.agents/skills/`)

- `/emil-design-eng` — motion, easing
- `/impeccable` — layout, spacing, typo
- `/design-taste-frontend` — anti-slop
- `/image-to-code` — image → analyse → code

## Environnements

| Env | DB | Stripe | Données |
|-----|-----|--------|---------|
| `local` | PostgreSQL locale | test keys | seed dev |
| `recette` | DB dédiée | test, 0€ / 3DS | anonymisées |
| `preprod` | DB dédiée | test | copie rabattue |
| `production` | DB prod | live keys | réelles |

Voir `.cursor/rules/environnements.mdc` et `.cursor/environnements.json`.

## Sécurité — lignes rouges

1. Webhooks Stripe : signature + idempotence + scope tenant strict.
2. Auth : JWT, refresh, Argon2, rate limit, magic link, OTP, OAuth Google, Turnstile.
3. Honeypot sur formulaires publics.
4. RBAC via `permissions.py`.
5. QR JWT signé.
6. Backups prod quotidiens.

## Colonne vertébrale PRD → ADR → BMAD

Templates : `docs/templates/PRD-TEMPLATE.mdc` · `ADR-TEMPLATE.mdc` · `BMAD-TEMPLATE.mdc`
Rule : `prd-adr-bmad.mdc` (toujours actif). Index : `docs/templates/README.md`

Pas de code sans PRD. Pas d'archi sans ADR ACCEPTED.

## Rules actives

Toutes dans `.cursor/rules/*.mdc`. Index complet : `.cursor/skills.md`.
