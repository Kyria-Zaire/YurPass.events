---
paths:
  - "frontend/**"
---

# Constructeur UI — YurPass Frontend

Stack : Next.js 15 + TypeScript + Tailwind + shadcn/ui.

## Structure

```
frontend/
├── apps/web/       # Public : landing, events, wallet, passport
├── apps/admin/     # Cockpit : events ops, orgs, check-in
└── packages/
    ├── ui/         # Design system (Button, Card, EventCard, QRCard...)
    ├── types/      # User, Event, Ticket, Order...
    ├── utils/      # formatDate, formatPrice, buildQrPayload
    └── config/     # eslint, tailwind, prettier partagés
```

## Règles composants

1. **Composants réutilisables** → `packages/ui/`, jamais dupliqués entre apps
2. **Server Components** par défaut dans Next.js 15
3. **`"use client"`** uniquement pour interactivité (forms, modals, animations)
4. **Pas de fetch client** si Server Component peut le faire
5. **Accessibilité** : labels, aria, focus visible, contraste WCAG AA

## Design system (`packages/ui`)

Composants MVP :
`Button`, `Input`, `Card`, `Badge`, `Modal`, `Table`, `Sidebar`, `Navbar`, `QRCard`, `EventCard`

Utiliser shadcn/ui comme base, customiser pour YurPass.

## Apps

### web
Landing, catalogue events, détail event, achat billet, wallet, passport public.

### admin
Cockpit, Events Ops, Organizations, Hosts, Tickets, Payments, Check-in, Sponsors, Staff.

## Skills design à invoquer

1. `/design-taste-frontend` — direction anti-slop
2. `/image-to-code` — références visuelles d'abord
3. `/constructeur-ui` — implémentation
4. `/emil-design-eng` — motion
5. `/impeccable` — audit final

## Anti-patterns interdits

- Cards dans cards dans cards
- Hero dark cliché centré
- Tailwind arbitraire partout sans tokens
- `any` dans les props
- Styles inline sauf valeurs dynamiques
- Copier un composant au lieu de l'extraire dans `packages/ui`

## Tokens design

Définir dans `packages/config/tailwind` :
- Couleurs brand YurPass
- Spacing scale cohérente
- Typography scale (display, body, caption)
- Border radius, shadows

## Responsive

Mobile-first. Check-in staff en web responsive au MVP (avant app mobile).
