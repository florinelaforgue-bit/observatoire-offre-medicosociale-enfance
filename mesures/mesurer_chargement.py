"""Mesures fondant la taille des lots de chargement (etape F3).

La vitesse ayant ete mesuree insensible a ce parametre en F2, seule la memoire
est en jeu. Chaque taille est mesuree dans un processus neuf, pour que le pic
RSS ne soit pas celui d'une mesure precedente.
"""
import subprocess, sys, json
from pathlib import Path

SCRIPT = """
import resource, sys, time
from pathlib import Path
sys.path.insert(0, "/home/claude/f1")
from entrepot import Entrepot
from chargement import charger
from finess_structures import SourceFinessStructures
from contrat_source import CONTROLE_MINIMAL

lot = int(sys.argv[1])
base = Path(f"/tmp/mesure_{lot}.db")
for s in ("", "-wal", "-shm", "-journal"):
    p = Path(str(base) + s)
    if p.exists(): p.unlink()
base_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
with Entrepot(base) as e:
    e.creer(ecraser=True)
    r = charger(e, SourceFinessStructures(), Path(sys.argv[2]),
                taille_lot=lot, controle=CONTROLE_MINIMAL, verifier_apres=False)
    print(f"{lot}\\t{r.duree_s:.1f}\\t{r.rss_max_mio:.1f}\\t{base_rss:.1f}\\t{r.total}\\t{r.octets_base}")
base.unlink(missing_ok=True)
"""

if __name__ == "__main__":
    fichier = sys.argv[1]
    Path("/tmp/mesure_lot.py").write_text(SCRIPT, encoding="utf-8")
    print(f"{'LOT':>8}{'DURÉE':>9}{'RSS MAX':>10}{'RSS DÉPART':>12}"
          f"{'LIGNES':>10}{'BASE':>10}")
    for lot in (500, 2000, 10000, 50000, 200000):
        sortie = subprocess.run([sys.executable, "/tmp/mesure_lot.py", str(lot), fichier],
                                capture_output=True, text=True)
        if sortie.returncode:
            print(f"{lot:>8}  ÉCHEC : {sortie.stderr.strip().splitlines()[-1][:70]}")
            continue
        l, d, rss, base, n, octets = sortie.stdout.strip().split("\t")
        print(f"{int(l):>8}{float(d):>8.1f}s{float(rss):>9.1f}M{float(base):>11.1f}M"
              f"{int(n):>10}{int(octets)/2**20:>9.1f}M")
