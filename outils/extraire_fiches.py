#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extraction des fiches produits C & Wine (PDF) vers un JSON exploitable par le site.

    python3 outils/extraire_fiches.py <dossier_pdf> [--json data/produits.json]

Les fiches arrivent par lots, dans six mises en page différentes. Le script
détecte la mise en page de chaque PDF, en extrait les fiches, normalise les
champs, et MASQUE les informations que C & Wine signale comme non vérifiées
(elles sont listées à part dans data/manques.csv pour être complétées).
"""
import argparse, csv, json, re, sys, unicodedata
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("pypdf est requis :  pip3 install pypdf")

# ---------------------------------------------------------------- utilitaires

# tournures employées par C & Wine pour signaler une information non établie
NON_VERIFIE = re.compile(
    r"non\s+(communiqu|v[ée]rifi|retrouv|document|identifi|lisibl|repris|"
    r"[ée]tabli|confirm|attribu|pr[ée]cis|d[ée]crit|renseign|disponible)"
    r"|aucune?\s+(note|description|information|donn[ée]e|millésime|source)"
    r"|sans\s+source|non\s+trouv|indisponible",
    re.I)

def texte_utile(valeur):
    """Retire les incises « ... non vérifié » d'une valeur, garde le reste.
    Renvoie (valeur_nettoyée_ou_None, motif_si_masqué)."""
    if not valeur:
        return None, "vide"
    v = re.sub(r"\s+", " ", valeur).strip(" .;,")
    if not v:
        return None, "vide"
    # une valeur peut mêler du solide et une réserve : « Robe ambrée ; teinte exacte non décrite »
    morceaux = [m.strip() for m in re.split(r"\s*;\s*", v) if m.strip()]
    gardes = [m for m in morceaux if not NON_VERIFIE.search(m)]
    if not gardes:
        return None, v[:120]
    propre = " ; ".join(gardes).strip(" .;,")
    return (propre + ".") if propre else None, (None if len(gardes) == len(morceaux) else v[:120])

def slug(*parties):
    base = " ".join(p for p in parties if p)
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()
    return re.sub(r"-{2,}", "-", base)[:70]

MOTS_TYPE = [
    ("bulles",     r"champagne|cr[ée]mant|effervescent|mousseux|brut nature|p[ée]tillant|prosecco"),
    ("rose",       r"\bros[ée]s?\b"),
    ("blanc",      r"vin blanc|\bblancs?\b|chardonnay|sauvignon|chenin|muscadet|riesling|vermentino|albari[nñ]o|viognier|s[ée]millon|gew[üu]rztraminer|pinot gris|melon de bourgogne|clairette|rolle|mauzac|savagnin"),
    ("moelleux",   r"moelleux|liquoreux|doux naturel|macvin|vin de liqueur|sauternes|juran[çc]on"),
    ("rouge",      r"vin rouge|\brouges?\b|syrah|grenache|malbec|merlot|cabernet|pinot noir|tempranillo|tannat|n[ée]grette|carignan|mourv[èe]dre|cinsault|gamay|sangiovese|nebbiolo|shiraz"),
    ("biere",      r"\bbi[èe]re|\bale\b|ipa\b|brass"),
    ("spiritueux", r"ap[ée]ritif|spritz|verm[o]uth|sans alcool|rhum|whisky|whiskey|gin\b|vodka|liqueur|arm[ao]gnac|cognac|tequila|mezcal|pastis|absinthe|eau-de-vie"),
]

def deduire_type(*sources):
    blob = " ".join(s for s in sources if s).lower()
    # les spiritueux d'abord : « liqueur de framboise » ne doit pas devenir un rouge
    for nom in ("spiritueux", "biere", "bulles", "moelleux", "rose", "blanc", "rouge"):
        motif = dict(MOTS_TYPE)[nom]
        if re.search(motif, blob):
            return nom
    return "autre"

def photos_de(txt):
    return sorted({"IMG_" + n for n in re.findall(r"IMG[_\\ ]?(\d{4})", txt)})

def urls_de(txt):
    return sorted({u.rstrip(" .;,)") for u in re.findall(r"https?://\S+", txt)})

def alcool_contenance(valeur):
    """« 40 % vol. - 70 cl » -> ('40', '70 cl')"""
    if not valeur:
        return None, None
    deg = re.search(r"(\d{1,2}(?:[.,]\d)?)\s*%", valeur)
    cont = re.search(r"(\d{2,4}\s*(?:cl|ml|l)\b)", valeur, re.I)
    return (deg.group(1).replace(".", ",") if deg else None,
            cont.group(1).replace(" ", "") if cont else None)

# ------------------------------------------------------------- lecture des PDF

def pages_de(chemin):
    return [(p.extract_text() or "") for p in PdfReader(str(chemin)).pages]

def detecter_format(texte):
    if "FICHE DÉGUSTATION" in texte:                 return "degustation"
    if "COLLECTION SPIRITUEUX" in texte:             return "spiritueux"
    if re.search(r"Lot 0?2 — Informations v", texte): return "tableau"
    if "Fiches produits vérifiées" in texte:         return "verifiees"
    if "C & WINE - FICHE PRODUIT" in texte:          return "img_titre"
    if "PHRASE CARTE RESTAURANT" in texte:           return "img_pied"
    return "inconnu"

# --- petites aides de découpage ------------------------------------------------

# Toutes les étiquettes rencontrées dans les six mises en page. Le découpage
# se fait en repérant leurs positions : une valeur s'arrête à l'étiquette suivante,
# ce qui évite qu'un champ déborde sur le suivant.
ETIQUETTES = [
    r"Producteur\s*/\s*domaine", r"PRODUCTEUR\s*/\s*MARQUE", r"Producteur",
    r"Origine\s*/\s*appellation", r"ORIGINE", r"Origine",
    r"Appellation", r"Cépages\s*/\s*composition", r"Cépages\s*/\s*assemblage",
    r"COMPOSITION\s*/\s*ÉLABORATION", r"Cépages?\s*\(s\)", r"Cépages?",
    r"Degré alcoolique", r"Degré d[’']alcool", r"ALCOOL\s*/\s*CONTENANCE",
    r"Degrés", r"Alcool",
    r"MILLÉSIME\s*/\s*VIEILLISSEMENT", r"Millésime",
    r"Vinification\s*/\s*élevage", r"NOTES DE DÉGUSTATION", r"Note de dégustation",
    r"Dégustation", r"VISUEL\s*/\s*ROBE", r"VISUEL", r"Visuel",
    r"NEZ", r"Nez", r"BOUCHE", r"Bouche",
    r"ACCORDS METS & VINS?", r"ACCORDS[^\n:]*", r"Accords[^\n:]*",
    r"FIABILITÉ ET MILLÉSIME",
    r"PHRASE POUR UNE CARTE DE RESTAURANT", r"Phrase pour la carte du restaurant",
    r"PHRASE CARTE RESTAURANT",
    r"SOURCES VÉRIFIÉES", r"Sources vérifiables", r"SOURCES", r"Sources",
    r"Photo\(s\)", r"Photos", r"Photographies correspondantes",
]
_SEP = re.compile(r"^[ \t]*(" + "|".join(ETIQUETTES) + r")[ \t]*:?[ \t]*$|"
                  r"^[ \t]*(" + "|".join(ETIQUETTES) + r")[ \t]*:[ \t]*(.*)$",
                  re.M)

def decouper(bloc):
    """Renvoie {etiquette_normalisée: valeur} en tranchant le texte aux étiquettes."""
    trouves, champs = [], {}
    for m in _SEP.finditer(bloc):
        label = (m.group(1) or m.group(2) or "").strip().lower()
        reste = (m.group(3) or "").strip()
        trouves.append((m.start(), m.end(), label, reste))
    for i, (deb, fin, label, reste) in enumerate(trouves):
        suite = trouves[i + 1][0] if i + 1 < len(trouves) else len(bloc)
        valeur = (reste + " " + bloc[fin:suite]).strip()
        valeur = re.sub(r"\s+", " ", valeur).strip()
        if valeur and label not in champs:
            champs[label] = valeur
    return champs

def prendre(champs, *cles):
    """Première étiquette renseignée parmi celles proposées (comparaison souple)."""
    for c in cles:
        c = c.lower()
        for k, v in champs.items():
            if k == c or k.startswith(c.split("(")[0].strip()):
                return v
    return None

# --------------------------------------------------------- un parseur par format

def _entete(pg, sauter=0):
    return [l.strip() for l in pg.split("\n") if l.strip()][sauter:]

def _fiche(pg, nom, categorie, lot):
    c = decouper(pg)
    return dict(
        nom=nom, categorie=categorie,
        producteur=prendre(c, "producteur / domaine", "producteur / marque", "producteur"),
        origine=prendre(c, "origine / appellation", "origine"),
        appellation=prendre(c, "appellation"),
        cepages=prendre(c, "cépages / composition", "cépages / assemblage",
                        "composition / élaboration", "cépage(s)", "cépages", "cépage"),
        alcool_brut=prendre(c, "degré alcoolique", "degré d’alcool", "degré d'alcool",
                            "alcool / contenance", "degrés", "alcool"),
        millesime=prendre(c, "millésime / vieillissement", "millésime"),
        visuel=prendre(c, "visuel / robe", "visuel"),
        nez=prendre(c, "nez"), bouche=prendre(c, "bouche"),
        accords=prendre(c, "accords mets & vins", "accords mets & vin", "accords"),
        phrase=prendre(c, "phrase pour une carte de restaurant",
                       "phrase pour la carte du restaurant", "phrase carte restaurant"),
        sources=urls_de(pg), photos=photos_de(pg), lot=lot)

def p_verifiees(pages, lot):
    fiches = []
    for pg in pages[1:]:
        if "Producteur" not in pg: continue
        l = _entete(pg)
        i = next((k for k, x in enumerate(l) if x.isdigit()), 0)
        entete = l[i + 1:i + 4]
        cat = next((x for x in entete if x.isupper() and len(x) > 3), "")
        titre = [x for x in entete if x != cat][:2]
        fiches.append(_fiche(pg, " — ".join(titre) if titre else "Sans titre", cat, lot))
    return fiches

def p_degustation(pages, lot):
    fiches = []
    for pg in pages:
        if "FICHE DÉGUSTATION" not in pg: continue
        l = _entete(pg)
        k = next(i for i, x in enumerate(l) if x.startswith("FICHE DÉGUSTATION"))
        nom = l[k + 1] if k + 1 < len(l) else "Sans titre"
        sous = l[k + 2] if k + 2 < len(l) else ""
        f = _fiche(pg, nom, sous.split("·")[0].strip(), lot)
        mill = re.search(r"MILLÉSIME\s*:\s*([^\s·]+)", sous)
        if mill: f["millesime"] = mill.group(1)
        fiches.append(f)
    return fiches

def p_spiritueux(pages, lot):
    fiches = []
    for pg in pages:
        if "PRODUCTEUR / MARQUE" not in pg: continue
        l = _entete(pg)
        k = next(i for i, x in enumerate(l) if "COLLECTION SPIRITUEUX" in x)
        nom = l[k + 1] if k + 1 < len(l) else "Sans titre"
        cat = l[k + 2] if k + 2 < len(l) and l[k + 2].isupper() else ""
        fiches.append(_fiche(pg, nom, cat, lot))
    return fiches

def p_tableau(pages, lot):
    fiches = []
    for pg in pages:
        if "Producteur" not in pg: continue
        plat = re.sub(r"Producteur\s*/\s*\n\s*domaine", "Producteur / domaine", pg)
        plat = re.sub(r"Cépages\s*/\s*\n\s*composition", "Cépages / composition", plat)
        plat = re.sub(r"Degré\s*\n?\s*d[’']alcool", "Degré d’alcool", plat)
        l = _entete(plat)
        k = next((i for i, x in enumerate(l) if x.startswith("Page ")), 0)
        nom = l[k + 1] if k + 1 < len(l) else "Sans titre"
        f = _fiche(plat, nom, "", lot)
        phrase = None
        for x in reversed(l):
            if x.startswith("http") or x.startswith("•") or x.lower() == "sources": break
            if len(x) > 25: phrase = x; break
        f["phrase"] = f["phrase"] or phrase
        fiches.append(f)
    return fiches

def p_img_titre(pages, lot):
    fiches = []
    for pg in pages:
        if "Producteur" not in pg or "Sommaire" in pg: continue
        l = _entete(pg)
        k = next((i for i, x in enumerate(l) if "FICHE PRODUIT" in x), -1)
        nom = l[k + 1] if 0 <= k < len(l) - 1 else "Sans titre"
        sous = l[k + 2] if 0 <= k < len(l) - 2 else ""
        fiches.append(_fiche(pg, nom, sous, lot))
    return fiches

def p_img_pied(pages, lot):
    fiches = []
    for pg in pages:
        if "Producteur / domaine" not in pg: continue
        l = _entete(pg)
        nom, cat = "Sans titre", ""
        for i, x in enumerate(l):
            if re.match(r"C & Wine - Fiches produits Page", x) and i + 1 < len(l):
                nom, cat = l[i + 1], (l[i + 2] if i + 2 < len(l) else "")
                break
        fiches.append(_fiche(pg, nom, cat, lot))
    return fiches

PARSEURS = dict(verifiees=p_verifiees, degustation=p_degustation, spiritueux=p_spiritueux,
                tableau=p_tableau, img_titre=p_img_titre, img_pied=p_img_pied)

# ------------------------------------------------------------------ pipeline

def normaliser(brut):
    """Applique le masquage des données non vérifiées et met en forme."""
    manques, produit = [], {}
    for cle in ("producteur", "origine", "appellation", "cepages",
                "millesime", "visuel", "nez", "bouche", "accords", "phrase"):
        val, motif = texte_utile(brut.get(cle))
        produit[cle] = val
        if motif == "vide":
            continue                      # champ absent de cette mise en page : pas un manque
        if val is None:
            manques.append((cle, motif))
        elif motif:
            manques.append((cle + " (partiel)", motif))

    deg, cont = alcool_contenance(brut.get("alcool_brut"))
    val_alc, motif_alc = texte_utile(brut.get("alcool_brut"))
    produit["alcool"] = deg
    produit["contenance"] = cont
    if deg is None:
        manques.append(("alcool", motif_alc or brut.get("alcool_brut") or "absent"))

    # millésime : on ne garde qu'une année ; « non millésimé » est un état normal
    # (spiritueux, liqueurs) et non une information manquante.
    brut_mill = brut.get("millesime") or ""
    produit["vieillissement"] = None
    v = re.search(r"vieillissement\s*:?\s*([^;.]+)", brut_mill, re.I)
    if v: produit["vieillissement"] = v.group(1).strip()
    if re.search(r"non\s+millésim|sans\s+millésime", brut_mill, re.I):
        produit["millesime"] = None
        manques[:] = [m for m in manques if not m[0].startswith("millesime")]
    else:
        an = re.search(r"\b(19|20)\d{2}\b", produit["millesime"] or "")
        produit["millesime"] = an.group(0) if an else None

    produit["nom"] = re.sub(r"\s+", " ", brut["nom"]).strip(" —-·")
    produit["type"] = deduire_type(brut.get("categorie"), produit["nom"],
                                   produit.get("appellation"), produit.get("cepages"),
                                   produit.get("origine"))
    produit["photos"] = brut.get("photos", [])
    produit["sources"] = brut.get("sources", [])
    produit["lot"] = brut.get("lot")
    produit["prix"] = None                       # « prix en boutique » pour l'instant
    if produit["type"] in ("spiritueux", "biere") and not produit["millesime"]:
        manques[:] = [m for m in manques if not m[0].startswith("millesime")]

    produit["id"] = slug(produit["nom"], produit["millesime"] or "")
    return produit, manques

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dossier")
    ap.add_argument("--json", default="data/produits.json")
    ap.add_argument("--manques", default="data/manques.csv")
    a = ap.parse_args()

    produits, tous_manques, resume = [], [], []
    for pdf in sorted(Path(a.dossier).glob("*.pdf")):
        pages = pages_de(pdf)
        fmt = detecter_format("\n".join(pages[:3]))
        if fmt == "inconnu":
            resume.append((pdf.name, "?", 0, "format non reconnu")); continue
        brutes = PARSEURS[fmt](pages, pdf.stem)
        for b in brutes:
            p, m = normaliser(b)
            produits.append(p)
            for champ, motif in m:
                tous_manques.append((p["id"], p["nom"], champ, motif))
        resume.append((pdf.name, fmt, len(brutes), ""))

    # dédoublonnage : une version « REPRIS » remplace la version d'origine
    par_id = {}
    for p in produits:
        vieux = par_id.get(p["id"])
        if not vieux or "REPRIS" in (p["lot"] or ""):
            par_id[p["id"]] = p
    produits = sorted(par_id.values(), key=lambda p: (p["type"], p["nom"]))

    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    json.dump(produits, open(a.json, "w"), ensure_ascii=False, indent=1)
    with open(a.manques, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "produit", "champ", "ce que dit la fiche"])
        w.writerows(tous_manques)

    print(f"{'PDF':<52} {'format':<12} fiches")
    for nom, fmt, n, note in resume:
        print(f"{nom[:50]:<52} {fmt:<12} {n:>4} {note}")
    print(f"\n{len(produits)} produits -> {a.json}")
    print(f"{len(tous_manques)} informations à compléter -> {a.manques}")
    types = {}
    for p in produits: types[p["type"]] = types.get(p["type"], 0) + 1
    print("Répartition :", ", ".join(f"{k} {v}" for k, v in sorted(types.items())))
    sans_photo = [p for p in produits if not p["photos"]]
    print(f"Sans photo : {len(sans_photo)} / {len(produits)}")

if __name__ == "__main__":
    main()
