#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Envoie les 254 fiches de data/produits.json dans la table Supabase.

À lancer une seule fois, depuis votre machine, avec la clé de service dans
l'environnement — elle ne touche ni le dépôt ni le navigateur :

    export SUPABASE_SERVICE_KEY='la-cle-service_role'
    python3 outils/importer_produits.py

Rejouable sans danger : les fiches sont appariées sur leur `reference`
(l'identifiant d'origine), donc un second passage met à jour au lieu de
dupliquer. Options : --simuler pour voir sans écrire.
"""
import json, os, sys, urllib.request, urllib.error

URL = "https://xdbudbqqwfyfcivnvqzu.supabase.co"
TAILLE_LOT = 40          # PostgREST accepte de gros lots, on reste raisonnable

CHAMPS = ("nom", "type", "producteur", "appellation", "origine", "cepages",
          "millesime", "alcool", "contenance", "visuel", "nez", "bouche",
          "accords", "phrase", "style", "vieillissement", "lot", "prix")

def ligne(p, rang):
    d = {c: (p.get(c) or None) for c in CHAMPS}
    d["reference"] = p["id"]
    d["sources"] = p.get("sources") or []
    d["images"] = p.get("images") or []
    d["rang"] = rang
    d["statut"] = "publie"
    d["prix"] = str(d["prix"]) if d["prix"] is not None else None
    d["alcool"] = str(d["alcool"]) if d["alcool"] is not None else None
    return d

def envoyer(lot, cle):
    corps = json.dumps(lot, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        URL + "/rest/v1/produits?on_conflict=reference",
        data=corps, method="POST",
        headers={"apikey": cle, "Authorization": "Bearer " + cle,
                 "Content-Type": "application/json; charset=utf-8",
                 "Prefer": "resolution=merge-duplicates,return=minimal"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status

def main():
    simuler = "--simuler" in sys.argv
    cle = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
    if not cle and not simuler:
        sys.exit("SUPABASE_SERVICE_KEY manquante.\n"
                 "  export SUPABASE_SERVICE_KEY='...'  puis relancez.")
    if cle:
        import base64
        charge = cle.split(".")[1]
        role = json.loads(base64.urlsafe_b64decode(charge + "=" * (-len(charge) % 4))).get("role")
        if role != "service_role":
            sys.exit(f"Cette clé a le rôle « {role} », il faut la clé service_role.")

    produits = json.load(open("data/produits.json", encoding="utf-8"))
    lignes = [ligne(p, i) for i, p in enumerate(produits)]
    avec_photo = sum(1 for l in lignes if l["images"])
    avec_source = sum(1 for l in lignes if l["sources"])
    print(f"{len(lignes)} fiches prêtes — {avec_photo} avec photo, {avec_source} avec sources")
    if simuler:
        print(json.dumps(lignes[0], ensure_ascii=False, indent=2)[:600])
        print("\n(simulation : rien n'a été envoyé)")
        return

    envoyees = 0
    for i in range(0, len(lignes), TAILLE_LOT):
        lot = lignes[i:i + TAILLE_LOT]
        try:
            envoyer(lot, cle)
        except urllib.error.HTTPError as e:
            sys.exit(f"\nÉchec au lot {i // TAILLE_LOT + 1} : {e.code} {e.read().decode()[:300]}")
        envoyees += len(lot)
        print(f"  {envoyees}/{len(lignes)}", end="\r", flush=True)
    print(f"  {envoyees}/{len(lignes)} fiches importées ✓")
    print("\nRelancez ensuite : python3 outils/generer_catalogue.py")

if __name__ == "__main__":
    main()
