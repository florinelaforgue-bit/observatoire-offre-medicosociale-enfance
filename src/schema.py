"""
schema.py — Couche 2 (entrepôt), étape F1.

Définition déclarative du schéma SQLite, dérivée des types d'enregistrements
de la couche 1. Les colonnes ne sont pas recopiées : elles proviennent de
`finess_commun.TOUS_LES_TYPES`. Le jour où le contrat de la couche 1 change,
le schéma suit sans intervention.

PRINCIPE DIRECTEUR — aucune déclaration sans justification
-----------------------------------------------------------

Aucun type, aucune clé, aucune contrainte ne peut être déclaré par intuition.
Toute déclaration porte une justification de l'une des trois natures suivantes,
faute de quoi la construction du schéma échoue :

    ARTEFACT   un fait mesuré sur les fichiers FINESS, avec sa valeur
    MESURE     une mesure expérimentale, avec son chiffre
    BESOIN     un besoin fonctionnel documenté, avec sa provenance

C'est la transposition à la couche 2 de ce qui a tenu la couche 1 : une règle
qu'aucun code ne vérifie s'érode. Le registre `DECISIONS_SCHEMA.md` est
engendré depuis ces déclarations, jamais rédigé à la main.

PRINCIPE DIRECTEUR — fidélité aux données
------------------------------------------

La couche 2 stocke verbatim. Elle ne normalise pas les espaces de bordure, ne
convertit pas les dates sentinelles en nul, ne déduplique pas, n'invente aucun
lien absent des données. Lorsqu'une limitation vient de la source ou du modèle
conceptuel qu'elle exprime, la couche 2 la documente et la contrôle plutôt que
de la contourner par une déformation des données.

Conséquence directe : trois relations ne sont pas exprimables en SQL et sont
déclarées comme contrôles après chargement, non comme clés étrangères.

Aucune dépendance tierce. Compatible Python 3.9+.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import finess_commun as fc
from contrat_source import TypeEnregistrement

__all__ = [
    "ARTEFACT", "MESURE", "BESOIN", "Justification",
    "CLE_PRIMAIRE", "UNICITE", "CLE_ETRANGERE",
    "Contrainte", "ControlePostChargement", "Table", "Schema",
    "SCHEMA", "ErreurSchema",
]

# --- natures de justification ----------------------------------------------
ARTEFACT = "artefact"
MESURE = "mesure"
BESOIN = "besoin"
NATURES = frozenset({ARTEFACT, MESURE, BESOIN})

# --- genres de contrainte ---------------------------------------------------
CLE_PRIMAIRE = "clé primaire"
UNICITE = "unicité"
CLE_ETRANGERE = "clé étrangère"
GENRES = frozenset({CLE_PRIMAIRE, UNICITE, CLE_ETRANGERE})

# --- types SQL --------------------------------------------------------------
TEXTE_SQL = "TEXT"


class ErreurSchema(Exception):
    """Déclaration incomplète, injustifiée ou incohérente."""


class Justification:
    """Le motif d'une déclaration, et l'endroit où il est vérifiable."""

    __slots__ = ("nature", "texte", "source")

    def __init__(self, nature: str, texte: str, source: str) -> None:
        if nature not in NATURES:
            raise ErreurSchema(f"Nature de justification inconnue : {nature!r}")
        if not texte.strip():
            raise ErreurSchema("Justification vide")
        if not source.strip():
            raise ErreurSchema(f"Justification sans source vérifiable : {texte[:60]!r}")
        self.nature = nature
        self.texte = texte.strip()
        self.source = source.strip()

    def __str__(self) -> str:
        return f"[{self.nature}] {self.texte} ({self.source})"


class Contrainte:
    __slots__ = ("genre", "colonnes", "table_cible", "colonnes_cibles", "justification")

    def __init__(self, genre: str, colonnes: Sequence[str],
                 justification: Justification,
                 table_cible: Optional[str] = None,
                 colonnes_cibles: Optional[Sequence[str]] = None) -> None:
        if genre not in GENRES:
            raise ErreurSchema(f"Genre de contrainte inconnu : {genre!r}")
        if not colonnes:
            raise ErreurSchema(f"Contrainte {genre} sans colonne")
        if genre == CLE_ETRANGERE and not (table_cible and colonnes_cibles):
            raise ErreurSchema("Clé étrangère sans cible")
        self.genre = genre
        self.colonnes = tuple(colonnes)
        self.table_cible = table_cible
        self.colonnes_cibles = tuple(colonnes_cibles) if colonnes_cibles else ()
        self.justification = justification


class ControlePostChargement:
    """Une propriété que SQL ne peut pas déclarer, et qui est donc vérifiée
    par une requête après chargement.

    `motif` explique **pourquoi** la contrainte n'est pas déclarable. Ce champ
    est obligatoire : sans lui, rien ne distingue un contrôle légitime d'une
    contrainte oubliée.
    """

    __slots__ = ("nom", "description", "requete", "motif", "justification")

    def __init__(self, nom: str, description: str, requete: str, motif: str,
                 justification: Justification) -> None:
        if not motif.strip():
            raise ErreurSchema(f"Contrôle {nom!r} sans motif de non-déclarabilité")
        self.nom = nom
        self.description = description.strip()
        self.requete = requete.strip()
        self.motif = motif.strip()
        self.justification = justification


class Table:
    """Une table du schéma, dont les colonnes viennent de la couche 1."""

    __slots__ = ("type_enregistrement", "contraintes", "controles",
                 "absence_cle_primaire", "commentaire")

    def __init__(self, type_enregistrement: TypeEnregistrement,
                 contraintes: Iterable[Contrainte] = (),
                 controles: Iterable[ControlePostChargement] = (),
                 absence_cle_primaire: Optional[Justification] = None,
                 commentaire: str = "") -> None:
        self.type_enregistrement = type_enregistrement
        self.contraintes = tuple(contraintes)
        self.controles = tuple(controles)
        self.absence_cle_primaire = absence_cle_primaire
        self.commentaire = commentaire.strip()

    @property
    def nom(self) -> str:
        return self.type_enregistrement.nom

    @property
    def colonnes(self) -> Tuple[str, ...]:
        return self.type_enregistrement.noms

    def cle_primaire(self) -> Optional[Contrainte]:
        for contrainte in self.contraintes:
            if contrainte.genre == CLE_PRIMAIRE:
                return contrainte
        return None

    def colonnes_uniques(self) -> List[Tuple[str, ...]]:
        cles = [c.colonnes for c in self.contraintes
                if c.genre in (CLE_PRIMAIRE, UNICITE)]
        return cles

    def non_nulles(self) -> Tuple[str, ...]:
        return tuple(c.nom for c in self.type_enregistrement.champs if c.obligatoire)


class Schema:
    """L'ensemble des tables, validé à la construction."""

    def __init__(self, tables: Iterable[Table],
                 regle_type_defaut: Justification,
                 justification_non_nul: Justification,
                 justification_absence_index: Justification) -> None:
        self.tables = tuple(tables)
        self.regle_type_defaut = regle_type_defaut
        self.justification_non_nul = justification_non_nul
        self.justification_absence_index = justification_absence_index
        self._par_nom = {t.nom: t for t in self.tables}
        self._valider()

    # -- validation ---------------------------------------------------------

    def _valider(self) -> None:
        types_couche_1 = {t.nom for t in fc.TOUS_LES_TYPES}
        declarees = {t.nom for t in self.tables}
        if declarees != types_couche_1:
            manquantes = sorted(types_couche_1 - declarees)
            surnumeraires = sorted(declarees - types_couche_1)
            raise ErreurSchema(
                f"Le schéma doit couvrir exactement les types de la couche 1. "
                f"Manquantes : {manquantes} ; hors contrat : {surnumeraires}")

        for nom, mecanisme in self.couverture_relations().items():
            if not mecanisme:
                raise ErreurSchema(
                    f"La relation {nom!r}, déclarée en couche 1, n'est couverte "
                    f"ni par une clé étrangère ni par un contrôle après "
                    f"chargement. La migration des contrôles d'intégrité vers "
                    f"SQL en perdrait la garantie")

        for table in self.tables:
            connues = set(table.colonnes)
            if table.cle_primaire() is None and table.absence_cle_primaire is None:
                raise ErreurSchema(
                    f"Table {table.nom!r} sans clé primaire ni justification d'absence")
            if table.cle_primaire() is not None and table.absence_cle_primaire is not None:
                raise ErreurSchema(
                    f"Table {table.nom!r} : clé primaire et justification d'absence")

            for contrainte in table.contraintes:
                inconnues = sorted(set(contrainte.colonnes) - connues)
                if inconnues:
                    raise ErreurSchema(
                        f"Table {table.nom!r}, contrainte {contrainte.genre} : "
                        f"colonnes inconnues {inconnues}")
                if contrainte.genre != CLE_ETRANGERE:
                    continue
                cible = self._par_nom.get(contrainte.table_cible)
                if cible is None:
                    raise ErreurSchema(
                        f"Table {table.nom!r} : cible inconnue "
                        f"{contrainte.table_cible!r}")
                if tuple(contrainte.colonnes_cibles) not in cible.colonnes_uniques():
                    raise ErreurSchema(
                        f"Table {table.nom!r} : la clé étrangère vise "
                        f"{contrainte.table_cible}.{contrainte.colonnes_cibles}, "
                        f"qui n'est ni clé primaire ni sous contrainte d'unicité. "
                        f"Une telle relation doit être déclarée comme contrôle "
                        f"après chargement, avec son motif.")

    # -- couverture des relations déclarées par la couche 1 -----------------

    def couverture_relations(self) -> Dict[str, str]:
        """Associe à chaque relation déclarée en couche 1 le mécanisme SQL qui
        la garantit : une clé étrangère, ou un contrôle après chargement.

        Cette correspondance est vérifiée à la construction du schéma : une
        relation que ni l'un ni l'autre ne couvrirait ferait échouer le
        chargement du module. La migration des contrôles d'intégrité vers SQL
        ne peut donc pas en perdre une en chemin.
        """
        etrangeres = {
            (t.nom, c.colonnes, c.table_cible, c.colonnes_cibles)
            for t in self.tables for c in t.contraintes if c.genre == CLE_ETRANGERE}
        couverture: Dict[str, str] = {}
        for relation in fc.RELATIONS_PIVOT:
            signature = (relation.type_enfant, (relation.colonne_enfant,),
                         relation.type_parent, (relation.colonne_parent,))
            if signature in etrangeres:
                couverture[relation.nom] = "clé étrangère"
                continue
            controles = [c.nom for t in self.tables for c in t.controles
                         if t.nom == relation.type_enfant]
            couverture[relation.nom] = (
                f"contrôle après chargement : {controles[0]}" if controles else "")
        return couverture

    # -- génération du DDL --------------------------------------------------

    def ddl(self) -> str:
        morceaux = [
            "-- Schéma engendré par schema.py depuis les types d'enregistrements",
            "-- de la couche 1. Ne pas modifier à la main.",
            "-- Aucun index de performance : voir DECISIONS_SCHEMA.md.",
            "",
        ]
        for table in self.tables:
            morceaux.append(self._ddl_table(table))
        return "\n".join(morceaux)

    def _ddl_table(self, table: Table) -> str:
        non_nulles = set(table.non_nulles())
        lignes = [f"CREATE TABLE {table.nom} ("]
        corps = []
        for colonne in table.colonnes:
            suffixe = " NOT NULL" if colonne in non_nulles else ""
            corps.append(f"    {colonne} {TEXTE_SQL}{suffixe}")
        cle = table.cle_primaire()
        if cle is not None:
            corps.append(f"    PRIMARY KEY ({', '.join(cle.colonnes)})")
        for contrainte in table.contraintes:
            if contrainte.genre == UNICITE:
                corps.append(f"    UNIQUE ({', '.join(contrainte.colonnes)})")
        for contrainte in table.contraintes:
            if contrainte.genre == CLE_ETRANGERE:
                corps.append(
                    f"    FOREIGN KEY ({', '.join(contrainte.colonnes)}) "
                    f"REFERENCES {contrainte.table_cible} "
                    f"({', '.join(contrainte.colonnes_cibles)})")
        lignes.append(",\n".join(corps))
        lignes.append(");")
        return "\n".join(lignes) + "\n"

    # -- génération du registre --------------------------------------------

    def registre_markdown(self) -> str:
        lignes = [
            "# DECISIONS_SCHEMA.md",
            "",
            "**Registre des justifications du schéma de la couche 2.**",
            "",
            "Ce document est **engendré** par `schema.py` depuis les déclarations "
            "elles-mêmes. Il n'est jamais rédigé à la main : toute déclaration "
            "dépourvue de justification fait échouer la construction du schéma.",
            "",
            "Trois natures de justification sont admises : `artefact` — un fait "
            "mesuré sur les fichiers FINESS ; `mesure` — une mesure "
            "expérimentale ; `besoin` — un besoin fonctionnel documenté.",
            "",
            "## Règles générales",
            "",
            f"**Type de toutes les colonnes : `{TEXTE_SQL}`.** {self.regle_type_defaut}",
            "",
            f"**Contraintes de non-nullité.** {self.justification_non_nul}",
            "",
            f"**Aucun index de performance.** {self.justification_absence_index}",
            "",
            "## Déclarations par table",
            "",
        ]
        for table in self.tables:
            lignes.append(f"### `{table.nom}` — {len(table.colonnes)} colonnes")
            lignes.append("")
            if table.commentaire:
                lignes.append(table.commentaire)
                lignes.append("")
            cle = table.cle_primaire()
            if cle is not None:
                lignes.append(f"- **Clé primaire** `({', '.join(cle.colonnes)})` — "
                              f"{cle.justification}")
            else:
                lignes.append(f"- **Aucune clé primaire** — {table.absence_cle_primaire}")
            for contrainte in table.contraintes:
                if contrainte.genre == UNICITE:
                    lignes.append(f"- **Unicité** `({', '.join(contrainte.colonnes)})` — "
                                  f"{contrainte.justification}")
            for contrainte in table.contraintes:
                if contrainte.genre == CLE_ETRANGERE:
                    lignes.append(
                        f"- **Clé étrangère** `({', '.join(contrainte.colonnes)})` → "
                        f"`{contrainte.table_cible}"
                        f"({', '.join(contrainte.colonnes_cibles)})` — "
                        f"{contrainte.justification}")
            non_nulles = table.non_nulles()
            if non_nulles:
                lignes.append(f"- **Non nulles** : `{'`, `'.join(non_nulles)}`")
            for controle in table.controles:
                lignes.append(f"- **Contrôle après chargement** `{controle.nom}` — "
                              f"{controle.description}")
                lignes.append(f"    - *Non déclarable en SQL* : {controle.motif}")
                lignes.append(f"    - {controle.justification}")
            lignes.append("")
        return "\n".join(lignes)

    def controles(self) -> List[Tuple[str, ControlePostChargement]]:
        return [(t.nom, c) for t in self.tables for c in t.controles]

    def __getitem__(self, nom: str) -> Table:
        return self._par_nom[nom]


