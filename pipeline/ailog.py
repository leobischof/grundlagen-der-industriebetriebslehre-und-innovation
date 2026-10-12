"""The AI-call log curation/ai-log.jsonl: append one entry, summarise all of them.

The pipeline itself never calls a model. Every *interpretive* step done by an
AI (vision QC of crops, caption transcription, figure descriptions, SVG
reconstruction) is logged here – one JSON line per batch, append-only – so the
token cost of the knowledge base stays visible and a second run can prove it
made no new calls. Token numbers are estimates (no API usage report is
available inside an agent session); images count ≈ 1.6 tokens per 1000 px.

  python -m pipeline.ailog                 # summary
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from . import config

FIELDS = ("date", "stage", "model", "purpose", "inputs", "est_input_tokens", "est_output_tokens", "result")
TOKENS_PER_MEGAPIXEL = 1600


def image_tokens(width: int, height: int) -> int:
    """Rough input-token estimate for one image of width × height pixels."""
    return round(width * height / 1_000_000 * TOKENS_PER_MEGAPIXEL)


def append(entry: dict, path: Path = config.AI_LOG) -> dict:
    """Append one log line; fills `date` with today, rejects incomplete entries."""
    entry = {"date": date.today().isoformat(), **entry}
    missing = [k for k in FIELDS if entry.get(k) in (None, "")]
    if missing:
        raise ValueError(f"KI-Log-Eintrag unvollständig, es fehlt: {', '.join(missing)}")
    for k in ("est_input_tokens", "est_output_tokens"):
        if not isinstance(entry[k], int) or entry[k] < 0:
            raise ValueError(f"{k} muss eine nicht-negative ganze Zahl sein")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({k: entry[k] for k in FIELDS} | {k: v for k, v in entry.items() if k not in FIELDS},
                            ensure_ascii=False) + "\n")
    return entry


def read(path: Path = config.AI_LOG) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def summarize(entries: list[dict]) -> dict:
    """Totals overall and per stage: calls (= log lines), estimated input/output tokens."""
    per_stage: dict[str, dict[str, int]] = defaultdict(lambda: {"calls": 0, "input": 0, "output": 0})
    for e in entries:
        s = per_stage[str(e.get("stage", "?"))]
        s["calls"] += 1
        s["input"] += int(e.get("est_input_tokens") or 0)
        s["output"] += int(e.get("est_output_tokens") or 0)
    total = {k: sum(s[k] for s in per_stage.values()) for k in ("calls", "input", "output")}
    dates = sorted(str(e.get("date")) for e in entries if e.get("date"))
    return {"total": total, "per_stage": dict(per_stage),
            "first": dates[0] if dates else None, "last": dates[-1] if dates else None}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    s = summarize(read())
    t = s["total"]
    print(f"KI-Aufrufe: {t['calls']} · geschätzte Tokens: {t['input']:,} Eingabe / {t['output']:,} Ausgabe"
          .replace(",", "."))
    for stage, v in sorted(s["per_stage"].items()):
        print(f"  {stage:<28} {v['calls']:>3} Aufrufe  {v['input']:>8} / {v['output']:>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
