---
paths:
  - "infra/**"
  - ".env*"
  - "docker-compose*.yml"
---

# Environnements YurPass

4 environnements isolés. Config détaillée : `.claude/environnements.json`.

## Matrice

| | local | recette | preprod | production |
|---|-------|---------|---------|------------|
| DB | yurpass_dev | yurpass_recette | yurpass_preprod | yurpass_prod |
| Stripe | test | test | test | live |
| Turnstile | optionnel | requis | requis | requis |
| Données | seed dev | synthétiques | copie rabattue | réelles |
| Backup | non | non | non | quotidien |

## Fichiers env

```
.env.example      # commité, template
.env.local        # gitignore
.env.recette      # gitignore
.env.preprod      # gitignore
.env.production   # gitignore, JAMAIS lu par IA
```

## Stripe dev/recette

- Cartes test : `4242424242424242`, `4000002500003155` (3DS)
- Paiements 0€ autorisés en test
- Webhook secret test séparé du live

## Règle webhook

Un webhook qui touche ou supprime des données hors scope tenant → **code abandonné**.

## Rabattages DB

- recette : refresh hebdomadaire depuis seed
- preprod : refresh avant chaque release, données anonymisées

## Backups prod

PostgreSQL quotidien + S3 versioning. Test restore mensuel obligatoire.
