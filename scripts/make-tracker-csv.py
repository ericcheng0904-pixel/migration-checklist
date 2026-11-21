#!/usr/bin/env python3
"""Write tracker-import CSV files from the checklist Markdown.

Run from anywhere:

    python3 scripts/make-tracker-csv.py
    python3 scripts/make-tracker-csv.py OUTDIR

With no argument the six files are written to tracker-import/ in this
repository. OUTDIR, when given, receives the same six file names.

A check is a line that starts with "- [ ] ". Phase is the nearest preceding
"## " heading. Trailing Markdown links are removed from the text and their
URLs are written in Source, separated by spaces. Check is the text before
" Why it bites:". Details is "Why it bites: ..." with those links removed.
The text is not reworded.

Output is UTF-8 with LF line endings and no byte-order mark, so a second run
matches the first byte for byte. A cell that begins with "=", "+", "-", or
"@" is prefixed with a single quote.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "tracker-import"

# Checklist file, then the CSV name under tracker-import/.
PLATFORMS = (
    ("CHECKLIST.md", "woocommerce.csv"),
    ("MAGENTO.md", "magento.csv"),
    ("BIGCOMMERCE.md", "bigcommerce.csv"),
    ("SQUARESPACE.md", "squarespace.csv"),
    ("WIX.md", "wix.csv"),
    ("SPOT-CHECKS.md", "spot-checks.csv"),
)

COLUMNS = ("Phase", "Check", "Details", "Source")
CHECK_PREFIX = "- [ ] "
HEADING_PREFIX = "## "
BITE_MARKER = " Why it bites:"
FORMULA_PREFIXES = ("=", "+", "-", "@")

# One Markdown link. URLs in these checklists have no spaces or parentheses.
_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
# One or more links at the end of the line, with spaces between them.
_TRAILING_LINKS = re.compile(r"(?:[ \t]*\[[^\]]*\]\([^)\s]+\))+[ \t]*$")


def guard_cell(value: str) -> str:
    """Prefix a formula-like cell so a spreadsheet treats it as text."""
    if value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def parse_checklist(text: str, name: str) -> list[tuple[str, str, str, str]]:
    """Return (phase, check, details, source) in source order."""
    phase = ""
    rows: list[tuple[str, str, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.startswith(HEADING_PREFIX):
            phase = line[len(HEADING_PREFIX) :].strip()
            continue
        if not line.startswith(CHECK_PREFIX):
            continue
        if not phase:
            raise SystemExit(f"{name}:{lineno}: check before any ## heading")
        body = line[len(CHECK_PREFIX) :]
        trailing = _TRAILING_LINKS.search(body)
        if trailing:
            urls = [match.group(2) for match in _LINK.finditer(trailing.group(0))]
            body = body[: trailing.start()].rstrip(" \t")
        else:
            urls = []
        if BITE_MARKER not in body:
            raise SystemExit(f"{name}:{lineno}: check has no {BITE_MARKER!r}")
        check, rest = body.split(BITE_MARKER, 1)
        details = "Why it bites:" + rest
        rows.append((phase, check, details, " ".join(urls)))
    if not rows:
        raise SystemExit(f"{name}: no checks found")
    return rows


def write_csv(path: Path, rows: list[tuple[str, str, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([guard_cell(column) for column in COLUMNS])
        for row in rows:
            writer.writerow([guard_cell(cell) for cell in row])


def write_tracker(out_dir: Path, root: Path | None = None) -> None:
    root = ROOT if root is None else root
    for source_name, csv_name in PLATFORMS:
        text = (root / source_name).read_text(encoding="utf-8")
        write_csv(out_dir / csv_name, parse_checklist(text, source_name))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        print("Usage: python3 scripts/make-tracker-csv.py [OUTDIR]", file=sys.stderr)
        return 2
    if args:
        out_dir = Path(args[0])
        if not out_dir.is_absolute():
            out_dir = Path.cwd() / out_dir
    else:
        out_dir = DEFAULT_OUT
    write_tracker(out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
