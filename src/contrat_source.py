"""
contrat_source.py — Couche 1 (acquisition), étape E2.

Contrat que tout connecteur de source doit respecter, et instrumentation
commune : compteurs, registre d'anomalies, inventaire des codes.

Le module est générique. Il ne connaît ni FINESS, ni INSEE, ni aucune source
particulière : il ne définit que le vocabulaire et les garde-fous. Les
connecteurs déclarent leurs types d'enregistrements et produisent des
dictionnaires ; le pilote convertit, contrôle, compte et réémet.

Garantie de mémoire. Aucune structure ne croît avec le volume traité :
- les compteurs sont bornés par le nombre de types d'enregistrements ;
- le registre d'anomalies est borné par un nombre maximal d'exemples par code ;
- l'inventaire des codes est borné par domaine, avec saturation explicite.
Cette garantie est la contrainte d'architecture héritée d'E1.

Aucune dépendance tierce. Compatible Python 3.9+.
"""

from __future__ import annotations

import hashlib
import re
import time
from operator import itemgetter
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple

__all__ = [
    "TEXTE", "DATE", "HORODATAGE", "ENTIER_TEXTE", "TYPES_VALEUR",
    "BLOQUANT", "AVERTISSEMENT",
    "Champ", "TypeEnregistrement", "TYPE_ENTETE",
    "Lot", "Anomalie", "RegistreAnomalies", "InventaireCodes",
    "ContexteSource", "Source", "RapportIngestion",
    "empreinte_fichier", "parcourir_source",
    "ErreurContrat",
]

# --- types de valeur admis dans le pivot -----------------------------------
TEXTE = "TEXTE"
DATE = "DATE"
HORODATAGE = "HORODATAGE"
ENTIER_TEXTE = "ENTIER_TEXTE"
TYPES_VALEUR = frozenset({TEXTE, DATE, HORODATAGE, ENTIER_TEXTE})

# --- gravités ---------------------------------------------------------------
BLOQUANT = "bloquant"
AVERTISSEMENT = "avertissement"

# --- modes de contrôle ------------------------------------------------------
CONTROLE_MINIMAL = "minimal"        # cardinalité et présence des champs seulement
CONTROLE_ECHANTILLON = "echantillon"  # + format sur un échantillon
CONTROLE_STRICT = "strict"          # + format sur toutes les lignes

_MOTIF_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MOTIF_HORODATAGE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")
_MOTIF_ENTIER = re.compile(r"^-?\d+$")


class ErreurContrat(Exception):
    """Violation du contrat détectée à la déclaration, non à l'exécution."""


# ---------------------------------------------------------------------------
# Déclaration du schéma
# ---------------------------------------------------------------------------

class Champ:
    """Un champ d'un type d'enregistrement.

    `obligatoire` signifie « jamais nul », et autorise donc un contrôle
    bloquant. `domaine` désigne la nomenclature à laquelle la valeur renvoie ;
    c'est lui, et lui seul, qui déclenche l'alimentation de l'inventaire des
    codes.
    """

    __slots__ = ("nom", "type_valeur", "obligatoire", "domaine", "commentaire")

    def __init__(self, nom: str, type_valeur: str = TEXTE, obligatoire: bool = False,
                 domaine: Optional[str] = None, commentaire: str = "") -> None:
        if not nom or not nom.replace("_", "").isalnum():
            raise ErreurContrat(f"Nom de champ invalide : {nom!r}")
        if type_valeur not in TYPES_VALEUR:
            raise ErreurContrat(f"Type de valeur inconnu pour {nom!r} : {type_valeur!r}")
        self.nom = nom
        self.type_valeur = type_valeur
        self.obligatoire = obligatoire
        self.domaine = domaine
        self.commentaire = commentaire

    def __repr__(self) -> str:  # pragma: no cover - confort de mise au point
        return f"Champ({self.nom!r}, {self.type_valeur}, obligatoire={self.obligatoire})"


