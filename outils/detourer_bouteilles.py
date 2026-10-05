#!/usr/bin/env python3
"""Détoure les bouteilles du catalogue — « python3 outils/detourer_bouteilles.py ».

    python3 outils/detourer_bouteilles.py              toutes les photos du catalogue
    python3 outils/detourer_bouteilles.py IMG_3201 …   seulement celles-ci

On repart toujours de l'original HEIC (contenu-visuel/photos-produits-bouteilles),
jamais de l'image recadrée du site : le recadrage automatique du début avait
coupé la capsule de 22 bouteilles, et un détourage fait dessus donnait des
bouteilles décapitées, flottant au milieu du fond.

Le détourage est celui de macOS (Vision, le « soulever le sujet » de Photos) :
local, gratuit, et propre jusque sur le verre transparent des blancs et des
rosés. outils/detourer.swift est compilé à la première utilisation.

Le résultat va dans images/cave/detoure/, à côté des originales — jamais par
écrasement : les images sont servies avec un cache d'un an « immutable ».
generer_catalogue.py substitue la version détourée quand elle existe.
"""
import io, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ORIGINAUX = os.path.join(RACINE, "..", "contenu-visuel", "photos-produits-bouteilles")
SORTIE = os.path.join(RACINE, "images", "cave", "detoure")
OUTIL = os.path.join(os.path.expanduser("~"), ".cache", "chai-detourer")
L, H = 675, 900                    # le cadre 3:4 du catalogue


def outil():
    """Compile l'outil Vision au premier passage."""
    source = os.path.join(RACINE, "outils", "detourer.swift")
    if not os.path.exists(OUTIL) or os.path.getmtime(OUTIL) < os.path.getmtime(source):
        os.makedirs(os.path.dirname(OUTIL), exist_ok=True)
        print("  compilation de l'outil de détourage…")
        subprocess.run(["swiftc", "-O", source, "-o", OUTIL], check=True)
    return OUTIL


def composer(png, sortie):
    """La bouteille à 88 % de la hauteur, centrée, sur une ombre douce, fond
    transparent : c'est le dégradé crème des cartes qui fait le fond."""
    sujet = Image.open(png).convert("RGBA")
    a = np.array(sujet.getchannel("A")) > 40
    ys, xs = np.where(a)
    sujet = sujet.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    h = int(H * 0.88); w = int(sujet.width * h / sujet.height)
    if w > L * 0.9:
        w = int(L * 0.9); h = int(sujet.height * w / sujet.width)
    sujet = sujet.resize((w, h), Image.LANCZOS)
    cadre = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    ombre = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    pied = (H - h) // 2 + h
    ImageDraw.Draw(ombre).ellipse([L / 2 - w * 0.55, pied - 14, L / 2 + w * 0.55, pied + 14],
                                  fill=(60, 40, 30, 75))
    cadre = Image.alpha_composite(cadre, ombre.filter(ImageFilter.GaussianBlur(13)))
    cadre.alpha_composite(sujet, ((L - w) // 2, (H - h) // 2))
    cadre.save(sortie, "WEBP", quality=82, method=4)


def main():
    binaire = outil()
    heic = {os.path.splitext(f)[0].upper(): f for f in os.listdir(ORIGINAUX) if f.lower().endswith(".heic")}
    if len(sys.argv) > 1:
        noms = [n if n.endswith(".webp") else n + ".webp" for n in sys.argv[1:]]
    else:
        produits = json.load(io.open(os.path.join(RACINE, "data", "produits.json"), encoding="utf-8"))
        noms = sorted({os.path.basename(i) for p in produits for i in (p.get("images") or [])
                       if i.startswith("/images/cave/")})
    os.makedirs(SORTIE, exist_ok=True)
    tmp = os.path.join(os.path.expanduser("~"), ".cache", "chai-detoure-png")
    os.makedirs(tmp, exist_ok=True)

    def un(nom):
        base = os.path.splitext(nom)[0]
        if base.upper() not in heic:
            return nom, "pas d'original HEIC"
        png = os.path.join(tmp, base + ".png")
        r = subprocess.run([binaire, os.path.join(ORIGINAUX, heic[base.upper()]), png, "1600"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return nom, "échec : " + r.stderr.strip()[:60]
        composer(png, os.path.join(SORTIE, nom))
        return nom, "ok"

    t0 = time.time()
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(un, noms))
    rates = [r for r in res if r[1] != "ok"]
    print(f"  {len(res) - len(rates)}/{len(res)} bouteilles détourées en {time.time() - t0:.0f} s")
    for nom, motif in rates:
        print(f"    ✗ {nom} — {motif}")
    print("  Relancez ensuite : python3 outils/generer_catalogue.py && python3 outils/generer_etagere.py")


if __name__ == "__main__":
    main()
