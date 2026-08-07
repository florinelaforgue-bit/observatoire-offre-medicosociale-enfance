# Modèle de données

## Objectif

Le logiciel manipule plusieurs types d'objets représentant l'offre médico-sociale française.

Ce document décrit ces objets de manière conceptuelle, indépendamment de leur implémentation informatique.

Il constitue le référentiel de données du projet.

---

# Principes

Chaque objet représente une entité réelle.

Les relations entre ces objets doivent rester stables, même si les sources de données évoluent.

Le modèle de données doit rester indépendant :

- des fichiers CSV ;
- des exports Excel ;
- des bases de données ;
- des technologies utilisées.

---

# Objet : Établissement

Représente un établissement géographique (ET).

Exemples :

- IME
- DITEP
- SESSAD
- MECS
- CMPP

Principales informations :

- numéro FINESS ET
- numéro FINESS EJ
- raison sociale
- catégorie FINESS
- catégorie agrégée
- dates
- département
- commune
- adresse
- téléphone
- SIRET
- code APE

Relations :

- appartient à une Entité Juridique ;
- possède zéro, un ou plusieurs Équipements Sociaux ;
- appartient à une catégorie FINESS ;
- appartient à une famille taxonomique.

---

# Objet : Entité Juridique

Représente le gestionnaire administratif d'un ou plusieurs établissements.

Exemples :

- association
- fondation
- établissement public
- organisme gestionnaire

Principales informations :

- numéro FINESS EJ
- liste des établissements rattachés

Relations :

- possède plusieurs établissements.

---

# Objet : Équipement Social

Représente une activité ou une autorisation portée par un établissement.

Informations principales :

- discipline
- fonctionnement
- clientèle
- champs complémentaires

Relations :

- appartient à un établissement.

---

# Objet : Catégorie FINESS

Représente la classification officielle d'un établissement.

Exemples :

- DITEP
- IME
- SESSAD
- MECS

Relations :

- appartient à une famille taxonomique.

---

# Objet : Famille taxonomique

Classification scientifique développée dans le cadre de l'observatoire.

Exemples :

- Handicap
- Protection de l'enfance
- Sanitaire
- Petite enfance

Une famille contient plusieurs sous-familles.

---

# Objet : Sous-famille

Subdivision d'une famille taxonomique.

Exemples :

- IME
- DITEP
- IEM
- EEAP

Chaque sous-famille contient une ou plusieurs catégories FINESS.

---

# Objet : Source de données

Une source représente un producteur de données.

Exemples :

- FINESS
- INSEE
- DREES
- CNSA
- IGN
- OpenStreetMap

Chaque source possède :

- un millésime ;
- une date de mise à jour ;
- une version ;
- une méthode de téléchargement.

---

# Objet : Millésime

Représente une photographie des données à une date donnée.

Exemple :

FINESS 2026

Un millésime est toujours associé à :

- une source ;
- une date ;
- une version.

Le projet permettra de comparer plusieurs millésimes successifs.

---

# Objet : Indicateur

Un indicateur est une mesure reproductible calculée à partir des données.

Exemples :

- nombre d'établissements ;
- nombre de places ;
- densité d'offre ;
- établissements pour 10 000 habitants ;
- taux d'équipement.

Les indicateurs sont indépendants des exports.

Ils peuvent être utilisés dans plusieurs analyses.

---

# Objet : Analyse

Une analyse est un traitement scientifique réalisé à partir des indicateurs.

Exemples :

- analyse territoriale ;
- comparaison régionale ;
- évolution temporelle ;
- accessibilité ;
- inégalités territoriales.

Une analyse peut produire :

- des tableaux ;
- des graphiques ;
- des cartes ;
- des publications scientifiques.

---

# Relations entre les objets

Source de données
        │
        ▼
 Millésime
        │
        ▼
 Établissement
        │
 ┌──────┴────────┐
 ▼               ▼
Équipement     Entité Juridique
        │
        ▼
 Catégorie FINESS
        │
        ▼
 Sous-famille
        │
        ▼
 Famille taxonomique
        │
        ▼
 Indicateurs
        │
        ▼
 Analyses
