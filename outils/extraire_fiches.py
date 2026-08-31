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

# Détection de la catégorie. Certains mots ne sont fiables que dans le nom,
# le style ou le lot : « ambré » ou « malt » décrivent aussi des rhums, et
# « jus de » apparaît dans la composition de liqueurs.
BIERE_NOM = (r"\bbi[èe]res?\b|\bblonde\b|\bbrune\b|ambr[ée]e|\btriple\b|\blager\b|"
             r"\bstout\b|\bipa\b|pale ale|\bale\b|midinette|barriqu[ée]e")
EPICERIE_NOM = (r"\bmiel\b|confiture|\bjus\b|huile d[’']olive|terrine|conserve|"
                r"chocolat|tapenade|verger")
MOTS_TYPE = [
    ("spiritueux", r"rhum|whisky|whiskey|\bgin\b|vodka|liqueur|arm[ao]gnac|cognac|tequila|"
                   r"mezcal|pastis|absinthe|eau-de-vie|infusion|mac[ée]ration|distill|"
                   r"ap[ée]ritif|spritz|vermouth"),
    ("bulles",     r"champagne|cr[ée]mant|effervescent|mousseux|brut nature|p[ée]tillant|prosecco|\bcava\b"),
    ("moelleux",   r"moelleux|liquoreux|doux naturel|macvin|vin de liqueur|sauternes|juran[çc]on"),
    ("rose",       r"\bros[ée]s?\b|\brosato\b|\brosado\b"),
    ("blanc",      r"vin blanc|\bblancs?\b|\bbianco\b|\bbranco\b|\bblanco\b|chardonnay|sauvignon|chenin|"
                   r"muscadet|riesling|vermentino|albari[nñ]o|viognier|s[ée]millon|gew[üu]rztraminer|"
                   r"pinot gris|melon de bourgogne|clairette|rolle|mauzac|savagnin|greco|fiano|"
                   r"gr[üu]ner veltliner|grillo|manseng|muscaris|souvignier|verdejo|colombard|"
                   r"marsanne|roussanne|petit meslier|altesse"),
    ("rouge",      r"vin rouge|\brouges?\b|\brosso\b|\btinto\b|syrah|grenache|malbec|merlot|cabernet|"
                   r"pinot noir|pinot nero|tempranillo|tannat|n[ée]grette|carignan|mourv[èe]dre|cinsault|"
                   r"gamay|sangiovese|nebbiolo|shiraz|aglianico|montepulciano|primitivo|dolcetto|"
                   r"barbera|nerello|monica|trousseau|poulsard|zweigelt|corvina|touriga|margaux|"
                   r"m[ée]doc|saint-[ée]milion"),
]

def deduire_type(nom, style, categorie, lot, *autres):
    fort = " ".join(x for x in (nom, style, categorie) if x).lower()
    tout = (fort + " " + " ".join(x for x in autres if x)).lower()
    if lot and re.search(r"_bieres", lot.lower()):        return "biere"
    if re.search(BIERE_NOM, fort):                        return "biere"
    if re.search(EPICERIE_NOM, fort):                     return "epicerie"
    for nom_type, motif in MOTS_TYPE:
        if re.search(motif, tout): return nom_type
    return "autre"

def photos_de(txt):
    """Repère IMG_3013, IMG_3013-3017 (plage) et IMG_3338.jpeg."""
    vues = set()
    for m in re.finditer(r"IMG[_\\ ]?(\d{4})(?:\s*[-–]\s*(\d{4}))?", txt):
        a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else a
        if b < a or b - a > 12: b = a          # « 3160_3179 » d'un nom de lot : on ignore la plage
        for n in range(a, b + 1): vues.add(f"IMG_{n}")
    return sorted(vues)

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


# --- petites aides de découpage ------------------------------------------------

