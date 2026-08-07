"""Equivalence et cout de la migration des controles d'integrite vers SQL (F5).

Compare, sur les MEMES donnees, ce que detecte la verification en Python de la
couche 1 (etape E6) et ce que detecte la verification en SQL de la couche 2.
"""
import gzip, json, shutil, sys, time
from pathlib import Path

from contrat_source import CONTROLE_MINIMAL
from entrepot import Entrepot
from chargement import charger
from finess_structures import SourceFinessStructures
from finess_activites import SourceFinessActivites
import finess_commun as fc
from controles import VerificateurRelations
from contrat_source import (InventaireCodes, Lot, RapportIngestion,
                            RegistreAnomalies, parcourir_source)

BANC = Path("/tmp/f5"); BANC.mkdir(exist_ok=True)

def positions():
    return {t.nom: {c: i for i, c in enumerate(t.noms)} for t in fc.TOUS_LES_TYPES}

def verification_python(structures, activites):
    """Reproduit la commande `cli.py integrite` : trois passes en Python."""
    registre = RegistreAnomalies()
    v = VerificateurRelations(fc.RELATIONS_PIVOT, positions(), registre)
    depart = time.time()
    def passe(source, chemin, action):
        rap = RapportIngestion(Lot("","","","",0), RegistreAnomalies(),
                               InventaireCodes(), CONTROLE_MINIMAL)
        for nom, ligne in parcourir_source(source, chemin, controle=CONTROLE_MINIMAL,
                                           rapport=rap, inventorier_codes=False):
            action(nom, ligne)
    passe(SourceFinessStructures(), structures, v.indexer)
    v.figer()
    passe(SourceFinessStructures(), structures, v.controler)
    passe(SourceFinessActivites(), activites, v.controler)
    orphelines = {nom: n for nom, n in v.orphelines.items() if n}
    return time.time() - depart, orphelines, v.octets_index()

def verification_sql(base, structures, activites):
    """Verification par le SQL de la couche 2 : cles etrangeres et controles."""
    for s in ("", "-wal", "-shm", "-journal"):
        p = Path(str(base) + s)
        if p.exists(): p.unlink()
    with Entrepot(base) as e:
        e.creer(ecraser=True)
        for source, chemin in ((SourceFinessStructures(), structures),
                               (SourceFinessActivites(), activites)):
            charger(e, source, chemin, controle=CONTROLE_MINIMAL, verifier_apres=False)
        depart = time.time()
        integrite = e.verifier_integrite()
        controles = e.executer_controles()
        duree = time.time() - depart
        orphelines = {}
        for v in integrite["violations_cles_etrangeres"]:
            cle = f"{v['table']} -> {v['cible']}"
            orphelines[cle] = orphelines.get(cle, 0) + 1
        for c in controles:
            if c["anomalies"]:
                orphelines[c["nom"]] = c["anomalies"]
        octets = e.octets()
    return duree, orphelines, octets

def corrompre(structures, sortie, cible, remplacement):
    """Casse une reference dans le fichier structures, sans rien d'autre changer."""
    with gzip.open(structures, "rt", encoding="utf-8") as f:
        document = json.load(f)
    document["gcc"][0]["pmejDuGcc"][0]["pmSmsseId"] = remplacement
    with gzip.open(sortie, "wt", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False)
    return sortie

if __name__ == "__main__":
    structures, activites = Path(sys.argv[1]), Path(sys.argv[2])
    print("=== Données intactes ===")
    dp, op, iop = verification_python(structures, activites)
    ds, os_, ios = verification_sql(BANC / "sain.db", structures, activites)
    print(f"  Python (E6) : {dp:6.2f} s · {len(op)} relation(s) en défaut · "
          f"index {iop/2**20:.2f} Mio")
    print(f"  SQL (F5)    : {ds:6.2f} s · {len(os_)} relation(s) en défaut · "
          f"base {ios/2**20:.1f} Mio")
    print(f"  Même verdict : {bool(op) == bool(os_)}")

    print("\n=== Une référence délibérément cassée ===")
    casse = corrompre(structures, BANC / "finess-structures-mensuel-202607-casse_json.gz",
                      None, "PM_INEXISTANTE")
    dp, op, _ = verification_python(casse, activites)
    ds, os_, _ = verification_sql(BANC / "casse.db", casse, activites)
    print(f"  Python (E6) : {dp:6.2f} s · {op}")
    print(f"  SQL (F5)    : {ds:6.2f} s · {os_}")
    meme = (sum(op.values()) == sum(os_.values()))
    print(f"  Même nombre d'orphelins détecté : {meme}")
