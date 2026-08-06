# 06 – Modèle analytique

## 1. Philosophie

L'observatoire a pour vocation de décrire, comparer et suivre dans le temps l'offre sanitaire, sociale et médico-sociale en France à partir de données publiques.

Le logiciel est conçu comme une plateforme générique capable d'intégrer l'ensemble des établissements, activités, capacités et dispositifs présents dans les sources nationales.

Les travaux scientifiques issus de ce projet portent principalement sur l'offre destinée aux enfants et adolescents. Cette spécialisation relève des analyses réalisées et non de l'architecture du logiciel.

La séparation entre les données, leur qualification et leur exploitation garantit la reproductibilité des analyses ainsi que l'évolutivité de l'observatoire.

---

# 2. Principe général

L'ensemble des données disponibles est importé dans l'entrepôt.

Aucune donnée n'est supprimée lors de l'importation.

La sélection des éléments pertinents est réalisée uniquement par la couche de qualification, à partir de règles scientifiques versionnées.

Ainsi, toute évolution des critères de recherche peut être appliquée sans réimporter les données sources.

---

# 3. Qualification des données

Chaque activité, établissement ou dispositif reçoit une ou plusieurs qualifications indépendantes.

Une qualification n'est jamais limitée à une simple notion de périmètre. Elle décrit plusieurs dimensions scientifiques.

Exemples :

- domaine de population concerné ;
- public accueilli ;
- type de dispositif ;
- statut d'activité ;
- appartenance au champ de recherche.

Une même activité peut donc recevoir simultanément plusieurs qualifications.

---

# 4. Domaine de population

Chaque activité appartient à l'une des catégories suivantes.

## ENFANCE

Offre principalement destinée aux enfants et adolescents.

Exemples :

- DITEP
- IME
- IEM
- SESSAD
- CAMSP
- CMPP
- UEMA
- UEEA

---

## ADULTE

Offre destinée aux adultes.

Exemples :

- ESAT
- SAVS
- SAMSAH
- FAM
- MAS

---

## PERSONNES_AGEES

Offre destinée aux personnes âgées.

Exemples :

- EHPAD
- USLD
- Résidences autonomie
- SSIAD personnes âgées

---

## TRANSITION

Structures assurant une continuité entre plusieurs périodes de vie.

Exemples :

- établissements accueillant 6–25 ans ;
- dispositifs passerelles ;
- structures d'insertion.

Cette qualification est essentielle pour étudier les ruptures de parcours.

---

## TOUS_AGES

Structures ou activités intervenant sans restriction significative d'âge.

Exemples :

- équipes mobiles ;
- plateformes territoriales ;
- certains dispositifs de coordination.

---

## HORS_PERIMETRE

Structures présentes dans les sources mais exclues des analyses scientifiques du projet.

Les données restent néanmoins conservées dans l'entrepôt.

---

## INDETERMINE

Qualification