# Toutes les étiquettes rencontrées dans les six mises en page. Le découpage
# se fait en repérant leurs positions : une valeur s'arrête à l'étiquette suivante,
# ce qui évite qu'un champ déborde sur le suivant.
ETIQUETTES = [
    r"Producteur\s*/\s*domaine", r"PRODUCTEUR\s*/\s*MARQUE", r"Producteur", r"Domaine",
    r"Origine\s*/\s*appellation", r"Origine", r"Appellation", r"Terroir",
    r"Type", r"Couleur", r"Culture", r"Certification",
    r"STYLE\s*/\s*TYPE", r"Style\s*/\s*type", r"STYLE", r"Style",
    r"Cépages?\s*\(s\)\s*/\s*composition", r"Cépages?\s*/\s*composition",
    r"Cépages?\s*/\s*assemblage", r"COMPOSITION\s*/\s*ÉLABORATION",
    r"Cépages?\s*\(s\)", r"Cépages?", r"Assemblage",
    r"Accords conseillés", r"Degré", r"Cépage\s*/\s*composition", r"Cuvée",
    r"Profil de dégustation", r"Précision sur les sources",
    r"Degré\s*/\s*format", r"FORMAT\s*/\s*ALCOOL", r"ALCOOL\s*/\s*CONTENANCE",
    r"Degré alcoolique", r"Degré d[’']alcool", r"Degrés", r"Alcool", r"Format",
    r"MILLÉSIME\s*/\s*VIEILLISSEMENT", r"Millésime", r"Vieillissement",
    r"Vinification\s*/\s*élevage", r"Élevage",
    r"NOTES DE DÉGUSTATION", r"Notes de dégustation", r"Note de dégustation", r"Dégustation",
    r"FICHE TECHNIQUE",
    r"VISUEL\s*/\s*NEZ", r"VISUEL\s*/\s*ROBE", r"VISUEL", r"Visuel", r"ROBE", r"Robe",
    r"NEZ", r"Nez", r"BOUCHE", r"Bouche", r"FINALE", r"Finale",
    r"SERVICE\s*&\s*ACCORDS", r"Service\s*&\s*accords", r"Service",
    r"ACCORDS METS\s*&\s*VINS?", r"ACCORDS[^\n:]*", r"Accords[^\n:]*",
    r"FIABILITÉ ET MILLÉSIME", r"Fiabilité et limites", r"Fiabilité[^\n:]*",
    r"PHRASE COURTE\s*[—-]\s*CARTE RESTAURANT", r"PHRASE COURTE POUR CARTE RESTAURANT",
    r"PHRASE POUR LA CARTE DU RESTAURANT", r"PHRASE POUR UNE CARTE DE RESTAURANT",
    r"Phrase pour la carte du restaurant", r"Phrase courte pour la carte",
    r"PHRASE CARTE RESTAURANT", r"PHRASE COURTE POUR CARTE DE RESTAURANT",
    r"Phrase courte pour une carte de restaurant", r"Phrase[^\n:]*carte[^\n:]*",
    r"SOURCES VÉRIFIÉES", r"Sources vérifiables", r"SOURCES", r"Sources",
    r"Photo\(s\)", r"Photos", r"Photographies correspondantes", r"Visuel fourni",
]
_SEP = re.compile(r"^[ \t]*(" + "|".join(ETIQUETTES) + r")[ \t]*:?[ \t]*$|"
                  r"^[ \t]*(" + "|".join(ETIQUETTES) + r")[ \t]*:[ \t]*(.*)$",
                  re.M | re.I)

