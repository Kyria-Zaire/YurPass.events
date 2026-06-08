---
paths:
  - "backend/**"
  - "frontend/**"
  - "infra/**"
  - "**/.env*"
---

# Reviewer Sécurité Code — YurPass

Posture : expert cybersécurité applicative. Objectif : éviter le scénario "tout mon SaaS infecté, redirection Melbet".

## Lignes rouges absolues

### Webhooks (Stripe et autres)

```python
# OBLIGATOIRE avant tout traitement
event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
# Vérifier idempotence (event.id déjà traité → skip)
# Scope strict au tenant/order concerné
```

**INTERDIT** :
- Traiter un webhook sans vérification signature
- DELETE/UPDATE sans clause WHERE tenant-scoped
- Modifier des données d'un autre client
- Exécuter des actions destructives sur `event.type` ambigu

Si un webhook touche ou supprime des données hors scope → **ABANDONNER le code**.

### Auth

- Passwords : Argon2id ou bcrypt (cost ≥ 12)
- JWT access court (15min), refresh rotatif avec révocation
- Rate limiting login : 5 tentatives / 15min / IP+email
- Magic link : token unique, expiration 15min, usage unique
- OTP : 6 chiffres, expiration 5min, max 3 tentatives
- OAuth Google : state CSRF, vérifier `email_verified`
- Cloudflare Turnstile : obligatoire login/register en recette+

### Formulaires publics

- Honeypot field (`website_url` hidden) — si rempli → reject silencieux
- Validation serveur systématique (jamais confiance client seul)
- CSP headers stricts
- Pas de `dangerouslySetInnerHTML` sans sanitization

### RBAC

```python
# permissions.py — jamais en dur dans router
@require_permission("events:write", scope="organization")
async def create_event(...):
```

Rôles MVP : `superadmin`, `org_admin`, `host`, `staff`, `participant`.

### QR Tickets

- JWT signé avec `event_id`, `ticket_id`, `exp`
- Vérification à chaque scan
- Pas de données PII dans le QR payload

### Injection & XSS

- SQL : ORM/SQLAlchemy paramétré uniquement
- Pas de f-string SQL
- Échapper outputs HTML
- Valider tous les inputs Pydantic/Zod

### Environnements

- Jamais de clé prod dans le repo
- Stripe test keys en local/recette/preprod uniquement
- `.env.production` jamais commité, jamais lu par l'IA

### Headers sécurité (prod)

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: [strict]
Referrer-Policy: strict-origin-when-cross-origin
```

## Checklist review sécu

- [ ] Inputs validés serveur
- [ ] Auth sur toutes routes sensibles
- [ ] RBAC vérifié
- [ ] Webhook signature + idempotence
- [ ] Pas de secret en clair
- [ ] Rate limiting sur auth
- [ ] Turnstile sur forms publics
- [ ] Honeypot sur forms publics
- [ ] Logs sans PII/passwords
- [ ] CORS restrictif (pas `*` en prod)
