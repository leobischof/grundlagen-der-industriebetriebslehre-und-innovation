# Interaktiver Kapitelreader: PDF, Audio und Zeitmarkierungen

Der lokale Reader verbindet pro Kapitel den bereinigten Skriptexport mit einer Audio- oder
Videoerklärung. PDF.js übernimmt die PDF-Ansicht einschließlich Textauswahl, Suche, Zoom und
Seitenwechsel. Ein SVG-Overlay zeigt zeitgesteuerte Rechtecke, Hervorhebungen und Pfeile.
Das PDF bleibt unverändert. Die Wiedergabe läuft beim Scrollen weiter. Automatisches Mitgehen
ist optional und anfangs ausgeschaltet.

Die Seitenleiste startet eingeklappt und merkt sich ihre Einstellung in diesem Browser.
Am Rand bleiben Öffnen/Einklappen, Abspielen/Pause, zehn Sekunden zurück/vor, Stummschalten,
Wiedergabetempo, automatisches Mitgehen, Markierungen ein/aus und die Wiedergabezeit sichtbar.
Es gibt keinen separaten Header: GIL und Kapitelauswahl stehen mittig in der PDF-Werkzeugleiste.
Auf kleinen Bildschirmen öffnet sich die Leiste über dem PDF,
statt dem Dokument zusätzlichen Platz wegzunehmen. Das Audio läuft beim Einklappen weiter.

Die Audio-/Video-Timeline bleibt unter dem PDF sichtbar, auch bei eingeklappter Seitenleiste.
Sie zeigt Wiedergabezeit, Gesamtdauer und die zugeordneten Markierungsintervalle. Ziehen auf der
Leiste springt im Medium; aktivierte automatische Navigation folgt der zugehörigen PDF-Stelle.
Der Autoscroller schaltet sich bei eigenem Scrollen mit Mausrad/Touch, Scrolltasten, Ziehen am
Scrollbalken oder manuellem Seitenwechsel und bei PDF-Suche ab. Programmatische Sprünge zur
Erklärung schalten ihn nicht ab. Der Pfeilknopf aktiviert ihn wieder. Ohne zeitlich zugeordnete
Stelle bleibt die PDF-Position stehen; es wird keine passende Stelle erfunden.

## Lokal vorbereiten und starten

Einrichtung und Alltag unter Windows:

```powershell
.\dev.ps1 setup   # .venv, Python-Abhängigkeiten und node_modules einrichten
.\dev.ps1         # Audio-Pipeline ausführen, Reader starten und Browser öffnen
.\dev.ps1 build   # nur automatisch vorbereiten und bauen
.\dev.ps1 test    # Python-/JS-Tests und Offline-Validierung
.\dev.ps1 release # lokale Release-Pakete bauen, ohne Veröffentlichung
```

Python 3.11+ und Node.js 22+ müssen installiert sein. Änderungen an `pyproject.toml` oder
`interactive/package-lock.json` lösen beim nächsten Aufruf eine passende Neuinstallation aus;
sonst wird die vorhandene Einrichtung verwendet. `-Reinstall` installiert Abhängigkeiten erneut,
`-Port 8766` wählt einen anderen Port, `-NoOpen` unterdrückt das Öffnen des Browsers.
VS Code bietet dieselben Befehle in `.vscode/tasks.json` unter „Tasks: Run Task“;
Strg+Umschalt+B führt den Reader-Build aus.

Der gemeinsame Pipeline-Befehl lautet **`python -m pipeline audio-reader`**: Audios erkennen und
kanonisch benennen → Kapitel-PDFs rendern → lokal transkribieren (Cache) → Themen-/Detailmarkierungen
vorbereiten → Reader bauen. `python -m pipeline sync-audio` führt nur die Audio-Vorbereitung aus.
Nach einem frischen Checkout ohne lokale Audios bleiben die Kapitel als PDF lesbar. Die Audios
aus dem privaten Audio-Release lassen sich später in `audio/` ablegen.