# ===========================================================================
# Déclarations
# ===========================================================================

_F1 = "passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607"
_F1_PROFIL = "passe F1, profiler_colonnes.py, fichiers complets 202607"
_E6 = "étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements"
_BILAN = "BILAN_COUCHE_1.md § 7"


def _unique(table: str, colonnes: str, lignes: int) -> Justification:
    return Justification(
        ARTEFACT,
        f"{lignes} lignes, {lignes} valeurs distinctes, aucune nulle sur "
        f"{table}.{colonnes}",
        _F1)


def _etrangere(verifiees: int) -> Justification:
    return Justification(
        ARTEFACT,
        f"{verifiees} rattachements vérifiés, aucune référence orpheline",
        _E6)


REGLE_TYPE_DEFAUT = Justification(
    ARTEFACT,
    "La couche 1 émet toute valeur en texte, verbatim. 898 numéros FINESS "
    "d'établissement et 460 d'entité juridique commencent par 2A ou 2B et ne "
    "sont donc pas des entiers. Les onze colonnes numériques par nature ne "
    "portent ni zéro de tête, ni valeur négative, ni valeur non numérique sur "
    "4 767 700 valeurs : leur conversion en entier serait possible sans perte, "
    "mais elle constituerait une interprétation, que la couche 2 s'interdit. "
    "Elle pourra être introduite plus tard sur justification de nature besoin",
    _F1_PROFIL)

