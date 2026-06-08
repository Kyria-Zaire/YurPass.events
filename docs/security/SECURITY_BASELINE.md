# YurPass — Security Baseline

> Baseline sécurité obligatoire dès Sprint 0.
> Référencé par : `.claude/reviewer-securite-code.md` · `.cursor/rules/reviewer-securite-code.mdc`

## Objectif

Éviter les compromissions classiques SaaS : redirections malveillantes, data leak cross-tenant, webhooks non vérifiés, credentials exposés.

---

## 1. Authentification

| Exigence | Détail |
|----------|--------|
| Password hashing | Argon2id (préféré) ou bcrypt cost ≥ 12 |
| JWT access | Durée courte (~15 min) |
| Refresh token | Rotatif, révocable, stocké Redis |
| Magic link | Token unique, expiration 15 min, usage unique |
| OTP | 6 chiffres, expiration 5 min, max 3 tentatives |
| OAuth Google | State CSRF, vérifier `email_verified` |
| Email verification | Obligatoire avant accès complet |

---

## 2. Autorisation (RBAC)

- Permissions dans `permissions.py` — **jamais en dur dans routes**
- Scope tenant sur toutes opérations données
- Rôles MVP : `superadmin`, `org_admin`, `host`, `staff`, `participant`
- Principe du moindre privilège

---

## 3. Rate limiting

| Endpoint | Limite |
|----------|--------|
| Login | 5 tentatives / 15 min / IP + email |
| Register | 3 / heure / IP |
| Magic link request | 3 / heure / email |
| OTP verify | 5 / 15 min / session |
| API publiques | Configurable par route |

---

## 4. Abuse prevention

| Mécanisme | Usage |
|-----------|-------|
| **Honeypot** | Champ hidden `website_url` sur formulaires publics — si rempli → reject silencieux |
| **Cloudflare Turnstile** | Login/register recette+ (requis prod) |
| **CSP** | Headers stricts en production |
| **CORS** | Restrictif — pas `*` en prod |

---

## 5. Webhooks (Stripe)

```python
# OBLIGATOIRE — avant tout traitement
event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
```

| Règle | Obligatoire |
|-------|-------------|
| Vérification signature | OUI |
| Idempotence (`event.id`) | OUI |
| Scope tenant | OUI |
| Log sans PII | OUI |

**INTERDIT :**
- Traiter sans signature
- DELETE/UPDATE sans WHERE tenant-scoped
- Accès cross-tenant
- Actions destructives sur `event.type` ambigu

**Si un webhook touche ou supprime des données hors scope → ABANDONNER le code.**

---

## 6. QR Tickets

- JWT signé : `event_id`, `ticket_id`, `exp`
- Vérification à chaque scan
- Pas de PII dans le payload QR
- Révocation possible côté serveur

---

## 7. Données & injection

- SQL : ORM/SQLAlchemy paramétré uniquement
- XSS : pas de `dangerouslySetInnerHTML` sans sanitization
- Validation : Pydantic (backend) + Zod (frontend) sur tous inputs
- Logs : jamais de passwords, tokens, PII complètes

---

## 8. Secrets & environnements

| Règle | Détail |
|-------|--------|
| Secrets dans repo | **INTERDIT** |
| `.env.production` | Gitignore · Jamais lu par IA |
| Stripe live keys | Production uniquement |
| Stripe test keys | local, recette, preprod uniquement |
| Fichiers commités | `.env.example` sans valeurs réelles |

---

## 9. Headers sécurité (production)

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: [strict policy]
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: [restrictive]
```

---

## 10. Backups production

| Élément | Fréquence |
|---------|-----------|
| PostgreSQL dump | Quotidien |
| Rétention | 30 jours |
| S3 uploads | Versioning activé |
| Test restore | Mensuel |

---

## 11. Review obligatoire

Invoquer `/reviewer-securite-code` pour tout code touchant :

- Auth / sessions
- RBAC / permissions
- Webhooks / paiements
- Formulaires publics
- QR / tickets
- Upload fichiers
- Admin actions

**Verdict FAIL = merge bloqué.**

---

## 12. Threat model MVP (résumé)

| Menace | Mitigation |
|--------|------------|
| Credential stuffing | Rate limit + Turnstile |
| CSRF | Tokens, SameSite cookies |
| XSS | CSP, sanitization, pas d'innerHTML |
| SQL injection | ORM paramétré |
| Webhook forgery | Signature Stripe |
| Cross-tenant access | RBAC + scope queries |
| Secret leak | Gitignore, vault prod |
| Account takeover | MFA-ready, OTP, email verify |