Die einzelnen Schritte lassen sich weiterhin getrennt ausführen:

```powershell
# Repository-Wurzel; Windows, Python und Node.js erforderlich
& .\.venv\Scripts\Activate.ps1
python -m pip install -e ".[pipeline,audio,dev]"
npm ci --prefix interactive --ignore-scripts
python -m pipeline.chapter_audio
python -m pipeline render-pdf
python -m pipeline.audio_sync --model tiny
python -m pipeline interactive
python -m pipeline.reader_serve --directory build/interactive --open
```

Adresse: `http://127.0.0.1:8765/reader.html`; ein Kapitel direkt wählen, z. B.
`http://127.0.0.1:8765/reader.html?chapter=2`. Der Server bindet nur an Loopback und unterstützt
HTTP-Byte-Ranges für Medien-Seeks. Er gibt keine Verzeichnislisten aus. Nach dem Entpacken eines
Reader-Releases reichen Python und `Reader-starten.cmd` bzw. `python reader_serve.py --open`;
Node.js und Internet werden für die Wiedergabe nicht benötigt.

## Dateien und Quellen

- `audio/`: lokale Aufnahmen; vollständig git-ignoriert. Namen:
  `GIL-<Kapitelnummer>-Audio-<Kapiteltitel>.m4a` (andere unterstützte Medienendungen bleiben erhalten).
  `chapter_audio` benennt alte `Kap2.m4a`-Namen um, ohne den Inhalt zu ändern. Doppelte Audios pro
  Kapitel oder ein vorhandenes Umbenennungsziel stoppen den Vorgang vor den Änderungen.
- `curation/interactive/GIL-<N>-Timeline.json`: kuratierbare Zuordnung mit Zeiten, Seiten und
  normierten Koordinaten. SHA-256 von PDF und Audio bindet sie an die richtigen Dateiversionen.
- `build/transcripts/`: lokale Whisper-Transkripte und neue Timeline-Vorschläge (git-ignoriert).
- `build/interactive/`: eigenständig abspielbares Paket mit Reader, lokalem PDF.js, Kapitel-PDFs,
  separatem `audio/`-Ordner, Timeline je Kapitel und `reader-manifest.json`.

Die Kapitel-PDFs sind die vorhandenen bereinigten Exporte mit eigenen SVG-Rekonstruktionen.
Original-PDFs und Original-Abbildungsausschnitte werden nicht ins Paket kopiert.
Ein fehlendes Audio verhindert das Lesen des Kapitels nicht; die Oberfläche zeigt den fehlenden
Audiostand an. Derzeit existieren Aufnahmen für Kapitel 2–9, nicht für Kapitel 1.

Links gibt es eine getrennte, einklappbare PDF-Navigation: Kapitelwechsel und das echte
PDF-Inhaltsverzeichnis oder Seitenminiaturen. Miniaturen werden erst nahe am sichtbaren Bereich
gerendert. Plus/Minus, Zoomstufen, Seitenbreite und ganze Seite stehen oben bereit. Eine
Touchpad-Pinch-Geste (bzw. Strg+Mausrad) zoomt das PDF um den Zeiger; die Oberfläche bleibt gleich groß.

## Automatische Vorbereitung und Korrektur

`audio_sync` transkribiert mit lokalem faster-whisper (Deutsch, CPU/int8). Beim ersten Lauf wird
das gewählte Modell heruntergeladen; Aufnahmen werden nicht an einen Dienst geschickt.
Transkripte werden nach Audio-Hash und Modell gecacht. `tiny` ist der schnelle Einstieg;
`base` oder `small` erlauben eine erneute Vorbereitung mit einem größeren Modell.

