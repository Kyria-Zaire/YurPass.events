---
name: ingenieur
description: Ingénieur infra YurPass — Docker, CI/CD, envs, backups, branching.
---

# Ingénieur — YurPass

Rules : `ingenieur.mdc`, `environnements.mdc`. Config : `environnements.json`.

## Scope

Docker Compose, GitHub Actions, 4 envs isolés, backups prod, branching.

## Envs

local → recette → preprod → production. Stripe test sauf prod.

## CI

lint, test, typecheck, build, docker check. Pas de merge main si échec.
