# Gegenprobe der Abbildungs- und Tabellenbeschriftungen

Generiert von `python -m pipeline captions`. Jede kuratierte Beschriftung (`curation/figures.yaml`) wird mit zwei unabhängigen Lesungen verglichen: der OCR-Schicht des PDFs und einem lokalen Tesseract-Lauf (deu+eng).
Status „ok“: Nummer stimmt in mindestens einer Lesung, Titel-Ähnlichkeit ≥ 0.8; „ok (Nummer … verlesen)“: Titel-Ähnlichkeit ≥ 0.9, Nummer in keiner Lesung lesbar. „prüfen“: beide Lesungen zu schlecht – Beschriftung wurde nur visuell (Beschriftungsstreifen) bestätigt.

**Ergebnis: 86 von 92 Beschriftungen bestätigt.**

| ID | Status | Ähnlichkeit (OCR-Schicht / Tesseract) | Gelesen (beste Lesung) |
|---|---|---|---|
| `abb-01` | ok | 0.71 / 0.98 | Abbildung 1: Iistorische Entwicklung innerhalb der Industrie |
| `abb-02` | ok | 0.0 / 0.98 | Abbildung 2: Mögliche Elemente eines Betriehs der Industrie 4.0% |
| `tab-01` | ok | 1.0 / 0.97 | Tabelle 1: Unselbständig Beschäftigte in Österreich‘ |
| `tab-02` | ok | 0.0 / 0.98 | Tabelle 2: Prozentualer Anteil der Sektoren an der Gesamtwertschopfung im Jahr 2023° |
| `tab-03` | ok | 0.0 / 0.99 | Tabelle 3: Prozentualer Anteil der Sektoren an der Gesamtwertschöpfung im Jahr 20239 |
| `abb-03` | prüfen | 0.0 / 0.73 | Abbildung 3: Entwicklungen des “o-Anteils der Beschiiftigten an der Gesamtbevölkerung sowi |
| `abb-04` | ok | 0.97 / 0.94 | \bbildung 4: Alterspvramide Österreichs (Stand 2021} |
| `abb-05` | ok | 0.0 / 1.0 | Abbildung 5: Drei generische Strategien, die Unternehmen verfolgen können |
| `abb-06` | ok | 1.0 / 0.72 | Abbildung 6: Die innovativsten Unternehmen 2022} |
| `abb-07` | ok | 0.0 / 0.97 | Abbildung 7: Typischen Merkmale viner Innovation+ |
| `abb-08` | ok | 1.0 / 0.55 | Abbildung 8: Produktlebenszyklus |
| `abb-09` | ok (Nummer von der OCR verlesen) | 0.96 / 0.62 | Abbildung 6: Katezorien neuer Produkte |
| `abb-10` | ok | 0.0 / 0.96 | Abbildung 10; Portfolio Management fiir neue Produkte |
| `abb-11` | ok (Nummer von der OCR verlesen) | 0.21 / 0.92 | Abbildung 74: Ansoff Mütrix |
| `abb-12` | ok | 0.96 / 1.0 | Abbildung 12: Industriebetriebe im System der Wirtschaftseinheiten |
| `abb-13` | ok | 1.0 / 1.0 | \bbildung 13: Abgrenzung zwischen Industrie- und Dienstleistungsbetrieb |
| `abb-14` | ok | 1.0 / 1.0 | Abbildung 14: Abgrenzung zwischen Industriebetrieben und Werkstätten |
| `abb-15` | ok | 0.0 / 0.97 | Abbildung 15: Industriebetrieh als Arbeitssystem |
| `abb-16` | prüfen | 0.55 / 0.5 | Abhildung 16: Der Produktinnsprozess |
| `abb-17` | prüfen | 0.0 / 0.69 | Abhildung 17: Elemente des Produktionsprozesses |
| `abb-18` | ok | 0.0 / 0.98 | Abbildung 18: Abgrenzung des Industrie Managemen\| im Kontext der Wirtschuftseinheiten" |
| `tab-04` | prüfen | 0.72 / 0.65 | le 4: Kriterien für Innovalion: |
| `abb-19` | ok | 0.0 / 0.97 | Abbildung 19: Auswirkung von Innovationsbarrieren™ . me = _ = = . |
| `tab-05` | prüfen | 0.0 / 0.85 | Tahelle 5: Unterschiede zwischen SME und IDE Entrepreneurship |
| `abb-20` | ok | 1.0 / 1.0 | Abbildung 20: Vergleich zwischen SME- und IDE- Entrepreneurship” |
| `abb-21` | ok | 1.0 / 1.0 | Abbildung 21: Richtungen des Entrepreneurship |
| `abb-22` | ok | 1.0 / 1.0 | Abbildung 22: Entrepreneurship- Prozess“ |
| `abb-23` | ok | 0.0 / 1.0 | Abbildung 23: Geschichte der Produktentstehung“ |
| `abb-24` | ok | 0.0 / 1.0 | Abbildtmg 24: Produktentstehung als Teil des Produktlebenszyklus™ |
| `abb-25` | ok | 0.97 / 0.97 | Abbildung 25: Zielsvstem, Handlungssystem und Sachsystem |
| `abb-26` | ok | 0.73 / 1.0 | Abbildung 26: Integrierte Produktentstehung 2013° |
| `abb-27` | ok | 0.0 / 1.0 | Abbildung 27: Festgelegte und verursachte Kosten in der Produktentstehung |
| `abb-28` | ok | 1.0 / 1.0 | Abbildung 28: Arten der Integration” |
| `abb-29` | ok | 1.0 / 1.0 | \bbildung 29: Magisches Dreieck der Produktentstehung |
| `abb-30` | ok | 1.0 / 1.0 | Abbildung 30: Systematik des Simultaneous Engineering“ |
| `abb-31` | ok | 0.0 / 1.0 | Abbildung 31: Point-based Serial Engineering” |
| `abb-32` | ok | 0.0 / 1.0 | Abbildung 32: Point-based Concurrent Engineering!” |
| `abb-33` | ok | 0.0 / 1.0 | Abbildung 33: Set-based Concurrent Engineering" |
| `abb-34` | ok | 0.91 / 0.77 | ildung 34: Rahmenstruktur-Konzept für integrierte Produkt- und Prozessgestaltung nach FVER |
| `abb-35` | ok | 0.97 / 1.0 | Abbildung 35: Integrationsbereiche der Themen Innovationsprozess & Produktentwicklung!” |
| `abb-36` | ok | 0.0 / 1.0 | Abbildung 36: Innovationsprozess von Thom” |
| `abb-37` | ok | 0.0 / 0.96 | Abbildung 37: Stage-Gate-Prozess nach Cooper” LT, \ Een, eS eee. C - ... .n 51 . IR \| P P  |
| `abb-38` | ok | 0.0 / 0.94 | Abbildung 38: Aufbau eines Gates‘“ W OP RO NR > a a a be . w C 7 Sethe x = |
| `abb-39` | ok (Nummer von der OCR verlesen) | 0.0 / 1.0 | Abbildtng 49: 5-Step Prozess des Design Thinking*+ |
| `abb-40` | ok | 1.0 / 1.0 | Abbildung 46: Funktionen des Industrie Management |
| `abb-41` | ok | 0.0 / 0.97 | Abbildung 41: Zusammenhang der Kennerößen des Managements |
| `abb-42` | ok | 0.06 / 0.99 | Abbildung 42: Das Konzept Integriertes Managements (UE...Unternehmensumgebung) |
| `abb-43` | ok | 0.78 / 0.95 | Abbildung 43: interne und externe Treiber fiir standorthezogene Reaktionen |
| `abb-44` | ok | 0.38 / 0.95 | Abbildung 44: Planungsgrundfiille nach Grundig! |
| `abb-45` | ok | 0.0 / 0.99 | Abbildung 45: Typologisierung von Produktionssysteme'™ |
| `abb-46` | ok | 0.97 / 0.97 | Abbildung 46: Finordnung der Produktionsarten |
| `abb-47` | ok | 0.0 / 1.0 | Abbildung 47: Punktfertigung |
| `abb-48` | ok | 0.0 / 1.0 | Abbildung 48: Gruppenfertigung |
| `abb-49` | ok | 1.0 / 1.0 | Abbildung 49: Reihenfertigung |
| `abb-50` | ok | 0.0 / 0.99 | Abbildung 50: Zusammenhang - Produktionsart & Fertigungsfeorm |
| `abb-51` | ok | 0.57 / 1.0 | Abbildung 51: Planungsvorgehen nach Grundig" |
| `abb-52` | ok | 1.0 / 1.0 | Abbildung 52: Auszug aus der Gliederung der Flächen |
| `abb-53` | ok | 0.63 / 1.0 | Abbildung 53: Einschränkungen Realplanung!” |
| `abb-54` | ok | 1.0 / 0.95 | \bbildung 54: Unterteilung Ausführungsphase |
| `abb-55` | ok | 0.96 / 1.0 | Abbildung 55: Die SDGs der United Nations |
| `abb-56` | ok | 0.64 / 0.98 | Abbildung 56: Beispiele fir das Spannungsfeld unternehmerischen Wirkens ’“ |
| `abb-57` | ok (Nummer von der OCR verlesen) | 0.0 / 0.98 | Abbildung 37: Einfluss von Effizienz. Konsistenz und Suffizienz auf Aufwand und Ertrag'™"  |
| `abb-58` | ok | 0.99 / 0.97 | Abbildung 58: Möglichkeiten der Industrie zur Dekabonisierung |
| `abb-59` | ok | 0.97 / 0.96 | Abbildung 59: Maßnahmenhierarchie für Materialeifizienz |
| `abb-60` | ok | 0.0 / 0.96 | Abbildung 60: Praduktionsprogrammplanung |
| `abb-61` | ok | 0.95 / 0.95 | Abbildung 61: Beispiele für eine Zeitreihenanalvse (a) und ein Kausalmadell (} |
| `abb-62` | ok | 0.0 / 1.0 | Abbildung 62: Absatzplanung |
| `abb-63` | ok | 0.96 / 1.0 | Abbildung 63: Produktionsprogrammplanung |
| `abb-64` | ok | 0.0 / 1.0 | Abbildung 64: Produktfeld Beispiel |
| `abb-65` | ok | 0.0 / 1.0 | Abbildung 65: Beispiel einer Produktionsprogrammoptimierung |
| `abb-66` | ok | 1.0 / 1.0 | Abbildung 66: Gozintograph |
| `abb-67` | ok | 0.09 / 1.0 | Abbildung 67: Materialbedarfsplanung |
| `abb-68` | ok | 0.0 / 0.93 | Abbildung 68: Materialkdassen |
| `abb-69` | ok | 0.0 / 1.0 | Abbildung 69: Materialbedarf |
| `abb-70` | ok | 0.45 / 1.0 | Abbildung 70: ABC Analyse |
| `abb-71` | ok | 0.6 / 1.0 | Abbildung 71: Zeit- und Kapazitätsplanung |
| `abb-72` | ok | 1.0 / 1.0 | Abbildung 72: Planungsabhängigkeiten |
| `abb-73` | ok | 0.0 / 1.0 | Abbildung 73: Kapazitätsplanung |
| `abb-74` | ok | 1.0 / 0.92 | Abbildung 74: Gesamtanlageneffektivität |
| `abb-75` | ok | 0.0 / 1.0 | Abbildung 75: Enterprise resource planning |
| `abb-76` | ok | 1.0 / 1.0 | Abbildung 76: Planung und Steuerung über die Zeit |
| `abb-77` | ok | 1.0 / 0.95 | Abbildung 7: Produktionssteuerung |
| `abb-78` | ok | 0.98 / 0.59 | \bbildung 78* Produktionmsregelkreis |
| `tab-06` | ok | 0.0 / 1.0 | Tabelle 6: Beispiel Hauptbetriebsdaten |
| `abb-79` | ok | 0.0 / 1.0 | Abbildung 79: Dilemma der Ablaufplanung'** |
| `abb-80` | prüfen | 0.0 / 0.84 | Abbildung So: Dilemma der Ablaufplanung am Bsp. der Maschinenauslastung und Bestand |
| `abb-81` | ok | 0.98 / 0.98 | \bbildung 81: Dilemma der Ablaufplanung am Bsp. der Erhöhung der Kapazitätsanslastung |
| `abb-82` | ok | 0.0 / 0.98 | Abbildung 82: Visualisierung des Dilemmas der Ablaufplanung mit Preduktionskennlinien" |
| `abb-83` | ok | 0.0 / 1.0 | Abbildung 83: Ausgewählte KPIs im operativen Produktionsmanagement |
| `abb-84` | ok | 0.0 / 0.93 | Abbildung 84: Dimensionen der Produkiqualitat |
| `abb-85` | ok | 0.0 / 1.0 | Abbildung 85: Entkopplungspunkte |
| `tab-07` | ok | 0.0 / 0.9 | Tabelle 7: Arten der Flesibilitat |
