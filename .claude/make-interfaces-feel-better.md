# Make Interfaces Feel Better — YurPass

> Motion · Polish · Feedback utilisateur
> Path-scoped : `.claude/rules/make-interfaces-feel-better.md` · Complète `/emil-design-eng`

## Gouvernance

- Motion avec **but** — pas d'animation gratuite
- Respecter `prefers-reduced-motion` — obligatoire

## Durées

UI : 150-300ms · Page transitions : 300-500ms · Stagger listes : 30-50ms

## Patterns

- Button : scale 0.98 on press
- Modal : backdrop fade 200ms + content scale
- Toast : slide-in, auto-dismiss 4s
- EventCard hover : lift -2px + shadow

## Libs

CSS transitions par défaut · Framer Motion si layout complexe · Pas de GSAP sauf hero spécifique

## Interdit

Animation sans purpose · Motion qui bloque l'accessibilité
