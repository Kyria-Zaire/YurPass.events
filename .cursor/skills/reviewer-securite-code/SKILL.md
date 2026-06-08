---
name: reviewer-securite-code
description: Expert cybersécurité YurPass — webhooks, auth, RBAC, honeypot, Turnstile, anti-injection.
disable-model-invocation: true
---

# Reviewer Sécurité — YurPass

Rule : `reviewer-securite-code.mdc`.

## Audit

Webhooks : signature + idempotence + scope tenant. Hors scope → FAIL.
Auth : Argon2, JWT, rate limit, magic link, OTP, Turnstile.
Forms : honeypot + validation serveur.
RBAC : permissions.py. QR : JWT signé.

Verdict : **PASS | FAIL**
