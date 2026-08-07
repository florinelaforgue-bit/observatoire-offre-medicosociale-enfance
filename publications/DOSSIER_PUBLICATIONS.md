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

- **Niveau de preuve :** Démontré (architecturalement)
- **Maturité technique :** Implémenté
- **Maturité scientifique :** Démonstration en cours

### Description

Séparation explicite entre les producteurs de données et le modèle scientifique via un schéma pivot.

### Artefacts

- `docs/architecture/01_ARCHITECTURE_GLOBALE.md`
- `docs/architecture/03_SCHEMA_PIVOT.md`

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

| Publication | État |
|---|---|
| Article méthodologique décrivant l'infrastructure | Préparation |
| Article de premiers résultats sur l'offre enfance | Dépend de la V1 analytique |
| Articles thématiques | Perspective |

---

# 4. Questions scientifiques rendues possibles

Questions identifiées (sans résultats) :

- Disparités territoriales de l'offre.
- Évolution temporelle.
- Adéquation offre / population.
- Comparaisons inter-régionales.

---

# 5. Résultats déjà démontrés

Résultats techniques documentés :

- Architecture modulaire documentée.
- Schéma pivot documenté.
- Organisation d'une chaîne d'acquisition reproductible.

---

# 6. Résultats restant à démontrer

- Validation sur plusieurs millésimes.
- Validation multi-sources.
- Validation scientifique des indicateurs.

---

# 7. Expériences réalisées

- Documentation de l'architecture.
- Conception et documentation du schéma pivot.
- Structuration du dépôt (code, tests, documentation, publications).

---

# 8. Expériences complémentaires à prévoir

- Reproductibilité indépendante.
- Comparaison avec des publications institutionnelles.
- Tests de montée en charge.

---

# 9. Figures, tableaux et schémas

À produire progressivement :

- Architecture globale.
- Schéma pivot.
- Flux d'acquisition.
- Cycle de reproductibilité.

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

| ID | Contribution | Preuve | Maturité technique | Maturité scientifique | Publication cible |
|---|---|---|---|---|---|
| C-01 | Observatoire reproductible | En cours | Implémenté | Contribution identifiée | Article méthodologique |
| C-02 | Découplage acquisition/modèle | Démontré (architecture) | Implémenté | Démonstration en cours | Data engineering |
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

- **Date / période** : Phase de conception de la V1
- **Statut** : Active
- **Contexte** : Structuration de la stratégie de valorisation scientifique.
- **Décision prise** : Adopter un carnet de valorisation scientifique vivant comme document de référence du projet.
- **Motivation scientifique** : Garantir la traçabilité des contributions, des validations et des choix méthodologiques tout au long du projet.
- **Artefacts justificatifs** : `publications/DOSSIER_PUBLICATIONS.md`
- **Conséquences** : Les futurs artefacts alimenteront ce carnet plutôt que de modifier sa structure.
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

---

## Structure gelée

À compter de cette version, la structure du `DOSSIER_PUBLICATIONS.md` est considérée comme **gelée**.

Les évolutions ultérieures porteront exclusivement sur :

- l'ajout de nouvelles contributions ;
- la mise à jour des niveaux de preuve ;
- l'enrichissement des sections existantes ;
- la mise à jour du tableau de bord, du journal des décisions et de la chronologie.

Aucune nouvelle section ne sera créée sans décision explicite.

