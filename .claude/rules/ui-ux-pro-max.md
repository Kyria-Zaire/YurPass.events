---
paths:
  - "frontend/**"
---

# UI/UX Pro Max — YurPass

Standards UX premium pour éviter les interfaces génériques AI.

## Hiérarchie visuelle

1. Un point focal par écran (hero CTA, action principale)
2. Max 3 niveaux typographiques visibles simultanément
3. Contraste suffisant : texte body ≥ 4.5:1, large text ≥ 3:1
4. Whitespace généreux — respiration entre sections

## Layout

- Grille 12 colonnes desktop, 4 mobile
- Alignement cohérent (pas de micro-décalages)
- Sections avec rythme vertical constant (multiples de 8px)
- Sidebar admin fixe, content scrollable

## États UI obligatoires

Chaque composant interactif doit gérer :
- `default` | `hover` | `focus` | `active` | `disabled` | `loading` | `error` | `empty`

## Micro-copy

- Labels actionnels ("Créer l'événement", pas "Submit")
- Messages erreur utiles ("Email invalide", pas "Error 400")
- Empty states avec CTA ("Aucun événement — Créer le premier")

## Patterns YurPass

- **EventCard** : image, titre, date, lieu, prix, badge statut
- **QRCard** : QR centré, infos ticket, countdown expiration
- **Wallet** : liste tickets avec statut visuel clair
- **Check-in** : gros bouton scan, feedback immédiat vert/rouge

## Accessibilité

- Focus visible sur tous éléments interactifs
- `aria-label` sur icônes seules
- Navigation clavier complète
- `prefers-reduced-motion` respecté
