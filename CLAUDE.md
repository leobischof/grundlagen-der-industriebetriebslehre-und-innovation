# CLAUDE.md

**Maßgeblich ist [AGENTS.md](AGENTS.md)** – Dateikarte, Quellenbindung, Vertrauensstufen, die fünf
Lernmodi und der Lernfortschritt. Lies es vor der ersten Antwort. Sprache gegenüber der lernenden
Person: Deutsch.

Ergänzungen für Claude:

- **Gezielt lesen, Kontext sparen.** Einstieg über [content/README.md](content/README.md) oder
  [exams/topic-mapping.json](exams/topic-mapping.json), dann nur den einen Abschnitt bzw. die eine
  Metadatendatei öffnen. Nie ganze Verzeichnisse, die OCR-Schicht (`sources/ocr/`) oder PDFs in den
  Kontext laden. Bilder (`figures/originals/*.png`, Fotos von Skizzen) nur ansehen, wenn Text und
  `curation/figures/<id>.yaml` nicht reichen.
- **Lösungen zurückhalten.** In „Aktives Abfragen“, „Prüfungssimulation“ und „Zeichentraining“ erst
  die Antwort der Person abwarten.
- **Fortschritt nur über `python -m pipeline.progress`** (Python aus `.venv`, falls vorhanden:
  `.venv/Scripts/python` unter Windows). Die Datei ist lokal und wird nie committet.
- **Zitieren:** „Skript S. X (PDF Y) / sec-X.Y“; Ergänzungen als „Zusatzwissen, nicht im Skript“;
  Unsicherheit aussprechen.
- **Pflege statt Lernen:** Wer die Wissensbasis ändert, hält sich an AGENTS.md Abschnitt 6 und
  protokolliert jeden KI-Durchgang über `pipeline/ailog.py` in `curation/ai-log.jsonl`
  (Token-Schätzung, Bilder ≈ 1600 Tokens je Megapixel). Die Pipeline selbst ruft nie ein Modell auf;
  Details in [docs/pipeline.md](docs/pipeline.md).