class TypeEnregistrement:
    """Un type d'enregistrement du pivot, à l'ordre des champs figé.

    L'ordre de déclaration est l'ordre d'émission, donc l'ordre des colonnes
    attendu par l'entrepôt. Il ne change pas sans changement de version du
    contrat.
    """

    __slots__ = ("nom", "champs", "noms", "_position", "_obligatoires",
                 "_codifies", "_formats", "_cardinalite", "_extracteur")

    def __init__(self, nom: str, champs: Iterable[Champ]) -> None:
        self.nom = nom
        self.champs: Tuple[Champ, ...] = tuple(champs)
        if not self.champs:
            raise ErreurContrat(f"Type {nom!r} sans aucun champ")
        self.noms: Tuple[str, ...] = tuple(c.nom for c in self.champs)
        if len(set(self.noms)) != len(self.noms):
            doublons = sorted({n for n in self.noms if self.noms.count(n) > 1})
            raise ErreurContrat(f"Type {nom!r} : champs en double {doublons}")
        self._position = {c.nom: i for i, c in enumerate(self.champs)}
        self._cardinalite = len(self.champs)
        self._obligatoires = tuple(i for i, c in enumerate(self.champs) if c.obligatoire)
        self._codifies = tuple((i, c.domaine) for i, c in enumerate(self.champs) if c.domaine)
        self._formats = tuple(
            (i, c.type_valeur) for i, c in enumerate(self.champs)
            if c.type_valeur in (DATE, HORODATAGE, ENTIER_TEXTE)
        )
        # Extraction en une seule opération de la bibliothèque standard, trois
        # fois plus rapide qu'une compréhension sur un enregistrement large.
        # itemgetter lève KeyError si un champ manque ; conjugué au contrôle de
        # cardinalité, cela garantit que le dictionnaire porte exactement les
        # champs déclarés, ni plus ni moins.
        if self._cardinalite == 1:
            unique = self.noms[0]
            self._extracteur: Callable[[Dict[str, Any]], Tuple[Any, ...]] = \
                lambda valeurs: (valeurs[unique],)
        else:
            self._extracteur = itemgetter(*self.noms)

    # -- construction de lignes --------------------------------------------

    def gabarit(self) -> Dict[str, None]:
        """Dictionnaire de tous les champs à None, point de départ d'un connecteur."""
        return {nom: None for nom in self.noms}

    def ligne(self, valeurs: Dict[str, Any]) -> Tuple[Any, ...]:
        """Convertit un dictionnaire en tuple, dans l'ordre figé.

        Tous les champs déclarés doivent être présents, éventuellement à None.
        Cette exigence est délibérée : elle oblige le connecteur à se prononcer
        sur chaque champ, ce qui est la condition de l'exhaustivité.
        """
        if len(valeurs) != self._cardinalite:
            self._diagnostiquer(valeurs)
        try:
            return self._extracteur(valeurs)
        except KeyError:
            self._diagnostiquer(valeurs)
            raise  # pragma: no cover - _diagnostiquer lève toujours

    def _diagnostiquer(self, valeurs: Dict[str, Any]) -> None:
        attendus = set(self.noms)
        fournis = set(valeurs)
        manquants = sorted(attendus - fournis)
        inconnus = sorted(fournis - attendus)
        details = []
        if manquants:
            details.append(f"champs manquants {manquants}")
        if inconnus:
            details.append(f"champs hors contrat {inconnus}")
        if not details:
            details.append(f"cardinalité {len(valeurs)} au lieu de {self._cardinalite}")
        raise ErreurContrat(f"Type {self.nom!r} : " + " ; ".join(details))

    # -- contrôles ----------------------------------------------------------

    def controler(self, ligne: Tuple[Any, ...], approfondi: bool) -> List[Tuple[str, str, str]]:
        """Retourne la liste des anomalies (code, champ, détail) d'une ligne.

        La nullité des champs obligatoires est vérifiée sur toutes les lignes :
        c'est une anomalie de donnée, donc sporadique par nature. La nature
        textuelle des valeurs et le format des dates ne sont vérifiés que sur
        les lignes retenues par l'échantillonnage : ce sont des anomalies de
        connecteur, systématiques par nature, qu'un échantillon suffit à
        révéler. Contrôler les 47 champs de chaque ligne coûterait trente fois
        le prix du contrôle des seuls champs obligatoires.

        La garantie repose sur la discipline suivante : tout connecteur est
        validé une fois en mode « strict » sur le fichier complet avant d'être
        gelé ; les exécutions courantes se contentent de l'échantillon.
        """
        anomalies: List[Tuple[str, str, str]] = []
        for i in self._obligatoires:
            if ligne[i] is None:
                anomalies.append(("champ_obligatoire_nul", self.noms[i], ""))
        if approfondi:
            for i, valeur in enumerate(ligne):
                if valeur is not None and not isinstance(valeur, str):
                    anomalies.append(
                        ("valeur_non_textuelle", self.noms[i], type(valeur).__name__))
            for i, type_valeur in self._formats:
                valeur = ligne[i]
                if valeur is None or not isinstance(valeur, str):
                    continue
                motif = (_MOTIF_DATE if type_valeur == DATE
                         else _MOTIF_HORODATAGE if type_valeur == HORODATAGE
                         else _MOTIF_ENTIER)
                if not motif.match(valeur):
                    anomalies.append(("format_inattendu", self.noms[i], valeur[:24]))
        return anomalies

    def champs_codifies(self) -> Tuple[Tuple[int, str], ...]:
        return self._codifies

    def position(self, nom: str) -> int:
        return self._position[nom]

    def __repr__(self) -> str:  # pragma: no cover
        return f"TypeEnregistrement({self.nom!r}, {len(self.champs)} champs)"