JUSTIFICATION_NON_NUL = Justification(
    ARTEFACT,
    "Les colonnes portant NOT NULL sont exactement celles déclarées "
    "obligatoires dans SCHEMA_PIVOT.md. Le contrôle strict sur les deux "
    "fichiers complets n'a relevé aucune valeur nulle sur ces colonnes, sur "
    "5 242 334 lignes",
    _F1_PROFIL)

JUSTIFICATION_ABSENCE_INDEX = Justification(
    MESURE,
    "Aucun index de performance n'est déclaré, et la mesure confirme qu'aucun "
    "n'est justifiable. Le seul besoin de requête documenté à ce jour est "
    "l'exécution des cinq contrôles après chargement déclarés ci-dessous : ils "
    "s'exécutent en 4,1 s sur la base complète de 5 242 334 lignes, le plus "
    "coûteux — evenement_porteur_existe, 1 961 124 lignes — en 3,8 s. Les plans "
    "d'exécution montrent que les quatre sous-requêtes empruntent les index que "
    "SQLite crée automatiquement pour les clés primaires et les contraintes "
    "d'unicité : 17 index, 96,8 Mio, soit 14,6 % de la base. Ces index sont donc "
    "un effet des contraintes justifiées par artefact, non un choix de "
    "performance. Un index supplémentaire ne pourra être déclaré qu'après "
    "qu'un besoin de requête des couches supérieures aura été documenté puis "
    "mesuré comme insatisfait",
    "étape F4, entrepot.executer_controles() sur la base complète 202607")


