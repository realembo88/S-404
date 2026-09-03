#!/usr/bin/env python3
"""
PUBG Clan Sync
==============
Holt die Matches der Clan-Mitglieder ueber die offizielle PUBG-API und haengt
sie an eine CSV-Datei an. Bereits erfasste Matches werden uebersprungen, das
Skript kann also beliebig oft laufen.

WICHTIG: Die PUBG-API haelt Matchdaten nur 14 Tage vor. Wer laenger als zwei
Wochen nicht synchronisiert, verliert die Matches dazwischen endgueltig.
Empfehlung: mindestens einmal pro Woche laufen lassen.

EINRICHTUNG
-----------
1. Python 3 installieren (python.org, beim Setup "Add to PATH" anhaken).
2. In der Kommandozeile:  pip install requests
3. Die Datei api_key.txt neben dieses Skript legen und den Key hineinkopieren.
   Alternativ: Umgebungsvariable PUBG_API_KEY setzen.
4. Starten mit:  python pubg_clan_sync.py

Ergebnis: pubg_matches.csv im selben Ordner.
"""

import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Modul 'requests' fehlt. Bitte ausfuehren:  pip install requests")

# ---------------------------------------------------------------- Konfiguration

SPIELER = ["real_embo", "Baerli162", "Lacan123", "Thalanthyr"]
SHARD = "steam"                      # PC ueber Steam
HIER = Path(__file__).resolve().parent
CSV_PFAD = HIER / "pubg_matches.csv"
WAFFEN_PFAD = HIER / "weapons.csv"
CLAN_PFAD = HIER / "clan.json"
KEY_PFAD = HIER / "api_key.txt"

BASIS = f"https://api.pubg.com/shards/{SHARD}"
CLAN_IDS: dict = {}


def api_key() -> str:
    key = os.environ.get("PUBG_API_KEY", "").strip()
    if not key and KEY_PFAD.exists():
        key = KEY_PFAD.read_text(encoding="utf-8").strip()
    if not key:
        sys.exit(
            f"Kein API-Key gefunden.\n"
            f"Lege den Key in {KEY_PFAD} ab oder setze PUBG_API_KEY."
        )
    return "".join(key.split())        # Zeilenumbrueche aus dem Copy-Paste entfernen


KOPF = {
    "Authorization": f"Bearer {api_key()}",
    "Accept": "application/vnd.api+json",
    "Accept-Encoding": "gzip",
}

# ------------------------------------------------------------------ API-Zugriff

