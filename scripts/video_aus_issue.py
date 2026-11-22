#!/usr/bin/env python3
"""
Traegt eine Videozeile aus einem GitHub-Issue in videos.txt ein.

Sicherheitsgrundsatz: Der Issue-Text wird NICHT uebernommen, sondern nur
gelesen. Aus den geprueften Bestandteilen baut das Skript eine neue Zeile
zusammen. Alles, was nicht in das Schema passt, faellt dabei weg - damit
kann ueber ein Issue kein beliebiger Inhalt in die Datei gelangen.

Aufruf:  python3 scripts/video_aus_issue.py <issue-body-datei>
Ausgabe: schreibt nach GITHUB_OUTPUT  status=ok|fehler  und  meldung=<text>
"""
import os
import re
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
VIDEOS = HIER / "videos.txt"

MAPS = {"erangel","miramar","sanhok","vikendi","taego","deston","rondo",
        "karakin","paramo","haven"}

# <link> JJJJMMTT Map #Platz (xK) - spieler1, spieler2
MUSTER = re.compile(
    r"^(?P<url>\S+)\s+"
    r"(?P<datum>\d{8})\s+"
    r"(?P<map>[A-Za-zÄÖÜäöü]+)\s*"
    r"#\s*(?P<platz>\d{1,3})\s*"
    r"(?:\(\s*(?P<kills>\d{1,3})\s*[Kk]\s*\))?\s*"
    r"[-–—]\s*(?P<wer>[A-Za-z0-9_, \-]+)$"
)
ID_MUSTER = re.compile(r"(?:youtu\.be/|v=|embed/|shorts/)([A-Za-z0-9_-]{11})")


def ausgeben(status: str, meldung: str) -> None:
    pfad = os.environ.get("GITHUB_OUTPUT")
    if pfad:
        with open(pfad, "a", encoding="utf-8") as fh:
            fh.write(f"status={status}\n")
            fh.write("meldung<<ENDE\n" + meldung + "\nENDE\n")
    print(f"[{status}] {meldung}")


def zeile_finden(body: str) -> str | None:
    """Erst im Codeblock suchen, sonst in allen Zeilen."""
    kandidaten = []
    for block in re.findall(r"```(.*?)```", body, re.S):
        kandidaten += block.splitlines()
    kandidaten += body.splitlines()
    for z in kandidaten:
        z = z.strip()
        if z and not z.startswith("#") and MUSTER.match(z):
            return z
    return None


def main() -> int:
    if len(sys.argv) < 2:
        ausgeben("fehler", "Kein Issue-Text uebergeben.")
        return 1

    body = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    roh = zeile_finden(body)
    if not roh:
        ausgeben("fehler",
                 "In dem Issue steht keine Zeile im erwarteten Format.\n\n"
                 "Erwartet wird:\n\n"
                 "    <youtube-link>  JJJJMMTT Map #Platz (xK) - spieler1, spieler2")
        return 0

    m = MUSTER.match(roh)
    vid = ID_MUSTER.search(m.group("url"))
    if not vid:
        ausgeben("fehler", f"`{m.group('url')}` ist keine YouTube-Adresse.")
        return 0

    karte = m.group("map").lower()
    if karte not in MAPS:
        ausgeben("fehler",
                 f"`{m.group('map')}` ist keine bekannte Map. Moeglich sind: "
                 + ", ".join(sorted(x.capitalize() for x in MAPS)))
        return 0

    platz = int(m.group("platz"))
    if not 1 <= platz <= 100:
        ausgeben("fehler", f"Platz {platz} liegt ausserhalb von 1 bis 100.")
        return 0

    spieler = [w.strip().lower() for w in m.group("wer").split(",") if w.strip()]
    if not spieler or not all(re.fullmatch(r"[A-Za-z0-9_\-]{1,32}", w) for w in spieler):
        ausgeben("fehler", "Die Spielernamen hinter dem Bindestrich sehen nicht plausibel aus.")
        return 0

    # Zeile neu zusammensetzen - nichts aus dem Issue wird uebernommen
    kills = f" ({int(m.group('kills'))}K)" if m.group("kills") else ""
    neu = (f"https://youtu.be/{vid.group(1)}  {m.group('datum')} "
           f"{karte.capitalize()} #{platz}{kills} - {', '.join(spieler)}")

    bestand = VIDEOS.read_text(encoding="utf-8") if VIDEOS.exists() else ""
    if vid.group(1) in bestand:
        ausgeben("fehler", f"Das Video `{vid.group(1)}` steht bereits in videos.txt.")
        return 0

    if bestand and not bestand.endswith("\n"):
        bestand += "\n"
    VIDEOS.write_text(bestand + neu + "\n", encoding="utf-8")
    ausgeben("ok", f"Eingetragen:\n\n    {neu}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
