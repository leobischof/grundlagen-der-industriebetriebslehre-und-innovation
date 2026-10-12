"""Local learning-progress CLI: `python -m pipeline.progress <show|record|due|reset>`.

Examples (German UI, see learning/progress/lernfortschritt-anleitung.md):
  python -m pipeline.progress record abb-08 zeichnung 3 --fehler "Achsen vergessen" --skizze ja
  python -m pipeline.progress due
  python -m pipeline.progress show --thema sec-2.5
  python -m pipeline.progress reset --thema abb-08 --ja

The file is personal and git-ignored; an AI tutor reads and writes it through
this CLI (or the same JSON format) – never the committed knowledge base.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import progress_store as store
from .qa_repo import RepoView


def _known_topics() -> set[str]:
    """Ids a topic may refer to; unknown ids are allowed but flagged (typo protection)."""
    view = RepoView()
    ids = {f"sec-{e.section_number}" for e in view.entries} | {f["id"] for f in view.figures}
    ids |= {str(t.get("id")) for t in (view.topic_mapping or {}).get("topics", [])}
    return ids


def _fmt(topic: str, comp: str, item: dict) -> str:
    sketch = {True: " · Skizze selbstständig", False: " · Skizze NICHT selbstständig"}.get(
        item.get("sketch_independent"), "")
    errs = f" · Fehler: {'; '.join(item['errors'])}" if item.get("errors") else ""
    return (f"{item['next_due']}  {topic:<28} {comp:<13} Ergebnis {item['last_result']}/5 · "
            f"{item['mastery_level']} ({item['mastery']:.2f}) · zuletzt {item['last_practiced']}{sketch}{errs}")


def cmd_show(args) -> int:
    rows = store.rows(store.load(args.datei))
    rows = [r for r in rows if not args.thema or r[0] == args.thema]
    if not rows:
        print("Noch keine Übungen gespeichert." if not args.thema else f"Keine Einträge für {args.thema}.")
        return 0
    print("fällig am    Thema                        Kompetenz")
    for row in rows:
        print(_fmt(*row))
    return 0


def cmd_record(args) -> int:
    if args.thema not in _known_topics():
        print(f"Hinweis: '{args.thema}' ist keine bekannte Abschnitts-, Abbildungs- oder Themen-ID "
              f"(trotzdem gespeichert).", file=sys.stderr)
    sketch = {"ja": True, "nein": False, None: None}[args.skizze]
    data = store.load(args.datei)
    try:
        item = store.record(data, args.thema, args.kompetenz, args.ergebnis, args.datum,
                            errors=args.fehler, sketch_independent=sketch)
    except ValueError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2
    store.save(data, args.datei)
    days = item["interval_days"]
    print(f"Gespeichert. Nächste Wiederholung: {item['next_due']} "
          f"(in {days} {'Tag' if days == 1 else 'Tagen'}, {item['mastery_level']}).")
    return 0


def cmd_due(args) -> int:
    rows = store.due(store.load(args.datei), args.datum)
    if not rows:
        print(f"Am {args.datum} ist nichts fällig.")
        return 0
    print(f"{len(rows)} fällige Wiederholungen (älteste zuerst):")
    for row in rows:
        print(_fmt(*row))
    return 0


def cmd_reset(args) -> int:
    if not args.ja:
        what = f"das Thema {args.thema}" if args.thema else "den GESAMTEN Lernfortschritt"
        print(f"Würde {what} löschen. Zum Bestätigen `--ja` anhängen.")
        return 1
    data = store.load(args.datei)
    removed = store.reset(data, args.thema)
    store.save(data, args.datei)
    print(f"{removed} Einträge gelöscht.")
    return 0


def _date(text: str) -> date:
    return date.fromisoformat(text)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m pipeline.progress",
                                description="Lokaler Lernfortschritt mit Wiederholungsplanung (SM-2).")
    p.add_argument("--datei", type=Path, default=store.PROGRESS_FILE,
                   help="Fortschrittsdatei (Standard: learning/progress/progress.json)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="alle Einträge anzeigen")
    s.add_argument("--thema")
    r = sub.add_parser("record", help="eine Übung eintragen")
    r.add_argument("thema", help="z. B. sec-2.5, abb-08 oder eine Themen-ID")
    r.add_argument("kompetenz", choices=store.competencies())
    r.add_argument("ergebnis", type=int, choices=range(6), metavar="ergebnis",
                   help="0 keine Ahnung · 1 falsch · 2 falsch, aber bekannt · 3 mühsam · 4 gut · 5 perfekt")
    r.add_argument("--fehler", action="append", default=[], help="konkreter Fehler (mehrfach möglich)")
    r.add_argument("--skizze", choices=["ja", "nein"], help="nur bei 'zeichnung': selbstständig gezeichnet?")
    r.add_argument("--datum", type=_date, default=date.today(), help="JJJJ-MM-TT (Standard: heute)")
    d = sub.add_parser("due", help="heute fällige Wiederholungen")
    d.add_argument("--datum", type=_date, default=date.today())
    x = sub.add_parser("reset", help="Fortschritt löschen (alles oder ein Thema)")
    x.add_argument("--thema")
    x.add_argument("--ja", action="store_true", help="Löschen bestätigen")
    return p


COMMANDS = {"show": cmd_show, "record": cmd_record, "due": cmd_due, "reset": cmd_reset}


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    return COMMANDS[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