# Les étiquettes se retrouvent parfois coupées en deux lignes par la mise en page
_COUPURES = [
    (r"Cépages?\s*/\s*\n\s*composition", "Cépage / composition"),
    (r"Cépages?\s*/\s*\n\s*assemblage", "Cépages / assemblage"),
    (r"Producteur\s*/\s*\n\s*domaine", "Producteur / domaine"),
    (r"Origine\s*/\s*\n\s*appellation", "Origine / appellation"),
    (r"Degré\s*\n\s*d[’']alcool", "Degré d’alcool"),
    (r"ACCORDS METS\s*&?\s*\n\s*VINS?", "ACCORDS METS & VIN"),
    (r"Accords\s*\n\s*conseillés", "Accords conseillés"),
    (r"MILLÉSIME\s*/\s*\n\s*VIEILLISSEMENT", "MILLÉSIME / VIEILLISSEMENT"),
    (r"VISUEL\s*/\s*\n\s*(ROBE|NEZ)", r"VISUEL / \1"),
    (r"SERVICE\s*&\s*\n\s*ACCORDS", "SERVICE & ACCORDS"),
    (r"Phrase courte pour une\s*\n\s*carte", "Phrase courte pour une carte"),
    (r"Fiabilité\s*\n\s*et limites", "Fiabilité et limites"),
]

def recoller(bloc):
    for motif, remplacement in _COUPURES:
        bloc = re.sub(motif, remplacement, bloc, flags=re.I)
    return bloc

def decouper(bloc):
    """Renvoie {etiquette_normalisée: valeur} en tranchant le texte aux étiquettes."""
    bloc = recoller(bloc)
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

# Lignes qui ne peuvent pas être un nom de produit (bandeaux, pagination, étiquettes)
_PAS_UN_TITRE = re.compile(
    r"^\s*$|^\d+\s*(/\s*\d+)?$|^page\s|^fiche\b|^référence\b|^lot\b|^sommaire$|"
    r"^c\s*&\s*wine|^fiches?\b|^données|^visuel fourni|^notes? de dégustation$|"
    r"^fiche technique$|^informations|^aucun|^document|^la couleur|^pour les spiritueux|"
    r"^chaque fiche|^les descriptions|^lorsqu|^une fiche par", re.I)
_EST_ETIQUETTE = re.compile(r"^\s*(" + "|".join(ETIQUETTES) + r")\s*:?\s*$", re.I)

def _titre_et_sous_titre(pg):
    """Le nom du produit est la première ligne « parlante » de la page."""
    lignes = [l.strip() for l in pg.split("\n") if l.strip()]
    titre, sous = None, ""
    for i, l in enumerate(lignes):
        if _PAS_UN_TITRE.match(l) or _EST_ETIQUETTE.match(l):
            continue
        if len(l) < 3 or l.startswith("http") or l.startswith("•"):
            continue
        titre = l
        # un titre qui déborde sur la ligne suivante (fin en tiret, suite en minuscule)
        j = i + 1
        while j < len(lignes):
            suite = lignes[j]
            if titre.rstrip().endswith(("-", "–", "—", "«", ",")) or re.match(r"^[a-zà-ÿ]", suite):
                if _EST_ETIQUETTE.match(suite) or _PAS_UN_TITRE.match(suite): break
                titre = titre.rstrip(" -–—") + " " + suite
                j += 1
                continue
            break
        for suite in lignes[j:j + 2]:
            if _EST_ETIQUETTE.match(suite) or _PAS_UN_TITRE.match(suite):
                break
            sous = suite
            break
        break
    return (titre or "Sans titre"), sous

def _producteur_du_sous_titre(sous):
    """« Casa Vinicola Corvezzo - Italie - 10,5 % vol. » -> « Casa Vinicola Corvezzo »."""
    if not sous: return None
    s = re.sub(r"IMG[_ ]?\d{4}(\s*[-–]\s*\d{4})?", "", sous)
    s = re.sub(r"\d{1,2}[.,]?\d*\s*%\s*vol\.?", "", s)
    s = re.sub(r"\b(19|20)\d{2}\b", "", s).strip(" -–·•,")
    if not s: return None
    for bout in re.split(r"\s+[-–•·]\s+|\s{2,}", s):
        bout = bout.strip(" -–·•,")
        # on saute les appellations et les couleurs pour ne garder que le domaine
        if not bout or re.match(r"^(AOP|AOC|IGP|D\.?O\.?|Vin de France|Rouge|Blanc|Rosé)", bout, re.I):
            continue
        if len(bout) > 2: return bout
    return None

