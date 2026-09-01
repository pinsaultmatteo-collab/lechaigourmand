#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertit les photos de bouteilles (HEIC, ~3,5 Mo) en WebP légers pour le site,
et inscrit les chemins obtenus dans data/produits.json.

    python3 outils/convertir_photos.py

Deux photos au plus par produit : la vignette du catalogue et la vue de détail
utilisent la même image, redimensionnée à 900 px de large.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cadrer_bouteilles import cadre
from PIL import Image

SOURCE = Path("../contenu-visuel/photos-produits-bouteilles")
CIBLE = Path("images/cave")
PLEINE = 1800          # rendu intermédiaire, avant recadrage
LARGE = 675            # largeur finale, pour un cadre 3/4
HAUTE = 900
QUALITE = 74
MAX_PAR_PRODUIT = 2

def convertir(heic, webp):
    """HEIC -> JPEG -> WebP.

    Les photos sont stockées en paysage mais destinées à être vues en portrait
    (orientation EXIF). cwebp ignore cette orientation : la rotation doit donc
    être appliquée dans l'image elle-même, sinon les bouteilles sont couchées.

    Le recadrage se fait sur l'image en pleine résolution, pas sur la vignette :
    on veut serrer le cadre sur le produit sans perdre en netteté.
    """
    with tempfile.NamedTemporaryFile(suffix=".jpg") as brut, \
         tempfile.NamedTemporaryFile(suffix=".jpg") as coupe:
        r = subprocess.run(["sips", "-s", "format", "jpeg", "-Z", str(PLEINE),
                            str(heic), "--out", brut.name], capture_output=True)
        if r.returncode != 0:
            return False, r.stderr.decode()[:80]
        r = subprocess.run(["sips", "-r", "90", brut.name], capture_output=True)
        if r.returncode != 0:
            return False, r.stderr.decode()[:80]

        im, boite = cadre(brut.name)
        if boite:
            im = im.crop(boite)
        im = im.resize((LARGE, HAUTE), Image.LANCZOS)
        im.save(coupe.name, "JPEG", quality=94)

        r = subprocess.run(["cwebp", "-quiet", "-q", str(QUALITE), coupe.name, "-o", str(webp)],
                           capture_output=True)
        return (r.returncode == 0), r.stderr.decode()[:80]

REFAIRE = "--refaire" in sys.argv     # recalcule même si le WebP existe déjà

def main():
    produits = json.load(open("data/produits.json"))
    CIBLE.mkdir(parents=True, exist_ok=True)
    dispo = {f.stem: f for f in SOURCE.iterdir() if f.is_file()}

    faits, erreurs, deja = 0, [], 0
    for p in produits:
        images = []
        for nom in p["photos"][:MAX_PAR_PRODUIT]:
            src = dispo.get(nom)
            if not src:
                continue
            dest = CIBLE / f"{nom}.webp"
            if dest.exists() and not REFAIRE:
                deja += 1
            else:
                ok, msg = convertir(src, dest)
                if not ok:
                    erreurs.append((nom, msg)); continue
                faits += 1
            images.append(f"/{CIBLE}/{nom}.webp")
        p["images"] = images

    json.dump(produits, open("data/produits.json", "w"), ensure_ascii=False, indent=1)

    avec = sum(1 for p in produits if p["images"])
    poids = sum(f.stat().st_size for f in CIBLE.iterdir()) / 1e6
    print(f"converties : {faits}   déjà présentes : {deja}   erreurs : {len(erreurs)}")
    for n, m in erreurs[:5]:
        print("  ⚠", n, m)
    print(f"produits illustrés : {avec}/{len(produits)}")
    print(f"poids total des images : {poids:.1f} Mo")

if __name__ == "__main__":
    main()
