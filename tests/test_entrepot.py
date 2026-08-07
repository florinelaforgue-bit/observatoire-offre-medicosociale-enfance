"""test_entrepot.py — Critère de sortie de F2."""
from __future__ import annotations
import sqlite3, sys
from pathlib import Path

import schema
from entrepot import (Entrepot, ErreurEntrepot, Reglage, REGLAGES_CHARGEMENT,
                      REGLAGES_DEFAUT)

BASE = Path("/tmp/tests_entrepot"); BASE.mkdir(exist_ok=True)
ok = ko = 0

def verifier(intitule, condition, detail=""):
    global ok, ko
    if condition: ok += 1; print(f"  OK    {intitule}")
    else: ko += 1; print(f"  ECHEC {intitule} — {detail}")

def neuve(nom="e.db"):
    chemin = BASE / nom
    for suffixe in ("", "-wal", "-shm", "-journal"):
        p = Path(str(chemin) + suffixe)
        if p.exists(): p.unlink()
    return chemin

LOT = ("l:202607:0000", "finess_structures", "202607", "v1.0.0", None, "f", "e", "1")
EJ = ("010008400", "100", "A", "A LONGUE", None, None, "60", "1", None, None,
      None, None, "1980-01-01", None, "A", "2026-01-01", LOT[0])
ET = ("010000020", "G0", "010008400", "100", "IME", "IME LONG", None, "183", None,
      None, None, None, "01", "01", "1990-01-01", None, None, "A", "2026-01-01", LOT[0])

print("1. Création et cycle de vie")
chemin = neuve()
with Entrepot(chemin) as e:
    e.creer()
    verifier("16 tables créées", len(e.tables_existantes()) == 16, e.tables_existantes())
    conforme, ecarts = e.schema_conforme()
    verifier("schéma conforme aux déclarations", conforme, ecarts)
    verifier("toutes les tables sont vides", sum(e.compter().values()) == 0)
verifier("fermeture propre", True)

with Entrepot(chemin) as e:
    try:
        e.creer(); verifier("refus d'écraser un schéma existant", False)
    except ErreurEntrepot: verifier("refus d'écraser un schéma existant", True)

try:
    Entrepot(neuve("absente.db")).ouvrir(creer_si_absent=False)
    verifier("refus d'ouvrir une base absente", False)
except ErreurEntrepot: verifier("refus d'ouvrir une base absente", True)

print("2. Réglages : appliqués, relus, vérifiés")
with Entrepot(chemin) as e:
    verifier("foreign_keys actif et relu à 1", e.reglages_effectifs["foreign_keys"] == 1,
             e.reglages_effectifs)
    with e.reglages_temporaires(REGLAGES_CHARGEMENT):
        verifier("désactivation temporaire effective",
                 e.reglages_effectifs["foreign_keys"] == 0)
    verifier("réglage nominal rétabli en sortie de bloc",
             e.reglages_effectifs["foreign_keys"] == 1)

faux = Reglage("foreign_keys", "ON", schema.REGLE_TYPE_DEFAUT, verifier=True, attendu=99)
try:
    Entrepot(chemin, reglages=(faux,)).ouvrir()
    verifier("réglage non appliqué → erreur", False)
except ErreurEntrepot: verifier("réglage non appliqué → erreur", True)
try:
    Reglage("x", "1", "pas une justification")
    verifier("réglage sans justification refusé", False)
except ErreurEntrepot: verifier("réglage sans justification refusé", True)

print("3. Contraintes réellement appliquées")
chemin = neuve("c.db")
with Entrepot(chemin) as e:
    e.creer()
    with e.transaction() as c:
        c.execute("INSERT INTO entete VALUES (?,?,?,?,?,?,?,?)", LOT)
        c.execute("INSERT INTO entite_juridique VALUES (" + ",".join("?"*17) + ")", EJ)
    try:
        with e.transaction() as c:
            c.execute("INSERT INTO etablissement VALUES (" + ",".join("?"*20) + ")",
                      ET[:2] + ("INEXISTANTE",) + ET[3:])
        verifier("clé étrangère violée → rejet", False)
    except sqlite3.IntegrityError: verifier("clé étrangère violée → rejet", True)
    try:
        with e.transaction() as c:
            c.execute("INSERT INTO entite_juridique VALUES (" + ",".join("?"*17) + ")", EJ)
        verifier("clé primaire dupliquée → rejet", False)
    except sqlite3.IntegrityError: verifier("clé primaire dupliquée → rejet", True)
    try:
        with e.transaction() as c:
            c.execute("INSERT INTO entite_juridique VALUES (" + ",".join("?"*17) + ")",
                      ("010008401", "100") + EJ[2:])
        verifier("contrainte d'unicité violée → rejet", False)
    except sqlite3.IntegrityError: verifier("contrainte d'unicité violée → rejet", True)
    try:
        with e.transaction() as c:
            c.execute("INSERT INTO entite_juridique VALUES (" + ",".join("?"*17) + ")",
                      ("010008402", "101", None) + EJ[3:])
        verifier("NOT NULL violé → rejet", False)
    except sqlite3.IntegrityError: verifier("NOT NULL violé → rejet", True)