Zeitfenster des Transkripts werden über gewichtete Wortübereinstimmung mit PDF-Textblöcken
verglichen. Auch ein Rücksprung zu einer früheren PDF-Seite ist erlaubt. Schwache Treffer bleiben
ohne Markierung; es werden keine Zeitpunkte nach Kapitellänge erfunden. Wo eine Bildunterschrift
zugeordnet wird, wird ein angrenzendes Bild in die Rechteckfläche aufgenommen, soweit der PDF-
Renderer es als Bild ausweist. Vektorgrafiken können eine manuelle Flächenkorrektur benötigen.

**Jeder automatische Treffer ist ein ungeprüfter Vorschlag.** Freie Umschreibungen, Fachwörter,
Zeichnungen und ASR-Fehler können zu fehlenden oder falschen Treffern führen. Ein Ähnlichkeitswert
ist keine fachliche Richtigkeitswahrscheinlichkeit. Das Skript bleibt maßgeblich.

Die Darstellung hat zwei Ebenen: Große blaue Themenrahmen umfassen den zugehörigen Abschnitt
auf einer halben oder fast ganzen Seite, bei mehrseitigen Themen auch mehrere Seiten. Sie bleiben
bis zum nächsten ausreichend erkannten Themenwechsel sichtbar, auch während erläuternder Beispiele.
Orange Detailrahmen und Pfeile erscheinen ausschließlich im Zeitfenster des konkreten Treffers.
Sie verschwinden am Ende dieses Fensters, auch wenn anschließend keine neue Detailstelle erkannt
wird. Nur die großen Themenrahmen bleiben als Kontext sichtbar. Themen- und Detailzuordnungen
sind vollständig ungeprüft und korrigierbar.

Im Reader eine Stelle auswählen, „Markierungen korrigieren“ öffnen, Start/Ende, PDF-Seite und
Koordinaten ändern oder ein Rechteck, Highlight bzw. einen Pfeil aufziehen. „Inhaltlich geprüft“
ist eine bewusste Bestätigung der Person. Änderungen werden in diesem Browser unter dem
PDF-/Audio-Hash gespeichert. Die heruntergeladene Timeline ersetzt nach Prüfung die zugehörige
Datei in `curation/interactive/`; danach `python -m pipeline interactive` erneut ausführen.
Import mit falschem Kapitel oder falschem PDF-/Audio-Hash wird abgewiesen.

Der gemeinsame Pipeline-Lauf aktualisiert eine bestehende Timeline nur, wenn ihr gespeicherter
Generierungs-Hash unverändert ist und alle Einträge ungeprüft aus der Automatik stammen. Schon
eine manuelle Inhaltsänderung oder ein geprüfter Eintrag schützt die Datei. Neue Vorschläge liegen
dann getrennt in `build/transcripts/GIL-<N>-Timeline-Vorschlag.json`. Der direkte Aufruf von
`pipeline.audio_sync` schützt bestehende Dateien standardmäßig immer; `--refresh-unreviewed`
aktiviert dieselbe Hash-Prüfung wie die Pipeline. Bei Änderungen an PDF/Audio und gleichzeitig
manuell korrigierter Timeline die Vorschläge prüfen und übernehmen. Ein Paket mit veralteter
Dokumentzuordnung wird nicht gebaut.

## Timeline-Vertrag (Version 1)

```json
{
  "version": 1,
  "chapter": 2,
  "pdf_sha256": "<SHA-256 des Kapitel-PDFs>",
  "audio_sha256": "<SHA-256 des Audios>",
  "annotations": [{
    "id": "markierung-1",
    "start": 205,
    "end": 221,
    "page": 3,
    "type": "rect",
    "rect": [0.12, 0.35, 0.70, 0.18],
    "label": "Erklärter Abschnitt",
    "status": "unreviewed",
    "animation": "none"
  }]
}
```

