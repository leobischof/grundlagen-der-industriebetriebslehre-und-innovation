# Freie Icons in Abbildungs-Rekonstruktionen

Beschriftete Platzhalter für Piktogramme werden durch frei nutzbare Bibliotheksicons ergänzt.
Die fachliche Beschriftung bleibt erhalten; die Bibliotheksgrafik ist eine Annäherung und kein
Original-Piktogramm. Bei den SDG-Kacheln bleiben insbesondere Nummer und Titel unverändert;
die eingesetzten Icons sind keine offiziellen UN-SDG-Piktogramme.

Die SVG-Quelle enthält ein Suchfeld, z. B.:

```xml
<g data-icon-query="cog" data-icon-box="807 212 56 56" data-icon-color="#555555">
  <text x="835" y="296" text-anchor="middle">Zahnrad</text>
</g>
```

`python -m pipeline figure-icons` sucht automatisch in den fest versionierten Iconify-Paketen
**Lucide** (ISC, einschließlich MIT-Hinweis für Feather-Ableitungen) und **Material Design Icons**
(Apache-2.0). Namen werden exakt bzw. über übereinstimmende Namensbestandteile gesucht. Bei einem
exakten Treffer gewinnt dieser vor einer ungefähren Entsprechung. Ohne Treffer bleibt die
Beschriftung erhalten und die Pipeline meldet die Lücke, statt ein Symbol zu erfinden.

Der Import lädt ausschließlich Pakete aus der offiziellen npm-Registry, prüft SHA-512 sowie
Paket-/Iconlizenz und speichert die Bibliothek lokal unter `build/icon-cache/`. Der SVG-Inhalt
wird als selbständige Vektorgeometrie eingebettet. Externe Referenzen und aktive Inhalte sind
nicht erlaubt. `curation/icon-provenance.json` nennt je Einsatz Suchbegriff, gewähltes Icon,
Paketversion, Lizenz, Quelle und Geometrie-Hash; `curation/icon-library-licenses.txt` enthält die
vollständigen Hinweise. Die Hinweise stehen zusätzlich im SVG und in den XMP-Rechtemetadaten
der erzeugten PDFs. Markdown-Exporte erhalten die Lizenzdatei neben den SVGs.

Erste Umstellung: Abbildungen 1, 2, 39 und 55. Weitere Platzhalter lassen sich durch ein Suchfeld
mit passender Position und lesbarer Beschriftung ergänzen. Diese Zuordnung ist bewusst kuratiert:
eine rein bildbasierte automatische Deutung unbekannter Symbole wäre fachlich unsicher.

Nach Änderungen: `python -m pipeline figure-icons`, `python -m pipeline exercises`,
`python -m pipeline offline` und `python -m pytest`. `offline`, PDF-Rendering und Wiedergabe
suchen nicht im Internet. Quellen: [Lucide-Lizenz](https://lucide.dev/license),
[Material-Design-Icons-Lizenz](https://github.com/Templarian/MaterialDesign/blob/master/LICENSE).
