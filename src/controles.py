"""
controles.py — Couche 0 (socle), étape E6.

Déclaration et évaluation des invariants de rattachement, avec classement par
sévérité. Le module est générique : il ne connaît aucune source, seulement des
relations déclarées entre un type d'enregistrement enfant et un type parent.

Deux portées :

- **locale** — l'enfant suit immédiatement son parent dans le flux. La
  vérification se fait sur une fenêtre d'un élément, à mémoire constante.
- **différée** — l'enfant et le parent sont dans deux fichiers distincts, ou
  éloignés dans le même. Un index d'identifiants est constitué en une passe,
  puis interrogé lors d'une passe ultérieure.


CE QUE L'ARCHITECTURE IMPOSE, ET CE QU'ELLE N'IMPOSE PAS
--------------------------------------------------------

L'architecture exige **l'existence d'un index exact d'identifiants**, et rien
de plus. Le contrat tient en quatre points :

    ajouter(valeur)      accepte une chaîne ou None ; None est ignoré
    figer()              rend l'index interrogeable ; interdit les ajouts
    valeur in index      appartenance EXACTE : ni faux positif, ni faux négatif
    len(index)           nombre d'identifiants distincts retenus

Deux méthodes complémentaires servent au seul rapport et peuvent être des
approximations : `octets()` et `part_non_numerique()`.

Trois garanties sont exigées de toute implémentation :

1. **exactitude** — aucune structure probabiliste, aucun repli sur un
   condensé pouvant produire une collision ;
2. **faible empreinte mémoire** — le budget de la couche 1 est de l'ordre
   de 100 Mio, index compris ;
3. **absence de perte** — tout identifiant ajouté est retrouvé, quelle que
   soit sa forme : chiffres, lettres, zéros de tête, longueur variable.

`IndexIdentifiants` ci-dessous est **une** implémentation de ce contrat, pas
la règle du projet. Son encodage des chaînes numériques en entiers 64 bits par
préfixage d'un « 1 » — injectif, préservant longueur et zéros de tête, de sorte
que `010000024` donne 1010000024 et `10000024` donne 110000024 — est une
optimisation interne. Coût mesuré : 8 octets par identifiant numérique contre
environ 90 pour une chaîne dans un ensemble, soit 4,4 Mio au lieu de 49 sur les
545 352 identifiants du fichier structures. Les identifiants non numériques,
tels les numéros FINESS corses `2A…` et `2B…`, sont conservés littéralement.

Toute autre implémentation offrant les trois garanties doit pouvoir la
remplacer **sans modifier aucun autre module** : `VerificateurRelations` reçoit
pour cela une fabrique d'index en paramètre. Seul l'algorithme peut évoluer ;
l'interface est stable. Le test `test_controles.py` le démontre en substituant
une implémentation naïve fondée sur un ensemble de chaînes et en vérifiant que
le comportement observable est identique.

Aucune dépendance tierce. Compatible Python 3.9+.
"""

from __future__ import annotations

from array import array
from bisect import bisect_left
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

from contrat_source import AVERTISSEMENT, BLOQUANT, RegistreAnomalies

__all__ = ["LOCALE", "DIFFEREE", "Relation", "IndexIdentifiants",
           "VerificateurRelations", "ErreurControle"]

LOCALE = "locale"
DIFFEREE = "differee"


class ErreurControle(Exception):
    """Relation mal déclarée, ou index interrogé avant d'être figé."""


class Relation:
    """Un rattachement à vérifier entre deux types d'enregistrements."""

    __slots__ = ("nom", "type_enfant", "colonne_enfant", "type_parent",
                 "colonne_parent", "portee", "gravite")

    def __init__(self, type_enfant: str, colonne_enfant: str, type_parent: str,
                 colonne_parent: str, portee: str = LOCALE,
                 gravite: str = BLOQUANT) -> None:
        if portee not in (LOCALE, DIFFEREE):
            raise ErreurControle(f"Portée inconnue : {portee!r}")
        self.type_enfant = type_enfant
        self.colonne_enfant = colonne_enfant
        self.type_parent = type_parent
        self.colonne_parent = colonne_parent
        self.portee = portee
        self.gravite = gravite
        self.nom = f"{type_enfant}.{colonne_enfant} -> {type_parent}.{colonne_parent}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"Relation({self.nom!r}, {self.portee})"


