# DOSSIER_PUBLICATIONS.md

> **Carnet de valorisation scientifique vivant**  
> Ce document accompagne le développement de l'observatoire jusqu'aux publications scientifiques. Il est enrichi progressivement. Les sections validées ne sont pas réécrites ; seules des informations nouvelles ou des changements de niveau de preuve sont ajoutés.

---

# Règles de fonctionnement

- Toute affirmation doit être rattachée à un ou plusieurs artefacts.
- Ne jamais inventer de résultat.
- Distinguer systématiquement :
  - **Niveau de preuve** : Démontré / En cours de démonstration / Perspective / Question ouverte.
  - **Maturité technique** : Conçu / Implémenté / Testé / Validé.
  - **Maturité scientifique** : Hypothèse / Contribution identifiée / Démonstration en cours / Démontrée / Publiée.
- Lorsqu'un élément n'est pas suffisamment démontré, le laisser volontairement incomplet.

## Hiérarchie des preuves

Toute affirmation inscrite dans ce carnet doit être classée selon la hiérarchie suivante.

### Artefact démontré

Existence d'un élément objectivement établi par un ou plusieurs artefacts identifiés.

Exemples :
- document d'architecture ;
- contrat d'interface ;
- implémentation ;
- protocole expérimental ;
- rapport de validation.

Un artefact démontre uniquement son existence et son contenu. Il ne constitue pas, à lui seul, une contribution scientifique.

### Propriété démontrée

Propriété objectivement établie par une validation empirique ou une démonstration formelle documentée.

Exemples :
- déterminisme ;
- mémoire bornée ;
- absence de perte ;
- exhaustivité ;
- reproductibilité démontrée.

Une propriété démontrée peut s'appuyer sur plusieurs artefacts.

### Contribution scientifique

Connaissance généralisable soutenue par plusieurs propriétés démontrées.

Une contribution scientifique ne correspond pas à une décision d'implémentation ni à une caractéristique particulière du code. Elle doit être formulée à un niveau d'abstraction permettant d'être réutilisée, discutée ou comparée dans la littérature scientifique.

Une contribution ne peut être considérée comme démontrée que si les trois conditions suivantes sont simultanément satisfaites :

1. elle est explicitement étayée par un ou plusieurs artefacts identifiés ;
2. elle repose sur une validation empirique ou une démonstration formelle documentée ;
3. elle est formulée à un niveau d'abstraction suffisant pour constituer une véritable contribution scientifique ou méthodologique.

## Chaîne de valorisation scientifique

Le carnet suit la chaîne logique de production des connaissances du projet :

**Artefacts → Propriétés démontrées → Contributions scientifiques → Questions scientifiques rendues possibles → Publications**

Chaque niveau dépend du précédent :

- les **artefacts** documentent objectivement le projet ;
- les **propriétés démontrées** sont établies par des validations empiriques ou des démonstrations formelles ;
- les **contributions scientifiques** généralisent plusieurs propriétés démontrées ;
- les **questions scientifiques rendues possibles** découlent des contributions et définissent les nouvelles connaissances que l'observatoire permet d'étudier ;
- les **publications** répondent à ces questions scientifiques.

Ainsi, une publication ne constitue pas la preuve d'une contribution. Elle représente la formalisation scientifique des réponses apportées à des questions rendues accessibles par les contributions développées au cours du projet.

## Gouvernance du carnet

À compter de la stabilisation de cette version, la structure conceptuelle du présent carnet est considérée comme **gelée**.

Les évolutions ultérieures portent exclusivement sur l'enrichissement du contenu scientifique à partir des artefacts produits par le projet.

En particulier, les mises à jour consistent uniquement à :

- ajouter de nouveaux artefacts ;
- documenter de nouvelles propriétés démontrées ;
- réévaluer le niveau de preuve de contributions existantes lorsque de nouvelles validations le justifient ;
- identifier de nouvelles contributions scientifiques ;
- enrichir les questions scientifiques rendues possibles ;
- préparer progressivement les futures publications.

## Principe de conservation des niveaux de preuve

Les niveaux de preuve attribués aux éléments validés du carnet ne sont pas modifiés rétroactivement.

Une propriété, contribution ou question scientifique ne peut voir son niveau de preuve évoluer que sur la base de nouveaux artefacts ou de nouvelles expériences explicitement documentés.

