# shadcn/ui — YurPass

> Design system base · packages/ui
> Path-scoped : `.claude/rules/shadcn.md`

## Gouvernance

- shadcn vit dans `packages/ui/src/components/ui/`
- Apps importent via `@yurpass/ui` — **jamais** shadcn direct
- Pas d'install shadcn hors ticket frontend foundation

## Structure

```
packages/ui/src/components/ui/       # shadcn base
packages/ui/src/components/yurpass/  # wrappers (EventCard, QRCard...)
```

## Wrappers YurPass MVP

EventCard · QRCard · TicketBadge · AdminSidebar

## Theming

CSS variables brand dans `globals.css` · Dark mode via next-themes (`class` strategy)

## Composants MVP

button · input · card · badge · dialog · table · tabs · toast · form · select · sidebar
