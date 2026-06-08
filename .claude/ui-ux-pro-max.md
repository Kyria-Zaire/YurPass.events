# UI/UX Pro Max — YurPass

> UX premium · Hiérarchie · États · Accessibilité
> Path-scoped : `.claude/rules/ui-ux-pro-max.md`

## Gouvernance

- Scope : `frontend/**` · Pas de redesign hors ticket/PRD
- Chaque composant interactif : 8 états obligatoires

## Hiérarchie

1 focal par écran · Max 3 niveaux typo · Contraste WCAG AA · Whitespace généreux

## États obligatoires

`default` · `hover` · `focus` · `active` · `disabled` · `loading` · `error` · `empty`

## Patterns YurPass

- **EventCard** : image, titre, date, lieu, prix, statut
- **QRCard** : QR centré, infos ticket, expiration
- **Wallet** : tickets avec statut visuel
- **Check-in** : feedback immédiat vert/rouge

## Micro-copy

Labels actionnels · Erreurs utiles · Empty states avec CTA

## Accessibilité

Focus visible · `aria-label` sur icônes · Navigation clavier · `prefers-reduced-motion`
