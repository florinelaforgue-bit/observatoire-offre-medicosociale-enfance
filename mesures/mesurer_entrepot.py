"""Mesures experimentales fondant les reglages de l'entrepot (etape F2).

Aucun reglage SQLite n'est retenu par convention : chaque valeur retenue dans
entrepot.py doit renvoyer a une mesure de ce script.

Table de mesure : evenement, 14 colonnes, 1 961 124 lignes dans le pivot reel.
C'est la plus volumineuse ; c'est donc elle qui dicte les reglages.
"""
import os, sqlite3, sys, time
from pathlib import Path

BANC = Path("/tmp/banc")
BANC.mkdir(exist_ok=True)
N = 200_000
COLONNES = ["evenement_id", "type_porteur", "id_porteur", "rang", "code_evenement",
            "date_evenement", "date_enregistrement", "code_etat_objet_1",
            "code_type_objet_1", "identifiant_objet_1", "code_type_objet_2",
            "identifiant_objet_2", "code_systeme_maitre", "id_lot"]

def lignes(n, decalage=0):
    for i in range(decalage, decalage + n):
        yield (str(i), "ET", str(i % 174508), str(i % 100), "005",
               "2020-01-01", "2020-01-02 10:00:00", "100", "EGE", str(i),
               None, None, "FINESS", "finess_structures:202607:9645bd12")

def creer(chemin, page_size=None, journal="delete", sync="full",
          sans_rowid=False, cle="PRIMARY KEY (evenement_id)"):
    if chemin.exists():
        chemin.unlink()
    for suffixe in ("-wal", "-shm", "-journal"):
        p = Path(str(chemin) + suffixe)
        if p.exists():
            p.unlink()
    c = sqlite3.connect(chemin)
    if page_size:
        c.execute(f"PRAGMA page_size={page_size}")
    c.execute(f"PRAGMA journal_mode={journal}")
    c.execute(f"PRAGMA synchronous={sync}")
    corps = ",\n".join(f"  {n} TEXT" for n in COLONNES)
    suffixe = " WITHOUT ROWID" if sans_rowid else ""
    c.execute(f"CREATE TABLE evenement (\n{corps},\n  {cle}\n){suffixe}")
    return c

def taille(chemin):
    total = chemin.stat().st_size
    for suffixe in ("-wal", "-shm", "-journal"):
        p = Path(str(chemin) + suffixe)
        if p.exists():
            total += p.stat().st_size
    return total

def inserer(c, n, lot=5000, decalage=0):
    requete = f"INSERT INTO evenement VALUES ({','.join('?' * len(COLONNES))})"
    depart = time.time()
    tampon = []
    for ligne in lignes(n, decalage):
        tampon.append(ligne)
        if len(tampon) >= lot:
            c.executemany(requete, tampon)
            tampon.clear()
    if tampon:
        c.executemany(requete, tampon)
    c.commit()
    return time.time() - depart

def essai(intitule, **kw):
    lot = kw.pop("lot", 5000)
    chemin = BANC / "banc.db"
    c = creer(chemin, **kw)
    duree = inserer(c, N, lot=lot)
    journal_effectif = list(c.execute("PRAGMA journal_mode"))[0][0]
    c.close()
    octets = taille(chemin)
    print(f"  {intitule:<46}{duree:7.2f} s{N/duree/1000:9.0f} kl/s"
          f"{octets/2**20:9.1f} Mio   journal={journal_effectif}")
    return duree, octets

if __name__ == "__main__":
    etape = sys.argv[1] if len(sys.argv) > 1 else "tout"
    print(f"Banc : {N} lignes de la table evenement, 14 colonnes textuelles\n")

    if etape in ("tout", "journal"):
        print("1. Mode de journalisation et synchronisation")
        for journal in ("delete", "wal", "off"):
            for sync in ("full", "normal", "off"):
                essai(f"journal={journal} · synchronous={sync}",
                      journal=journal, sync=sync)
        print()

    if etape in ("tout", "page"):
        print("2. Taille de page (journal=wal, synchronous=normal)")
        for page in (4096, 8192, 16384, 32768):
            essai(f"page_size={page}", page_size=page, journal="wal", sync="normal")
        print()

    if etape in ("tout", "lot"):
        print("3. Taille des lots d'insertion (wal/normal, page 4096)")
        for lot in (500, 5000, 20000, 100000):
            essai(f"lot={lot}", journal="wal", sync="normal", lot=lot)
        print()

    if etape in ("tout", "rowid"):
        print("4. WITHOUT ROWID, clé primaire textuelle")
        essai("avec rowid (défaut)", journal="wal", sync="normal")
        essai("WITHOUT ROWID", journal="wal", sync="normal", sans_rowid=True)
        essai("sans aucune clé primaire", journal="wal", sync="normal",
              cle="CHECK (1=1)")
        print()

def repetitions(intitule, reps=5, **kw):
    durees, tailles = [], []
    for _ in range(reps):
        d, o = 0, 0
        lot = kw.get("lot", 5000)
        chemin = BANC / "banc.db"
        c = creer(chemin, **{k: v for k, v in kw.items() if k != "lot"})
        d = inserer(c, N, lot=lot)
        c.close()
        o = taille(chemin)
        durees.append(d); tailles.append(o)
    durees.sort()
    return durees[len(durees) // 2], min(durees), max(durees), tailles[0]