Une nouvelle expérience peut renforcer, confirmer, nuancer ou conduire à réévaluer un élément existant, mais aucune réévaluation ne doit effacer l'état antérieur ni masquer les conditions dans lesquelles le niveau de preuve précédent avait été établi.

Toute modification de la structure ou de la gouvernance du carnet constitue une décision scientifique exceptionnelle et doit être documentée dans le Journal des décisions scientifiques.


---

# 0. Vision scientifique du projet

## Élément V-01

**Statut :** En cours de démonstration

### Constat

Construire un observatoire national reproductible de l'offre médico-sociale française à partir de multiples sources ouvertes afin de disposer d'une infrastructure scientifique permettant des analyses territoriales et temporelles.

### Artefacts

- `docs/00_Vision_du_projet.md`
- `recherche_scientifique/01_Cadre_scientifique_*.md`

### Remarque

La démonstration scientifique de la nécessité de cet observatoire sera étayée par la revue de littérature.

---

> **Important**
>
> Les contributions recensées dans cette section ne correspondent pas à des composants logiciels mais à des connaissances scientifiques ou méthodologiques.
>
> Une architecture, un algorithme ou un contrat d'interface peuvent constituer des artefacts ou démontrer certaines propriétés sans pour autant constituer eux-mêmes une contribution scientifique.
>
> Cette section est volontairement conservatrice. En cas de doute, une contribution reste "en cours de démonstration".

# 1. Contributions scientifiques originales

## C-01 — Observatoire scientifique reproductible

- **Niveau de preuve :** En cours de démonstration
- **Maturité technique :** Implémenté
- **Maturité scientifique :** Contribution identifiée

### Description

Création d'un observatoire fondé sur une infrastructure reproductible plutôt que sur un traitement ponctuel.

### Artefacts

- `docs/00_Vision_du_projet.md`
- `docs/01_Architecture.md`
- `recherche_scientifique/01_Cadre_scientifique_*.md`

### Publication pressentie

- Article méthodologique principal.

---

## C-02 — Découplage acquisition / modèle scientifique

- **Niveau de preuve :** En cours de démonstration
- **Maturité technique :** Validé
- **Maturité scientifique :** Démonstration en cours

### Description

Séparation explicite entre les producteurs de données et le modèle scientifique via un schéma pivot.

### Dossier de preuves

Les propriétés démontrées P-01 à P-09 apportent des éléments supplémentaires au dossier de preuves de cette contribution, sans modifier son statut :

- dérivation du schéma depuis la couche 1 ;
- contrôle des déclarations structurantes ;
- couverture des relations ;
- complémentarité entre contraintes SQL et contrôles post-chargement ;
- exactitude du chargement complet ;
- cohérence avec les contrôles de la couche 1 ;
- bornage de la mémoire ;
- atomicité, idempotence et cohérence du millésime ;
- exécution effective des contrôles déclarés.

Ces propriétés sont établies dans les conditions expérimentales documentées par `BILAN_COUCHE_2.md`, principalement sur le millésime FINESS 202607. Elles renforcent le dossier de preuves sans permettre, à ce stade, de considérer C-02 comme une contribution scientifique démontrée.

### Artefacts

- `docs/architecture/01_ARCHITECTURE_GLOBALE.md`
- `docs/architecture/03_SCHEMA_PIVOT.md`
- `BILAN_COUCHE_2.md`
- `schema.py`
- `entrepot.py`
- `chargement.py`
- `test_schema.py`
- `test_entrepot.py`
- `test_chargement.py`
- `mesurer_chargement.py`
- `mesurer_entrepot.py`
- `mesurer_integrite_sql.py`
---

# 2. Contributions méthodologiques

## M-01 — Schéma pivot indépendant des sources

- **Niveau de preuve :** Démontré
- **Maturité technique :** Implémenté
- **Maturité scientifique :** Démonstration en cours

### Artefacts

- `docs/architecture/03_SCHEMA_PIVOT.md`

---

## M-02 — Architecture modulaire

- **Niveau de preuve :** Démontré
- **Maturité technique :** Implémenté
- **Maturité scientifique :** Contribution identifiée

### Artefacts

- `docs/01_Architecture.md`
- `docs/03_Architecture_cible.md`
- Arborescence GitHub (organisation des modules `src/`, `tests/`, `docs/`)

