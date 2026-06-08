---
paths:
  - "infra/**"
  - "docker-compose*.yml"
  - ".github/**"
  - "scripts/**"
---

# Ingénieur Infra — YurPass

Stack : Docker + VPS Hetzner/OVH + GitHub Actions + PostgreSQL + Redis + S3.

## Docker local

```yaml
# docker-compose.yml services MVP
services:
  backend:     # FastAPI
  postgres:    # PostgreSQL 16
  redis:       # Redis 7
  frontend-web:
  frontend-admin:
# Mobile Expo hors Docker au début
```

## Environnements

| Env | Hébergement | DB | Refresh données |
|-----|-------------|-----|-----------------|
| local | machine dev | yurpass_dev | on demand |
| recette | VPS staging | yurpass_recette | hebdomadaire |
| preprod | VPS preprod | yurpass_preprod | avant release |
| production | VPS prod | yurpass_prod | live |

3 DB identiques en schéma, données différentes. Rabattages fréquents recette/preprod.

## CI/CD (GitHub Actions minimum)

```yaml
jobs:
  - backend-lint      # ruff
  - backend-tests     # pytest
  - frontend-typecheck
  - frontend-lint
  - frontend-build
  - docker-build-check
```

Pas de merge sur `main` si checks critiques échouent.

## Branching

```
main          # production
develop       # intégration
feature/*     # nouvelles features
fix/*         # corrections
hotfix/*      # urgences prod
```

Format : `feature/sprint-0-ticket-001-monorepo-foundation`

## Backups production

- PostgreSQL : dump quotidien, rétention 30 jours
- S3 uploads : versioning activé
- Test restore mensuel
- Config critique versionnée (hors secrets)

## Secrets

- `.env.example` commité (sans valeurs)
- `.env.local`, `.env.recette`, `.env.preprod`, `.env.production` → gitignore
- Prod secrets : vault ou variables hôte, jamais repo

## Stripe par environnement

- local/recette/preprod : clés `sk_test_`, cartes test, paiements 0€ OK
- production : clés `sk_live_`, webhook secret live séparé

## Monitoring (Sprint 10+)

- Health checks `/api/health`
- Logs structurés JSON
- Alertes erreurs 5xx