# --- type d'en-tête, commun à toutes les sources ----------------------------

TYPE_ENTETE = TypeEnregistrement("entete", [
    Champ("id_lot", TEXTE, obligatoire=True),
    Champ("source", TEXTE, obligatoire=True),
    Champ("millesime", TEXTE, obligatoire=True),
    Champ("schema_version", TEXTE, obligatoire=True),
    Champ("genere_le", HORODATAGE),
    Champ("nom_fichier", TEXTE, obligatoire=True),
    Champ("empreinte", TEXTE, obligatoire=True),
    Champ("octets", ENTIER_TEXTE, obligatoire=True),
])


# ---------------------------------------------------------------------------
# Lot d'ingestion
# ---------------------------------------------------------------------------

class Lot:
    """Identité d'une exécution d'ingestion sur un fichier.

    L'identifiant est déterministe : rejouer la même ingestion sur le même
    fichier produit le même identifiant, ce qui rend l'étape idempotente.
    """

    __slots__ = ("source", "millesime", "nom_fichier", "empreinte", "octets",
                 "schema_version", "genere_le")

    def __init__(self, source: str, millesime: str, nom_fichier: str,
                 empreinte: str, octets: int) -> None:
        self.source = source
        self.millesime = millesime
        self.nom_fichier = nom_fichier
        self.empreinte = empreinte
        self.octets = octets
        self.schema_version: Optional[str] = None
        self.genere_le: Optional[str] = None

    @property
    def identifiant(self) -> str:
        return f"{self.source}:{self.millesime}:{self.empreinte[:8]}"

    def ligne_entete(self) -> Dict[str, Any]:
        return {
            "id_lot": self.identifiant,
            "source": self.source,
            "millesime": self.millesime,
            "schema_version": self.schema_version,
            "genere_le": self.genere_le,
            "nom_fichier": self.nom_fichier,
            "empreinte": self.empreinte,
            "octets": str(self.octets),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"Lot({self.identifiant!r}, {self.octets} octets)"


def empreinte_fichier(chemin: Path, taille_bloc: int = 1 << 20) -> Tuple[str, int]:
    """SHA-256 du fichier tel qu'il est sur le disque, calculé en flux.

    L'empreinte porte sur l'octet, pas sur le contenu décompressé : c'est
    l'identité du fichier reçu qui doit être tracée.
    """
    condensat = hashlib.sha256()
    octets = 0
    with open(chemin, "rb") as f:
        while True:
            bloc = f.read(taille_bloc)
            if not bloc:
                break
            octets += len(bloc)
            condensat.update(bloc)
    return condensat.hexdigest(), octets


# ---------------------------------------------------------------------------
# Registre d'anomalies
# ---------------------------------------------------------------------------

class Anomalie:
    __slots__ = ("code", "gravite", "type_enregistrement", "champ", "detail", "contexte")

    def __init__(self, code: str, gravite: str, type_enregistrement: str = "",
                 champ: str = "", detail: str = "", contexte: str = "") -> None:
        self.code = code
        self.gravite = gravite
        self.type_enregistrement = type_enregistrement
        self.champ = champ
        self.detail = detail
        self.contexte = contexte

    def __str__(self) -> str:
        morceaux = [f"[{self.gravite}] {self.code}"]
        if self.type_enregistrement:
            morceaux.append(self.type_enregistrement)
        if self.champ:
            morceaux.append(f"champ {self.champ}")
        if self.detail:
            morceaux.append(str(self.detail))
        if self.contexte:
            morceaux.append(f"({self.contexte})")
        return " · ".join(morceaux)


class RegistreAnomalies:
    """Comptage exhaustif, conservation bornée d'exemples.

    Le comptage est complet : aucune anomalie n'est perdue statistiquement.
    Seuls les exemples sont plafonnés, ce qui borne la mémoire quel que soit
    le nombre d'anomalies rencontrées.
    """

    __slots__ = ("max_exemples", "_comptes", "_exemples", "_bloquantes")

    def __init__(self, max_exemples: int = 10) -> None:
        self.max_exemples = max_exemples
        self._comptes: Dict[Tuple[str, str, str, str], int] = {}
        self._exemples: Dict[str, List[Anomalie]] = {}
        self._bloquantes = 0

    def signaler(self, code: str, gravite: str, type_enregistrement: str = "",
                 champ: str = "", detail: str = "", contexte: str = "") -> None:
        cle = (code, gravite, type_enregistrement, champ)
        self._comptes[cle] = self._comptes.get(cle, 0) + 1
        if gravite == BLOQUANT:
            self._bloquantes += 1
        exemples = self._exemples.setdefault(code, [])
        if len(exemples) < self.max_exemples:
            exemples.append(
                Anomalie(code, gravite, type_enregistrement, champ, detail, contexte))

    @property
    def bloquantes(self) -> int:
        return self._bloquantes

    def total(self) -> int:
        return sum(self._comptes.values())

    def par_code(self) -> Dict[str, int]:
        agrege: Dict[str, int] = {}
        for (code, _g, _t, _c), n in self._comptes.items():
            agrege[code] = agrege.get(code, 0) + n
        return dict(sorted(agrege.items(), key=lambda x: -x[1]))

    def detail(self) -> List[Tuple[str, str, str, str, int]]:
        return sorted(
            ((code, gravite, type_enr, champ, n)
             for (code, gravite, type_enr, champ), n in self._comptes.items()),
            key=lambda x: -x[4],
        )

    def exemples(self, code: str) -> List[Anomalie]:
        return list(self._exemples.get(code, ()))


# ---------------------------------------------------------------------------
# Inventaire des codes
# ---------------------------------------------------------------------------

class InventaireCodes:
    """Valeurs distinctes rencontrées sur les champs codifiés, par domaine.

    Alimente la couche 3 (nomenclatures) et rend visibles les codes inconnus.
    Chaque domaine est plafonné : au-delà, les valeurs déjà connues continuent
    d'être comptées, les nouvelles sont dénombrées globalement et le domaine
    est marqué saturé. La mémoire reste donc bornée même si une source émet
    par erreur un identifiant technique dans un champ codifié.
    """

    __slots__ = ("max_valeurs_par_domaine", "_valeurs", "_satures", "_debordements")

    def __init__(self, max_valeurs_par_domaine: int = 5000) -> None:
        self.max_valeurs_par_domaine = max_valeurs_par_domaine
        self._valeurs: Dict[str, Dict[str, int]] = {}
        self._satures: Dict[str, bool] = {}
        self._debordements: Dict[str, int] = {}

    def observer(self, domaine: str, valeur: str) -> None:
        connues = self._valeurs.setdefault(domaine, {})
        n = connues.get(valeur)
        if n is not None:
            connues[valeur] = n + 1
        elif len(connues) < self.max_valeurs_par_domaine:
            connues[valeur] = 1
        else:
            self._satures[domaine] = True
            self._debordements[domaine] = self._debordements.get(domaine, 0) + 1

    def domaines(self) -> List[str]:
        return sorted(self._valeurs)

    def valeurs(self, domaine: str) -> Dict[str, int]:
        return dict(sorted(self._valeurs.get(domaine, {}).items(), key=lambda x: -x[1]))

    def nombre_distinct(self, domaine: str) -> int:
        return len(self._valeurs.get(domaine, ()))

    def sature(self, domaine: str) -> bool:
        return self._satures.get(domaine, False)

    def resume(self) -> List[Tuple[str, int, int, bool]]:
        """(domaine, valeurs distinctes, occurrences, saturé)."""
        return [
            (d, len(v), sum(v.values()), self._satures.get(d, False))
            for d, v in sorted(self._valeurs.items())
        ]


# ---------------------------------------------------------------------------
# Contrat des connecteurs
# ---------------------------------------------------------------------------

class ContexteSource:
    """Ce qu'un connecteur reçoit du pilote, et le seul canal par lequel il
    signale quoi que ce soit. Un connecteur n'écrit jamais sur la sortie
    standard et ne lève jamais d'exception pour une anomalie de données."""

    __slots__ = ("lot", "registre", "inventaire", "_lus", "_ignores")

    def __init__(self, lot: Lot, registre: RegistreAnomalies,
                 inventaire: InventaireCodes) -> None:
        self.lot = lot
        self.registre = registre
        self.inventaire = inventaire
        self._lus: Dict[str, int] = {}
        self._ignores: Dict[str, int] = {}

    def compter_lu(self, categorie: str, nombre: int = 1) -> None:
        """Objets source lus, avant toute traduction."""
        self._lus[categorie] = self._lus.get(categorie, 0) + nombre

    def compter_ignore(self, categorie: str, nombre: int = 1) -> None:
        """Objets source volontairement non traduits. Doit rester à zéro."""
        self._ignores[categorie] = self._ignores.get(categorie, 0) + nombre

    def signaler(self, code: str, gravite: str = AVERTISSEMENT, **details: str) -> None:
        self.registre.signaler(code, gravite, **details)

    @property
    def lus(self) -> Dict[str, int]:
        return dict(self._lus)

    @property
    def ignores(self) -> Dict[str, int]:
        return dict(self._ignores)


class Source:
    """Contrat que tout connecteur implémente.

    Les futures sources — INSEE, CNSA, ROR, IGN, OpenStreetMap — s'accrochent
    ici, sans que rien d'autre ne change dans la chaîne.
    """

    nom: str = ""

    def millesime(self, chemin: Path) -> str:
        raise NotImplementedError

    def types_enregistrements(self) -> Tuple[TypeEnregistrement, ...]:
        raise NotImplementedError

    def produire(self, chemin: Path, contexte: ContexteSource
                 ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """Émet des couples (nom du type d'enregistrement, dictionnaire).

        En un seul passage, dans l'ordre du document, sans jamais construire
        de collection complète. Le premier couple émis doit être l'en-tête.
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Rapport d'ingestion
# ---------------------------------------------------------------------------

class RapportIngestion:
    __slots__ = ("lot", "emis", "lus", "ignores", "registre", "inventaire",
                 "duree_s", "termine", "controle", "lignes_controlees")

    def __init__(self, lot: Lot, registre: RegistreAnomalies,
                 inventaire: InventaireCodes, controle: str) -> None:
        self.lot = lot
        self.registre = registre
        self.inventaire = inventaire
        self.controle = controle
        self.emis: Dict[str, int] = {}
        self.lus: Dict[str, int] = {}
        self.ignores: Dict[str, int] = {}
        self.duree_s = 0.0
        self.termine = False
        self.lignes_controlees = 0

    @property
    def total_emis(self) -> int:
        return sum(self.emis.values())

    @property
    def statut(self) -> str:
        if not self.termine:
            return "ECHEC"
        if self.registre.bloquantes:
            return "ECHEC"
        if self.total_emis <= 1:      # l'en-tête seul ne constitue pas une ingestion
            return "ECHEC"
        return "SUCCES"

    def texte(self) -> str:
        lignes = [
            f"Lot        : {self.lot.identifiant}",
            f"Fichier    : {self.lot.nom_fichier} ({self.lot.octets / 2**20:.0f} Mio)",
            f"Schéma     : {self.lot.schema_version} · généré le {self.lot.genere_le}",
            f"Statut     : {self.statut} · {self.duree_s:.1f} s · contrôle « {self.controle} »",
            f"Émis       : {self.total_emis} lignes",
        ]
        for nom, n in sorted(self.emis.items(), key=lambda x: -x[1]):
            lignes.append(f"    {nom:<28} {n:>10}")
        if self.lus:
            lignes.append("Lus        : " + ", ".join(
                f"{k}={v}" for k, v in sorted(self.lus.items())))
        if any(self.ignores.values()):
            lignes.append("Ignorés    : " + ", ".join(
                f"{k}={v}" for k, v in sorted(self.ignores.items())))
        lignes.append(
            f"Anomalies  : {self.registre.total()} dont {self.registre.bloquantes} bloquantes")
        for code, gravite, type_enr, champ, n in self.registre.detail()[:12]:
            cible = f"{type_enr}.{champ}" if champ else type_enr
            lignes.append(f"    [{gravite}] {code:<26} {cible:<34} {n:>8}")
        if self.inventaire.resume():
            lignes.append("Codes      :")
            for domaine, distincts, occurrences, sature in self.inventaire.resume():
                marque = " (SATURÉ)" if sature else ""
                lignes.append(
                    f"    {domaine:<34} {distincts:>6} distincts · {occurrences:>10} occurrences{marque}")
        return "\n".join(lignes)


# ---------------------------------------------------------------------------
# Pilote
# ---------------------------------------------------------------------------

def parcourir_source(
    source: Source,
    chemin: Path,
    controle: str = CONTROLE_ECHANTILLON,
    pas_echantillon: int = 1000,
    max_exemples: int = 10,
    max_codes_par_domaine: int = 5000,
    inventorier_codes: bool = True,
    rapport: Optional[RapportIngestion] = None,
) -> Iterator[Tuple[str, Tuple[Any, ...]]]:
    """Exécute un connecteur et réémet ses lignes, contrôlées et comptées.

    Émet des couples (nom du type, tuple de valeurs dans l'ordre figé), prêts
    à être insérés tels quels par la couche 2. Aucune ligne n'est conservée.

    Le contrôle de format porte sur toutes les lignes en mode « strict », sur
    une ligne sur `pas_echantillon` en mode « echantillon », et sur aucune en
    mode « minimal ». La cardinalité et la nature textuelle des valeurs sont
    toujours vérifiées.
    """
    if controle not in (CONTROLE_MINIMAL, CONTROLE_ECHANTILLON, CONTROLE_STRICT):
        raise ErreurContrat(f"Mode de contrôle inconnu : {controle!r}")

    chemin = Path(chemin)
    if not chemin.exists():
        raise ErreurContrat(f"Fichier introuvable : {chemin}")

    types = {t.nom: t for t in source.types_enregistrements()}
    if TYPE_ENTETE.nom not in types:
        raise ErreurContrat(
            f"La source {source.nom!r} ne déclare pas le type {TYPE_ENTETE.nom!r}")

    empreinte, octets = empreinte_fichier(chemin)
    lot = Lot(source.nom, source.millesime(chemin), chemin.name, empreinte, octets)
    registre = RegistreAnomalies(max_exemples=max_exemples)
    inventaire = InventaireCodes(max_valeurs_par_domaine=max_codes_par_domaine)
    contexte = ContexteSource(lot, registre, inventaire)

    rap = rapport if rapport is not None else RapportIngestion(
        lot, registre, inventaire, controle)
    rap.lot = lot
    rap.registre = registre
    rap.inventaire = inventaire
    rap.controle = controle

    depart = time.time()
    rang = 0
    codes_par_type: Dict[str, Tuple[Tuple[int, str], ...]] = {}

    for nom_type, valeurs in source.produire(chemin, contexte):
        type_enr = types.get(nom_type)
        if type_enr is None:
            registre.signaler("type_hors_contrat", BLOQUANT,
                              type_enregistrement=nom_type, contexte=f"rang {rang}")
            rang += 1
            continue

        if rang == 0 and nom_type != TYPE_ENTETE.nom:
            registre.signaler("entete_absente", BLOQUANT, type_enregistrement=nom_type,
                              detail="le premier enregistrement doit être l'en-tête")

        try:
            ligne = type_enr.ligne(valeurs)
        except ErreurContrat as erreur:
            registre.signaler("ligne_hors_contrat", BLOQUANT,
                              type_enregistrement=nom_type, detail=str(erreur),
                              contexte=f"rang {rang}")
            rang += 1
            continue

        approfondi = (controle == CONTROLE_STRICT
                      or (controle == CONTROLE_ECHANTILLON and rang % pas_echantillon == 0))
        if approfondi:
            rap.lignes_controlees += 1
        for code, champ, detail in type_enr.controler(ligne, approfondi):
            gravite = BLOQUANT if code in ("champ_obligatoire_nul", "valeur_non_textuelle") \
                else AVERTISSEMENT
            registre.signaler(code, gravite, type_enregistrement=nom_type,
                              champ=champ, detail=detail, contexte=f"rang {rang}")

        if inventorier_codes:
            codifies = codes_par_type.get(nom_type)
            if codifies is None:
                codifies = type_enr.champs_codifies()
                codes_par_type[nom_type] = codifies
            for indice, domaine in codifies:
                valeur = ligne[indice]
                if valeur is not None:
                    inventaire.observer(domaine, valeur)

        rap.emis[nom_type] = rap.emis.get(nom_type, 0) + 1
        rang += 1
        yield (nom_type, ligne)

    rap.lus = contexte.lus
    rap.ignores = contexte.ignores
    rap.duree_s = time.time() - depart
    rap.termine = True

    if rap.emis.get(TYPE_ENTETE.nom, 0) != 1:
        registre.signaler("entete_manquante_ou_multiple", BLOQUANT,
                          type_enregistrement=TYPE_ENTETE.nom,
                          detail=str(rap.emis.get(TYPE_ENTETE.nom, 0)))
    if rap.total_emis <= 1:
        registre.signaler("aucune_donnee", BLOQUANT,
                          detail="aucun enregistrement au-delà de l'en-tête")
    for categorie, nombre in contexte.ignores.items():
        if nombre:
            registre.signaler("objets_ignores", BLOQUANT,
                              type_enregistrement=categorie, detail=str(nombre))