---

# 3. Stratégie de publication

> La stratégie de publication est construite à partir des questions scientifiques rendues possibles par les contributions démontrées ou en cours de démonstration.
>
> Les publications ne constituent pas une finalité indépendante du projet : elles représentent la formalisation des connaissances produites en réponse à des questions scientifiques devenues accessibles grâce à l'infrastructure développée.

| Publication | État |
|---|---|
| Article méthodologique décrivant l'infrastructure | Préparation |
| Article de premiers résultats sur l'offre enfance | Dépend de la V1 analytique |
| Articles thématiques | Perspective |

---

# 4. Questions scientifiques rendues possibles

> Cette section occupe une position centrale dans la stratégie de valorisation.
>
> Les questions recensées ici ne sont ni des résultats ni des hypothèses de publication. Elles représentent les questions scientifiques qui deviennent investigables grâce aux contributions méthodologiques et scientifiques développées par le projet.
>
> Une même contribution peut rendre possibles plusieurs questions scientifiques, et une même question peut conduire à plusieurs publications.

Questions identifiées (sans résultats) :

- Disparités territoriales de l'offre.
- Évolution temporelle.
- Adéquation offre / population.
- Comparaisons inter-régionales.

---

# 5. Résultats déjà démontrés

## Propriétés démontrées — couche 2

Les propriétés suivantes sont **démontrées** dans les conditions expérimentales documentées par `BILAN_COUCHE_2.md`. Elles ne constituent pas, à elles seules, des contributions scientifiques démontrées.

### P-01 — Dérivation du schéma depuis la couche 1

- **Niveau de preuve :** Propriété démontrée
- **Conditions expérimentales :** Millésime FINESS 202607 ; schéma construit à partir des types d'enregistrements de la couche 1 ; test d'égalité des colonnes.
- **Artefacts :**
  - `schema.py`
  - `schema.sql`
  - `DECISIONS_SCHEMA.md`
  - `test_schema.py`
  - `BILAN_COUCHE_2.md`
- **Limites :** propriété démontrée sur le périmètre et le millésime de référence ; la stabilité sur plusieurs millésimes reste à établir.

### P-02 — Aucune déclaration injustifiée

- **Niveau de preuve :** Propriété démontrée
- **Conditions expérimentales :** sept garde-fous testés sur des déclarations fautives fabriquées.
- **Artefacts :**
  - `schema.py`
  - `test_schema.py`
  - `DECISIONS_SCHEMA.md`
  - `BILAN_COUCHE_2.md`
- **Limites :** démonstration portant sur les catégories de fautes couvertes par les tests de la couche 2.

### P-03 — Une clé étrangère ne peut viser une colonne non unique

- **Niveau de preuve :** Propriété démontrée
- **Conditions expérimentales :** contrôle à la construction du schéma et test d'une déclaration fautive visant une colonne non unique.
- **Artefacts :**
  - `schema.py`
  - `test_schema.py`
  - `DECISIONS_SCHEMA.md`
  - `BILAN_COUCHE_2.md`
- **Limites :** propriété démontrée dans le mécanisme de validation du schéma de la couche 2.

### P-04 — Couverture explicite des 13 relations de la couche 1

- **Niveau de preuve :** Propriété démontrée
- **Conditions expérimentales :** couverture vérifiée à la construction ; retrait d'une clé étrangère provoquant l'échec du module.
- **Artefacts :**
  - `schema.py`
  - `test_schema.py`
  - `DECISIONS_SCHEMA.md`
  - `BILAN_COUCHE_2.md`
- **Limites :** périmètre correspondant aux 13 relations déclarées pour le millésime et le contrat de référence.

### P-05 — Chargement complet et exact

- **Niveau de preuve :** Propriété démontrée
- **Conditions expérimentales :** chargement du millésime FINESS 202607 ; 5 242 334 lignes ; volumétrie conforme à la référence ; vérifications exécutées après chargement.
- **Artefacts :**
  - `chargement.py`
  - `entrepot.py`
  - `test_chargement.py`
  - `mesurer_chargement.py`
  - `BILAN_COUCHE_2.md`
- **Limites :** démonstration sur le jeu de référence 202607 ; aucune généralisation à d'autres millésimes sans réplication.

