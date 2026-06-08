---
paths:
  - "frontend/**"
---

# shadcn/ui — YurPass

shadcn/ui comme base du design system dans `packages/ui`.

## Installation

```bash
cd frontend/packages/ui
npx shadcn@latest init
npx shadcn@latest add button input card badge dialog table sidebar
```

## Conventions

- Composants shadcn dans `packages/ui/src/components/ui/`
- Wrappers YurPass dans `packages/ui/src/components/yurpass/`
- Pas d'import direct shadcn depuis les apps — toujours via `@yurpass/ui`

## Customisation

```typescript
// packages/ui/src/components/ui/button.tsx
// Modifier les variants ici, pas dans les apps
const buttonVariants = cva("...", {
  variants: {
    variant: {
      default: "bg-brand-primary ...",
      destructive: "...",
      outline: "...",
      ghost: "...",
    },
  },
});
```

## Composants MVP shadcn

`button`, `input`, `label`, `card`, `badge`, `dialog`, `dropdown-menu`, `table`, `tabs`, `toast`, `form`, `select`, `avatar`, `separator`, `sheet` (mobile sidebar)

## Wrappers YurPass à créer

- `EventCard` — compose Card + Badge + image
- `QRCard` — Card + QR display
- `TicketBadge` — Badge avec statut coloré
- `AdminSidebar` — Sidebar + navigation items

## Theming

CSS variables dans `globals.css` :
```css
:root {
  --brand-primary: ...;
  --brand-secondary: ...;
  --radius: 0.5rem;
}
```

Dark mode via `class` strategy (next-themes).
