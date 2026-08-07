"""
entrepot.py — Couche 2 (entrepôt), étape F2.

Ouverture de la base, création et reconstruction du schéma, transactions,
vérification de l'intégrité. Ne charge rien : l'écriture des lignes appartient
à `chargement`, étape F3.

PRINCIPE — aucun réglage par convention
----------------------------------------

Chaque réglage SQLite retenu ici renvoie à une mesure de `mesurer_entrepot.py`.
Les valeurs par défaut de SQLite sont conservées partout où la mesure n'a
montré aucune différence décisive : ne pas décider est aussi une décision, et
elle doit être justifiée au même titre.

Mesures fondatrices, banc de 200 000 lignes de la table `evenement`, médiane
sur 5 répétitions, machine de développement :

    journal=delete · synchronous=full     0,79 s   (défaut SQLite)
    journal=delete · synchronous=normal   0,81 s
    journal=wal    · synchronous=full     0,86 s
    journal=wal    · synchronous=normal   0,91 s
    journal=off    · synchronous=off      0,73 s

L'écart entre le plus rapide et le plus lent est de 12 %, et le mode par défaut
figure parmi les plus rapides. La première campagne, non répétée, avait donné
1,40 s pour delete/full et désigné wal/normal comme meilleur choix : c'était un
artefact de cache froid. C'est la répétition qui l'a révélé.

AVERTISSEMENT — ces mesures proviennent d'une machine de développement, sur
stockage rapide. Sur Termux, `synchronous=FULL` est susceptible de coûter bien
davantage, et le mode WAL peut échouer selon le système de fichiers. Toute
dérogation aux défauts devra être fondée sur une mesure refaite sur l'appareil
cible, non sur celles-ci.

DEUX CONSTATS FONCTIONNELS ÉTABLIS EN F2
-----------------------------------------

1. **`PRAGMA foreign_keys` est silencieusement ignoré à l'intérieur d'une
   transaction.** Un premier essai a vu un enregistrement orphelin accepté
   alors que les contraintes étaient réputées actives. Le réglage est donc posé
   à l'ouverture, avant toute instruction, puis **relu pour vérification** ;
   une divergence est une erreur.

2. **L'ordre du document de la couche 1 n'est pas un ordre d'insertion
   valide.** Les groupements précèdent les entités juridiques dans le flux,
   alors que `groupement_membre.id_membre` les référence. Contraintes actives,
   l'insertion est rejetée. Vérifié : charger contraintes désactivées puis
   exécuter `PRAGMA foreign_key_check` donne la même garantie sans imposer
   d'ordre, et détecte bien un orphelin réel. C'est la stratégie retenue, et
   elle prolonge celle déjà adoptée pour les cinq contrôles après chargement.

Aucune dépendance tierce. Compatible Python 3.9+.
"""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from schema import (ARTEFACT, BESOIN, MESURE, Justification, Schema, SCHEMA,
                    ErreurSchema)

__all__ = ["Reglage", "REGLAGES_DEFAUT", "REGLAGES_CHARGEMENT", "Entrepot",
           "ErreurEntrepot"]

_BANC = "mesurer_entrepot.py, banc de 200 000 lignes, médiane sur 5 répétitions"
_F2 = "étape F2, essais d'ordre d'insertion et de prise en compte des PRAGMA"


class ErreurEntrepot(Exception):
    """Base absente, schéma incohérent, ou réglage non appliqué."""


class Reglage:
    """Un PRAGMA, sa valeur, et le motif de cette valeur.

    `verifier` indique que la valeur effective doit être relue après
    application : c'est le seul moyen de détecter un PRAGMA ignoré.
    """

    __slots__ = ("nom", "valeur", "justification", "verifier", "attendu")

    def __init__(self, nom: str, valeur: object, justification: Justification,
                 verifier: bool = False, attendu: object = None) -> None:
        if not isinstance(justification, Justification):
            raise ErreurEntrepot(f"Réglage {nom!r} sans justification")
        self.nom = nom
        self.valeur = valeur
        self.justification = justification
        self.verifier = verifier
        self.attendu = attendu if attendu is not None else valeur