### P-06 — Absence de références orphelines et complémentarité SQL / contrôles post-chargement

- **Niveau de preuve :** Propriété démontrée
- **Conditions expérimentales :** `foreign_key_check` et les cinq contrôles déclarés à zéro sur la base complète ; équivalence avec les contrôles Python de la couche 1 sur données intactes et sur une référence volontairement cassée ; un rattachement polymorphe orphelin, invisible pour `foreign_key_check`, est détecté par le contrôle déclaré.
- **Artefacts :**
  - `schema.py`
  - `chargement.py`
  - `test_chargement.py`
  - `mesurer_integrite_sql.py`
  - `BILAN_COUCHE_2.md`
- **Limites :** validation effectuée sur les relations et scénarios couverts par le rapport, avec le millésime 202607.

### P-07 — Mémoire bornée au chargement

- **Niveau de preuve :** Propriété démontrée
- **Conditions expérimentales :** mesure par taille de lot dans des processus distincts ; pire cas mesuré à 100,1 Mio de mémoire pour le chargement ; campagne réalisée sur la machine de développement.
- **Artefacts :**
  - `chargement.py`
  - `mesurer_chargement.py`
  - `BILAN_COUCHE_2.md`
- **Limites :** aucune mesure sur Termux ; la propriété est donc établie dans les conditions expérimentales documentées et ne doit pas être extrapolée à un environnement matériel différent.

### P-08 — Atomicité, idempotence et cohérence du millésime

- **Niveau de preuve :** Propriété démontrée
- **Conditions expérimentales :** tests de panne en cours de flux, rechargement du même fichier, remplacement sans duplication et refus d'un second millésime avant écriture.
- **Artefacts :**
  - `chargement.py`
  - `test_chargement.py`
  - `BILAN_COUCHE_2.md`
- **Limites :** démonstration sur les scénarios de test documentés et sur le modèle mono-millésime de la couche 2.

### P-09 — Exécution effective des contrôles déclarés par le chemin nominal

- **Niveau de preuve :** Propriété démontrée
- **Conditions expérimentales :** `charger()` exécute les contrôles déclarés ; un orphelin fabriqué provoque l'échec de l'ingestion.
- **Artefacts :**
  - `chargement.py`
  - `test_chargement.py`
  - `mesurer_integrite_sql.py`
  - `BILAN_COUCHE_2.md`
- **Limites :** démonstration sur les contrôles déclarés et les anomalies fabriquées couvertes par les tests.

### Synthèse de niveau de preuve

Les propriétés P-01 à P-09 constituent des **propriétés démontrées**, et non des contributions scientifiques démontrées.

Aucune de ces propriétés n'est convertie en contribution scientifique générale. Leur éventuelle généralisation devra être établie par des expériences complémentaires.

---

# 6. Résultats restant à démontrer

- Validation sur plusieurs millésimes.
- Validation multi-sources.
- Validation scientifique des indicateurs.
- Détermination de la robustesse des propriétés P-01 à P-09 au-delà du millésime FINESS 202607.
- Détermination de la reproductibilité des performances et du comportement mémoire sur l'environnement cible, notamment Termux.


---

# 7. Expériences réalisées

- Documentation de l'architecture.
- Conception et documentation du schéma pivot.
- Structuration du dépôt (code, tests, documentation, publications).
- Validation des propriétés P-01 à P-09 de la couche 2 selon `BILAN_COUCHE_2.md`.
- Mesures de chargement, d'intégrité et de comportement de l'entrepôt sur le millésime FINESS 202607.
- Tests d'atomicité, d'idempotence et de cohérence du millésime.
- Tests de détection d'une anomalie fabriquée sur une relation polymorphe.

---

# 8. Expériences complémentaires à prévoir

- Reproductibilité indépendante.
- Comparaison avec des publications institutionnelles.
- Tests de montée en charge.
- Réplication sur plusieurs millésimes, afin de distinguer les propriétés propres au millésime FINESS 202607 des propriétés réellement robustes de l'infrastructure.
- Réplication des mesures de performance et de mémoire sur l'environnement cible, notamment Termux.
- Validation multi-sources.
- Validation scientifique des indicateurs.

La réplication sur plusieurs millésimes constitue une piste expérimentale prioritaire pour qualifier la robustesse temporelle des propriétés actuellement démontrées sur 202607.

---

