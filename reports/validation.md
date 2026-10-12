# Validierungsbericht

Generiert von `python -m pipeline validate` – nicht von Hand bearbeiten. Prüft nur versionierte Dateien (keine PDFs, keine OCR, keine KI) und läuft deshalb auch in der CI.

**Ergebnis: bestanden** – 0 Fehler, 3 Warnungen, 1 Hinweise.

Fehler lassen den Lauf scheitern (Exit-Code 1); Warnungen und Hinweise nicht.

| Prüfung | Fehler | Warnungen | Hinweise |
|---|---:|---:|---:|
| Quellen | 0 | 0 | 0 |
| Seiten | 0 | 0 | 0 |
| Kapitel und Abschnitte | 0 | 0 | 0 |
| OCR-Qualität | 0 | 1 | 0 |
| Abbildungen | 0 | 0 | 1 |
| Bilderkennung und Beschriftungen | 0 | 1 | 0 |
| Prüfungsfragen | 0 | 0 | 0 |
| Links | 0 | 0 | 0 |
| Fußnoten | 0 | 1 | 0 |
| Dateinamen | 0 | 0 | 0 |

## Warnungen

### OCR-Qualität

- 1 Seiten mit schwacher OCR-Textschicht: [176]

### Bilderkennung und Beschriftungen

- 6 Beschriftungen nur visuell bestätigt (reports/captions-check.md): ['abb-03', 'abb-16', 'abb-17', 'tab-04', 'tab-05', 'abb-80']

### Fußnoten

- 5 Fußnotendefinitionen ohne Textanker (ohne sicheren Anker – im Original nachsehen)


## Hinweise

### Abbildungen

- 82 von 98 Abbildungen haben noch keine Metadaten (B)