_JUSTIFICATION_DEFAUTS = Justification(
    MESURE,
    "Aucune différence décisive mesurée entre les modes de journalisation et de "
    "synchronisation : 0,73 s à 0,91 s sur 200 000 lignes, soit 12 % d'écart, "
    "le mode par défaut figurant parmi les plus rapides. Les défauts de SQLite "
    "sont donc conservés, faute de justification pour s'en écarter. La mesure "
    "devra être refaite sur Termux avant toute dérogation",
    _BANC)

REGLAGES_DEFAUT: Tuple[Reglage, ...] = (
    Reglage("foreign_keys", "ON",
            Justification(
                ARTEFACT,
                "Le schéma déclare 14 clés étrangères, justifiées par 3 687 802 "
                "rattachements vérifiés sans orphelin. SQLite ne les applique pas "
                "par défaut : sans ce réglage, elles seraient décoratives",
                "DECISIONS_SCHEMA.md"),
            verifier=True, attendu=1),
)

REGLAGES_CHARGEMENT: Tuple[Reglage, ...] = (
    Reglage("foreign_keys", "OFF",
            Justification(
                ARTEFACT,
                "L'ordre du document de la couche 1 n'est pas un ordre "
                "d'insertion valide : les groupements précèdent les entités "
                "juridiques qu'ils référencent, et l'insertion est rejetée "
                "contraintes actives. La vérification différée par "
                "PRAGMA foreign_key_check donne la même garantie sans imposer "
                "d'ordre, ce qui a été vérifié, y compris sur un orphelin réel",
                _F2),
            verifier=True, attendu=0),
)