Das Beispiel zeigt nur das Format, keine inhaltlich geprüfte Audiostelle. Zeiten sind Sekunden,
aktiv ist `start <= currentTime < end`. `page` ist die 1-basierte Seite des **Kapitel-Exports**,
nicht die Seitenzahl im Original. Koordinaten sind 0–1 relativ zur sichtbaren, ungedrehten
Kapitel-PDF-Seite, Ursprung links oben. `rect` bedeutet `[x, y, Breite, Höhe]`. Für `arrow`
wird stattdessen `points: [x1, y1, x2, y2]` verwendet. Ein optionales `pointer: true` ergänzt
ein Rechteck um einen automatisch platzierten Pfeil vom Seitenrand zur markierten Fläche.
Typen: `rect`, `highlight`, `arrow`;
Prüfstatus: `unreviewed` oder `reviewed`; optionale Animation: `none` oder `pulse`. Die Animation
berücksichtigt die Betriebssystem-Einstellung für reduzierte Bewegung.

## Releases und Prüfungen

`.\dev.ps1 package` erzeugt nach der Audio-Pipeline neun eigenständige HTML-Dateien unter
`build/standalone/`, benannt `GIL-<N>-Lernpaket-<Titel>.html`. Alternativ nach dem Reader-Build:
`python -m pipeline package-reader`. PDF, vorhandenes Audio, Timeline, Reader, PDF.js und dessen
Schriften sind eingebettet; die Kapiteldatei benötigt keine danebenliegenden Dateien.
Kapitel 1 enthält derzeit nur das PDF. Lokales Öffnen benötigt einen Browser, der JavaScript
in HTML-Dateien ausführt. Die iOS-Dateivorschau ist dafür nicht zuverlässig geeignet.

Der Reader ist zusätzlich eine installierbare PWA. Für Mobilgeräte das entpackte Reader-Paket
über **HTTPS** bereitstellen; der lokale Entwicklungsserver funktioniert über `localhost`.
„Kapitel offline speichern“ lädt das gewählte PDF, Audio und die Timeline in den Browsercache.
Danach ist dieses Kapitel auch ohne Verbindung nutzbar. Auf iOS lässt sich die HTTPS-Seite über
Safari zum Home-Bildschirm hinzufügen. Browser können gespeicherte Daten bei Speicherknappheit
entfernen. Das Erzeugen des Pakets veröffentlicht oder hostet es nicht.

`python -m pipeline release` ergänzt lokale Audios als `GIL-Audio-je-Kapitel.zip` und im
Gesamtpaket unter `6-Audio/`. Ist der Reader gebaut, kommt ein eigener, vollständiger Download
`GIL-Interaktiver-Kapitelreader.zip` mit PWA und lokalem Server hinzu. Die HTML-Kapiteldateien
kommen in `GIL-Lernpakete-je-Kapitel.zip` und im Gesamtpaket unter `7-Lernpakete/` hinzu.
`.\dev.ps1 release` führt alle nötigen Schritte einschließlich Paketbildung aus.
Audios bleiben außerhalb Git; in CI fehlen sie bewusst.
Veröffentlicht werden Releases ausschließlich nach dem Merge auf `main`, im privaten Repository.

Tests: `python -m pytest`, `npm test --prefix interactive`, `python -m pipeline offline`.
Die JS-Tests prüfen Zeitsprünge und Timeline-Verträge; die Python-Tests prüfen u. a. sichere
Umbenennung, Audio-Release-Zuordnung, Matching, Dokumentidentität, HTTP-Byte-Ranges,
eingebettete Kapiteldateien und deterministische, speicherschonende ZIP-Erzeugung.

PWA-Grundlagen: [MDN: Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API),
[WebKit: Home Screen web apps](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/).

Technische Quellen: [PDF.js-Komponentenbeispiel](https://github.com/mozilla/pdf.js/blob/master/examples/components/simpleviewer.mjs),
[PDF.js](https://mozilla.github.io/pdf.js/), [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
PDF hat zwar RichMedia-Annotationen, deren Unterstützung ist jedoch vom Reader abhängig;
siehe [PDF Association: Leveling up RichMedia](https://pdfa.org/presentation/leveling-up-richmedia/).
Das HTML-Paket ist ein eigenes, dokumentiertes Paketformat und kein neuer PDF-Standard.
