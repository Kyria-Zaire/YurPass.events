# YurPass — Index des Skills & Gouvernance IA (Cursor)

> TICKET-002 — AI Governance Files Hardening
> Manifeste : `.cursor/rules.json` · Workflow : `docs/architecture/AI_WORKFLOW.md`

## Lignes rouges

Pas de code sans PRD · Pas d'archi sans ADR · Pas de feature hors ticket · **DO NOT COMMIT** sans validation humaine

## Claude équivalent

Fichiers miroir dans `.claude/*.md` — harmonisés avec `.cursor/rules/*.mdc`

## Skills projet (`.cursor/skills/`)

| Skill | Commande | Rôle |
|-------|----------|------|
| Senior Dev | `/seniordev` | Code propre, diff minimal |
| Architecte API | `/architecte-api` | FastAPI, modules, DTO |
| Constructeur UI | `/constructeur-ui` | Next.js, shadcn, design system |
| Code Review | `/code-review` | Revue PR |
| Reviewer Sécu | `/reviewer-securite-code` | OWASP, auth, webhooks |
| Ingénieur | `/ingenieur` | Docker, CI, envs |
| Créateur Workflow | `/createur-workflow` | Tickets BMAD |

## Skills design externes (`.agents/skills/`)

| Skill | Commande | Focus |
|-------|----------|-------|
| Emil Design Eng | `/emil-design-eng` | Motion, easing |
| Impeccable | `/impeccable` | Layout, spacing, typo |
| Design Taste | `/design-taste-frontend` | Anti-slop |
| Image to Code | `/image-to-code` | Image → code |
| GPT Taste | `/gpt-taste` | Variante stricte |
| Redesign | `/redesign-existing-projects` | Audit UI |
| Minimalist UI | `/minimalist-ui` | Style minimal |
| High-end Visual | `/high-end-visual-design` | UI premium |
| Brutalist UI | `/industrial-brutalist-ui` | Brutalisme |
| Imagegen Web/Mobile | `/imagegen-frontend-web` | Comps |
| Brandkit | `/brandkit` | Identité |
| Full Output | `/full-output-enforcement` | Anti-troncature |

## Rules (`.cursor/rules/*.mdc`)

| Rule | Fichier | Scope |
|------|---------|-------|
| Core | `yurpass-core.mdc` | Toujours |
| Senior Dev | `seniordev.mdc` | Toujours |
| Architecte API | `architecte-api.mdc` | `backend/**` |
| Constructeur UI | `constructeur-ui.mdc` | `frontend/**` |
| Code Review | `code-review.mdc` | Manuel |
| Sécurité | `reviewer-securite-code.mdc` | Auth, webhooks |
| Ingénieur | `ingenieur.mdc` | `infra/**` |
| Workflow | `createur-workflow.mdc` | `docs/**` |
| UI/UX Pro Max | `ui-ux-pro-max.mdc` | `frontend/**` |
| shadcn | `shadcn.mdc` | `frontend/**` |
| Feel Better | `make-interfaces-feel-better.mdc` | `frontend/**` |
| Simplify | `simplify.mdc` | Toujours |
| Frontend Design | `frontend-design.mdc` | `frontend/**` |
| Architecture | `improve-codebase-architecture.mdc` | Toujours |
| Environnements | `environnements.mdc` | `infra/**`, `.env*` |

## Workflow UI recommandé

1. `/design-taste-frontend` ou `/image-to-code`
2. `/constructeur-ui` + rule `shadcn.mdc`
3. `/emil-design-eng` + `make-interfaces-feel-better.mdc`
4. `/impeccable` — audit final
