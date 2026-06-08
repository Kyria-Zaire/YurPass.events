---
paths:
  - "frontend/**"
---

# Frontend Design — YurPass

Direction visuelle et processus design pour YurPass.

## Identité YurPass

- **Produit** : infrastructure identité + invitation + accès expériences locales
- **Ton** : premium mais accessible, local et humain, pas corporate froid
- **Éviter** : dark hero cliché, gradients violets, cards spam, look "AI slop"

## Processus design (obligatoire pour nouvelles pages)

1. **Brief inference** — lire le contexte, audience, vibe (voir `/design-taste-frontend`)
2. **Références** — `/image-to-code` génère des comps avant de coder
3. **Tokens** — couleurs, typo, spacing dans `packages/config`
4. **Composants** — shadcn base + wrappers YurPass
5. **Motion** — `/emil-design-eng` pour polish
6. **Audit** — `/impeccable` avant livraison

## Typographie

- Display : une police distinctive (pas Inter partout)
- Body : lisible, 16px minimum
- Hiérarchie : display > h1 > h2 > body > caption

## Couleurs

- Palette brand définie (primary, secondary, accent, neutral)
- Dark mode cohérent, pas juste inversion
- Statuts : success/warning/error/info distincts

## Spacing

- Scale 4px base : 4, 8, 12, 16, 24, 32, 48, 64, 96
- Sections : padding vertical 64-96px desktop, 48px mobile
- Cards : padding 16-24px

## Skills à combiner

```
/image-to-code → /constructeur-ui → /emil-design-eng → /impeccable
```

Plugin Claude : `frontend-design@claude-plugins-official`