SCHEMA = Schema(
    regle_type_defaut=REGLE_TYPE_DEFAUT,
    justification_non_nul=JUSTIFICATION_NON_NUL,
    justification_absence_index=JUSTIFICATION_ABSENCE_INDEX,
    tables=[
        Table(fc.TYPE_ENTETE, commentaire=(
            "Une ligne par fichier ingéré. L'identifiant de lot est déterministe : "
            "rejouer la même ingestion sur le même fichier produit le même "
            "identifiant."),
            contraintes=[Contrainte(CLE_PRIMAIRE, ("id_lot",), _unique("entete", "id_lot", 2))]),

        Table(fc.TYPE_ENTITE_JURIDIQUE, contraintes=[
            Contrainte(CLE_PRIMAIRE, ("num_finess_ej",),
                       _unique("entite_juridique", "num_finess_ej", 98168)),
            Contrainte(UNICITE, ("pm_smsse_id",),
                       _unique("entite_juridique", "pm_smsse_id", 98168)),
        ]),

        Table(fc.TYPE_ETABLISSEMENT, contraintes=[
            Contrainte(CLE_PRIMAIRE, ("num_finess_et",),
                       _unique("etablissement", "num_finess_et", 174508)),
            Contrainte(UNICITE, ("ege_id",),
                       _unique("etablissement", "ege_id", 174508)),
            Contrainte(CLE_ETRANGERE, ("num_finess_ej",),
                       _etrangere(174508), "entite_juridique", ("num_finess_ej",)),
        ]),

        Table(fc.TYPE_ADRESSE, commentaire=(
            "Cardinalité mesurée : une adresse par porteur en médiane, jusqu'à 150."),
            contraintes=[
                Contrainte(CLE_PRIMAIRE, ("type_porteur", "id_porteur", "rang"),
                           _unique("adresse", "(type_porteur, id_porteur, rang)", 278615)),
            ],
            controles=[ControlePostChargement(
                "adresse_porteur_existe",
                "Tout porteur d'adresse existe dans entite_juridique ou etablissement, "
                "selon la valeur de type_porteur.",
                "SELECT COUNT(*) FROM adresse a WHERE\n"
                "  (a.type_porteur = 'EJ' AND NOT EXISTS (SELECT 1 FROM entite_juridique e"
                " WHERE e.pm_smsse_id = a.id_porteur))\n"
                "  OR (a.type_porteur = 'ET' AND NOT EXISTS (SELECT 1 FROM etablissement s"
                " WHERE s.ege_id = a.id_porteur));",
                motif=(
                    "Rattachement polymorphe : id_porteur désigne tantôt une entité "
                    "juridique, tantôt un établissement, selon type_porteur. Aucune clé "
                    "étrangère SQL ne peut exprimer une cible variable. Scinder la table "
                    "par type de porteur déformerait le modèle émis par la couche 1"),
                justification=Justification(
                    ARTEFACT,
                    "278 615 adresses réparties sur 272 676 porteurs, 98 168 entités "
                    "juridiques et 174 508 établissements",
                    _F1_PROFIL))]),

        Table(fc.TYPE_CONTACT, commentaire=(
            "Cardinalité mesurée : exactement un contact par porteur sur les "
            "222 505 porteurs, sans exception."),
            contraintes=[
                Contrainte(CLE_PRIMAIRE, ("type_porteur", "id_porteur", "rang"),
                           _unique("contact", "(type_porteur, id_porteur, rang)", 222505)),
            ],
            controles=[ControlePostChargement(
                "contact_porteur_existe",
                "Tout porteur de contact existe dans entite_juridique ou etablissement.",
                "SELECT COUNT(*) FROM contact c WHERE\n"
                "  (c.type_porteur = 'EJ' AND NOT EXISTS (SELECT 1 FROM entite_juridique e"
                " WHERE e.pm_smsse_id = c.id_porteur))\n"
                "  OR (c.type_porteur = 'ET' AND NOT EXISTS (SELECT 1 FROM etablissement s"
                " WHERE s.ege_id = c.id_porteur));",
                motif="Rattachement polymorphe, comme pour adresse",
                justification=Justification(
                    ARTEFACT, "222 505 contacts, un par porteur", _F1_PROFIL))]),

        Table(fc.TYPE_ENGAGEMENT, commentaire=(
            "engagement_id n'est pas une clé naturelle : 50 identifiants "
            "apparaissent plusieurs fois, pour 144 lignes, un même arrêté étant "
            "rattaché à plusieurs porteurs. 37 de ces 50 identifiants portent en "
            "outre des nom_engagement et identifiant_engagement divergents selon "
            "l'occurrence. La table est donc une table de rattachements, et non "
            "d'entités ; aucune déduplication n'est opérée."),
            contraintes=[
                Contrainte(CLE_PRIMAIRE, ("engagement_id", "type_porteur", "id_porteur"),
                           _unique("engagement",
                                   "(engagement_id, type_porteur, id_porteur)", 77487)),
            ],
            controles=[ControlePostChargement(
                "engagement_porteur_existe",
                "Tout porteur d'engagement existe dans sa table selon type_porteur : "
                "EJ, ET, GROUPEMENT ou ACTIVITE_EJ.",
                "SELECT type_porteur, COUNT(*) FROM engagement g WHERE\n"
                "  (g.type_porteur = 'EJ' AND NOT EXISTS (SELECT 1 FROM entite_juridique e"
                " WHERE e.pm_smsse_id = g.id_porteur))\n"
                "  OR (g.type_porteur = 'ET' AND NOT EXISTS (SELECT 1 FROM etablissement s"
                " WHERE s.ege_id = g.id_porteur))\n"
                "  OR (g.type_porteur = 'GROUPEMENT' AND NOT EXISTS (SELECT 1 FROM groupement r"
                " WHERE r.groupement_id = g.id_porteur))\n"
                "  OR (g.type_porteur = 'ACTIVITE_EJ' AND NOT EXISTS (SELECT 1 FROM activite v"
                " WHERE v.activite_ae_id = g.id_porteur))\n"
                "GROUP BY type_porteur;",
                motif=("Rattachement polymorphe à quatre cibles possibles"),
                justification=Justification(
                    ARTEFACT,
                    "77 487 engagements : 77 268 issus du fichier structures, 219 du "
                    "fichier activités",
                    _F1_PROFIL))]),

        Table(fc.TYPE_ENGAGEMENT_AUTORITE, commentaire=(
            "Table sans clé. 316 lignes pour 223 combinaisons distinctes, y "
            "compris en retenant les trois colonnes disponibles : 93 lignes sont "
            "des doublons exacts, produits par la réémission des autorités à "
            "chaque rattachement de l'engagement. La colonne de porteur qui les "
            "distinguerait n'existe pas dans le contrat gelé de la couche 1, et "
            "celui-ci n'est pas rouvert pour ce seul cas."),
            absence_cle_primaire=Justification(
                ARTEFACT,
                "Aucune combinaison de colonnes n'est unique : 316 lignes, 223 "
                "distinctes sur (engagement_id, rang, code_autorite_regulation). "
                "Déclarer une clé exigerait d'ajouter les colonnes de porteur, donc "
                "de modifier le contrat gelé de la couche 1, ce qui a été écarté "
                "faute de nécessité démontrée",
                _F1),
            controles=[ControlePostChargement(
                "autorite_engagement_existe",
                "Tout engagement_id référencé existe dans la table engagement.",
                "SELECT COUNT(*) FROM engagement_autorite a\n"
                "WHERE NOT EXISTS (SELECT 1 FROM engagement g"
                " WHERE g.engagement_id = a.engagement_id);",
                motif=(
                    "La clé primaire d'engagement est (engagement_id, type_porteur, "
                    "id_porteur) ; engagement_id seul n'est pas unique, et SQL "
                    "n'autorise pas une clé étrangère vers une colonne non unique"),
                justification=Justification(
                    ARTEFACT,
                    "316 autorités rattachées à 221 engagements distincts, "
                    "1,2 autorité par engagement en moyenne, 9 au maximum",
                    _F1_PROFIL))]),

        Table(fc.TYPE_EVENEMENT, commentaire=(
            "1 961 124 lignes : la table la plus volumineuse du pivot. "
            "evenement_id est unique sur les deux fichiers réunis."),
            contraintes=[
                Contrainte(CLE_PRIMAIRE, ("evenement_id",),
                           _unique("evenement", "evenement_id", 1961124)),
            ],
            controles=[ControlePostChargement(
                "evenement_porteur_existe",
                "Tout porteur d'évènement existe dans sa table selon type_porteur : "
                "EJ, ET, GROUPEMENT, ACTIVITE_EJ ou ACTIVITE_ET.",
                "SELECT type_porteur, COUNT(*) FROM evenement v WHERE\n"
                "  (v.type_porteur = 'EJ' AND NOT EXISTS (SELECT 1 FROM entite_juridique e"
                " WHERE e.pm_smsse_id = v.id_porteur))\n"
                "  OR (v.type_porteur = 'ET' AND NOT EXISTS (SELECT 1 FROM etablissement s"
                " WHERE s.ege_id = v.id_porteur))\n"
                "  OR (v.type_porteur = 'GROUPEMENT' AND NOT EXISTS (SELECT 1 FROM groupement r"
                " WHERE r.groupement_id = v.id_porteur))\n"
                "  OR (v.type_porteur IN ('ACTIVITE_EJ','ACTIVITE_ET') AND NOT EXISTS"
                " (SELECT 1 FROM activite a WHERE a.activite_ae_id = v.id_porteur))\n"
                "GROUP BY type_porteur;",
                motif="Rattachement polymorphe à cinq cibles possibles",
                justification=Justification(
                    ARTEFACT,
                    "1 961 124 évènements : 629 075 du fichier structures et "
                    "1 332 049 du fichier activités",
                    _F1_PROFIL))]),

        Table(fc.TYPE_GROUPEMENT, commentaire=(
            "GCO et GCC réunis. groupement_id reste unique même en confondant les "
            "deux natures."),
            contraintes=[
                Contrainte(CLE_PRIMAIRE, ("groupement_id",),
                           _unique("groupement", "groupement_id", 1991)),
            ]),

        Table(fc.TYPE_GROUPEMENT_MEMBRE, contraintes=[
            Contrainte(CLE_PRIMAIRE, ("groupement_id", "rang"),
                       _unique("groupement_membre", "(groupement_id, rang)", 763)),
            Contrainte(CLE_ETRANGERE, ("groupement_id",),
                       _etrangere(763), "groupement", ("groupement_id",)),
            Contrainte(CLE_ETRANGERE, ("id_membre",),
                       _etrangere(763), "entite_juridique", ("pm_smsse_id",)),
        ]),

        Table(fc.TYPE_RELATION_ETABLISSEMENT, contraintes=[
            Contrainte(CLE_PRIMAIRE, ("ege_id", "rang"),
                       _unique("relation_etablissement", "(ege_id, rang)", 47474)),
            Contrainte(CLE_ETRANGERE, ("ege_id",),
                       _etrangere(47474), "etablissement", ("ege_id",)),
            Contrainte(CLE_ETRANGERE, ("ege_id_porteuse",),
                       _etrangere(47474), "etablissement", ("ege_id",)),
            Contrainte(CLE_ETRANGERE, ("ege_id_non_porteuse",),
                       _etrangere(47474), "etablissement", ("ege_id",)),
        ]),

        Table(fc.TYPE_ACTIVITE, commentaire=(
            "Les deux niveaux, EJ et ET, coexistent dans une table unique, "
            "discriminés par la colonne niveau. Leurs identifiants sont "
            "entièrement disjoints : 292 873 au niveau EJ, 292 873 au niveau ET, "
            "585 746 distincts au total. **Aucun lien n'existe dans les données "
            "entre une activité autorisée et l'activité exercée correspondante.** "
            "Le schéma n'en invente aucun : ce sont deux ensembles indépendants, "
            "propriété du millésime observé et non lacune du modèle."),
            contraintes=[
                Contrainte(CLE_PRIMAIRE, ("activite_ae_id",),
                           _unique("activite", "activite_ae_id", 585746)),
                Contrainte(CLE_ETRANGERE, ("num_finess_ej",),
                           _etrangere(585746), "entite_juridique", ("num_finess_ej",)),
                Contrainte(CLE_ETRANGERE, ("pm_smsse_id",),
                           _etrangere(585746), "entite_juridique", ("pm_smsse_id",)),
                Contrainte(CLE_ETRANGERE, ("num_finess_et",),
                           _etrangere(292873), "etablissement", ("num_finess_et",)),
                Contrainte(CLE_ETRANGERE, ("ege_id",),
                           _etrangere(292873), "etablissement", ("ege_id",)),
            ]),

        Table(fc.TYPE_CAPACITE, commentaire=(
            "Cardinalité mesurée : 1,9 capacité par activité en moyenne, 26 au "
            "maximum. 22 lignes portent un nombre nul."),
            contraintes=[
                Contrainte(CLE_PRIMAIRE, ("id_capacite",),
                           _unique("capacite", "id_capacite", 537233)),
                Contrainte(CLE_ETRANGERE, ("activite_ae_id",),
                           _etrangere(537233), "activite", ("activite_ae_id",)),
            ]),

        Table(fc.TYPE_APPAREIL, commentaire=(
            "Cardinalité mesurée : exactement 8 appareils sur chacune des "
            "2 012 activités concernées, sans exception."),
            contraintes=[
                Contrainte(CLE_PRIMAIRE, ("activite_ae_id", "rang"),
                           _unique("appareil", "(activite_ae_id, rang)", 16096)),
                Contrainte(CLE_ETRANGERE, ("activite_ae_id",),
                           _etrangere(16096), "activite", ("activite_ae_id",)),
            ]),

        Table(fc.TYPE_ZONE_INTERVENTION, contraintes=[
            Contrainte(CLE_PRIMAIRE, ("zone_intervention_id",),
                       _unique("zone_intervention", "zone_intervention_id", 8336)),
            Contrainte(CLE_ETRANGERE, ("activite_ae_id",),
                       _etrangere(8336), "activite", ("activite_ae_id",)),
        ]),

        Table(fc.TYPE_ZONE_INTERVENTION_COMMUNE, commentaire=(
            "Cardinalité mesurée : 41 communes par zone en médiane, 4 057 au "
            "maximum."),
            contraintes=[
                Contrainte(CLE_PRIMAIRE, ("zone_intervention_id", "rang"),
                           _unique("zone_intervention_commune",
                                   "(zone_intervention_id, rang)", 1231970)),
                Contrainte(CLE_ETRANGERE, ("zone_intervention_id",),
                           _etrangere(1231970), "zone_intervention",
                           ("zone_intervention_id",)),
            ]),
    ])


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    analyseur = argparse.ArgumentParser(
        description="Schéma de la couche 2 : DDL et registre des justifications.")
    analyseur.add_argument("--ddl", type=Path, help="fichier SQL à écrire")
    analyseur.add_argument("--registre", type=Path, help="fichier Markdown à écrire")
    arguments = analyseur.parse_args()

    if arguments.ddl:
        arguments.ddl.write_text(SCHEMA.ddl(), encoding="utf-8")
        print(f"DDL écrit : {arguments.ddl}")
    if arguments.registre:
        arguments.registre.write_text(SCHEMA.registre_markdown(), encoding="utf-8")
        print(f"Registre écrit : {arguments.registre}")
    if not (arguments.ddl or arguments.registre):
        print(SCHEMA.ddl())