def _prose_degustation(txt):
    """Extrait robe/nez/bouche d'un paragraphe rédigé d'un seul tenant."""
    if not txt: return (None, None, None)
    def bout(cle, arret):
        m = re.search(rf"\b{cle}\b\s*[.:]?\s*(.+?)(?=\s\b(?:{arret})\b\s*[.:]|$)",
                      txt, re.I | re.S)
        if not m: return None
        v = re.sub(r"\s+", " ", m.group(1)).strip(" .;,")
        return v or None
    return (bout("robe", "nez|bouche"), bout("nez", "bouche"), bout("bouche", "sources|accords"))

def p_generique(pages, lot):
    """Une fiche par page dans (presque) toutes les mises en page de C & Wine.
    Le découpage par étiquettes rend le parseur indépendant de la disposition."""
    fiches = []
    for pg in pages:
        if re.search(r"^\s*SOMMAIRE\s*$", pg, re.M): continue
        c = decouper(pg)
        # une fiche porte au moins trois étiquettes dont une de dégustation
        if len(c) < 3: continue
        if not any(re.search(r"nez|bouche|robe|visuel|dégustation", k) for k in c):
            continue
        titre, sous = _titre_et_sous_titre(pg)

        visuel = prendre(c, "visuel / robe", "visuel", "robe")
        nez = prendre(c, "nez")
        # certaines fiches fusionnent « VISUEL / NEZ » : on rescinde sur « Nez ... »
        bloc_prose = prendre(c, "dégustation", "profil de dégustation", "notes de dégustation")
        if bloc_prose and not (visuel and nez):
            pr_robe, pr_nez, pr_bouche = _prose_degustation(bloc_prose)
            visuel = visuel or pr_robe
            nez = nez or pr_nez
            c.setdefault("bouche", pr_bouche or "")
        fusion = prendre(c, "visuel / nez")
        if fusion and not (visuel and nez):
            coupe = re.split(r"\bnez\b\s*:?\s*", fusion, maxsplit=1, flags=re.I)
            visuel = visuel or coupe[0].strip()
            nez = nez or (coupe[1].strip() if len(coupe) > 1 else None)

        producteur = prendre(c, "producteur / domaine", "producteur / marque",
                             "producteur", "domaine") or _producteur_du_sous_titre(sous)
        fiches.append(dict(
            nom=titre, categorie=" ".join(x for x in (sous, prendre(c, "type", "couleur") or "") if x),
            producteur=producteur,
            origine=prendre(c, "origine / appellation", "origine", "terroir"),
            appellation=prendre(c, "appellation"),
            cepages=prendre(c, "cépage(s) / composition", "cépages / composition",
                            "cépages / assemblage", "composition / élaboration",
                            "cépage(s)", "cépages", "cépage", "assemblage"),
            alcool_brut=prendre(c, "degré / format", "format / alcool", "alcool / contenance",
                                "degré alcoolique", "degré d’alcool", "degré d'alcool",
                                "degrés", "alcool", "format"),
            millesime=prendre(c, "millésime / vieillissement", "millésime", "vieillissement"),
            style=prendre(c, "style / type", "style"),
            visuel=visuel, nez=nez, bouche=prendre(c, "bouche"),
            accords=prendre(c, "accords mets & vins", "accords mets & vin", "accords",
                            "service & accords", "service"),
            phrase=prendre(c, "phrase courte — carte restaurant", "phrase courte - carte restaurant",
                           "phrase courte pour carte restaurant", "phrase pour la carte du restaurant",
                           "phrase pour une carte de restaurant", "phrase courte pour la carte",
                           "phrase carte restaurant", "phrase"),
            sources=urls_de(pg), photos=photos_de(pg), lot=lot))
    return fiches

