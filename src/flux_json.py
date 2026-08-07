"""
flux_json.py — Couche 1 (acquisition). Version de référence gelée, E1.

Lecture incrémentale d'un document JSON volumineux dont la racine est un objet
contenant un ou plusieurs tableaux (structure des flux FINESS mensuels).

Ce module est gelé. Toute reprise ultérieure doit repasser l'intégralité de
test_flux_json.py et de preuve_exhaustivite.py sur les deux fichiers réels.
Optimisation reportée et consignée : dans decoder(), l'agrandissement du tampon
procède par doublement, ce qui porte le tampon à 16-18 Mio pour un
enregistrement de 9,86 Mio. À réévaluer seulement si le budget mémoire devient
contraignant.

Principe retenu : `json.JSONDecoder.raw_decode` sur un tampon glissant.
Le décodeur standard, écrit en C, décode une valeur complète à la fois ; le
tampon est rempli à la demande et compacté régulièrement. Le module est donc :

- indifférent à la mise en forme du producteur (indenté ou minifié) ;
- correct sur les échappements et l'Unicode, puisque c'est le décodeur
  standard qui les traite (985 séquences \\" et 159 \\\\ mesurées dans les
  304 premiers Mio du fichier structures) ;
- à mémoire bornée : un seul enregistrement racine est matérialisé à la fois ;
- sans aucune dépendance tierce (gzip, json, pathlib, time), donc utilisable
  sous Termux.

Le module ne connaît rien de FINESS. Il ne fait que découper.

Compatible Python 3.9+.
"""

from __future__ import annotations

import gzip
import json
import time
from pathlib import Path
from typing import Any, Iterator, Tuple

__all__ = ["Compteurs", "ouvrir", "parcourir", "ErreurFluxJson"]

# Clé conventionnelle sous laquelle sont émises les valeurs scalaires de
# l'objet racine (schemaVersion, generatedAt).
CLE_ENTETE = "__entete__"

TAILLE_BLOC_DEFAUT = 1 << 18        # 256 Kio : optimum mesuré
SEUIL_COMPACTAGE_DEFAUT = 1 << 18   # compactage du tampon au-delà de 256 Kio
_ESPACES = " \t\r\n"


class ErreurFluxJson(Exception):
    """Document illisible, tronqué ou de forme inattendue."""


class Compteurs:
    """Compteurs d'un parcours. Renseignés au fil de l'eau, lisibles à la fin."""

    __slots__ = ("caracteres_lus", "objets_par_cle", "entetes",
                 "taille_max_enregistrement", "cle_taille_max",
                 "tampon_max", "duree_s", "termine")

    def __init__(self) -> None:
        self.caracteres_lus = 0
        self.objets_par_cle: dict[str, int] = {}
        self.entetes: dict[str, Any] = {}
        self.taille_max_enregistrement = 0
        self.cle_taille_max = ""
        self.tampon_max = 0
        self.duree_s = 0.0
        self.termine = False

    def total_objets(self) -> int:
        return sum(self.objets_par_cle.values())

    def resume(self) -> str:
        objets = ", ".join(f"{c}={n}" for c, n in self.objets_par_cle.items())
        return (f"{self.caracteres_lus / 2**20:.0f} Mio lus | {objets} | "
                f"enregistrement max {self.taille_max_enregistrement / 2**20:.2f} Mio "
                f"({self.cle_taille_max}) | tampon max {self.tampon_max / 1024:.0f} Kio | "
                f"{self.duree_s:.1f} s | terminé={self.termine}")


def ouvrir(chemin: Path):
    """Ouvre le fichier en texte UTF-8, en décompressant si nécessaire.

    La détection se fait sur le nombre magique gzip, pas sur l'extension.
    Aucune détection d'encodage : JSON est UTF-8 par spécification (RFC 8259).
    """
    chemin = Path(chemin)
    if not chemin.exists():
        raise ErreurFluxJson(f"Fichier introuvable : {chemin}")
    with open(chemin, "rb") as brut:
        magique = brut.read(2)
    if magique == b"\x1f\x8b":
        return gzip.open(chemin, "rt", encoding="utf-8")
    return open(chemin, "r", encoding="utf-8")


