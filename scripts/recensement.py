"""recensement.py — Outil de support de la couche 1.

Recensement exhaustif des chemins JSON sur la totalite d'un fichier FINESS :
pour chaque chemin, le nombre d'occurrences, de valeurs nulles, les types
rencontres, les cardinalites et un echantillon de valeurs courtes.

C'est de ce recensement que procedent SCHEMA_PIVOT.md et les jeux de cles
declares par les connecteurs : aucun champ ne doit etre decouvert apres coup.
Les preuves d'absence de perte s'y confrontent egalement.

A rejouer a chaque nouveau millesime, AVANT toute ingestion : c'est lui qui
revele une derive de schema.

Utilise le lecteur gele flux_json. Aucune dependance tierce.
"""
import gzip, json, sys, time
from collections import Counter, defaultdict

from flux_json import CLE_ENTETE, parcourir


def recenser(noeud, chemin, presents, nuls, types, cardinalites, valeurs, longueurs):
    if isinstance(noeud, dict):
        types[chemin]['objet'] += 1
        for cle, val in noeud.items():
            sous = chemin + '.' + cle if chemin else cle
            presents[sous] += 1
            if val is None:
                nuls[sous] += 1
                types[sous]['null'] += 1
            else:
                recenser(val, sous, presents, nuls, types, cardinalites, valeurs, longueurs)
    elif isinstance(noeud, list):
        types[chemin]['liste'] += 1
        cardinalites[chemin][len(noeud)] += 1
        for val in noeud:
            recenser(val, chemin + '[]', presents, nuls, types, cardinalites, valeurs, longueurs)
    else:
        t = type(noeud).__name__
        types[chemin][t] += 1
        if isinstance(noeud, str):
            longueurs[chemin] = max(longueurs[chemin], len(noeud))
            if len(valeurs[chemin]) < 60 and len(noeud) <= 16:
                valeurs[chemin][noeud] += 1


def main(chemin_fichier, sortie):
    presents, nuls = Counter(), Counter()
    types = defaultdict(Counter)
    cardinalites = defaultdict(Counter)
    valeurs = defaultdict(Counter)
    longueurs = defaultdict(int)
    racines = Counter()
    t0 = time.time()

    for cle_racine, _rang, objet in parcourir(chemin_fichier, taille_bloc=1 << 18):
        racines[cle_racine] += 1
        if cle_racine == CLE_ENTETE:
            continue
        presents[cle_racine] += 1
        recenser(objet, cle_racine, presents, nuls, types, cardinalites, valeurs, longueurs)

    duree = time.time() - t0
    with open(sortie, 'w', encoding='utf-8') as f:
        f.write(f"# Recensement : {chemin_fichier}\n")
        f.write(f"# Duree {duree:.0f} s | tableaux racines : {dict(racines)}\n\n")
        f.write(f"{'CHEMIN':<95} {'PRESENT':>10} {'NULS':>10} {'TYPES':<28} {'CARDINALITES':<22} MAXLEN\n")
        for chemin in sorted(presents):
            t = dict(types.get(chemin, {}))
            card = dict(sorted(cardinalites[chemin].items())) if chemin in cardinalites else ''
            card_txt = str(card)[:20] if card else ''
            f.write(f"{chemin:<95} {presents[chemin]:>10} {nuls[chemin]:>10} "
                    f"{str(t)[:26]:<28} {card_txt:<22} {longueurs.get(chemin,'')}\n")
        f.write("\n\n# Valeurs distinctes observees (champs courts)\n")
        for chemin in sorted(valeurs):
            v = valeurs[chemin]
            f.write(f"{chemin} -> {len(v)}{'+' if len(v)>=60 else ''} valeurs : {dict(v.most_common(12))}\n")
    print(f"{chemin_fichier.split('/')[-1]} : {duree:.0f} s, {len(presents)} chemins distincts -> {sortie}")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
