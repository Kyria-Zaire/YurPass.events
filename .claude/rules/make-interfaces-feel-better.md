---
paths:
  - "frontend/**"
---

# Make Interfaces Feel Better — YurPass

Motion et polish pour interfaces qui "se sentent bien". Complète `/emil-design-eng`.

## Principes

1. **Motion a un but** — guider l'attention, confirmer une action, montrer une transition
2. **Durées courtes** — 150-300ms UI, 300-500ms page transitions
3. **Easing naturel** — `cubic-bezier(0.25, 0.1, 0.25, 1)` ou spring pour playful
4. **Stagger subtil** — listes qui apparaissent avec délai 30-50ms entre items
5. **Pas de motion gratuite** — si ça ne sert rien, supprime

## Patterns YurPass

### Page load
```css
@keyframes fade-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-in { animation: fade-up 0.4s ease-out; }
```

### Button feedback
- Scale 0.98 on press
- Ripple ou background shift on hover
- Loading spinner remplace le texte, pas en plus

### Modal/Dialog
- Backdrop fade 200ms
- Content scale 0.95→1 + fade 250ms
- Focus trap immédiat

### Toast notifications
- Slide in from right, auto-dismiss 4s
- Success vert, error rouge, info bleu

### EventCard hover
- Subtle lift (translateY -2px) + shadow increase
- Image scale 1.02 inside overflow hidden

## `prefers-reduced-motion`

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Librairies

- CSS transitions/animations pour UI simple
- Framer Motion pour layouts complexes (page transitions)
- Pas de GSAP sauf effets hero spécifiques

## Invoquer

`/emil-design-eng` pour les décisions motion approfondies.