class Entrepot:
    """Une base SQLite portant le schéma du pivot."""

    def __init__(self, chemin: Path, schema: Schema = SCHEMA,
                 reglages: Sequence[Reglage] = REGLAGES_DEFAUT) -> None:
        self.chemin = Path(chemin)
        self.schema = schema
        self.reglages = tuple(reglages)
        self.connexion: Optional[sqlite3.Connection] = None
        self.reglages_effectifs: Dict[str, object] = {}

    # -- cycle de vie --------------------------------------------------------

    def ouvrir(self, creer_si_absent: bool = False) -> "Entrepot":
        if not creer_si_absent and not self.chemin.exists():
            raise ErreurEntrepot(f"Base absente : {self.chemin}")
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        # isolation_level=None : aucune transaction implicite, sans quoi les
        # PRAGMA seraient posés à l'intérieur d'une transaction et ignorés.
        self.connexion = sqlite3.connect(self.chemin, isolation_level=None)
        self._appliquer_reglages()
        return self

    def _appliquer_reglages(self) -> None:
        assert self.connexion is not None
        for reglage in self.reglages:
            self.connexion.execute(f"PRAGMA {reglage.nom}={reglage.valeur}")
        for reglage in self.reglages:
            effectif = list(self.connexion.execute(f"PRAGMA {reglage.nom}"))
            valeur = effectif[0][0] if effectif else None
            self.reglages_effectifs[reglage.nom] = valeur
            if reglage.verifier and valeur != reglage.attendu:
                raise ErreurEntrepot(
                    f"PRAGMA {reglage.nom} demandé à {reglage.valeur!r} mais relu "
                    f"à {valeur!r}. Un PRAGMA posé dans une transaction est "
                    f"silencieusement ignoré")

    def fermer(self) -> None:
        if self.connexion is not None:
            self.connexion.close()
            self.connexion = None

    def __enter__(self) -> "Entrepot":
        if self.connexion is None:
            self.ouvrir(creer_si_absent=True)
        return self

    def __exit__(self, *_exception) -> None:
        self.fermer()

    def _requiert_connexion(self) -> sqlite3.Connection:
        if self.connexion is None:
            raise ErreurEntrepot("Base non ouverte")
        return self.connexion

    # -- création et reconstruction -----------------------------------------

    def creer(self, ecraser: bool = False) -> None:
        """Crée le schéma. Refuse d'écraser une base existante sans consigne."""
        if self.chemin.exists() and self.tables_existantes() and not ecraser:
            raise ErreurEntrepot(
                f"{self.chemin} porte déjà un schéma. Utiliser ecraser=True "
                f"ou reconstruire()")
        connexion = self._requiert_connexion()
        if ecraser:
            self._supprimer_tables()
        connexion.executescript(self.schema.ddl())

    def reconstruire(self) -> None:
        """Supprime toutes les tables du schéma et les recrée, à vide."""
        self._supprimer_tables()
        self._requiert_connexion().executescript(self.schema.ddl())

    def _supprimer_tables(self) -> None:
        connexion = self._requiert_connexion()
        # Les clés étrangères empêchent la suppression dans un ordre quelconque.
        connexion.execute("PRAGMA foreign_keys=OFF")
        for table in reversed(self.schema.tables):
            connexion.execute(f"DROP TABLE IF EXISTS {table.nom}")
        self._appliquer_reglages()

    def tables_existantes(self) -> List[str]:
        connexion = self._requiert_connexion()
        return [r[0] for r in connexion.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name")]

    def schema_conforme(self) -> Tuple[bool, List[str]]:
        """Le schéma en base correspond-il aux déclarations ?"""
        ecarts = []
        attendues = {t.nom: t for t in self.schema.tables}
        presentes = set(self.tables_existantes())
        for nom in sorted(set(attendues) - presentes):
            ecarts.append(f"table absente : {nom}")
        for nom in sorted(presentes - set(attendues)):
            ecarts.append(f"table hors schéma : {nom}")
        connexion = self._requiert_connexion()
        for nom in sorted(set(attendues) & presentes):
            colonnes = [r[1] for r in connexion.execute(f"PRAGMA table_info({nom})")]
            if tuple(colonnes) != attendues[nom].colonnes:
                ecarts.append(
                    f"{nom} : colonnes {colonnes} au lieu de "
                    f"{list(attendues[nom].colonnes)}")
        return (not ecarts), ecarts

    # -- transactions --------------------------------------------------------

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Transaction explicite : validée à la sortie, annulée sur exception."""
        connexion = self._requiert_connexion()
        connexion.execute("BEGIN")
        try:
            yield connexion
        except BaseException:
            connexion.execute("ROLLBACK")
            raise
        else:
            connexion.execute("COMMIT")

    @contextmanager
    def reglages_temporaires(self, reglages: Sequence[Reglage]) -> Iterator[None]:
        """Applique des réglages le temps d'un bloc, puis rétablit les nominaux.

        Sert au chargement, qui exige `foreign_keys=OFF`.
        """
        anciens = self.reglages
        self.reglages = tuple(reglages)
        self._appliquer_reglages()
        try:
            yield
        finally:
            self.reglages = anciens
            self._appliquer_reglages()

    # -- vérification --------------------------------------------------------

    def verifier_integrite(self) -> Dict[str, object]:
        """Contrôles natifs de SQLite : cohérence interne et clés étrangères."""
        connexion = self._requiert_connexion()
        debut = time.time()
        integrite = [r[0] for r in connexion.execute("PRAGMA integrity_check")]
        violations = [
            {"table": r[0], "rowid": r[1], "cible": r[2], "clef": r[3]}
            for r in connexion.execute("PRAGMA foreign_key_check")]
        return {
            "integrite": integrite,
            "integrite_ok": integrite == ["ok"],
            "violations_cles_etrangeres": violations,
            "duree_s": time.time() - debut,
        }

    def executer_controles(self) -> List[Dict[str, object]]:
        """Exécute les contrôles après chargement déclarés par le schéma.

        Ce sont les propriétés que SQL ne peut pas déclarer : rattachements
        polymorphes, et clé étrangère visant une colonne non unique. Chaque
        contrôle porte son motif de non-déclarabilité dans le schéma. Une
        propriété déclarée mais jamais vérifiée n'est pas une garantie.
        """
        connexion = self._requiert_connexion()
        resultats = []
        for table, controle in self.schema.controles():
            debut = time.time()
            lignes = list(connexion.execute(controle.requete))
            # La requête compte les lignes fautives : soit un total, soit un
            # décompte par type de porteur.
            anomalies = sum(int(r[-1]) for r in lignes) if lignes else 0
            resultats.append({
                "nom": controle.nom,
                "table": table,
                "anomalies": anomalies,
                "detail": lignes if anomalies else [],
                "duree_s": time.time() - debut,
            })
        return resultats

    # -- observation ---------------------------------------------------------

    def compter(self) -> Dict[str, int]:
        connexion = self._requiert_connexion()
        return {t.nom: list(connexion.execute(f"SELECT COUNT(*) FROM {t.nom}"))[0][0]
                for t in self.schema.tables}

    def etat(self) -> Dict[str, object]:
        """Ce que porte l'entrepôt : lots, sources, millésime, et cohérence.

        Ne juge pas de la complétude — savoir quelles sources sont attendues
        n'appartient pas à l'entrepôt, qui ignore tout de FINESS. Il constate
        et signale l'incohérence.
        """
        connexion = self._requiert_connexion()
        if "entete" not in self.tables_existantes():
            return {"lots": [], "millesimes": [], "sources": [], "coherent": False,
                    "motifs": ["table entete absente"]}
        lots = [
            {"id_lot": r[0], "source": r[1], "millesime": r[2],
             "schema_version": r[3], "genere_le": r[4], "fichier": r[5],
             "empreinte": r[6]}
            for r in connexion.execute(
                "SELECT id_lot, source, millesime, schema_version, genere_le, "
                "nom_fichier, empreinte FROM entete ORDER BY source")]
        millesimes = sorted({l["millesime"] for l in lots})
        sources = sorted(l["source"] for l in lots)
        motifs = []
        if len(millesimes) > 1:
            motifs.append(f"plusieurs millésimes présents : {millesimes}")
        doublons = sorted({s for s in sources if sources.count(s) > 1})
        if doublons:
            motifs.append(f"sources chargées plusieurs fois : {doublons}")
        return {"lots": lots, "millesimes": millesimes, "sources": sources,
                "coherent": not motifs, "motifs": motifs}

    def octets(self) -> int:
        total = self.chemin.stat().st_size if self.chemin.exists() else 0
        for suffixe in ("-wal", "-shm", "-journal"):
            annexe = Path(str(self.chemin) + suffixe)
            if annexe.exists():
                total += annexe.stat().st_size
        return total

    def rapport(self) -> str:
        comptes = self.compter()
        lignes = [
            f"Base       : {self.chemin} ({self.octets() / 2**20:.1f} Mio)",
            f"Réglages   : " + ", ".join(
                f"{n}={v}" for n, v in sorted(self.reglages_effectifs.items())),
            f"Lignes     : {sum(comptes.values())}",
        ]
        for nom, n in sorted(comptes.items(), key=lambda x: -x[1]):
            if n:
                lignes.append(f"    {nom:<30}{n:>10}")
        etat = self.etat()
        if etat["lots"]:
            lignes.append(
                f"Millésime  : {', '.join(etat['millesimes'])} · sources "
                f"{', '.join(etat['sources'])}"
                + ("" if etat["coherent"] else "  ** INCOHÉRENT **"))
            for motif in etat["motifs"]:
                lignes.append(f"    {motif}")
        conforme, ecarts = self.schema_conforme()
        lignes.append(f"Schéma     : {'conforme' if conforme else 'NON CONFORME'}")
        for ecart in ecarts:
            lignes.append(f"    {ecart}")
        return "\n".join(lignes)


if __name__ == "__main__":
    import argparse

    analyseur = argparse.ArgumentParser(description="Entrepôt de la couche 2.")
    analyseur.add_argument("base", type=Path)
    analyseur.add_argument("--creer", action="store_true")
    analyseur.add_argument("--reconstruire", action="store_true")
    analyseur.add_argument("--verifier", action="store_true")
    arguments = analyseur.parse_args()

    with Entrepot(arguments.base) as entrepot:
        if arguments.creer:
            entrepot.creer(ecraser=False)
            print("Schéma créé.")
        if arguments.reconstruire:
            entrepot.reconstruire()
            print("Schéma reconstruit, tables vidées.")
        print(entrepot.rapport())
        if arguments.verifier:
            resultat = entrepot.verifier_integrite()
            print(f"Intégrité  : {'ok' if resultat['integrite_ok'] else resultat['integrite']}"
                  f" · {len(resultat['violations_cles_etrangeres'])} violation(s) de clé "
                  f"étrangère · {resultat['duree_s']:.2f} s")
