"""Arbitrage WITHOUT ROWID sur le volume reel (etape F3).

Le DDL de reference n'est pas modifie : la variante est produite par
post-traitement de la chaine engendree, uniquement pour la mesure.
"""
import re, sys, time
from pathlib import Path
import schema
from entrepot import Entrepot
from chargement import charger
from contrat_source import CONTROLE_MINIMAL
from finess_structures import SourceFinessStructures
from finess_activites import SourceFinessActivites

def ddl_sans_rowid(ddl: str):
    """Ajoute WITHOUT ROWID aux tables pourvues d'une cle primaire."""
    avec_cle = {t.nom for t in schema.SCHEMA.tables if t.cle_primaire() is not None}
    sortie, appliquees = [], []
    for bloc in ddl.split(");"):
        m = re.search(r"CREATE TABLE (\w+)", bloc)
        if m and m.group(1) in avec_cle:
            sortie.append(bloc + ") WITHOUT ROWID;")
            appliquees.append(m.group(1))
        elif m:
            sortie.append(bloc + ");")
        else:
            sortie.append(bloc)
    return "".join(sortie), appliquees

def campagne(intitule, sans_rowid, fichiers):
    base = Path(f"/tmp/rowid_{int(sans_rowid)}.db")
    for s in ("", "-wal", "-shm", "-journal"):
        p = Path(str(base) + s)
        if p.exists(): p.unlink()
    ddl = schema.SCHEMA.ddl()
    if sans_rowid:
        ddl, appliquees = ddl_sans_rowid(ddl)
    else:
        appliquees = []
    with Entrepot(base) as e:
        e.connexion.executescript(ddl)
        total, duree = 0, 0.0
        for source, chemin in fichiers:
            r = charger(e, source, chemin, taille_lot=2000,
                        controle=CONTROLE_MINIMAL, verifier_apres=False)
            total += r.total; duree += r.duree_s
        integrite = e.verifier_integrite()
        octets = e.octets()
    print(f"  {intitule:<26}{duree:8.1f} s{octets/2**20:11.1f} Mio{total:>11} lignes"
          f"   {len(integrite['violations_cles_etrangeres'])} violation(s)")
    base.unlink(missing_ok=True)
    return duree, octets, appliquees

if __name__ == "__main__":
    fichiers = [(SourceFinessStructures(), Path(sys.argv[1])),
                (SourceFinessActivites(), Path(sys.argv[2]))]
    print("Chargement complet, lots de 2 000, contrôle minimal\n")
    print(f"  {'VARIANTE':<26}{'DURÉE':>10}{'TAILLE':>15}{'LIGNES':>18}")
    d0, o0, _ = campagne("rowid (défaut)", False, fichiers)
    d1, o1, appliquees = campagne("WITHOUT ROWID", True, fichiers)
    print(f"\n  WITHOUT ROWID appliqué à {len(appliquees)} tables sur "
          f"{len(schema.SCHEMA.tables)} ; engagement_autorite en est exclue, "
          f"faute de clé primaire.")
    print(f"  Écart de taille : {(o1 - o0) / o0 * 100:+.1f} %  "
          f"({(o1 - o0) / 2**20:+.1f} Mio)")
    print(f"  Écart de durée  : {(d1 - d0) / d0 * 100:+.1f} %")
