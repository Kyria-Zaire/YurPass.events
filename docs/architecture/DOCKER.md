# YurPass — Architecture Docker

> TICKET-005 — Docker + Environments Foundation
> Sprint 0 clôture : stack locale multi-services reproductible.

---

## 1. Vue d'ensemble

```txt
docker compose up --build
```

Démarre 5 services :

| Service | Image / Build | Port hôte | Rôle |
|---------|---------------|-----------|------|
| `postgres` | postgres:16-alpine | 5432 | Base de données |
| `redis` | redis:7-alpine | 6379 | Cache / sessions |
| `backend` | `backend/Dockerfile` | 8000 | API FastAPI |
| `frontend-web` | `frontend/apps/web/Dockerfile` | 3000 | Next.js public |
| `frontend-admin` | `frontend/apps/admin/Dockerfile` | 3001 | Next.js admin |

---

## 2. Ordre de démarrage

```
postgres (healthy) ──┐
                     ├──► backend (healthy) ──┬──► frontend-web
redis (healthy) ─────┘                        └──► frontend-admin
```

Le backend attend `postgres` et `redis` healthy avant de démarrer.
Les frontends attendent le backend healthy.

---

## 3. Volumes

| Volume | Nom | Usage |
|--------|-----|-------|
| `postgres_data` | `yurpass_postgres_data` | Persistance PostgreSQL |

Les données PostgreSQL survivent à `docker compose down`.
`docker compose down -v` supprime le volume (destructif).

---

## 4. Healthchecks

### PostgreSQL

```bash
pg_isready -U yurpass -d yurpass
```

### Redis

```bash
redis-cli ping
```

### Backend

```bash
GET http://localhost:8000/api/health
```

Réponse attendue (Docker DEV) :

```json
{
  "status": "ok",
  "service": "yurpass-backend",
  "version": "0.1.0",
  "environment": "dev",
  "database": "connected",
  "redis": "connected"
}
```

Aucun secret (URL, password, token) dans la réponse.

---

## 5. URLs locales

| URL | Service |
|-----|---------|
| http://localhost:8000/api/health | Backend health |
| http://localhost:8000/docs | OpenAPI (dev) |
| http://localhost:3000 | Web |
| http://localhost:3001 | Admin |

---

## 6. Fichiers Docker

```txt
docker-compose.yml
backend/Dockerfile
frontend/apps/web/Dockerfile
frontend/apps/admin/Dockerfile
infra/env/.env.*.example
scripts/dev.sh
```

---

## 7. Variables d'environnement

Templates : `infra/env/`

| Fichier | Environnement |
|---------|---------------|
| `.env.dev.example` | DEV local Docker |
| `.env.recette.example` | RECETTE |
| `.env.preprod.example` | PREPROD |
| `.env.prod.example` | PROD (vide — vault only) |

Copier vers `infra/env/.env.dev` (gitignored) pour overrides locaux.

Le compose DEV utilise `infra/env/.env.dev.example` + overrides `environment:` pour les hostnames Docker (`postgres`, `redis`).

---

## 8. Backend Docker

- Base : `python:3.13-slim`
- Gestionnaire : `uv`
- Install : `uv sync --frozen --no-dev`
- Commande : `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`

---

## 9. Frontend Docker

- Base : `node:22-alpine`
- Mode : **DEV uniquement** (pas de build prod, pas de Nginx)
- Commande web : `pnpm --filter @yurpass/web dev --hostname 0.0.0.0`
- Commande admin : `pnpm --filter @yurpass/admin dev --hostname 0.0.0.0`

---

## 10. Sécurité

- Aucun secret dans le repository
- `.env` et `infra/env/.env.*` (hors `.example`) sont gitignored
- Stripe live keys : production uniquement
- Stripe test keys : dev / recette / preprod uniquement

---

## 11. Commandes utiles

```bash
# Démarrer (script développeur)
./scripts/dev.sh

# Valider la config
docker compose config

# État des services
docker compose ps

# Logs backend
docker compose logs -f backend

# Arrêter
docker compose down

# Tester persistance postgres
docker compose down && docker compose up -d postgres
docker compose exec postgres psql -U yurpass -d yurpass -c "SELECT 1"
```

---

## 12. Hors scope TICKET-005

- CI/CD GitHub Actions
- Déploiement VPS Hetzner/OVH
- Kubernetes
- Nginx reverse proxy
- Build production frontend
- Expo mobile
