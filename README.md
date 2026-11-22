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
| `videos.txt` | YouTube-Links zu einzelnen Matches |
| `.github/workflows/video-eintragen.yml` | Trägt Videos aus einem Issue in `videos.txt` ein |
| `scripts/video_aus_issue.py` | Prüft die Zeile aus dem Issue und schreibt sie |

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


## Videos verknüpfen

Die Links zu den Match-Aufzeichnungen stehen in `videos.txt`, eine Zeile je
Video: erst der YouTube-Link, dann der Videotitel. Bewusst von Hand statt
über die YouTube-API — unlisted Videos gibt ein einfacher API-Schlüssel nicht
heraus, und OAuth wäre für ein paar Links im Monat unverhältnismäßig.

### Der bequeme Weg

Auf der Seite im Einsatzprotokoll beim gewünschten Match auf **+** klicken,
YouTube-Link einfügen, **Speichern** drücken. Es öffnet sich ein
vorausgefülltes GitHub-Issue; nach dem Absenden trägt eine Action die Zeile
ein, schließt das Issue und kommentiert das Ergebnis. Nach dem nächsten
Seitenaufbau ist das Video verknüpft.

Daneben steht **von Hand** — das kopiert die fertige Zeile und öffnet
`videos.txt` im Editor, falls man lieber selbst committet.

### Das Format

Die Zuordnung zum Match läuft allein über den Titel:

    JJJJMMTT Map #Platz (xK) - spieler1, spieler2

Datum, Map, Platzierung und Besetzung machen rund 97 % der Runden eindeutig.
Für den Rest hilft die Killzahl des Erstgenannten in Klammern. Passt ein Titel
auf kein oder auf mehrere Matches, wird **nichts** verknüpft — das Video
erscheint im Abschnitt „Videos" unter „Nicht zugeordnet" mit dem Grund.

Hinweis: Das Repository und die Seite sind öffentlich. Dort hinterlegte Links
zu unlisted Videos sind damit für jeden erreichbar, der die Seite aufruft.

### Warum kein direktes Speichern aus der Seite

GitHub Pages liefert nur Dateien aus, dahinter läuft kein Server. Schreiben
könnte die Seite nur mit einem Token im Quelltext — und der wäre öffentlich
lesbar. Der Umweg über ein Issue hält das Schreibrecht bei GitHub.

### Sicherheit

In einem öffentlichen Repository kann jeder ein Issue anlegen. Deshalb:

- Die Action läuft nur für `OWNER`, `MEMBER` und `COLLABORATOR`. Wer kein
  Schreibrecht hat, bekommt einen Hinweis und das Issue wird geschlossen.
- `scripts/video_aus_issue.py` übernimmt den Issue-Text **nicht**, sondern
  baut die Zeile aus geprüften Bestandteilen neu zusammen: Video-ID, Datum,
  bekannte Map, Platz 1–100, plausible Spielernamen. Alles andere fällt weg.
- Bereits eingetragene Video-IDs werden abgelehnt.
- Die Seite maskiert jeden Text aus `videos.txt`, bevor er angezeigt wird.
