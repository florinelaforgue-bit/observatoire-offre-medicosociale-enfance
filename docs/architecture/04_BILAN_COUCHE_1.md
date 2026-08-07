# BILAN_COUCHE_1.md

**Gel de la couche 1 — acquisition. Étape E7.**

| | |
|---|---|
| Périmètre gelé | `flux_json`, `contrat_source`, `controles`, `sources/finess_commun`, `sources/finess_structures`, `sources/finess_activites`, `inventaire_codes`, `cli` |
| Contrat de données | SCHEMA_PIVOT.md version 1.3 |
| Millésime de référence | FINESS 202607, `schemaVersion` `v1.0.0` |
| Tests | 204, sept suites, aucun échec |
| Dépendances tierces | aucune |
| Version de Python | 3.9 et suivantes |

---

## 1. Empreintes de gel

Toute modification d'un de ces fichiers invalide le gel et impose de rejouer
l'intégralité des suites ainsi que les deux preuves d'absence de perte.

| Fichier | SHA-256 (24 premiers caractères) |
|---|---|
| `flux_json.py` | `713444ea7de73683ac3b67b1…` |
| `contrat_source.py` | `0cf16a6e664908c276a1829d…` |
| `controles.py` | `678ad17abb437101a75940bc…` |
| `finess_commun.py` | `b24961b3d8979f713d51efbb…` |
| `finess_structures.py` | `11539368a38b9c19427a4a51…` |
| `finess_activites.py` | `5a2a3560df88e89100700c7e…` |
| `inventaire_codes.py` | `fa1b0c4cf4b390114eae11e4…` |
| `cli.py` | `f776350a8955713e8cb29dd2…` |
| `SCHEMA_PIVOT.md` | `622c7db8b482fd73d7fc7f2d…` |
| `inventaire_codes_202607.csv` | `703bb350ce2fe96da29b694a…` |
| `echantillon/…structures…json.gz` | `9645bd12ef5257e80f510315…` |
| `echantillon/…activites…json.gz` | `e8df4c07c840759a720ac31e…` |

3 309 lignes de code de production, 1 967 lignes de tests et de preuves.

---

## 2. Métriques de référence — millésime 202607

Mesurées sur machine de développement. **Aucune mesure n'a été faite sur
Termux** : compter un facteur 3 à 8 sur les durées, la mémoire étant inchangée.

| Commande | Durée | RSS max | Lignes |
|---|---|---|---|
| `inspecter structures --controle strict` | 15,6 s | 62,9 Mio | 1 530 465 |
| `inspecter activites --controle strict` | 30,1 s | 100,3 Mio | 3 711 869 |
| `inventaire` | 54,9 s | 108,7 Mio | 5 242 334 |
| `integrite` | 49,8 s | 102,1 Mio | 6 772 799 sur trois passes |

Volumétrie du pivot, à figer comme test de non-régression : les seize types
d'enregistrements totalisent **5 242 334 lignes**, dont 1 961 124 évènements,
1 231 970 communes de zone d'intervention, 585 746 activités, 537 233 capacités,
278 615 adresses, 222 505 contacts, 174 508 établissements et 98 168 entités
juridiques. Le détail figure au § 7 de SCHEMA_PIVOT.md.

Registre des codes : **41 domaines alimentés sur 41 déclarés, 7 053 couples
(domaine, code)**, quatre constats de structure acquittés.

Intégrité : **13 relations, 3 687 802 rattachements vérifiés, zéro orphelin**,
pour 4,27 Mio d'index.

---

## 3. Échantillon réduit versionné

Deux fichiers, 0,91 Mio au total, dans `echantillon/`. Ce sont des
**sous-ensembles stricts** des fichiers réels : aucune valeur n'est modifiée,
seuls des enregistrements racines entiers sont retenus ou écartés. Le script
`construire_echantillon.py` les régénère à l'identique depuis les fichiers
complets.

L'échantillon est **référentiellement clos** : la fermeture transitive des
identifiants référencés a porté 11 graines et les 9 membres d'un GCC à
30 entités juridiques, en 4 tours. La chaîne complète y passe en contrôle
strict, sans anomalie et sans orphelin.