class IndexIdentifiants:
    """Ensemble exact d'identifiants, à faible empreinte mémoire.

    Les chaînes de chiffres sont encodées en entiers 64 bits par le préfixe
    « 1 », encodage injectif : deux chaînes distinctes donnent deux entiers
    distincts, quels que soient leur longueur et leurs zéros de tête. Les
    autres valeurs sont conservées littéralement.
    """

    __slots__ = ("nom", "_entiers", "_autres", "_fige")

    def __init__(self, nom: str = "") -> None:
        self.nom = nom
        self._entiers = array("q")
        self._autres: Set[str] = set()
        self._fige = False

    @staticmethod
    def _encoder(valeur: str) -> Optional[int]:
        if not valeur.isdigit() or len(valeur) > 18:
            return None
        return int("1" + valeur)

    def ajouter(self, valeur: Optional[str]) -> None:
        if valeur is None:
            return
        if self._fige:
            raise ErreurControle(f"Index {self.nom!r} déjà figé")
        entier = self._encoder(valeur)
        if entier is None:
            self._autres.add(valeur)
        else:
            self._entiers.append(entier)

    def figer(self) -> "IndexIdentifiants":
        """Trie et dédoublonne. L'index devient interrogeable."""
        if not self._fige:
            tries = sorted(set(self._entiers))
            self._entiers = array("q", tries)
            self._fige = True
        return self

    def __contains__(self, valeur: object) -> bool:
        if not self._fige:
            raise ErreurControle(f"Index {self.nom!r} interrogé avant d'être figé")
        if not isinstance(valeur, str):
            return False
        entier = self._encoder(valeur)
        if entier is None:
            return valeur in self._autres
        position = bisect_left(self._entiers, entier)
        return position < len(self._entiers) and self._entiers[position] == entier

    def __len__(self) -> int:
        return len(self._entiers) + len(self._autres)

    def octets(self) -> int:
        """Empreinte approximative, en octets."""
        return self._entiers.buffer_info()[1] * self._entiers.itemsize + \
            sum(len(v) + 49 for v in self._autres) + 32 * len(self._autres)

    def part_non_numerique(self) -> int:
        return len(self._autres)