print("4. Transactions")
with Entrepot(chemin) as e:
    avant = e.compter()["etablissement"]
    try:
        with e.transaction() as c:
            c.execute("INSERT INTO etablissement VALUES (" + ",".join("?"*20) + ")", ET)
            raise RuntimeError("panne simulée")
    except RuntimeError: pass
    verifier("annulation sur exception", e.compter()["etablissement"] == avant)
    with e.transaction() as c:
        c.execute("INSERT INTO etablissement VALUES (" + ",".join("?"*20) + ")", ET)
    verifier("validation en sortie de bloc", e.compter()["etablissement"] == avant + 1)

print("5. Chargement hors ordre, puis vérification différée")
chemin = neuve("o.db")
with Entrepot(chemin) as e:
    e.creer()
    with e.reglages_temporaires(REGLAGES_CHARGEMENT):
        with e.transaction() as c:
            c.execute("INSERT INTO entete VALUES (?,?,?,?,?,?,?,?)", LOT)
            c.execute("INSERT INTO groupement VALUES (?,?,?,?,?,?,?,?)",
                      ("GCC", "G1", None, None, "001", "A", "2026-01-01", LOT[0]))
            c.execute("INSERT INTO groupement_membre VALUES (?,?,?,?,?,?,?)",
                      ("G1", "GCC", "EJ", "100", "M", "0", LOT[0]))
        resultat = e.verifier_integrite()
        verifier("parent manquant détecté par la vérification différée",
                 len(resultat["violations_cles_etrangeres"]) == 1,
                 resultat["violations_cles_etrangeres"])
        with e.transaction() as c:
            c.execute("INSERT INTO entite_juridique VALUES (" + ",".join("?"*17) + ")", EJ)
        resultat = e.verifier_integrite()
        verifier("plus aucune violation une fois le parent arrivé",
                 not resultat["violations_cles_etrangeres"])
    verifier("intégrité interne de la base", e.verifier_integrite()["integrite_ok"])

print("6. Reconstruction")
with Entrepot(chemin) as e:
    verifier("données présentes avant reconstruction", sum(e.compter().values()) > 0)
    e.reconstruire()
    verifier("tables vidées", sum(e.compter().values()) == 0)
    verifier("schéma toujours conforme", e.schema_conforme()[0])
    verifier("contraintes rétablies après reconstruction",
             e.reglages_effectifs["foreign_keys"] == 1)

print("7. Détection d'un schéma divergent")
chemin = neuve("d.db")
with Entrepot(chemin) as e:
    e.creer()
    e.connexion.execute("DROP TABLE appareil")
    conforme, ecarts = e.schema_conforme()
    verifier("table manquante détectée", not conforme and any("appareil" in x for x in ecarts),
             ecarts)
    e.connexion.execute("CREATE TABLE intruse (a TEXT)")
    verifier("table hors schéma détectée",
             any("intruse" in x for x in e.schema_conforme()[1]))

print("8. Contrôles après chargement déclarés par le schéma")
chemin = neuve("k.db")
with Entrepot(chemin) as e:
    e.creer()
    resultats = e.executer_controles()
    verifier("les cinq contrôles déclarés sont exécutés", len(resultats) == 5,
             [r["nom"] for r in resultats])
    verifier("base vide → aucune anomalie",
             all(r["anomalies"] == 0 for r in resultats), resultats)
    with e.reglages_temporaires(REGLAGES_CHARGEMENT):
        with e.transaction() as c:
            c.execute("INSERT INTO entete VALUES (?,?,?,?,?,?,?,?)", LOT)
            # Contact rattaché à un établissement inexistant : la relation étant
            # polymorphe, elle n'est pas déclarable et SQL ne la voit pas.
            c.execute("INSERT INTO contact VALUES (?,?,?,?,?,?,?,?,?)",
                      ("ET", "FANTOME", "010000020", "0", "01", "0474000000",
                       None, None, LOT[0]))
    verifier("aucune violation vue par SQL, la relation n'étant pas déclarable",
             not e.verifier_integrite()["violations_cles_etrangeres"])
    resultats = {r["nom"]: r for r in e.executer_controles()}
    verifier("le contrôle déclaré, lui, détecte le rattachement orphelin",
             resultats["contact_porteur_existe"]["anomalies"] == 1,
             resultats["contact_porteur_existe"])
    verifier("les autres contrôles restent au vert",
             sum(r["anomalies"] for n, r in resultats.items()
                 if n != "contact_porteur_existe") == 0)

print(f"\n{ok} tests réussis, {ko} échecs")
sys.exit(1 if ko else 0)
