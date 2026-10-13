# Interaktiver Kapitelreader: PDF, Audio und Zeitmarkierungen

Der lokale Reader verbindet pro Kapitel den bereinigten Skriptexport mit einer Audio- oder
Videoerklärung. PDF.js übernimmt die PDF-Ansicht einschließlich Textauswahl, Suche, Zoom und
Seitenwechsel. Ein SVG-Overlay zeigt zeitgesteuerte Rechtecke, Hervorhebungen und Pfeile.
Das PDF bleibt unverändert. Die Wiedergabe läuft beim Scrollen weiter. Automatisches Mitgehen
ist optional und anfangs ausgeschaltet.

Die Seitenleiste startet eingeklappt und merkt sich ihre Einstellung in diesem Browser.
Am Rand bleiben nur Öffnen/Einklappen, Abspielen/Pause sowie zehn Sekunden zurück/vor sichtbar.
Der Header ist 40 Pixel hoch. Auf kleinen Bildschirmen öffnet sich die Leiste über dem PDF,
statt dem Dokument zusätzlichen Platz wegzunehmen. Das Audio läuft beim Einklappen weiter.

## Lokal vorbereiten und starten

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

Im Reader eine Stelle auswählen, „Markierungen korrigieren“ öffnen, Start/Ende, PDF-Seite und
Koordinaten ändern oder ein Rechteck, Highlight bzw. einen Pfeil aufziehen. „Inhaltlich geprüft“
ist eine bewusste Bestätigung der Person. Änderungen werden in diesem Browser unter dem
PDF-/Audio-Hash gespeichert. Die heruntergeladene Timeline ersetzt nach Prüfung die zugehörige
Datei in `curation/interactive/`; danach `python -m pipeline interactive` erneut ausführen.
Import mit falschem Kapitel oder falschem PDF-/Audio-Hash wird abgewiesen.

Eine bestehende Timeline wird von `audio_sync` nie überschrieben: neue Vorschläge liegen dann in
`build/transcripts/GIL-<N>-Timeline-Vorschlag.json`. Bei Änderungen an PDF oder Audio die Vorschläge
neu erzeugen, prüfen und übernehmen. Die Pipeline baut kein Paket mit veralteter Zuordnung.

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

`python -m pipeline release` ergänzt lokale Audios als `GIL-Audio-je-Kapitel.zip` und im
Gesamtpaket unter `6-Audio/`. Ist der Reader gebaut, kommt ein eigener, vollständiger Download
`GIL-Interaktiver-Kapitelreader.zip` hinzu. Audios bleiben außerhalb Git; in CI fehlen sie bewusst.
Veröffentlicht werden Releases ausschließlich nach dem Merge auf `main`, im privaten Repository.

Tests: `python -m pytest`, `npm test --prefix interactive`, `python -m pipeline offline`.
Die JS-Tests prüfen Zeitsprünge und Timeline-Verträge; die Python-Tests prüfen u. a. sichere
Umbenennung, Audio-Release-Zuordnung, Matching, Dokumentidentität und HTTP-Byte-Ranges.

Technische Quellen: [PDF.js-Komponentenbeispiel](https://github.com/mozilla/pdf.js/blob/master/examples/components/simpleviewer.mjs),
[PDF.js](https://mozilla.github.io/pdf.js/), [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
PDF hat zwar RichMedia-Annotationen, deren Unterstützung ist jedoch vom Reader abhängig;
siehe [PDF Association: Leveling up RichMedia](https://pdfa.org/presentation/leveling-up-richmedia/).
Das HTML-Paket ist ein eigenes, dokumentiertes Paketformat und kein neuer PDF-Standard.