class VerificateurRelations:
    """Évalue un jeu de relations sur un flux d'enregistrements."""

    def __init__(self, relations: Sequence[Relation],
                 positions: Dict[str, Dict[str, int]],
                 registre: Optional[RegistreAnomalies] = None,
                 fabrique_index: Callable[[str], Any] = IndexIdentifiants) -> None:
        """`fabrique_index` reçoit un nom et rend un index respectant le
        contrat décrit en tête de module. Le défaut est l'implémentation
        fournie ici ; toute autre convient dès lors qu'elle offre les mêmes
        garanties."""
        self.relations = tuple(relations)
        self.fabrique_index = fabrique_index
        self.positions = positions
        self.registre = registre if registre is not None else RegistreAnomalies()
        self.index: Dict[Tuple[str, str], IndexIdentifiants] = {}
        self._dernier: Dict[Tuple[str, str], Optional[str]] = {}
        self.verifiees: Dict[str, int] = {r.nom: 0 for r in self.relations}
        self.orphelines: Dict[str, int] = {r.nom: 0 for r in self.relations}
        self.ignorees: Dict[str, int] = {r.nom: 0 for r in self.relations}
        self._fige = False

        for relation in self.relations:
            if relation.portee == DIFFEREE:
                cle = (relation.type_parent, relation.colonne_parent)
                self.index.setdefault(cle, fabrique_index(f"{cle[0]}.{cle[1]}"))

        # Regroupements pour éviter tout parcours inutile ligne à ligne.
        self._locales: Dict[str, List[Relation]] = {}
        self._differees: Dict[str, List[Relation]] = {}
        self._parents_locaux: Dict[str, List[Tuple[str, str]]] = {}
        self._a_indexer: Dict[str, List[Tuple[str, str]]] = {}
        for relation in self.relations:
            cible = self._locales if relation.portee == LOCALE else self._differees
            cible.setdefault(relation.type_enfant, []).append(relation)
            if relation.portee == LOCALE:
                self._parents_locaux.setdefault(relation.type_parent, []).append(
                    (relation.type_parent, relation.colonne_parent))
            else:
                self._a_indexer.setdefault(relation.type_parent, []).append(
                    (relation.type_parent, relation.colonne_parent))

    # -- passe d'indexation --------------------------------------------------

    def indexer(self, nom_type: str, ligne: Tuple[Any, ...]) -> None:
        """Alimente les index des relations différées. Aucun contrôle."""
        cles = self._a_indexer.get(nom_type)
        if not cles:
            return
        pos = self.positions[nom_type]
        for cle in cles:
            self.index[cle].ajouter(ligne[pos[cle[1]]])

    def figer(self) -> None:
        for index in self.index.values():
            index.figer()
        self._fige = True

    # -- passe de contrôle ---------------------------------------------------

    def controler(self, nom_type: str, ligne: Tuple[Any, ...]) -> None:
        """Vérifie les relations dont cet enregistrement est l'enfant, et
        mémorise le parent des relations locales."""
        pos = self.positions[nom_type]

        for cle in self._parents_locaux.get(nom_type, ()):
            self._dernier[cle] = ligne[pos[cle[1]]]

        for relation in self._locales.get(nom_type, ()):
            reference = ligne[pos[relation.colonne_enfant]]
            if reference is None:
                self.ignorees[relation.nom] += 1
                continue
            self.verifiees[relation.nom] += 1
            attendu = self._dernier.get((relation.type_parent, relation.colonne_parent))
            if reference != attendu:
                self.orphelines[relation.nom] += 1
                self.registre.signaler(
                    "reference_orpheline", relation.gravite,
                    type_enregistrement=relation.nom, detail=str(reference),
                    contexte=f"parent courant {attendu!r}")

        differees = self._differees.get(nom_type)
        if not differees:
            return
        if not self._fige:
            raise ErreurControle(
                f"Relations différées de {nom_type!r} contrôlées avant figement des index")
        for relation in differees:
            reference = ligne[pos[relation.colonne_enfant]]
            if reference is None:
                self.ignorees[relation.nom] += 1
                continue
            self.verifiees[relation.nom] += 1
            if reference not in self.index[(relation.type_parent, relation.colonne_parent)]:
                self.orphelines[relation.nom] += 1
                self.registre.signaler(
                    "reference_orpheline_differee", relation.gravite,
                    type_enregistrement=relation.nom, detail=str(reference))

    # -- restitution ---------------------------------------------------------

    def octets_index(self) -> int:
        """Empreinte des index, si l'implémentation sait la rapporter."""
        return sum(getattr(i, "octets", lambda: 0)() for i in self.index.values())

    def resume(self) -> List[Tuple[str, str, int, int, int]]:
        """(relation, portée, vérifiées, orphelines, non renseignées)."""
        portees = {r.nom: r.portee for r in self.relations}
        return [(nom, portees[nom], self.verifiees[nom], self.orphelines[nom],
                 self.ignorees[nom]) for nom in sorted(self.verifiees)]

    def texte(self) -> str:
        largeur = max([len(r.nom) for r in self.relations] + [8]) + 2
        lignes = [f"{'RELATION':<{largeur}}{'PORTÉE':<11}{'VÉRIFIÉES':>11}"
                  f"{'ORPHELINES':>12}{'NON RENSEIGNÉES':>17}"]
        for nom, portee, verifiees, orphelines, ignorees in self.resume():
            lignes.append(f"{nom:<{largeur}}{portee:<11}{verifiees:>11}{orphelines:>12}"
                          f"{ignorees:>17}")
        detail = []
        for cle, index in sorted(self.index.items()):
            octets = getattr(index, "octets", lambda: 0)()
            part = getattr(index, "part_non_numerique", lambda: None)()
            suffixe = "" if part is None else f" · {part} non numériques"
            detail.append(f"    {cle[0] + '.' + cle[1]:<44} {len(index):>8} identifiants · "
                          f"{octets / 2**20:5.2f} Mio{suffixe}")
        if detail:
            lignes.append("")
            lignes.append(f"Index différés ({self.octets_index() / 2**20:.2f} Mio au total) :")
            lignes.extend(detail)
        return "\n".join(lignes)