def detecter_format(texte):
    return "generique"

PARSEURS = dict(generique=p_generique)

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

    if produit.get("phrase"):
        # la phrase de carte s'arrête avant les sources (parfois collées derrière)
        # une accroche de carte ne cite jamais ses sources : on coupe au premier marqueur
        ph = re.split(r"\bSources?\b|https?://", produit["phrase"])[0].strip(" .;,:")
        produit["phrase"] = (ph + ".") if ph else None
    produit["nom"] = re.sub(r"\s+", " ", brut["nom"]).strip(" —-·")
    produit["style"], _ = texte_utile(brut.get("style"))
    produit["type"] = deduire_type(produit["nom"], produit.get("style"),
                                   brut.get("categorie"), brut.get("lot"),
                                   produit.get("appellation"), produit.get("cepages"),
                                   produit.get("origine"), produit.get("visuel"))
    produit["style"], _ = texte_utile(brut.get("style"))
    produit["photos"] = brut.get("photos", [])
    produit["sources"] = brut.get("sources", [])
    produit["lot"] = brut.get("lot")
    produit["prix"] = None                       # « prix en boutique » pour l'instant
    if produit["type"] == "autre" and produit.get("alcool"):
        try:
            if float(produit["alcool"].replace(",", ".")) >= 16: produit["type"] = "spiritueux"
        except ValueError: pass

    if produit["type"] in ("spiritueux", "biere") and not produit["millesime"]:
        manques[:] = [m for m in manques if not m[0].startswith("millesime")]

    produit["id"] = slug(produit["nom"], produit["millesime"] or "")
    return produit, manques

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dossier")
    ap.add_argument("--json", default="data/produits.json")
    ap.add_argument("--manques", default="data/manques.csv")
    ap.add_argument("--photos", default="../contenu-visuel/photos-produits-bouteilles",
                    help="dossier des photos, pour signaler celles qui manquent")
    ap.add_argument("--rapport-photos", default="data/photos-manquantes.txt")
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

    # rapport photos : ce que les fiches réclament et que le dossier n'a pas
    dossier = Path(a.photos)
    if dossier.is_dir():
        dispo = {f.stem for f in dossier.iterdir() if f.is_file()}
        reclamees = {ph for p in produits for ph in p["photos"]}
        absentes, inutilisees = reclamees - dispo, dispo - reclamees

        def plages(noms):
            nums = sorted(int(n.split("_")[1]) for n in noms if "_" in n)
            if not nums: return "aucune"
            out, deb, prev = [], nums[0], nums[0]
            for n in nums[1:]:
                if n == prev + 1: prev = n; continue
                out.append((deb, prev)); deb = prev = n
            out.append((deb, prev))
            return ", ".join(f"IMG_{a}" if a == b else f"IMG_{a}→IMG_{b}" for a, b in out)

        with open(a.rapport_photos, "w") as f:
            f.write("PHOTOS — état des lieux\n" + "=" * 60 + "\n\n")
            f.write(f"Photos réclamées par les fiches : {len(reclamees)}\n")
            f.write(f"Présentes dans le dossier       : {len(reclamees & dispo)}\n\n")
            f.write(f"MANQUANTES ({len(absentes)}) — à demander au fournisseur :\n  {plages(absentes)}\n\n")
            f.write(f"PRÉSENTES MAIS JAMAIS CITÉES ({len(inutilisees)}) :\n  {plages(inutilisees)}\n\n")
            f.write(f"PRODUITS SANS AUCUNE PHOTO ({len(sans_photo)}) :\n")
            for p in sans_photo:
                f.write(f"  - {p['nom']}  [{p['lot']}]\n")
        print(f"Rapport photos -> {a.rapport_photos}")

if __name__ == "__main__":
    main()
