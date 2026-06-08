# YurPass — Environnements

> Matrice des 4 environnements · DB isolées · Stripe test/live séparés
> Config machine : `.claude/environnements.json` · `.cursor/environnements.json`
> Docker local : `docs/architecture/DOCKER.md` · Templates : `infra/env/`

---

## 0. Docker DEV (local)

```bash
docker compose up --build
# ou
./scripts/dev.sh
```

| Service | URL |
|---------|-----|
| Backend health | http://localhost:8000/api/health |
| Web | http://localhost:3000 |
| Admin | http://localhost:3001 |

Template : `infra/env/.env.dev.example` · Volume : `yurpass_postgres_data`

---

## 1. Vue d'ensemble

| Env | Usage | DB | Stripe | Données |
|-----|-------|-----|--------|---------|
| **local** | Dev machine | `yurpass_dev` | test | seed dev |
| **recette** | QA, démos | `yurpass_recette` | test | synthétiques/anonymisées |
| **preprod** | Validation prod-like | `yurpass_preprod` | test | copie rabattue |
| **production** | Live clients | `yurpass_prod` | **live** | réelles |

**Principe :** schéma identique, **données isolées**, jamais de DB partagée entre envs.

---

## 2. local

| Paramètre | Valeur |
|-----------|--------|
| Fichier secrets | `.env.local` (gitignore) |
| Database | PostgreSQL localhost, `yurpass_dev` |
| Redis | localhost |
| Stripe | `sk_test_*` · Cartes test · 0€ OK · 3DS test |
| Turnstile | Optionnel |
| Rate limiting | Relaxed |
| Backup | Non |

---

## 3. recette

| Paramètre | Valeur |
|-----------|--------|
| Fichier secrets | `.env.recette` (gitignore) |
| Database | `yurpass_recette` — instance dédiée |
| Stripe | test uniquement · **jamais live keys** |
| Turnstile | **Requis** |
| Rate limiting | Production-like |
| Refresh données | Hebdomadaire (seed/synthétique) |
| Backup | Non |

---

## 4. preprod

| Paramètre | Valeur |
|-----------|--------|
| Fichier secrets | `.env.preprod` (gitignore) |
| Database | `yurpass_preprod` — instance dédiée |
| Stripe | test uniquement |
| Turnstile | **Requis** |
| Données | Copie prod rabattue, PII anonymisée |
| Refresh | Avant chaque release |
| Backup | Non |

---

## 5. production

| Paramètre | Valeur |
|-----------|--------|
| Fichier secrets | Vault ou variables hôte — **jamais repo** |
| Database | `yurpass_prod` — instance dédiée |
| Stripe | `sk_live_*` · Webhook secret live séparé |
| Turnstile | **Requis** |
| Honeypot | **Requis** |
| Rate limiting | Strict |
| Backup PostgreSQL | **Quotidien**, rétention 30j |
| Backup S3 | Versioning activé |
| Test restore | Mensuel obligatoire |

---

## 6. Stripe par environnement

| Env | Mode | Cartes test | 0€ | Live keys |
|-----|------|-------------|-----|-----------|
| local | test | Oui | Oui | **INTERDIT** |
| recette | test | Oui | Oui | **INTERDIT** |
| preprod | test | Oui | Non recommandé | **INTERDIT** |
| production | live | Non | Non | Oui |

Cartes test courantes : `4242424242424242`, `4000002500003155` (3DS).

---

## 7. Fichiers environnement

| Fichier | Commité | Usage |
|---------|---------|-------|
| `.env.example` | Oui | Template sans valeurs |
| `.env.local` | Non | Dev local |
| `.env.recette` | Non | QA |
| `.env.preprod` | Non | Preprod |
| `.env.production` | Non | Prod — jamais lu par IA |

---

## 8. Webhook safety (tous envs)

| Règle | Obligatoire |
|-------|-------------|
| Vérification signature | Oui |
| Idempotence `event.id` | Oui |
| Scope tenant | Oui |
| Secret par env | Oui (`STRIPE_WEBHOOK_SECRET_TEST` vs `_LIVE`) |

Violation scope → **ABANDONNER le code**. Voir `docs/security/SECURITY_BASELINE.md`.

---

## 9. Rabattages DB

| Env | Politique |
|-----|-----------|
| local | On demand (seed dev) |
| recette | Hebdomadaire |
| preprod | Avant release |
| production | Jamais rabattu — backups uniquement |

---

## 10. Fichiers templates

| Fichier | Env | Commité |
|---------|-----|---------|
| `infra/env/.env.dev.example` | DEV | Oui |
| `infra/env/.env.recette.example` | RECETTE | Oui |
| `infra/env/.env.preprod.example` | PREPROD | Oui |
| `infra/env/.env.prod.example` | PROD (vide) | Oui |
| `infra/env/.env.*` | Secrets réels | **Non** (gitignore) |

## 11. Backups (futur — production)

- PostgreSQL : dump quotidien, rétention 30j
- S3 : versioning activé
- Test restore : mensuel obligatoire

## 12. Hébergement cible

VPS Hetzner ou OVH · Docker · PostgreSQL managé ou containerisé · Redis · S3 compatible.

Détail Docker local : `docs/architecture/DOCKER.md`
