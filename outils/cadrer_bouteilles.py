#!/usr/bin/env python3
"""Recadre les photos de bouteilles pour que le produit remplisse le cadre.

Les prises de vue sont toutes bâties pareil : fond clair, plan de travail
crème, bouteille debout quelque part au milieu. On repère la bouteille comme
la masse sombre centrale, puis on recadre autour en gardant le format 3/4.
"""
import numpy as np
from PIL import Image

MARGE_H = 0.16      # marge latérale, en fraction de la largeur de la bouteille
MARGE_HAUT = 0.07   # marge au-dessus du bouchon, en fraction de la hauteur du cadre
MARGE_BAS = 0.06   # marge sous le culot
BORD = 0.10         # part des bords ignorée : c'est le fond, parfois sombre

def _otsu(g):
    """Sépare le sombre du clair là où l'histogramme se creuse (méthode d'Otsu).
    Un seuil fixe ne marchait pas : le panneau de fond, gris, passait pour du
    sujet dès que le plan de travail était très clair."""
    h, _ = np.histogram(g, bins=256, range=(0, 256))
    p = h / max(h.sum(), 1)
    poids = np.cumsum(p)
    moyennes = np.cumsum(p * np.arange(256))
    total = moyennes[-1]
    denom = poids * (1 - poids)
    denom[denom == 0] = 1e-9
    variance = (total * poids - moyennes) ** 2 / denom
    return int(np.argmax(variance))

def masque(a):
    """Pixels du sujet : nettement plus sombres que le fond, ou vivement colorés."""
    g = a.mean(axis=2)
    seuil = min(_otsu(g), np.percentile(g, 80) - 30)
    m = g < seuil
    ecart = a.max(axis=2) - a.min(axis=2)          # étiquette colorée sur fond neutre
    return m | ((ecart > 70) & (g < np.percentile(g, 92)))

def _masque_doux(a):
    """Repli pour les sujets peu contrastés : on juge l'écart au fond mesuré
    dans les coins hauts, qui ne contiennent jamais le produit."""
    h, l = a.shape[:2]
    coins = np.concatenate([a[:int(h * .2), :int(l * .3)].reshape(-1, 3),
                            a[:int(h * .2), int(l * .7):].reshape(-1, 3)])
    fond = np.median(coins, axis=0)
    return np.abs(a - fond).sum(axis=2) > 42

def boite(chemin):
    im = Image.open(chemin).convert("RGB")
    a = np.asarray(im).astype(float)
    h, l = a.shape[:2]
    m = masque(a)
    m[:, :int(l * BORD)] = False                    # bords latéraux : décor, pas sujet
    m[:, int(l * (1 - BORD)):] = False

    if m.sum(axis=0).max() < h * 0.10:
        m = _masque_doux(a)                         # sujet pâle : pot de miel, bouteille claire
        m[:, :int(l * BORD)] = False
        m[:, int(l * (1 - BORD)):] = False
    colonnes = m.sum(axis=0)
    if colonnes.max() < h * 0.05:
        return None                                 # rien de net : on laisse la photo telle quelle
    seuil = max(colonnes.max() * 0.22, h * 0.06)
    pleines = np.where(colonnes >= seuil)[0]
    # on garde le bloc continu qui contient la colonne la plus dense
    pic = int(colonnes.argmax())
    g = d = pic
    tenu = set(pleines.tolist())
    while g - 1 in tenu: g -= 1
    while d + 1 in tenu: d += 1

    bande = m[:, g:d + 1]
    lignes = bande.sum(axis=1)
    larg = max(d - g + 1, 1)
    utiles = np.where(lignes >= max(larg * 0.20, 3))[0]
    if not len(utiles):
        return None
    haut, bas = int(utiles.min()), int(utiles.max())
    if (bas - haut) > h * 0.90 or (d - g) > l * 0.80:
        return None                                 # on a détouré le décor, pas le produit
    return g, haut, d, bas

def cadre(chemin, ratio=3 / 4):
    """Rend la boîte de recadrage finale (gauche, haut, droite, bas)."""
    im = Image.open(chemin).convert("RGB")
    L, H = im.size
    b = boite(chemin)
    if not b:
        # produit trop peu contrasté : zoom central prudent, le sujet est
        # toujours posé au milieu et un peu bas dans le cadre
        hauteur = H * 0.68
        largeur = hauteur * ratio
        y0 = min(max(H * 0.58 - hauteur / 2, 0), H - hauteur)
        x0 = (L - largeur) / 2
        return im, (int(x0), int(y0), int(x0 + largeur), int(y0 + hauteur))
    g, ht, d, bs = b
    hauteur = (bs - ht) * (1 + MARGE_HAUT + MARGE_BAS)
    largeur = max(hauteur * ratio, (d - g) * (1 + 2 * MARGE_H))
    hauteur = max(hauteur, largeur / ratio)
    cx = (g + d) / 2
    cy = ht - (bs - ht) * MARGE_HAUT + hauteur / 2

    x0, x1 = cx - largeur / 2, cx + largeur / 2
    y0, y1 = cy - hauteur / 2, cy + hauteur / 2
    # on recale dans l'image plutôt que de sortir du cadre
    if x0 < 0: x1 -= x0; x0 = 0
    if x1 > L: x0 -= x1 - L; x1 = L
    if y0 < 0: y1 -= y0; y0 = 0
    if y1 > H: y0 -= y1 - H; y1 = H
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(L, x1), min(H, y1)
    return im, (int(x0), int(y0), int(x1), int(y1))
