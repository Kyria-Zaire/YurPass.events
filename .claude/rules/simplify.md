# Simplify — YurPass

Réduire la complexité avant d'ajouter du code.

## Questions avant chaque ajout

1. Ce code existe-t-il déjà dans le projet ?
2. Peut-on résoudre avec 5 lignes au lieu de 50 ?
3. Cette abstraction sera-t-elle utilisée plus d'une fois ?
4. Le ticket demande-t-il vraiment cette feature ?

## Règles

- **Pas de helper pour 1 usage** — inline
- **Pas de wrapper inutile** — appeler directement
- **Pas de config pour 2 valeurs** — constantes suffisent
- **Pas de factory pattern** pour 1 implémentation
- **Supprimer le mort** — code commenté, imports inutilisés, fichiers orphelins

## Refactor autorisé seulement si

- Duplication ≥ 3 occurrences identiques
- Bug causé par la complexité actuelle
- Ticket explicitement demande refactor

## Frontend

- Un composant = une responsabilité
- Pas de prop drilling > 2 niveaux → context ou composition
- Pas de state global pour state local

## Backend

- Un service method = une action métier
- Pas de repository method "get_all_everything"
- Pas de middleware custom si FastAPI dependency suffit

## Signaux d'alarme spaghetti

- Fichier > 300 lignes sans raison
- Fonction > 50 lignes
- Plus de 4 niveaux d'indentation
- Commentaires "TODO: refactor later" qui traînent
- Imports circulaires