def hole(url: str, versuche: int = 4) -> dict:
    """GET mit Wiederholung bei Rate-Limit (HTTP 429)."""
    for i in range(versuche):
        r = requests.get(url, headers=KOPF, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            warte = int(r.headers.get("Retry-After", 12)) + 2
            print(f"   Rate-Limit erreicht, warte {warte}s ...")
            time.sleep(warte)
            continue
        if r.status_code == 401:
            sys.exit("API-Key wurde abgelehnt (401). Key pruefen.")
        if r.status_code == 404:
            return {}
        r.raise_for_status()
    sys.exit("Rate-Limit dauerhaft erreicht. Spaeter erneut versuchen.")


WAFFEN = {
    "HK416":"M416","AK47":"AKM","BerylM762":"Beryl M762","SCAR-L":"SCAR-L","G36C":"G36C",
    "QBZ95":"QBZ95","AUG":"AUG A3","Groza":"Groza","M16A4":"M16A4","Mk47Mutant":"Mk47 Mutant",
    "ACE32":"ACE32","FAMAS":"FAMAS","K2":"K2","Mini14":"Mini 14","SKS":"SKS","SLR":"SLR",
    "QBU88":"QBU","Mk14":"Mk14","Mk12":"Mk12","VSS":"VSS","Kar98k":"Kar98k","M24":"M24",
    "AWM":"AWM","Win94":"Win94","LynxAMR":"Lynx AMR","Mosin":"Mosin Nagant","UZI":"Micro UZI",
    "UMP":"UMP45","Vector":"Vector","Thompson":"Tommy Gun","BizonPP19":"PP-19 Bizon",
    "MP5K":"MP5K","P90":"P90","JS9":"JS9","DP12":"DBS","Saiga12":"S12K","Winchester":"S1897",
    "Berreta686":"S686","Sawnoff":"Sawed-off","M249":"M249","DP28":"DP-28","MG3":"MG3",
    "Crossbow":"Armbrust","M9":"P92","G18":"P18C","M1911":"P1911","NagantM1895":"R1895",
    "Rhino":"R45","DesertEagle":"Deagle","Pan":"Bratpfanne","Machete":"Machete",
    "Crowbar":"Brecheisen","Sickle":"Sichel","Grenade":"Granate","Molotov":"Molotow",
    "FlareGun":"Leuchtpistole","MortarProjectile":"Mörser","PanzerFaust100M":"Panzerfaust",
}


def waffenname(code: str) -> str:
    """Item_Weapon_HK416_C -> M416"""
    kern = code.replace("Item_Weapon_", "").replace("Item_Back_", "")
    kern = kern[:-2] if kern.endswith("_C") else kern
    return WAFFEN.get(kern, kern.replace("_", " "))


WAFFEN_FELDER = ["spieler", "waffe", "kills", "schaden", "kopfschuesse", "knocks",
                 "weitester_knock_m", "meiste_knocks_match", "level", "tier"]


def waffen_holen(konten: dict) -> list[dict]:
    """Weapon-Mastery je Spieler. Lebenslange Summen, kein 14-Tage-Fenster."""
    zeilen = []
    for konto_id, name in konten.items():
        daten = hole(f"{BASIS}/players/{konto_id}/weapon_mastery")
        if not daten:
            print(f"   Keine Waffendaten fuer {name}.")
            continue
        summaries = daten.get("data", {}).get("attributes", {}) \
                         .get("weaponSummaries", {})
        for code, w in summaries.items():
            # Seit Patch 18.2 getrennt; die alten StatsTotal werden nicht mehr gepflegt.
            st = w.get("OfficialStatsTotal") or w.get("StatsTotal") or {}
            kills = st.get("Kills", 0)
            if not kills and not st.get("DamagePlayer", 0):
                continue
            zeilen.append({
                "spieler": name,
                "waffe": waffenname(code),
                "kills": kills,
                "schaden": round(st.get("DamagePlayer", 0), 1),
                "kopfschuesse": st.get("HeadShots", 0),
                "knocks": st.get("Groggies", 0),
                "weitester_knock_m": round(st.get("LongestDefeat", 0), 2),
                "meiste_knocks_match": st.get("MostDefeatsInAGame", 0),
                "level": w.get("LevelCurrent", 0),
                "tier": w.get("TierCurrent", 0),
            })
        print(f"   {name}: {sum(1 for z in zeilen if z['spieler']==name)} Waffen")
    return zeilen


def clan_holen(clan_ids: dict) -> dict | None:
    """Clan-Infos. Der Endpunkt liefert nur Name, Tag, Level und Mitgliederzahl."""
    ids = [c for c in clan_ids.values() if c]
    if not ids:
        print("   Kein Clan bei den Spielern hinterlegt.")
        return None
    haeufigste = max(set(ids), key=ids.count)
    daten = hole(f"{BASIS}/clans/{haeufigste}")
    if not daten or not daten.get("data"):
        print("   Clan-Abfrage lieferte nichts.")
        return None
    a = daten["data"]["attributes"]
    im_clan = sorted(n for n, c in clan_ids.items() if c == haeufigste)
    return {
        "clanId": haeufigste,
        "clanName": a.get("clanName", ""),
        "clanTag": a.get("clanTag", ""),
        "clanLevel": a.get("clanLevel", 0),
        "clanMemberCount": a.get("clanMemberCount", 0),
        "erfassteMitglieder": im_clan,
        "stand": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def spieler_und_matches() -> tuple[dict, dict]:
    """Ein Aufruf fuer alle Spieler. Liefert (accountId -> Name, matchId -> set(Namen))."""
    namen = ",".join(SPIELER)
    daten = hole(f"{BASIS}/players?filter[playerNames]={namen}")
    if not daten.get("data"):
        sys.exit(
            "Keine Spieler gefunden. Schreibweise pruefen - die API "
            "unterscheidet Gross- und Kleinschreibung."
        )

    konten, matches = {}, {}
    gefunden = set()
    global CLAN_IDS
    CLAN_IDS = {}
    for p in daten["data"]:
        name = p["attributes"]["name"]
        konten[p["id"]] = name
        CLAN_IDS[name] = p["attributes"].get("clanId") or ""
        gefunden.add(name)
        for m in p["relationships"]["matches"]["data"]:
            matches.setdefault(m["id"], set()).add(name)

    for fehlt in set(SPIELER) - gefunden:
        print(f"   Hinweis: '{fehlt}' wurde nicht gefunden (Schreibweise?).")
    return konten, matches


FELDER = [
    "match_id", "zeitpunkt", "spieler", "modus", "perspektive", "map", "dauer_min",
    "platz", "teams_im_match", "team_id", "kills", "assists", "knocks", "kopfschuesse",
    "schaden", "weitester_kill_m", "ueberlebt_min", "revives", "heilitems", "boosts",
    "waffen", "zu_fuss_m", "gefahren_m", "geschwommen_m", "roadkills", "teamkills",
    "fahrzeuge_zerstoert", "mitspieler",
]

MODUS_MAP = {"solo": "Solo", "duo": "Duo", "squad": "Squad"}


def match_auswerten(match_id: str, wer: set) -> list[dict]:
    daten = hole(f"{BASIS}/matches/{match_id}")
    if not daten:
        return []

    attr = daten["data"]["attributes"]
    roh_modus = attr.get("gameMode", "")
    perspektive = "FPP" if roh_modus.endswith("-fpp") else "TPP"
    basis_modus = roh_modus.replace("-fpp", "")
    modus = MODUS_MAP.get(basis_modus, basis_modus or "unbekannt")

    teilnehmer, rosters = {}, []
    for inc in daten.get("included", []):
        if inc["type"] == "participant":
            teilnehmer[inc["id"]] = inc["attributes"]["stats"]
        elif inc["type"] == "roster":
            rosters.append(inc)

    zeilen = []
    for roster in rosters:
        ids = [p["id"] for p in roster["relationships"]["participants"]["data"]]
        namen_im_team = [teilnehmer[i]["name"] for i in ids if i in teilnehmer]
        if not (wer & set(namen_im_team)):
            continue

        rstat = roster["attributes"]["stats"]
        for pid in ids:
            s = teilnehmer.get(pid)
            if not s or s["name"] not in wer:
                continue
            zeilen.append({
                "match_id": match_id,
                "zeitpunkt": attr["createdAt"],
                "spieler": s["name"],
                "modus": modus,
                "perspektive": perspektive,
                "map": attr.get("mapName", ""),
                "dauer_min": round(attr.get("duration", 0) / 60, 1),
                "platz": rstat.get("rank"),
                "teams_im_match": len(rosters),
                "team_id": rstat.get("teamId"),
                "kills": s.get("kills"),
                "assists": s.get("assists"),
                "knocks": s.get("DBNOs"),
                "kopfschuesse": s.get("headshotKills"),
                "schaden": round(s.get("damageDealt", 0), 1),
                "weitester_kill_m": round(s.get("longestKill", 0), 2),
                "ueberlebt_min": round(s.get("timeSurvived", 0) / 60, 1),
                "revives": s.get("revives"),
                "heilitems": s.get("heals"),
                "boosts": s.get("boosts"),
                "waffen": s.get("weaponsAcquired"),
                "zu_fuss_m": round(s.get("walkDistance", 0)),
                "gefahren_m": round(s.get("rideDistance", 0)),
                "geschwommen_m": round(s.get("swimDistance", 0)),
                "roadkills": s.get("roadKills"),
                "teamkills": s.get("teamKills"),
                "fahrzeuge_zerstoert": s.get("vehicleDestroys"),
                "mitspieler": "|".join(sorted(n for n in namen_im_team if n != s["name"])),
            })
    return zeilen


def bereits_erfasst() -> set:
    if not CSV_PFAD.exists():
        return set()
    with CSV_PFAD.open(encoding="utf-8-sig", newline="") as f:
        return {(r["match_id"], r["spieler"]) for r in csv.DictReader(f, delimiter=";")}


def main():
    print("PUBG Clan Sync")
    print("-" * 46)

    konten, matches = spieler_und_matches()
    print(f"Spieler gefunden: {', '.join(sorted(konten.values()))}")
    print(f"Matches im 14-Tage-Fenster: {len(matches)}")

    print("\nClan:")
    clan = clan_holen(CLAN_IDS)
    if clan:
        CLAN_PFAD.write_text(json.dumps(clan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   {clan['clanName']} [{clan['clanTag']}] - Level {clan['clanLevel']}, "
              f"{clan['clanMemberCount']} Mitglieder")

    print("\nWaffen:")
    waffen = waffen_holen(konten)
    if waffen:
        with WAFFEN_PFAD.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=WAFFEN_FELDER, delimiter=";")
            w.writeheader()
            w.writerows(sorted(waffen, key=lambda z: (z["spieler"], -z["kills"])))
        print(f"   {len(waffen)} Zeilen -> {WAFFEN_PFAD.name}")

    print("\nMatches:")
    alt = bereits_erfasst()
    neu = []
    for i, (mid, wer) in enumerate(matches.items(), 1):
        offen = {n for n in wer if (mid, n) not in alt}
        if not offen:
            continue
        print(f"[{i}/{len(matches)}] {mid[:8]} ... ", end="", flush=True)
        try:
            zeilen = match_auswerten(mid, offen)
            neu += zeilen
            print(f"{len(zeilen)} Eintraege")
        except Exception as e:
            print(f"uebersprungen ({e})")

    if not neu:
        print("\nNichts Neues. CSV ist aktuell.")
        return

    neu.sort(key=lambda r: r["zeitpunkt"])
    existiert = CSV_PFAD.exists()
    with CSV_PFAD.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FELDER, delimiter=";", extrasaction="ignore")
        if not existiert:
            w.writeheader()
        w.writerows(neu)

    print(f"\n{len(neu)} neue Zeilen angehaengt -> {CSV_PFAD.name}")
    gesamt = len(alt) + len(neu)
    print(f"Datenbestand jetzt: {gesamt} Spieler-Matches")


if __name__ == "__main__":
    main()