| Cas limite couvert | Entité |
|---|---|
| Pire cas mémoire : 1 062 établissements, 9,86 Mio en un enregistrement | EJ 750721334 |
| DITEP, engagement `DISP`/`DIT` | ET 010784262 |
| Établissement à 150 adresses | ET 440040624 |
| Numéros FINESS corses `2A`/`2B` | EJ 060020443 |
| Séquences d'échappement dans une dénomination | EJ 970302477 |
| Entité juridique sans aucun établissement | EJ 010000016 |
| Établissement actif sans aucune activité | ET 010002285 |
| Activité de nature EML | ET 060000528 |
| Capacités de statuts 08 et 09 sur une même activité | ET 010780195 |
| Zone d'intervention avec communes | EJ 010000339 |
| Relation entre établissements croisée | ET 010780575 |
| Groupements GCC avec membres, et GCO sans membre | 1 GCC, 3 GCO |

Malgré ses 0,91 Mio, l'échantillon **conserve le profil mémoire du pire cas** :
93,9 Mio de RSS, contre 102,1 sur les fichiers complets. Il est donc utilisable
comme test de charge, et pas seulement comme test fonctionnel.

---

## 4. Couverture de tests

| Suite | Tests | Objet |
|---|---|---|
| `test_flux_json.py` | 15 | Lecture incrémentale, JSON minifié, gzip, blocs de 7 caractères, échappements, cinq formes de document invalide |
| `test_contrat_source.py` | 45 | Déclaration du schéma, contrôle des lignes, registre borné, inventaire borné, dix violations du contrat |
| `test_finess_structures.py` | 34 | Onze types d'enregistrements, rattachements, sept dérives de schéma |
| `test_finess_activites.py` | 40 | Les huit natures une par une, fentes uniques, neuf dérives de schéma |
| `test_inventaire_codes.py` | 25 | Complétude, couverture, unicité, saturation, constats acquittés ou non |
| `test_controles.py` | 28 | Exactitude de l'index, garde-fous, relations locales et différées, substituabilité |
| `test_cli.py` | 17 | Les quatre commandes de bout en bout, codes de retour, orphelins fabriqués |

Deux preuves complémentaires, exécutables sur les fichiers réels :
`preuve_exhaustivite.py` (double recensement des clés JSON) et
`preuve_valeurs_structures.py` / `preuve_valeurs_activites.py` (confrontation
des colonnes du pivot au recensement).

Principe suivi partout : **un contrôle qui ne se déclenche jamais ne prouve
rien**. Chaque contrôle bloquant est éprouvé sur un défaut fabriqué.

---

## 5. Garanties démontrées

| Garantie | Preuve |
|---|---|
| **Exhaustivité du parcours** | Deux recensements indépendants des clés JSON — par le lecteur, et par balayage textuel sans parseur — coïncident clé par clé : 20 737 253 et 38 098 626 occurrences, 107 et 112 clés distinctes, zéro écart |
| **Absence de perte de valeurs** | 90 colonnes du pivot confrontées au recensement exhaustif du JSON, écart nul. Les neuf colonnes entièrement nulles sont justifiées une à une |
| **Aucune clé non déclarée** | Jeu de clés contrôlé objet par objet, par nature pour les activités. Toute clé nouvelle ou disparue est bloquante |
| **Conformité de format** | Contrôle strict sur les deux fichiers complets : zéro anomalie sur 5 242 334 lignes |
| **Intégrité des rattachements** | 13 relations, 3 687 802 liens vérifiés, zéro orphelin |
| **Mémoire bornée** | Plafond mesuré à 108,7 Mio, indépendant du volume : vérifié en doublant le nombre de lignes à mémoire constante |
| **Déterminisme** | Identifiant de lot déterministe, séquence de lignes identique d'une exécution à l'autre |
| **Aucun échec silencieux** | Zéro donnée, en-tête absente, type hors contrat, objet ignoré : tous bloquants, avec code de retour non nul |

---

## 6. Contrats d'interface, et ce qui n'en fait pas partie

**Index d'identifiants.** L'architecture impose **l'existence d'un index exact
d'identifiants**, et rien d'autre. Le contrat se réduit à `ajouter(valeur)`,
`figer()`, `valeur in index` et `len(index)`, avec trois garanties :
exactitude — ni faux positif ni faux négatif, aucune structure probabiliste —,
faible empreinte mémoire, et absence de perte quelle que soit la forme de
l'identifiant.

