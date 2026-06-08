# YurPass — Index des Skills & Gouvernance IA

> TICKET-002 — AI Governance Files Hardening
> Skills invokables via `/nom-du-skill` dans Claude Code.
> Gouvernance maître : `Claude.md` · Workflow : `docs/architecture/AI_WORKFLOW.md`

## Lignes rouges

Pas de code sans PRD · Pas d'archi sans ADR · Pas de feature hors ticket · **DO NOT COMMIT** sans validation humaine

## Fichiers gouvernance racine (`.claude/`)

| Fichier | Rôle |
|---------|------|
| `Claude.md` | Entrée maître |
| `seniordev.md` | Dev senior, scope control |
| `architecte-api.md` | Backend FastAPI |
| `constructeur-ui.md` | Frontend Next.js |
| `code-review.md` | Revue PR |
| `reviewer-securite-code.md` | Sécurité |
| `ingenieur.md` | Infra, envs |
| `createur-workflow.md` | BMAD tickets |
| `ui-ux-pro-max.md` | UX premium |
| `frontend-design.md` | Direction visuelle |
| `shadcn.md` | Design system |
| `make-interfaces-feel-better.md` | Motion |
| `simplify.md` | Anti sur-ingénierie |
| `improve-codebase-architecture.md` | Architecture monorepo |

Path-scoped détaillé : `.claude/rules/` (conservé, non supprimé)

## Skills projet (`.claude/skills/`)

| Skill | Commande | Rôle | Déclencheur |
|-------|----------|------|-------------|
| Senior Dev | `/seniordev` | Code propre, diff minimal, conventions | Tout développement |
| Architecte API | `/architecte-api` | FastAPI, modules, DTO, permissions | `backend/**` |
| Constructeur UI | `/constructeur-ui` | Next.js, shadcn, design system | `frontend/**` |
| Code Review | `/code-review` | Revue PR, checklist qualité | Avant merge |
| Reviewer Sécu | `/reviewer-securite-code` | OWASP, auth, webhooks, RBAC | Auth, paiements, webhooks |
| Ingénieur | `/ingenieur` | Docker, CI/CD, envs, backups | `infra/**`, CI |
| Créateur Workflow | `/createur-workflow` | Tickets BMAD, sprints, ADR | Planification |

## Skills design externes (`.agents/skills/`)

| Skill | Commande | Focus |
|-------|----------|-------|
| Emil Design Eng | `/emil-design-eng` | Motion, easing, polish UI |
| Impeccable | `/impeccable` | Layout, spacing, typo, audit UI |
| Design Taste | `/design-taste-frontend` | Anti-slop frontend |
| Image to Code | `/image-to-code` | Références visuelles → code |
| GPT Taste | `/gpt-taste` | Variante stricte Codex |
| Redesign | `/redesign-existing-projects` | Audit UI existant |
| Minimalist UI | `/minimalist-ui` | Style Linear/Notion |
| High-end Visual | `/high-end-visual-design` | UI premium soft |
| Brutalist UI | `/industrial-brutalist-ui` | Typo forte, contraste |
| Imagegen Web | `/imagegen-frontend-web` | Comps web |
| Imagegen Mobile | `/imagegen-frontend-mobile` | Comps mobile |
| Brandkit | `/brandkit` | Identité visuelle |
| Full Output | `/full-output-enforcement` | Éviter troncature |

## Rules complémentaires (`.claude/rules/`)

| Rule | Fichier | Scope |
|------|---------|-------|
| UI/UX Pro Max | `ui-ux-pro-max.md` | `frontend/**` |
| shadcn | `shadcn.md` | `frontend/**` |
| Make Interfaces Feel Better | `make-interfaces-feel-better.md` | `frontend/**` |
| Simplify | `simplify.md` | Tout |
| Frontend Design | `frontend-design.md` | `frontend/**` |
| Improve Architecture | `improve-codebase-architecture.md` | Tout |
| Environnements | `environnements.md` | `infra/**`, `.env*` |
| Sécurité | `reviewer-securite-code.md` | Auth, webhooks |

## Stack frontend designer (plugins Claude Code)

```bash
/plugin marketplace add anthropics/claude-plugins-official
/plugin install frontend-design@claude-plugins-official
```

Workflow recommandé UI :
1. `/design-taste-frontend` ou `/image-to-code` — direction visuelle
2. `/constructeur-ui` — implémentation shadcn + packages/ui
3. `/emil-design-eng` — motion et polish
4. `/impeccable` — audit final layout/typo

## Ordre sprints (ADR-001)

```
S0 Monorepo+Docker+CI → S1 Auth → S2 Orgs → S3 Events → S4 Invitations
→ S5 Ticketing+Stripe → S6 Wallet+QR → S7 Check-in → S8 Host → S9 Admin → S10 Hardening
```
