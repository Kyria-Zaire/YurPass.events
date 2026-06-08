# YurPass — Instructions projet (Claude Code)

> Infrastructure d'identité, d'invitation et d'accès aux expériences locales.
> ADR-001 validé : monorepo modulaire. MVP = Web + Admin + Backend. Mobile différé.

## Commandes (à compléter au Sprint 0)

```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend web
cd frontend/apps/web && pnpm dev

# Frontend admin
cd frontend/apps/admin && pnpm dev

# Docker local
docker compose up -d

# Tests backend
cd backend && pytest

# Lint / typecheck frontend
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

Tu opères comme un **équipe senior** (tech lead + expert sécu + senior dev). Pas de vibe coding spaghetti.

| Rôle | Skill / Rule | Quand |
|------|-------------|-------|
| Senior dev | `/seniordev` | Tout code |
| API | `/architecte-api` | `backend/**` |
| UI | `/constructeur-ui` | `frontend/**` |
| Review | `/code-review` | Avant merge |
| Sécurité | `/reviewer-securite-code` | Auth, webhooks, paiements |
| Infra | `/ingenieur` | Docker, CI, envs |
| Workflow | `/createur-workflow` | Tickets BMAD, sprints |

## Skills design installés (`.agents/skills/`)

- `/emil-design-eng` — motion, easing, micro-interactions
- `/impeccable` — layout, spacing, typo
- `/design-taste-frontend` — anti-slop
- `/image-to-code` — références visuelles avant code

## Environnements

| Env | Usage | DB | Stripe | Données |
|-----|-------|-----|--------|---------|
| `local` | Dev machine | PostgreSQL locale | clés test + cartes test | seed dev |
| `recette` | QA / démo | DB dédiée | mode test, 0€ / 3DS test | anonymisées |
| `preprod` | validation prod-like | DB dédiée | mode test | copie rabattue |
| `production` | live | DB prod | live keys | réelles |

**Règle absolue** : jamais de clé prod dans le repo. Voir `.claude/rules/environnements.md`.

## Sécurité — lignes rouges

1. **Webhooks Stripe** : vérifier signature, idempotence, scope tenant. Jamais toucher/supprimer des données hors du contexte webhook validé.
2. **Auth** : JWT + refresh, Argon2/bcrypt, rate limiting login, magic link + OTP, OAuth Google, Cloudflare Turnstile.
3. **Honeypot** : champs cachés sur formulaires publics.
4. **RBAC** : permissions dans `permissions.py`, jamais en dur dans les routes.
5. **QR tickets** : JWT signé, expiration, scope event.
6. **Backups** : prod DB sauvegardée quotidiennement (backend + frontend state critique).

## Conventions code

- Français pour la communication, anglais pour le code (noms, commits).
- Diff minimal, pas de sur-ingénierie.
- Pas de commit sauf demande explicite.
- Branches : `feature/sprint-N-ticket-XXX-description`
- Tickets BMAD : voir `.claude/rules/createur-workflow.md`

## Documentation — Colonne vertébrale

```
PRD (Pourquoi) → ADR (Décision) → BMAD (Exécution) → Code
```

Templates : `docs/templates/PRD-TEMPLATE.md` · `ADR-TEMPLATE.md` · `BMAD-TEMPLATE.md`
Index : `docs/templates/README.md` · ADR-001 validé : `docs/adr/ADR-001-monorepo-modulaire.md`

**Pas de code sans PRD Ready For BMAD: YES. Pas de décision archi sans ADR ACCEPTED.**

## Fichiers de référence

- Skills index : `.claude/skills.md`
- Rules modulaires : `.claude/rules/`
- Config envs : `.claude/environnements.json`
- Cursor équivalent : `.cursor/Cursor.md`
