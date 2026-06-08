# Simplify — YurPass

> Anti sur-ingénierie · Diff minimal
> Path-scoped : `.claude/rules/simplify.md` · Always apply

## Gouvernance

Avant chaque ajout :

1. Existe déjà dans le projet ?
2. 5 lignes suffisent ?
3. Abstraction utilisée > 1 fois ?
4. Le ticket le demande ?

**Si non → ne pas ajouter.**

## Interdit

- Helper pour 1 usage
- Factory pour 1 implémentation
- Config pour 2 valeurs
- Refactor opportuniste hors ticket
- Code commenté / mort

## Alarmes spaghetti

Fichier > 300 lignes · Fonction > 50 lignes · Imports circulaires · TODO qui traînent

## Règle d'or

Le diff le plus simple qui résout le ticket correctement est le meilleur diff.