def parcourir(
    chemin: Path,
    taille_bloc: int = TAILLE_BLOC_DEFAUT,
    seuil_compactage: int = SEUIL_COMPACTAGE_DEFAUT,
    compteurs: Compteurs | None = None,
) -> Iterator[Tuple[str, int, Any]]:
    """Parcourt le document et émet ses valeurs une par une, dans l'ordre.

    Émet des triplets (cle_racine, rang, valeur) :
      - (CLE_ENTETE, rang, (nom, valeur))  pour chaque valeur scalaire racine ;
      - (nom_du_tableau, rang, objet)      pour chaque élément de tableau racine.

    Le rang est l'indice de l'élément dans son propre tableau, à partir de 0.
    Aucune collection complète n'est jamais construite.
    """
    cpt = compteurs if compteurs is not None else Compteurs()
    decodeur = json.JSONDecoder()
    depart = time.time()

    with ouvrir(chemin) as fichier:
        tampon = ""
        pos = 0

        def remplir(taille: int = taille_bloc) -> bool:
            """Ajoute un bloc au tampon. Retourne False en fin de fichier."""
            nonlocal tampon
            bloc = fichier.read(taille)
            if not bloc:
                return False
            cpt.caracteres_lus += len(bloc)
            tampon += bloc
            if len(tampon) > cpt.tampon_max:
                cpt.tampon_max = len(tampon)
            return True

        def avancer(caracteres: str) -> bool:
            """Saute les caractères indiqués. False si fin de fichier atteinte."""
            nonlocal pos
            while True:
                while pos < len(tampon) and tampon[pos] in caracteres:
                    pos += 1
                if pos < len(tampon):
                    return True
                if not remplir():
                    return False

        def decoder(depuis: int) -> Tuple[Any, int]:
            """Décode une valeur complète, en agrandissant le tampon si besoin."""
            taille = taille_bloc
            while True:
                try:
                    return decodeur.raw_decode(tampon, depuis)
                except ValueError as erreur:
                    if not remplir(taille):
                        raise ErreurFluxJson(
                            f"{Path(chemin).name} : document tronqué ou invalide "
                            f"vers le caractère {cpt.caracteres_lus} ({erreur})"
                        ) from erreur
                    taille = min(taille * 2, 1 << 24)

        # --- entrée dans l'objet racine -----------------------------------
        if not avancer(_ESPACES):
            raise ErreurFluxJson(f"{Path(chemin).name} : document vide")
        if tampon[pos] != "{":
            raise ErreurFluxJson(
                f"{Path(chemin).name} : la racine doit être un objet, "
                f"trouvé {tampon[pos]!r}"
            )
        pos += 1

        rang_entete = 0
        while True:
            if not avancer(_ESPACES + ","):
                raise ErreurFluxJson(f"{Path(chemin).name} : objet racine non refermé")
            if tampon[pos] == "}":
                pos += 1
                break

            nom, pos = decoder(pos)
            if not isinstance(nom, str):
                raise ErreurFluxJson(f"{Path(chemin).name} : clé racine non textuelle")
            if not avancer(_ESPACES + ":"):
                raise ErreurFluxJson(f"{Path(chemin).name} : clé {nom!r} sans valeur")

            # --- valeur scalaire ou objet : émise telle quelle -------------
            if tampon[pos] != "[":
                valeur, pos = decoder(pos)
                cpt.entetes[nom] = valeur
                yield (CLE_ENTETE, rang_entete, (nom, valeur))
                rang_entete += 1
                continue

            # --- tableau : émission élément par élément --------------------
            pos += 1
            cpt.objets_par_cle.setdefault(nom, 0)
            rang = 0
            while True:
                if not avancer(_ESPACES + ","):
                    raise ErreurFluxJson(f"{Path(chemin).name} : tableau {nom!r} non refermé")
                if tampon[pos] == "]":
                    pos += 1
                    break
                debut = pos
                element, pos = decoder(pos)
                taille = pos - debut
                if taille > cpt.taille_max_enregistrement:
                    cpt.taille_max_enregistrement = taille
                    cpt.cle_taille_max = nom
                cpt.objets_par_cle[nom] += 1
                yield (nom, rang, element)
                rang += 1
                if pos > seuil_compactage:
                    tampon = tampon[pos:]
                    pos = 0

        # --- vérification de fin de document ------------------------------
        reste = tampon[pos:].strip()
        while not reste:
            bloc = fichier.read(taille_bloc)
            if not bloc:
                break
            cpt.caracteres_lus += len(bloc)
            reste = bloc.strip()
        if reste:
            raise ErreurFluxJson(
                f"{Path(chemin).name} : contenu inattendu après l'objet racine "
                f"({reste[:40]!r})"
            )

    cpt.termine = True
    cpt.duree_s = time.time() - depart


# ---------------------------------------------------------------------------
# Inspection en ligne de commande (provisoire, sera reprise par la CLI)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import resource

    analyseur = argparse.ArgumentParser(description="Inspection d'un flux JSON volumineux.")
    analyseur.add_argument("fichier", type=Path)
    analyseur.add_argument("--bloc", type=int, default=TAILLE_BLOC_DEFAUT)
    analyseur.add_argument("--compactage", type=int, default=SEUIL_COMPACTAGE_DEFAUT)
    arguments = analyseur.parse_args()

    compteurs = Compteurs()
    for cle, rang, valeur in parcourir(
        arguments.fichier,
        taille_bloc=arguments.bloc,
        seuil_compactage=arguments.compactage,
        compteurs=compteurs,
    ):
        pass

    pic = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(f"Fichier   : {arguments.fichier.name}")
    print(f"En-tête   : {compteurs.entetes}")
    print(f"Parcours  : {compteurs.resume()}")
    print(f"RSS max   : {pic:.1f} Mio")
