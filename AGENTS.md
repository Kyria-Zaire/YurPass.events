# YurPass — Agent Instructions

> Point d'entrée pour Cursor Agent et outils compatibles.

## Projet

YurPass — infrastructure d'identité, d'invitation et d'accès aux expériences locales.
Monorepo modulaire (ADR-001). MVP = Web + Admin + Backend.

**Dépôt GitHub :** https://github.com/Kyria-Zaire/YurPass.events.git

## Configuration (TICKET-002)

| Outil | Fichier principal | Rules/Skills |
|-------|-------------------|--------------|
| Cursor | `.cursor/Cursor.md` | `.cursor/rules.json` + `.cursor/rules/*.mdc` + `.cursor/skills/` |
| Claude Code | `.claude/Claude.md` | `.claude/*.md` + `.claude/rules/` + `.claude/skills/` |
| Skills externes | — | `.agents/skills/` |

## Documentation gouvernance

- Workflow IA : `docs/architecture/AI_WORKFLOW.md`
- Sécurité : `docs/security/SECURITY_BASELINE.md`
- Environnements : `docs/architecture/ENVIRONMENTS.md`
- Templates : `docs/templates/`

## Posture

Équipe senior : tech lead + expert sécu + senior dev. Pas de vibe coding spaghetti.

## Skills à invoquer

- `/seniordev` — tout code
- `/architecte-api` — backend
- `/constructeur-ui` — frontend
- `/reviewer-securite-code` — auth, webhooks, paiements
- `/code-review` — avant merge
- `/ingenieur` — infra, CI, envs
- `/createur-workflow` — tickets BMAD

## Design

`/emil-design-eng` → `/impeccable` → `/design-taste-frontend` → `/image-to-code`

## Sécurité

Webhooks signés + idempotents. JWT + RBAC. Honeypot + Turnstile. Jamais clé prod dans repo.
