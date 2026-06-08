---
type: PRD
version: 3.1
status: PROPOSED
owner: CTO
project: YurPass
ready_for_bmad: pending
date: 2026-06-08
related_adr:
  - ADR-001
  - ADR-002
---

# YurPass — Product Requirements Document V3.1

> PRD global produit YurPass.
> Sections 1 à 14 : vision, scope MVP, modèle économique, architecture produit, parcours utilisateurs, fonctionnalités core, contraintes techniques et sécurité (validation CTO antérieure).
> Sections 15 à 20 : compléments stratégiques Sprint 1 (ci-dessous).

---

# 15. PERSONAS

## Persona 1 — Achraf (Organisateur Nightlife)

Profil :

* Gère la communication de plusieurs boîtes de nuit et événements.
* Organise ou accompagne des soirées, concerts et événements récurrents.
* Dispose déjà d'un réseau d'établissements partenaires.

Objectifs :

* Vendre rapidement des billets.
* Réduire les commissions des plateformes existantes.
* Contrôler les entrées efficacement.
* Centraliser la gestion des événements.

Motivations :

* Augmenter le taux de remplissage.
* Réduire les coûts.
* Améliorer l'expérience client.
* Disposer d'indicateurs de performance.

Freins :

* Changement d'outil.
* Complexité technique.
* Crainte des bugs le soir des événements.
* Dépendance à une plateforme externe.

Succès :

* Événements remplis.
* Contrôle d'accès fluide.
* Commission inférieure aux concurrents.
* Visibilité en temps réel des ventes.

---

## Persona 2 — Participant

Profil :

* Étudiant, jeune actif ou participant à des événements.
* Recherche une expérience simple et rapide.

Objectifs :

* Acheter un billet rapidement.
* Accéder facilement à l'événement.
* Conserver un historique de ses participations.

Motivations :

* Gain de temps.
* Simplicité.
* Expériences exclusives.

Freins :

* Processus d'achat trop long.
* Création de compte complexe.
* Problèmes de QR code.

Succès :

* Achat en quelques minutes.
* Entrée rapide.
* Historique disponible dans son Passport.

---

## Persona 3 — Staff Check-in

Profil :

* Agent d'accueil.
* Contrôleur d'accès.
* Personnel événementiel.

Objectifs :

* Vérifier rapidement les billets.
* Limiter la fraude.
* Gérer les files d'attente.

Motivations :

* Simplicité d'utilisation.
* Rapidité de validation.

Freins :

* Réseau faible.
* Interface complexe.

Succès :

* Validation rapide.
* Faible temps d'attente.

---

## Persona 4 — Admin YurPass

Profil :

* Équipe interne YurPass.

Objectifs :

* Superviser les organisations.
* Assurer la conformité.
* Gérer les incidents.

Motivations :

* Stabilité de la plateforme.
* Satisfaction des organisateurs.

Succès :

* Peu d'incidents.
* Forte adoption.
* Croissance du réseau.

---

# 16. RÔLE D'ACHRAF

Statut actuel :

* Partenaire stratégique.
* Canal d'acquisition principal de la phase de lancement.
* Early adopter prioritaire.

Responsabilités :

* Faciliter l'accès aux établissements partenaires.
* Fournir des retours terrain.
* Participer aux phases pilotes.

Impact produit :

Les besoins opérationnels remontés par Achraf servent de référence pour la priorisation du MVP V1.

YurPass n'est cependant pas développé pour un seul partenaire.

Toutes les fonctionnalités doivent rester génériques et réutilisables par n'importe quelle organisation.

---

# 17. GO-TO-MARKET

## Phase pilote

Objectif :

Valider YurPass sur des événements réels avant un déploiement à grande échelle.

Événements pilotes identifiés :

* Saint-Dizier
* Concert La Fouine
* Événements partenaires du réseau Achraf

## Processus d'onboarding

Étape 1 :
Identification d'un établissement partenaire.

Étape 2 :
Création de l'organisation sur YurPass.

Étape 3 :
Configuration Stripe Connect.

Étape 4 :
Création de l'événement.

Étape 5 :
Formation rapide du personnel de check-in.

Étape 6 :
Accompagnement du premier événement.

## Support lancement

Phase pilote :

* Support direct assuré par l'équipe fondatrice.
* Intervention rapide en cas d'incident.
* Monitoring des ventes et check-ins.

Objectif :

Obtenir les premiers cas clients réels et les premiers témoignages partenaires.

---

# 18. VISION 3 ANS

## Année 1

Objectif :

Devenir une solution reconnue dans la nightlife.

Cibles :

* Clubs
* Boîtes de nuit
* Concerts
* Festivals

Livrables :

* Billetterie
* Invitations
* Check-in QR
* Dashboard organisateur

---

## Année 2

Expansion verticale.

Nouveaux segments :

* BDE
* Associations
* Événements sportifs
* Centres de loisirs
* Conférences

Objectif :

Multiplier les organisations actives.

---

## Année 3

Écosystème Passport.

Le Passport devient une identité numérique transverse entre plusieurs produits.

Produits concernés :

* YurPass
* Yunicity
* SharingGO
* Produits futurs du groupe

Objectif :

Créer une identité numérique réutilisable dans tout l'écosystème.

---

# 19. KPIS LANCEMENT (90 JOURS)

Objectifs :

* 5 organisations onboardées.
* 15 événements créés.
* 1 000 billets vendus.
* 10 000 € de GMV.
* Commission moyenne : 3 %.
* Taux de check-in supérieur à 80 %.
* 0 incident critique bloquant lors d'un événement.

---

# 20. ÉCOSYSTÈME IMORIA

IMORIA est la structure entrepreneuriale porteuse des différents produits numériques développés par l'équipe fondatrice.

YurPass constitue le pôle événementiel de cet écosystème.

À long terme, plusieurs produits pourront partager une identité commune appelée Passport.

Le Passport est conçu comme une couche d'identité réutilisable entre les différentes applications du groupe afin d'offrir une expérience utilisateur cohérente et interconnectée.
