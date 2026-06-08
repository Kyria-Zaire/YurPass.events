# YurPass

Plateforme premium d'identité, d'invitation, de billetterie, de check-in et d'accès aux expériences locales.

## Vision

YurPass est l'infrastructure qui connecte organisateurs, participants et staff autour d'événements locaux : invitations, billets, wallet, passport et contrôle d'accès.

## Stack officielle

| Couche | Technologie |
|--------|-------------|
| Backend | FastAPI / Python |
| Database | PostgreSQL |
| Cache | Redis |
| Frontend Web | Next.js 15 / TypeScript / Tailwind |
| Frontend Admin | Next.js 15 / TypeScript / Tailwind |
| Mobile | Expo / React Native (différé post-MVP) |
| Paiement | Stripe |
| Storage | S3 compatible |
| Infra | Docker / VPS Hetzner ou OVH |

## Structure du monorepo

```
yurpass/
├── backend/                 # API FastAPI (modules métier)
├── frontend/
│   ├── apps/
│   │   ├── web/             # Site public
│   │   ├── admin/           # Cockpit organisateur
│   │   └── mobile/          # Expo (différé)
│   └── packages/
│       ├── ui/              # Design system
│       ├── types/           # Types partagés
│       ├── utils/           # Utilitaires
│       └── config/          # ESLint, Tailwind, Prettier
├── infra/
│   └── docker/              # Docker Compose, configs
├── docs/
│   ├── adr/                 # Architecture Decision Records
│   ├── prd/                 # Product Requirements Documents
│   ├── bmad/                # Tickets d'exécution
│   ├── architecture/        # Diagrammes, specs techniques
│   ├── sprints/             # Planification sprint
│   ├── security/            # Politiques sécurité
│   └── templates/           # Templates PRD / ADR / BMAD
├── scripts/                 # Scripts utilitaires
├── .claude/                 # Gouvernance IA Claude Code
└── .cursor/                 # Gouvernance IA Cursor
```

## Gouvernance projet

### Colonne vertébrale : PRD → ADR → BMAD

```
PRD (Pourquoi)  →  ADR (Décision)  →  BMAD (Comment)  →  Code  →  Review  →  Merge
```

Templates : `docs/templates/`

### Règles

1. **Pas de code sans PRD** validé (`Ready For BMAD: YES`)
2. **Pas de décision architecture sans ADR** (`ACCEPTED`)
3. **Pas de commit sans validation humaine explicite**
4. Chaque ticket suit le format BMAD (`docs/templates/BMAD-TEMPLATE.md`)

## Environnements

| Env | Usage |
|-----|-------|
| `local` | Développement |
| `recette` | QA / démo |
| `preprod` | Validation prod-like |
| `production` | Live |

Variables : copier `.env.example` vers `.env.local`. Ne jamais committer de secrets.

## MVP

Priorité : **Web + Admin + Backend**. Mobile reporté après validation des flux critiques.

## Documentation

- ADR-001 Monorepo : `docs/adr/ADR-001-monorepo-modulaire.md`
- Instructions Claude Code : `CLAUDE.md`
- Instructions Cursor : `.cursor/Cursor.md`
- Agents : `AGENTS.md`

## Licence

Propriétaire — IMORIA / YurPass. Tous droits réservés.
