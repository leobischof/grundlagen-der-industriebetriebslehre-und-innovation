"""Findings of the quality checks: one record per problem, rendered as German Markdown.

Every check module returns a list of `Finding`s instead of printing. That keeps
the checks pure (testable on a fixture tree) and lets `validate` decide about
the exit code: any ERROR fails the run, WARNINGs are reported but never fail it,
INFO lines only document what was not checkable yet.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

ERROR = "Fehler"
WARNING = "Warnung"
INFO = "Hinweis"
SEVERITY_ORDER = (ERROR, WARNING, INFO)
HEADINGS = {ERROR: "Fehler", WARNING: "Warnungen", INFO: "Hinweise"}


@dataclass(frozen=True)
class Finding:
    severity: str          # ERROR | WARNING | INFO
    check: str             # German name of the check group, e.g. "Abbildungen"
    message: str           # German, one line, names the file/id concerned

    def line(self) -> str:
        return f"- {self.message}"


def error(check: str, message: str) -> Finding:
    return Finding(ERROR, check, message)


def warning(check: str, message: str) -> Finding:
    return Finding(WARNING, check, message)


def info(check: str, message: str) -> Finding:
    return Finding(INFO, check, message)


def count(findings: list[Finding], severity: str) -> int:
    return sum(1 for f in findings if f.severity == severity)


def render(findings: list[Finding], checks_run: list[str]) -> str:
    """Markdown report: summary table, then findings grouped by severity and check."""
    errors, warnings = count(findings, ERROR), count(findings, WARNING)
    verdict = "**Ergebnis: bestanden**" if errors == 0 else "**Ergebnis: NICHT bestanden**"
    out = [
        "# Validierungsbericht",
        "",
        "Generiert von `python -m pipeline validate` – nicht von Hand bearbeiten. Prüft nur "
        "versionierte Dateien (keine PDFs, keine OCR, keine KI) und läuft deshalb auch in der CI.",
        "",
        f"{verdict} – {errors} Fehler, {warnings} Warnungen, {count(findings, INFO)} Hinweise.",
        "",
        "Fehler lassen den Lauf scheitern (Exit-Code 1); Warnungen und Hinweise nicht.",
        "",
        "| Prüfung | Fehler | Warnungen | Hinweise |",
        "|---|---:|---:|---:|",
    ]
    per_check: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for f in findings:
        per_check[f.check][f.severity] += 1
    for name in checks_run:
        c = per_check.get(name, {})
        out.append(f"| {name} | {c.get(ERROR, 0)} | {c.get(WARNING, 0)} | {c.get(INFO, 0)} |")
    for severity in SEVERITY_ORDER:
        group = [f for f in findings if f.severity == severity]
        if not group:
            continue
        out += ["", f"## {HEADINGS[severity]}", ""]
        for name in checks_run:
            lines = [f.line() for f in group if f.check == name]
            if lines:
                out += [f"### {name}", "", *lines, ""]
    return "\n".join(out).rstrip() + "\n"