# 9. Figures, tableaux et schémas

À produire progressivement :

- Architecture globale.
- Schéma pivot.
- Flux d'acquisition.
- Cycle de reproductibilité.
- Chaîne **artefacts → propriétés démontrées → contributions → questions scientifiques → publications**.
- Tableau de synthèse des propriétés démontrées P-01 à P-09 et de leurs conditions expérimentales.
  
---

# 10. Revues scientifiques potentielles

À confirmer après revue bibliographique :

- Journal of Biomedical Informatics
- International Journal of Medical Informatics
- Health & Place
- BMC Health Services Research

---

# 11. Références bibliographiques à rechercher

Thèmes :

- Observatoires nationaux.
- FAIR data.
- Reproductibilité.
- Géographie de la santé.
- ETL scientifique.

---

# 12. Collaborations potentielles

Section volontairement incomplète.

---

# 13. Financements potentiels

Section volontairement incomplète.

---

# 14. Tableau de bord scientifique

Le tableau de bord suit uniquement les contributions scientifiques et méthodologiques.

Les artefacts démontrés et les propriétés démontrées servent de preuves mais ne sont pas assimilés à des contributions.

Le passage d'une contribution au statut **« démontrée »** nécessite obligatoirement :

- des artefacts identifiés ;
- une validation empirique ou une démonstration formelle documentée ;
- une formulation généralisable indépendante des choix d'implémentation.

### Lecture du tableau de bord

Le tableau de bord suit la progression scientifique du projet selon la chaîne de valorisation :

Artefacts → Propriétés démontrées → Contributions → Questions scientifiques → Publications

Le tableau ne suit donc pas uniquement l'état des contributions, mais leur capacité progressive à produire de nouvelles connaissances scientifiques.

| ID | Contribution | Preuve | Maturité technique | Maturité scientifique | Publication cible |
|---|---|---|---|---|---|
| C-01 | Observatoire reproductible | En cours | Implémenté | Contribution identifiée | Article méthodologique |
| C-02 | Découplage acquisition/modèle | En cours de démonstration, dossier de preuves renforcé par P-01 à P-09 | Validé | Démonstration en cours | Data engineering |
| M-01 | Schéma pivot | Démontré | Implémenté | Démonstration en cours | Méthodologie |
| M-02 | Architecture modulaire | Démontré | Implémenté | Contribution identifiée | Méthodologie |
  
---

# 15. Journal des décisions scientifiques

Cette section constitue le registre des décisions structurantes du projet. Les décisions ne sont jamais supprimées : si elles évoluent, leur historique est conservé.

## Format des entrées

- **Identifiant** : D-XXX
- **Date / période**
- **Statut** : Active / Confirmée / Remplacée / Abandonnée
- **Contexte**
- **Décision prise**
- **Motivation scientifique**
- **Artefacts justificatifs**
- **Conséquences sur le projet**
- **Impact sur les publications potentielles**
- **Évolution du niveau de preuve**
- **Remarques**

### D-001

- **Date / période** : 07/08/2026 / Phase de conception de la V1
- **Statut** : Active
- **Contexte** : Structuration de la stratégie de valorisation scientifique.
- **Décision prise** : Adopter un carnet de valorisation scientifique vivant comme document de référence du projet.
- **Motivation scientifique** : Garantir la traçabilité des contributions, des validations et des choix méthodologiques tout au long du projet.
- **Artefacts justificatifs** : `publications/DOSSIER_PUBLICATIONS.md`
- **Conséquences** : Les futurs artefacts alimenteront ce carnet plutôt que de modifier sa structure.
- **Évolution du niveau de preuve** : Décision de gouvernance scientifique.

### D-002

- **Date / période** : 07/08/2026 / Phase de conception du carnet de valorisation scientifique
- **Statut** : Active
- **Contexte** : Les premières versions du carnet montraient un risque de confusion entre architecture logicielle, propriétés démontrées et véritables contributions scientifiques.
- **Décision prise** : Adopter une hiérarchie explicite des preuves distinguant les artefacts, les propriétés démontrées et les contributions scientifiques.
- **Motivation scientifique** : Garantir un niveau élevé de rigueur documentaire et éviter toute surestimation de la portée scientifique du projet.
- **Conséquences sur le projet** : Toute nouvelle contribution devra être évaluée selon cette hiérarchie et pourra être réévaluée à mesure que de nouvelles validations seront produites.
- **Évolution du niveau de preuve** : Décision de gouvernance scientifique.

