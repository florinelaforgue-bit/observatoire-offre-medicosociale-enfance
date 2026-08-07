# Architecture cible

## Objectif

Décrire l'architecture cible de l'Observatoire national de l'offre médico-sociale enfance.

Cette architecture est pensée pour évoluer pendant de nombreuses années sans nécessiter de réécriture majeure.

Le principe fondamental est la séparation stricte des responsabilités.

---

# Vue d'ensemble

```

```
                    Sources de données
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
     FINESS             INSEE              CNSA
        │                  │                  │
        └──────────────┬───┴──────────────────┘
                       │
                Import / Lecture
                       │
                Normalisation
                       │
                Modèle de données
                       │
       ┌───────────────┼────────────────┐
       │               │                │
   Taxonomie      Indicateurs      Géographie
       │               │                │
       └───────────────┼────────────────┘
                       │
                  Analyses
                       │
       ┌───────────────┼────────────────┐
       │               │                │
     Excel          Cartes          Articles
```

---

# 1. Sources

Le logiciel doit pouvoir intégrer plusieurs producteurs de données.

Exemples :

- FINESS
- INSEE
- DREES
- CNSA
- IGN
- OpenStreetMap
- autres jeux de données ouverts

Chaque source reste indépendante.

---

# 2. Lecture

Responsabilité :

Lire les données brutes.

Elle ne réalise jamais :

- d'analyse ;
- de statistiques ;
- de classification.

Elle transforme uniquement les fichiers en objets exploitables.

---

# 3. Normalisation

Responsabilité :

Transformer les données provenant des différentes sources dans un modèle commun.

Exemple :

FINESS :

"libelle_categorie_etablissement"

↓

Modèle interne :

categorie

Cette couche permet de rendre toutes les sources compatibles.

---

# 4. Modèle de données

Le modèle de données constitue le cœur du projet.

Tous les autres modules manipulent exclusivement ce modèle.

Aucun module d'analyse ne doit dépendre directement du format des fichiers sources.

---

# 5. Taxonomie

Responsabilité :

Classifier les établissements selon une logique scientifique indépendante de FINESS.

La taxonomie est :

- versionnée ;
- documentée ;
- reproductible.

Elle peut évoluer sans modifier les données sources.

---

# 6. Indicateurs

Les indicateurs sont des calculs reproductibles.

Exemples :

- nombre d'établissements ;
- nombre de places ;
- densité territoriale ;
- établissements pour 10 000 enfants ;
- distance moyenne ;
- accessibilité.

Ils sont indépendants des exports.

---

# 7. Analyses

Les analyses utilisent les indicateurs.

Exemples :

- comparaison régionale ;
- comparaison départementale ;
- évolution temporelle ;
- typologie territoriale ;
- analyses statistiques ;
- cartographie.

Une analyse peut produire plusieurs résultats.

---

# 8. Exports

Les exports ne réalisent aucun calcul.

Ils mettent uniquement en forme les résultats.

Exemples :

- Excel
- CSV
- GeoJSON
- Parquet
- PDF
- graphiques
- cartes

---

# 9. Publications scientifiques

Les résultats produits par les analyses pourront être utilisés pour :

- des articles scientifiques ;
- des communications ;
- des rapports institutionnels ;
- des tableaux de bord.

Le logiciel n'est pas une finalité.

Il constitue un instrument scientifique.

---

# Organisation cible des modules

```

```
src/

sources/
    finess/
    insee/
    cnsa/
    drees/
    ign/

normalisation/

models/

taxonomie/

indicateurs/

analyses/

geographie/

validation/

exports/

utils/

config/

cli/

```

---

# Principes d'architecture

Chaque module possède une seule responsabilité.

Les dépendances doivent toujours aller dans le même sens.

```

```
Sources
      ↓

Normalisation
      ↓

Modèle
      ↓

Indicateurs
      ↓

Analyses
      ↓

Exports

```

```

Aucun module ne doit dépendre d'un module situé "au-dessus".

Exemple :

Un export Excel ne doit jamais connaître FINESS.

Une analyse ne doit jamais lire directement un fichier CSV.

---

# Évolutivité

Cette architecture doit permettre :

- l'ajout de nouvelles sources de données ;
- l'ajout de nouveaux indicateurs ;
- l'ajout de nouvelles analyses ;
- l'ajout de nouveaux exports ;

sans modifier les modules existants.

L'objectif est d'assurer la pérennité scientifique et technique du projet sur le long terme.
