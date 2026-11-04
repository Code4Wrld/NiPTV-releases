"""Index des photos de joueurs (bustes) pour les pages Sports.

FootyLogos publie les photos officielles de la saison, détourées, mais son catalogue pèse
16 Mo : trop lourd pour une box. Ce script en tire un petit fichier par championnat
(nom du joueur -> photo en buste et club), à publier dans le dépôt public des versions :

    python tools/joueurs/index.py <dossier de sortie>

puis pousser le dossier dans NiPTV-releases, sous data/joueurs/ (servi par GitHub Pages).
L'appli ne lit que le fichier du championnat affiché. À relancer après les transferts.
"""
import json
import os
import re
import sys
import unicodedata
import urllib.request

SITE = "https://www.footylogos.com"
UA = {"User-Agent": "Mozilla/5.0"}

# Le format « buste » de chaque championnat (les autres sont en pied, en action ou en rond).
BUSTS = {
    "ligue-1": "bust",
    "premier-league": "portrait",
    "laliga": "square",
    "serie-a": "portrait",
    "bundesliga": "front",
    "liga-portugal": "portugal_head",
    "eredivisie": "eredivisie_portrait",
}
# En dernier recours : la tête de la Ligue des champions (sur fond blanc).
UCL = "ucl_head"
# Les fichiers produits : un par championnat, plus la Ligue des champions.
FILES = list(BUSTS) + ["ucl"]


def norm(text):
    text = "".join(c for c in unicodedata.normalize("NFD", text.lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()


def main(out):
    page = get(SITE + "/fr/player-pngs/ligue-1").decode("utf-8", "replace")
    bank = re.search(r'data-bank="([^"]+)"', page).group(1)
    catalogue = json.loads(get(SITE + bank))
    files = {name: {} for name in FILES}
    for player in catalogue["players"]:
        shots = [a for a in player.get("a", []) if not a.get("archive")]
        # Son buste le plus récent : d'abord celui de son championnat, sinon celui de la C1.
        best = sorted((a for a in shots if BUSTS.get(a["g"]) == a["f"]), key=lambda a: a["s"], reverse=True)
        best += sorted((a for a in shots if a["f"] == UCL), key=lambda a: a["s"], reverse=True)
        if not best:
            continue
        photo = [best[0]["k"], norm(best[0]["c"])]
        names = {norm(n) for n in [player["n"]] + player.get("alias", []) if norm(n)}
        # Rangé dans chaque compétition qu'il joue cette saison ou la précédente.
        for m in player.get("m", []):
            league = m["g"] if m["g"] in files else None
            if league and m["s"] >= "2025/26":
                for n in names:
                    entry = files[league].setdefault(n, [])
                    if photo not in entry:
                        entry.append(photo)
    os.makedirs(out, exist_ok=True)
    for league, players in files.items():
        text = json.dumps({"v": 1, "p": players}, separators=(",", ":"), ensure_ascii=False)
        with open(os.path.join(out, league + ".json"), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{league}: {len(players)} joueurs, {len(text) // 1024} Ko")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "joueurs")
