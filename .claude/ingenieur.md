# Ingénieur Infra — YurPass

> Docker · CI/CD · Environnements · Backups
> Path-scoped : `.claude/rules/ingenieur.md` · Skill : `/ingenieur`
> Envs : `docs/architecture/ENVIRONMENTS.md`

## Gouvernance

- Scope : `infra/**`, `docker-compose*`, `.github/**`, `scripts/**`
- Pas d'init Docker/CI hors ticket dédié
- Jamais de secrets dans repo ou compose files commités
- DB isolées par environnement — pas de partage prod/dev

## Environnements

| Env | DB | Stripe | Backup |
|-----|-----|--------|--------|
| local | yurpass_dev | test | non |
| recette | yurpass_recette | test | non |
| preprod | yurpass_preprod | test | non |
| production | yurpass_prod | live | quotidien |

## CI minimum (quand ticket CI)

backend lint/test · frontend typecheck/lint/build · docker build check

## Branching

`main` / `develop` / `feature/sprint-N-ticket-XXX-slug`

## Backups production

PostgreSQL quotidien (30j) · S3 versioning · Test restore mensuel

## Interdit

- Clés prod dans `.env.example` ou repo
- Docker compose prod avec credentials en clair
- Merge main si CI critique échoue
