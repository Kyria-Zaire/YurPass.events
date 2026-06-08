# Reviewer Sécurité Code — YurPass

> Expert cybersécurité · OWASP · Anti-compromission SaaS
> Path-scoped : `.claude/rules/reviewer-securite-code.md` · Skill : `/reviewer-securite-code`
> Baseline : `docs/security/SECURITY_BASELINE.md`

## Gouvernance

- Review **obligatoire** pour : auth, RBAC, webhooks, paiements, QR, formulaires publics
- Verdict **FAIL** = code abandonné, pas de contournement
- Jamais lire `.env.production` ou secrets prod

## Webhooks Stripe

```python
event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
# Idempotence event.id · Scope tenant strict
```

**INTERDIT :** traiter sans signature · DELETE/UPDATE sans WHERE tenant · cross-tenant access
**Si webhook touche données hors scope → ABANDONNER le code.**

## Auth

| Mécanisme | Exigence |
|-----------|----------|
| Passwords | Argon2id ou bcrypt cost ≥ 12 |
| JWT | Access 15min · Refresh rotatif révocable |
| Rate limit login | 5 tentatives / 15min / IP+email |
| Magic link | Token unique · 15min · usage unique |
| OTP | 6 chiffres · 5min · max 3 tentatives |
| OAuth Google | State CSRF · `email_verified` |
| Turnstile | Requis recette+ |

## Formulaires publics

Honeypot hidden (`website_url`) · Validation serveur · CSP strict

## RBAC

`permissions.py` uniquement — jamais en dur dans routes.
Rôles MVP : `superadmin`, `org_admin`, `host`, `staff`, `participant`

## QR Tickets

JWT signé (`event_id`, `ticket_id`, `exp`) · Pas de PII dans payload

## Environnements

Stripe test keys : local/recette/preprod uniquement. Live keys : production uniquement.

## Verdict

**PASS | FAIL** — FAIL bloque le merge.
