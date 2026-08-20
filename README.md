# PUBG Clan-Statistik

Holt die Matches der Clan-Mitglieder automatisch über die offizielle PUBG-API
und zeigt sie als Webseite an.

## Was hier drin liegt

| Datei | Zweck |
|---|---|
| `pubg_clan_sync.py` | Holt neue Matches und schreibt sie in `pubg_matches.csv` |
| `.github/workflows/pubg-sync.yml` | Startet das Skript alle 6 Stunden automatisch |
| `index.html` | Die Auswertung – liest die CSV und rechnet alles im Browser |
| `pubg_matches.csv` | Der Datenbestand. Entsteht beim ersten Lauf. |

## Einrichtung

1. **Repository anlegen** (öffentlich, damit GitHub Pages kostenlos ist) und
   diese Dateien hochladen. Ordnerstruktur beibehalten – die Workflow-Datei
   muss unter `.github/workflows/` liegen.

2. **API-Key hinterlegen:** Settings → Secrets and variables → Actions →
   *New repository secret*. Name exakt `PUBG_API_KEY`, Wert ist der Key von
   developer.pubg.com. Der Key steht danach nirgends im Code.

3. **Schreibrechte für den Workflow:** Settings → Actions → General →
   *Workflow permissions* → „Read and write permissions" auswählen und speichern.
   Ohne das kann der Lauf die CSV nicht zurückschreiben.

4. **Webseite aktivieren:** Settings → Pages → Source: *Deploy from a branch*,
   Branch `main`, Ordner `/ (root)`. Nach ein paar Minuten liegt die Seite unter
   `https://<benutzername>.github.io/<repo-name>/`.

5. **Ersten Lauf starten:** Tab *Actions* → „PUBG Sync" → *Run workflow*.
   Nicht auf den Zeitplan warten.

## Spieler ändern

Die Namen stehen oben in `pubg_clan_sync.py` in der Liste `SPIELER`.
Die PUBG-API unterscheidet Groß- und Kleinschreibung streng.

## Gut zu wissen

- Die PUBG-API hält Matches nur **14 Tage** vor. Was der Sync in dieser Zeit
  nicht abholt, ist endgültig weg. Der 6-Stunden-Takt ist reichlich Puffer.
- Geplante Läufe starten oft 5–30 Minuten später als eingetragen. Das ist normal.
- In öffentlichen Repositories schaltet GitHub geplante Workflows nach
  60 Tagen ohne Commit ab. Da jeder Sync mit neuen Matches selbst committet,
  passiert das nur, wenn zwei Monate niemand spielt. Dann im Actions-Tab
  einmal auf *Enable workflow* klicken.
- `index.html` lässt sich nicht per Doppelklick öffnen – Browser blockieren
  dabei das Laden der CSV. Über die Pages-URL funktioniert es.