### D-003

- **Date / période** : 07/08/2026 / Stabilisation de la gouvernance scientifique du carnet
- **Statut** : Active
- **Contexte** : Clarification de la relation entre contributions scientifiques et publications.
- **Décision prise** : Adopter une chaîne de valorisation distinguant explicitement les artefacts, les propriétés démontrées, les contributions scientifiques, les questions scientifiques rendues possibles et les publications.
- **Motivation scientifique** : Aligner la structure du carnet sur la logique de production des connaissances en recherche et éviter d'assimiler les publications aux contributions elles-mêmes.
- **Conséquences sur le projet** : Les futures publications seront systématiquement rattachées aux questions scientifiques auxquelles elles répondent, elles-mêmes reliées aux contributions qui les rendent possibles.
- **Évolution du niveau de preuve** : Décision de gouvernance scientifique.

### D-004

- **Date / période** : 07/08/2026 / Stabilisation de la gouvernance du carnet
- **Statut** : Active
- **Contexte** : Après plusieurs itérations, la structure conceptuelle du carnet est jugée suffisamment mature pour accompagner l'ensemble du projet.
- **Décision prise** : Geler définitivement la gouvernance et l'architecture conceptuelle du DOSSIER_PUBLICATIONS.md.
- **Motivation scientifique** : Garantir la stabilité de la traçabilité scientifique sur toute la durée du projet et éviter que les évolutions du carnet ne modifient a posteriori les critères d'évaluation des contributions.
- **Artefacts justificatifs** : DOSSIER_PUBLICATIONS.md
- **Conséquences sur le projet** : Les évolutions futures concerneront exclusivement l'enrichissement des sections existantes à partir des nouveaux artefacts.
- **Évolution du niveau de preuve** : Décision de gouvernance scientifique.

---

# 16. Chronologie du projet

Chronologie synthétique de la genèse et de l'évolution scientifique du projet.

## Format des jalons

- **Date / période**
- **Événement**
- **Nature** : Clinique / Scientifique / Méthodologique / Technique / Validation / Publication / Collaboration
- **Artefacts associés**
- **Conséquences scientifiques**

## Jalons connus

### J-001

- **Événement** : Émergence d'une problématique autour de l'observation de l'offre médico-sociale.
- **Nature** : Scientifique
- **Artefacts** : `docs/00_Vision_du_projet.md`, `recherche_scientifique/01_Cadre_scientifique_*.md`
- **Niveau de preuve** : En cours de démonstration.

### J-002

- **Événement** : Élargissement du projet vers un observatoire national couvrant l'ensemble du champ médico-social, avec une première application scientifique sur l'enfance.
- **Nature** : Scientifique / Méthodologique
- **Artefacts** : Documentation de vision, architecture et feuille de route.
- **Niveau de preuve** : Démontré par les artefacts documentaires.

### J-003

- **Événement** : Adoption d'une hiérarchie formelle des preuves scientifiques pour le carnet de valorisation.
- **Nature** : Gouvernance scientifique
- **Artefacts associés** : DOSSIER_PUBLICATIONS.md
- **Conséquences scientifiques** : Le carnet devient un registre de preuves où les contributions ne peuvent être qualifiées de démontrées qu'après validation documentaire, empirique et scientifique.

### J-004

- **Événement** : Gel définitif de la gouvernance et de l'architecture conceptuelle du carnet de valorisation scientifique.
- **Nature** : Gouvernance scientifique
- **Artefacts associés** : DOSSIER_PUBLICATIONS.md
- **Conséquences scientifiques** : Le carnet devient le registre scientifique de référence du projet. Toute évolution ultérieure concerne exclusivement son enrichissement documentaire.

---

## Structure gelée

À compter de cette version, la structure du `DOSSIER_PUBLICATIONS.md` est considérée comme **gelée**.

Les évolutions ultérieures porteront exclusivement sur :

- l'ajout de nouvelles contributions ;
- la mise à jour des niveaux de preuve ;
- l'enrichissement des sections existantes ;
- la mise à jour du tableau de bord, du journal des décisions et de la chronologie.

Aucune nouvelle section ne sera créée sans décision explicite.

