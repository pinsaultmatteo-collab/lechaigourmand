#!/usr/bin/env python3
"""Pose les prix appariés sur les fiches — « python3 outils/poser_prix.py ».

    python3 outils/poser_prix.py            écrit dans data/produits.json
    python3 outils/poser_prix.py --base     écrit aussi dans Supabase
    python3 outils/poser_prix.py --simuler  n'écrit rien, montre seulement

Seuls les appariements nets sont posés. Le reste garde « prix en boutique »,
comme le client l'a demandé, et attend une relecture dans
data/prix-a-verifier.csv.

Vers la base, on ne touche QUE la colonne prix, ligne par ligne : les fiches
qu'Adrien a corrigées depuis l'import ne doivent pas être écrasées.
"""
import getpass
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apparier_prix import apparier                                         # noqa: E402
from importer_produits import URL, verifier_cle                            # noqa: E402

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FICHIER = os.path.join(RACINE, "data/produits.json")


def texte_prix(v):
    """Un nombre propre, sans zéro inutile : « 23 », « 13.5 », « 9.9 »."""
    return f"{v:.2f}".rstrip("0").rstrip(".")


def patcher(reference, prix, cle):
    corps = json.dumps({"prix": prix}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{URL}/rest/v1/produits?reference=eq.{urllib.parse.quote(reference)}",
        data=corps, method="PATCH",
        headers={"apikey": cle, "Authorization": "Bearer " + cle,
                 "Content-Type": "application/json; charset=utf-8",
                 "Prefer": "return=minimal"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main():
    simuler = "--simuler" in sys.argv
    vers_base = "--base" in sys.argv

    resultats, _, _ = apparier()
    poses = {r["fiche"]["id"]: r for r in resultats if r["net"]}

    fiches = json.load(open(FICHIER, encoding="utf-8"))
    change, efface = 0, 0
    for f in fiches:
        r = poses.get(f["id"])
        if r:
            nouveau = texte_prix(r["tarif"]["prix"])
            if f.get("prix") != nouveau:
                change += 1
            f["prix"] = nouveau
        elif f.get("prix"):
            # Le tarif fait foi : un prix qu'il ne confirme plus s'en va.
            f["prix"] = None
            efface += 1

    avec = sum(1 for f in fiches if f.get("prix"))
    print(f"  {avec} fiches avec un prix, {len(fiches) - avec} en « prix en boutique »")
    print(f"  ({change} posés ou modifiés, {efface} retirés)\n")

    for f in [x for x in fiches if x.get("prix")][:8]:
        print(f"    {f['prix']:>7} €   {f['nom'][:56]}")

    if simuler:
        print("\n  --simuler : rien n'a été écrit.")
        return

    json.dump(fiches, open(FICHIER, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"\n  ✓ data/produits.json")

    if not vers_base:
        print("    (--base pour envoyer aussi dans Supabase)")
        return

    cle = getpass.getpass("\n  Collez la clé secrète Supabase (rien ne s'affiche) : ").strip()
    probleme = verifier_cle(cle)
    if probleme:
        print(f"  ✗ {probleme}")
        sys.exit(1)

    # Une fiche par requête : à 255 requêtes, la barre évite de se demander si
    # la machine a planté. Elle se réécrit sur place, sans dérouler l'écran.
    total, envoyes, rates = len(fiches), 0, []
    print()
    for i, f in enumerate(fiches, 1):
        try:
            patcher(f["id"], f.get("prix"), cle)
            envoyes += 1
        except urllib.error.HTTPError as err:
            rates.append((f["id"], err.code, err.read()[:120].decode("utf-8", "replace")))
        except Exception as err:
            rates.append((f["id"], "—", str(err)[:120]))
        plein = round(28 * i / total)
        print(f"\r  [{'█' * plein}{'·' * (28 - plein)}] {i}/{total}", end="", flush=True)
    print(f"\r  ✓ {envoyes} fiches mises à jour dans Supabase" + " " * 20)
    for ref, code, detail in rates[:10]:
        print(f"    ✗ {ref} : {code} {detail}")


if __name__ == "__main__":
    main()
