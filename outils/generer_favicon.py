#!/usr/bin/env python3
"""Fabrique l'icône du site — « python3 outils/generer_favicon.py ».

Le logo de l'en-tête (cercle de douelles, sarment, feuilles) est magnifique à
40 px et illisible à 16. L'icône d'onglet demande l'inverse : une silhouette,
deux couleurs, aucun détail. On dessine donc une forme à part, dérivée du même
verre, et on la décline en SVG (net à toute taille) et en PNG (pour ICO, iOS
et Android).

Le tracé est défini une seule fois, en coordonnées 0-100, puis rendu par les
deux chemins : le SVG et Pillow lisent la même liste de points. Pas de dessin
fait deux fois, donc pas de divergence entre les formats.
"""
import io, math, os

from PIL import Image, ImageDraw

NOIR = (26, 15, 20)        # #1a0f14 — le noir-brun de l'en-tête
OR = (201, 168, 118)       # #c9a876 — l'or de la marque
LIE = (124, 33, 64)        # #7c2140 — le bordeaux

RACINE = os.path.join(os.path.dirname(__file__), "..")


def bezier(p0, p1, p2, p3, n=48):
    """Échantillonne une cubique. n=48 suffit : à 512 px l'écart se voit pas."""
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((u**3 * p0[0] + 3 * u*u*t * p1[0] + 3 * u*t*t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u*u*t * p1[1] + 3 * u*t*t * p2[1] + t**3 * p3[1]))
    return pts


# ---------- le verre, en coordonnées 0-100 ----------
# Un calice large, une jambe fine, un pied net. Rien d'autre : à 16 px, chaque
# détail supplémentaire devient du bruit.
# Le buvant est un peu plus étroit que la panse : c'est ce galbe en tulipe qui
# fait lire « verre à vin » plutôt que « coupe » ou « trophée ».
RIM_G, RIM_D, RIM_Y = 26.0, 74.0, 13.0      # les deux bouts du buvant
FOND_Y = 55.0                                # le bas du calice
JAMBE_L = 3.9                                # demi-largeur de la jambe
PIED_G, PIED_D, PIED_Y, PIED_H = 25.0, 75.0, 81.0, 5.6

def calice():
    """Le contour du calice, du buvant gauche au buvant droit."""
    gauche = bezier((RIM_G, RIM_Y), (21.4, 28.0), (29.0, FOND_Y), (50.0, FOND_Y))
    droite = bezier((50.0, FOND_Y), (71.0, FOND_Y), (78.6, 28.0), (RIM_D, RIM_Y))
    return gauche + droite[1:]

def vin(hauteur=0.74):
    """La lie dans le calice : le même contour, coupé à mi-hauteur."""
    y = RIM_Y + (FOND_Y - RIM_Y) * (1 - hauteur)
    bas = [p for p in calice() if p[1] >= y]
    if not bas:
        return []
    return [(bas[0][0], y)] + bas + [(bas[-1][0], y)]

def jambe():
    return [(50 - JAMBE_L, FOND_Y - 2), (50 + JAMBE_L, FOND_Y - 2),
            (50 + JAMBE_L, PIED_Y + 1), (50 - JAMBE_L, PIED_Y + 1)]

def pied():
    """Un pied légèrement galbé, pas un simple rectangle."""
    haut = bezier((PIED_G, PIED_Y + PIED_H), (PIED_G + 6, PIED_Y + 1),
                  (PIED_D - 6, PIED_Y + 1), (PIED_D, PIED_Y + PIED_H))
    return haut + [(PIED_D, PIED_Y + PIED_H + 1.6), (PIED_G, PIED_Y + PIED_H + 1.6)]


def rendre(taille, arrondi=True, avec_vin=True, marge=0.0):
    """Un PNG carré, dessiné à 8× puis réduit — les bords restent doux."""
    e = 8
    n = taille * e
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(n * 0.22) if arrondi else 0
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=r, fill=NOIR)

    def ech(pts):
        k = (100 - 2 * marge) / 100
        return [((marge + x * k) / 100 * n, (marge + y * k) / 100 * n) for x, y in pts]

    d.polygon(ech(calice()), fill=OR)
    if avec_vin:
        v = vin()
        if v:
            d.polygon(ech(v), fill=LIE)
    d.polygon(ech(jambe()), fill=OR)
    d.polygon(ech(pied()), fill=OR)
    return img.resize((taille, taille), Image.LANCZOS)


def chemin_svg(pts):
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"

def svg(avec_vin=True):
    v = vin()
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">\n'
        f'  <rect width="100" height="100" rx="22" fill="#1a0f14"/>\n'
        f'  <path d="{chemin_svg(calice())}" fill="#c9a876"/>\n'
        + (f'  <path d="{chemin_svg(v)}" fill="#7c2140"/>\n' if avec_vin and v else "")
        + f'  <path d="{chemin_svg(jambe())}" fill="#c9a876"/>\n'
        f'  <path d="{chemin_svg(pied())}" fill="#c9a876"/>\n'
        "</svg>\n")


def ecrire(dossier=RACINE, avec_vin=True):
    def p(*n):
        return os.path.join(dossier, *n)

    with io.open(p("favicon.svg"), "w", encoding="utf-8") as f:
        f.write(svg(avec_vin))

    # L'ICO reste le filet de sécurité : Safari et tous les agrégateurs de liens
    # vont le chercher à la racine, même quand un SVG est déclaré.
    rendre(64, avec_vin=avec_vin).save(p("favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    rendre(96, avec_vin=avec_vin).save(p("favicon-96.png"))

    # iOS masque lui-même les coins : on lui donne un carré plein, avec un peu
    # d'air autour du verre pour que le rognage ne le mange pas.
    fond = Image.new("RGB", (180, 180), NOIR)
    fond.paste(rendre(180, arrondi=False, avec_vin=avec_vin, marge=9), (0, 0),
               rendre(180, arrondi=False, avec_vin=avec_vin, marge=9))
    fond.save(p("apple-touch-icon.png"))

    for t in (192, 512):
        rendre(t, avec_vin=avec_vin).save(p(f"icone-{t}.png"))

    for n in ("favicon.svg", "favicon.ico", "favicon-96.png", "apple-touch-icon.png",
              "icone-192.png", "icone-512.png"):
        print(f"  ✓ {n}  ({os.path.getsize(p(n)):,} o)".replace(",", " "))


if __name__ == "__main__":
    ecrire()
