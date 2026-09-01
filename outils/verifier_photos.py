#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifie — et corrige — l'association entre les fiches et les photos.

Les références « IMG_xxxx » inscrites dans les PDF du client se sont révélées
fausses par endroits (tout un lot inversé, quelques décalages ailleurs). Plutôt
que de leur faire confiance, on lit l'étiquette de chaque photo (reconnaissance
de texte macOS, voir outils/ocr.swift) et on réattribue les photos par
ressemblance avec le nom, le producteur et l'appellation de la fiche.

    python3 outils/verifier_photos.py --lire      # relit les étiquettes
    python3 outils/verifier_photos.py             # réattribue et écrit le JSON
    python3 outils/verifier_photos.py --simuler   # montre sans rien écrire
"""
import json, re, subprocess, sys, unicodedata
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

ETIQUETTES = Path("data/etiquettes-ocr.tsv")
OCR = Path("outils/ocr")
IMAGES = Path("images/cave")
SEUIL = 1.2          # preuve minimale exigée de l'étiquette elle-même
FIDELITE = 1.0       # prime à la référence du PDF, à preuve égale

def net(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t)

VIDES = {"chateau", "domaine", "grand", "cru", "vin", "wine", "de", "du", "des", "la", "le",
         "les", "et", "aop", "aoc", "igp", "mis", "en", "bouteille", "au", "france", "product",
         "of", "appellation", "protegee", "controlee", "origine", "cl", "vol", "alc", "contient",
         "sulfites", "bio", "organic", "red", "blanc", "rouge", "rose", "millesime", "par"}

def mots(t):
    return {m for m in net(t).split() if len(m) > 3 and m not in VIDES}

def lire_etiquettes():
    fichiers = sorted(str(f) for f in IMAGES.glob("*.webp"))
    sortie = subprocess.run([str(OCR)] + fichiers, capture_output=True, text=True)
    ETIQUETTES.write_text(sortie.stdout, encoding="utf-8")
    print(f"{len(sortie.stdout.splitlines())} étiquettes lues → {ETIQUETTES}")

def etiquettes():
    d = {}
    for ligne in ETIQUETTES.read_text(encoding="utf-8").splitlines():
        chemin, _, texte = ligne.partition("\t")
        d[Path(chemin).stem] = texte
    return d

# Mentions légales : elles trahissent une contre-étiquette. À preuve égale on
# préfère montrer le recto, c'est lui qui porte le nom du vin.
DOS = re.compile(r"mis en bouteille|sulfites|contient|product of|produit de|"
                 r"consommer avec mod|www\.|\d{8,}|nutri|ingredients", re.I)

def poids_des_mots(fiches):
    """« Fumées Blanches » revient sur six cuvées du même lot : ce mot ne
    distingue rien. « Calcaires » n'apparaît qu'une fois : il vaut de l'or.
    On pondère donc chaque mot par sa rareté dans le lot."""
    freq = {}
    for p in fiches:
        for m in mots(" ".join(str(p.get(k) or "") for k in
                               ("nom", "producteur", "appellation", "origine"))):
            freq[m] = freq.get(m, 0) + 1
    return {m: 1.0 / n for m, n in freq.items()}

def score(produit, texte, poids=None):
    """Somme des mots partagés, pondérés par leur rareté ; le nom compte double."""
    lus = mots(texte)
    if not lus:
        return 0.0
    nom = mots(produit.get("nom"))
    reste = mots(" ".join(str(produit.get(k) or "") for k in
                          ("producteur", "appellation", "origine"))) - nom
    def w(m):
        return (poids or {}).get(m, 1.0)
    s = sum(2.0 * w(m) for m in nom & lus) + sum(1.0 * w(m) for m in reste & lus)
    millesime = str(produit.get("millesime") or "")
    if millesime and millesime in texte:
        s += 0.5
    if DOS.search(texte):
        s *= 0.8                       # probable contre-étiquette
    return s

def main():
    if "--lire" in sys.argv:
        lire_etiquettes()
    if not ETIQUETTES.exists():
        sys.exit("étiquettes absentes : lancer d'abord --simuler --lire")

    lus = etiquettes()
    produits = json.load(open("data/produits.json"))

    # on raisonne lot par lot : les photos d'un lot ne servent qu'à ses fiches
    lots = {}
    for p in produits:
        lots.setdefault(p.get("lot") or "", []).append(p)

    confirmes = corriges = orphelins = 0
    rapport, a_verifier = [], []
    for lot, fiches in lots.items():
        vues = sorted({v for p in fiches for v in p["photos"] if v in lus})
        if not vues:
            continue
        # appariement optimal fiche / photo sur l'ensemble du lot : le glouton
        # se laissait piéger par les étiquettes qui se ressemblent
        poids = poids_des_mots(fiches)
        brut = np.zeros((len(fiches), len(vues)))
        M = np.zeros((len(fiches), len(vues)))
        for i, p in enumerate(fiches):
            for j, v in enumerate(vues):
                brut[i, j] = score(p, lus[v], poids)
                M[i, j] = brut[i, j] + (FIDELITE if v in p["photos"][:1] else 0)
        lignes, colonnes = linear_sum_assignment(-M)

        # on ne retient que les appariements que l'étiquette justifie d'elle-même
        choix = {fiches[i]["id"]: (vues[j], brut[i, j]) for i, j in zip(lignes, colonnes)
                 if brut[i, j] >= SEUIL}
        pris_v = {v for v, _ in choix.values()}

        # une seule photo par fiche : celle dont l'étiquette porte son nom.
        # Les contre-étiquettes ne sont de toute façon jamais affichées.
        for p in fiches:
            trouve = choix.get(p["id"])
            if trouve:
                v, s = trouve
                if v != (p["photos"] or [None])[0]:
                    corriges += 1
                    rapport.append((p["nom"][:40], p["photos"][:2], [v], round(s, 1)))
                else:
                    confirmes += 1
                p["photos"] = [v]
                continue
            # étiquette illisible : on garde la référence du PDF si personne
            # d'autre ne l'a réclamée, sinon la fiche part sans photo
            orphelins += 1
            reste = [v for v in p["photos"][:1] if v not in pris_v]
            a_verifier.append((p["nom"][:40], p["id"], reste[0] if reste else "aucune"))
            p["photos"] = reste

    print(f"confirmées : {confirmes}   corrigées : {corriges}   sans étiquette lisible : {orphelins}")
    for nom, avant, apres, s in rapport[:40]:
        print(f"  {nom:42s} {str(avant):26s} → {str(apres):26s} (score {s})")
    if len(rapport) > 40:
        print(f"  … et {len(rapport) - 40} autres")

    if "--simuler" in sys.argv:
        print("\n(simulation : data/produits.json inchangé)")
        return

    with open("data/photos-a-verifier.csv", "w", encoding="utf-8") as f:
        f.write("produit;identifiant;photo retenue;remarque\n")
        for nom, pid, v in a_verifier:
            f.write(f"{nom};{pid};{v};étiquette illisible, référence du PDF conservée\n")
        for nom, avant, apres, sc in rapport:
            f.write(f"{nom};;{apres[0]};le PDF indiquait {avant[0] if avant else '?'}, "
                    f"l'étiquette lue dit {apres[0]}\n")
    print(f"détail dans data/photos-a-verifier.csv ({len(a_verifier) + len(rapport)} lignes)")

    json.dump(produits, open("data/produits.json", "w"), ensure_ascii=False, indent=1)
    print("\ndata/produits.json mis à jour — relancer convertir_photos.py puis generer_catalogue.py")

if __name__ == "__main__":
    main()
