#!/usr/bin/env python3
"""Lit le PDF des tarifs envoyé par le fournisseur et rend une liste propre.

Le PDF est l'impression d'un courriel : deux colonnes, « Désignation » et
« Pv Part ». À l'extraction le prix se retrouve collé en fin de ligne. On le
détache, et on refuse tout ce qui ressemble à un millésime — une ligne sans
prix se terminant par « 2023 » ne doit pas donner un vin à 2023 euros.
"""
import re
import unicodedata

# Le PDF vit à côté du dépôt, dans les documents du client.
TARIFS = "../../contenu-visuel/Gmail - Prix vente particulier.pdf"

# Le prix : un nombre en fin de ligne, virgule ou point décimal.
PRIX = re.compile(r"^(.*?)[\s ]+(\d{1,3}(?:[.,]\d{1,2})?)\s*$")

# Ce qui n'est pas un produit : en-têtes du courriel et de la table.
BRUIT = re.compile(r"^(Mattéo Pinsault|Prix vente particulier|C & Wine|À : |Bonjour|"
                   r"voici les prix|Désignation)", re.I)


def _sans_accents(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def normaliser(t):
    """Minuscules, sans accents, sans ponctuation : la forme qui sert à comparer."""
    t = _sans_accents(str(t or "").lower())
    t = t.replace("’", "'").replace("œ", "oe")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def lire(chemin=None):
    from pypdf import PdfReader
    import os
    chemin = chemin or os.path.join(os.path.dirname(__file__), TARIFS)
    lignes = []
    for page in PdfReader(chemin).pages:
        lignes += (page.extract_text() or "").split("\n")

    tarifs, sans_prix = [], []
    for brute in lignes:
        ligne = brute.replace(" ", " ").strip()
        if not ligne or BRUIT.match(ligne):
            continue
        m = PRIX.match(ligne)
        if not m:
            sans_prix.append(ligne)
            continue
        designation, valeur = m.group(1).strip(), m.group(2)
        prix = float(valeur.replace(",", "."))
        # Un millésime traîne en fin de ligne : ce n'est pas un prix.
        if re.fullmatch(r"(19|20)\d{2}", valeur) or not designation:
            sans_prix.append(ligne)
            continue
        tarifs.append({"designation": designation, "prix": prix,
                       "cle": normaliser(designation)})
    return tarifs, sans_prix


if __name__ == "__main__":
    tarifs, sans_prix = lire()
    print(f"  {len(tarifs)} tarifs lus, {len(sans_prix)} lignes sans prix\n")
    print("  ── les cinq premiers ──")
    for t in tarifs[:5]:
        print(f"    {t['prix']:>7.2f} €   {t['designation'][:72]}")
    print("\n  ── extrêmes ──")
    for t in sorted(tarifs, key=lambda x: x["prix"])[:3]:
        print(f"    {t['prix']:>7.2f} €   {t['designation'][:72]}")
    for t in sorted(tarifs, key=lambda x: -x["prix"])[:3]:
        print(f"    {t['prix']:>7.2f} €   {t['designation'][:72]}")
    print("\n  ── lignes sans prix (à laisser en « prix en boutique ») ──")
    for l in sans_prix:
        print(f"    {l[:88]}")