L'encodage entier des chaînes numériques par préfixage d'un « 1 » est une
**optimisation interne de `IndexIdentifiants`, pas une règle du projet**. Toute
implémentation offrant les trois garanties doit pouvoir la remplacer **sans
modifier aucun autre module** : `VerificateurRelations` reçoit pour cela une
fabrique d'index en paramètre. La substituabilité n'est pas seulement
documentée, elle est éprouvée : `test_controles.py` injecte une implémentation
naïve fondée sur un ensemble de chaînes et vérifie que le comportement
observable est strictement identique. Seul l'algorithme peut évoluer ;
l'interface est stable.

**Contrat des sources.** Tout connecteur — INSEE, CNSA, ROR, IGN,
OpenStreetMap — implémente `Source` : identité, millésime, types
d'enregistrements déclarés, production en un seul passage. Le pilote
`parcourir_source` se charge du reste. Aucun autre module ne change lors de
l'ajout d'une source.

**Contrat de données.** Les couches supérieures ne connaissent que les noms
déclarés dans SCHEMA_PIVOT.md. Le jour où FINESS renomme un champ, seule la
couche 1 change.

---

## 7. Limites connues avant le passage à la couche 2

**Aucune mesure sur Termux.** Toutes les durées de ce document proviennent
d'une machine de développement. C'est la vérification la plus urgente à mener.

**Plancher mémoire à environ 100 Mio.** Il tient au plus gros enregistrement du
fichier activités — 9,86 Mio de texte, 19 Mio une fois décodé — et au
doublement du tampon dans `flux_json`, qui le porte à 16-18 Mio. L'optimisation
est consignée dans l'en-tête du module, reportée par décision explicite.

**Le contrôle approfondi n'est échantillonné en usage courant.** La nullité des
champs obligatoires est vérifiée sur toutes les lignes, mais la nature
textuelle des valeurs et le format des dates seulement sur les lignes
échantillonnées. La garantie repose sur la discipline retenue : validation en
mode strict sur le fichier complet avant tout gel de connecteur.

**Aucun libellé n'existe.** Les seuls champs textuels du jeu de données sont
`libelleVoie` et `libelleZI`. La couche 3 doit constituer **41 nomenclatures**
depuis une source externe, dont 4 760 valeurs pour `type_activite_smsse` et 622
pour `activite_regulee`. Tant qu'elles manquent, aucune analyse par catégorie,
discipline ou public n'est possible.

**Quatre constats de structure acquittés**, détaillés au § 6 de
SCHEMA_PIVOT.md : `code_etat_objet_1` recopie `code_evenement` à 96,4 %,
vocabulaires d'évènements disjoints entre les deux fichiers, et 63 des 191
codes `type_voie` ne sont que des variantes d'écriture. Retirer une entrée de
`CONSTATS_ACQUITTES` fait de nouveau échouer l'inventaire.

**Champs sans pouvoir discriminant** : `role_contact`, `habilitation` et
`type_personne_morale` n'ont qu'une seule valeur distincte. Le courriel est
renseigné 104 fois sur 222 505 contacts. Les bornes d'âge ne couvrent que 11 %
des activités sociales et médico-sociales.

**Un numéro FINESS n'est jamais un entier** : 898 numéros d'établissement et
460 d'entité juridique commencent par `2A` ou `2B`. Tout stockage, toute clé,
tout index doit le traiter comme une chaîne — y compris en couche 2.

**Forme inconnue des membres établissements de groupement.** `egeDuGco` et
`egeDuGcc` sont vides sur la totalité de 202607. Un millésime qui les
renseignerait ferait échouer l'ingestion de façon bloquante, le temps de réviser
le contrat. C'est délibéré.

**Le millésime est lu dans le nom du fichier**, pas dans le document :
`generatedAt` est une date de génération, pas une date d'arrêté des données.
Renommer un fichier fausse donc le millésime du lot.

**Un seul millésime a été observé.** Aucune vérification n'a pu porter sur la
stabilité du schéma d'un mois sur l'autre.

**Les contrôles d'intégrité coûtent trois passes**, soit environ 50 s. Ils ont
vocation à migrer vers SQL en couche 2, où ils seront quasi gratuits.

---

## 8. Ce que la couche 2 hérite

Un flux de couples (nom de type, tuple de valeurs), dans l'ordre figé des
colonnes déclarées, prêts à être insérés sans aucune recherche préalable.
Chaque ligne porte son `id_lot`, déterministe. Aucune valeur n'est convertie :
tout est textuel, verbatim, y compris les champs numériques par nature, dont la
conversion appartient à l'entrepôt.

Le budget mémoire de 100 Mio est une contrainte d'architecture héritée : la
couche 2 doit écrire par lots et ne rien accumuler.
