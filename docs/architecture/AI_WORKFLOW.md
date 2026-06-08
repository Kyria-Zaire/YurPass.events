# YurPass — AI Workflow

> Comment Cursor et Claude Code exécutent YurPass sans dérive.
> TICKET-002 — AI Governance Files Hardening

---

## 1. Philosophie

YurPass utilise le **vibe coding contrôlé** : les agents IA accélèrent l'exécution, mais ne décident pas du scope, de l'architecture ou des commits.

```
Humain (CTO) décide → PRD/ADR/BMAD cadrent → Agent exécute → Humain valide
```

---

## 2. Outils & fichiers

| Outil | Config principale | Rules / Skills |
|-------|-------------------|----------------|
| **Claude Code** | `.claude/Claude.md` | `.claude/*.md` + `.claude/rules/` + `.claude/skills/` |
| **Cursor** | `.cursor/Cursor.md` | `.cursor/rules/*.mdc` + `.cursor/skills/` + `rules.json` |
| **Commun** | `AGENTS.md`, `CLAUDE.md` | `.agents/skills/` (design externes) |

---

## 3. Workflow complet

```
┌─────────────┐
│    PRD      │  Pourquoi · Qui · Business goals
│ Ready: YES  │
└──────┬──────┘
       ↓
┌─────────────┐
│    ADR      │  Décision architecture (si applicable)
│  ACCEPTED   │
└──────┬──────┘
       ↓
┌─────────────┐
│    BMAD     │  Ticket sprint · Scope · Critères
│   TICKET    │
└──────┬──────┘
       ↓
┌─────────────┐
│    Agent    │  Cursor ou Claude Code
│  Execution  │  Skill/rôle approprié
└──────┬──────┘
       ↓
┌─────────────┐
│   Review    │  /code-review + /reviewer-securite-code
└──────┬──────┘
       ↓
┌─────────────┐
│ Validation  │  Humain CTO
│  + Merge    │  DO NOT COMMIT sans validation
└─────────────┘
```

---

## 4. Rôles agents

| Rôle | Claude | Cursor | Scope |
|------|--------|--------|-------|
| Senior Dev | `seniordev.md` | `seniordev.mdc` | Toujours |
| Architecte API | `architecte-api.md` | `architecte-api.mdc` | `backend/**` |
| Constructeur UI | `constructeur-ui.md` | `constructeur-ui.mdc` | `frontend/**` |
| Code Review | `code-review.md` | `code-review.mdc` | Avant merge |
| Sécurité | `reviewer-securite-code.md` | `reviewer-securite-code.mdc` | Auth, webhooks |
| Ingénieur | `ingenieur.md` | `ingenieur.mdc` | `infra/**` |
| Workflow | `createur-workflow.md` | `createur-workflow.mdc` | Planification |

---

## 5. Lignes rouges agents

| # | Règle |
|---|-------|
| 1 | Pas de code sans PRD Ready For BMAD: YES |
| 2 | Pas de décision archi sans ADR ACCEPTED |
| 3 | Pas de feature hors ticket BMAD |
| 4 | Pas de modification hors scope ticket |
| 5 | DO NOT COMMIT sans validation humaine |
| 6 | Pas de secret dans le repo |
| 7 | Pas de suppression fichier sans demande |
| 8 | Pas de dépendance installée hors ticket |

---

## 6. Exécution d'un ticket

### Avant de coder

1. Lire le ticket BMAD actif (`docs/sprints/` ou `docs/bmad/`)
2. Vérifier PRD et ADR liés
3. Identifier le rôle (`[ROLE]` dans le ticket)
4. Invoquer le skill correspondant

### Pendant le code

1. Diff minimal — fichiers INCLUS uniquement
2. Respecter EXCLUSIONS STRICTES du ticket
3. Backend : `router → service → repository`
4. Frontend : `packages/ui`, `packages/types`
5. Sécu : baseline si auth/paiements/webhooks

### Après le code

1. Rapport OUTPUT ATTENDU (fichiers, commandes, validation)
2. **Pas de commit** — attendre validation humaine
3. Si demandé : `/code-review` + `/reviewer-securite-code`

---

## 7. Workflow design UI

```
/design-taste-frontend ou /image-to-code
        ↓
/constructeur-ui + shadcn
        ↓
/emil-design-eng + make-interfaces-feel-better
        ↓
/impeccable (audit final)
```

---

## 8. Harmonisation Claude ↔ Cursor

Les règles sont **équivalentes** entre plateformes :

| Claude (`.claude/`) | Cursor (`.cursor/rules/`) |
|---------------------|---------------------------|
| `seniordev.md` | `seniordev.mdc` |
| `architecte-api.md` | `architecte-api.mdc` |
| etc. | etc. |

Index Cursor : `.cursor/rules.json`

---

## 9. Anti-patterns vibe coding

| Dérive | Prévention |
|--------|------------|
| Code spaghetti | `seniordev` + `simplify` |
| Features inventées | BMAD INCLUS/EXCLUSIONS |
| Dette invisible | `code-review` + ADR |
| Failles sécurité | `reviewer-securite-code` + SECURITY_BASELINE |
| Commits sauvages | DO NOT COMMIT rule |
| Scope creep | Ticket unique, rapport CTO |

---

## 10. Références

- Templates : `docs/templates/`
- Sécurité : `docs/security/SECURITY_BASELINE.md`
- Environnements : `docs/architecture/ENVIRONMENTS.md`
- ADR-001 : `docs/adr/ADR-001-monorepo-modulaire.md`
