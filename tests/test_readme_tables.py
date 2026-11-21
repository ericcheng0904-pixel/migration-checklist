#!/usr/bin/env python3
"""The README tables match the checklist files and the practice catalogs.

A check is a line that starts with "- [ ] " (dash, space, open bracket,
space, close bracket, space). The Checks column is that count from the
linked file. The number is not hardcoded here.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CHECK_PREFIX = "- [ ] "
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
SEPARATOR = re.compile(r"^:?-{3,}:?$")

# Checklist file, then the practice-catalog folders for that row.
PRACTICE = {
    "CHECKLIST.md": (
        "test-catalogs/small-clean",
        "test-catalogs/common-mistakes",
        "test-catalogs/variable-products",
    ),
    "MAGENTO.md": ("test-catalogs/magento-basic",),
    "BIGCOMMERCE.md": ("test-catalogs/bigcommerce-basic",),
    "SQUARESPACE.md": ("test-catalogs/squarespace-basic",),
    "WIX.md": ("test-catalogs/wix-basic",),
}


def count_checks(path: Path) -> int:
    """A check is a line that starts with "- [ ] "."""
    text = path.read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines() if line.startswith(CHECK_PREFIX))


def parse_tables(text: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            current.append(cells)
        elif current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def table_rows(text: str, required: set[str]) -> list[dict[str, str]]:
    for table in parse_tables(text):
        header = table[0]
        if not required <= set(header):
            continue
        rows = []
        for raw in table[1:]:
            if all(SEPARATOR.fullmatch(cell) for cell in raw):
                continue
            if len(raw) != len(header):
                raise AssertionError(f"row {raw} does not match {header}")
            rows.append(dict(zip(header, raw)))
        return rows
    raise AssertionError(f"no table with columns {sorted(required)}")


def link_targets(cell: str) -> list[str]:
    return [target for _label, target in LINK.findall(cell)]


def local_path(url: str) -> Path:
    path = (ROOT / url).resolve()
    path.relative_to(ROOT.resolve())
    return path


class ReadmeTableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = README.read_text(encoding="utf-8")
        self.platforms = table_rows(
            self.readme,
            {"Checklist file", "Checks", "Practice catalog"},
        )
        self.catalogs = table_rows(
            self.readme,
            {"Folder", "Source platform", "What is planted"},
        )

    def test_check_counts_match_the_checklist_files(self) -> None:
        """A check is a line that starts with "- [ ] "."""
        self.assertEqual(
            [link_targets(row["Checklist file"]) for row in self.platforms],
            [[name] for name in PRACTICE],
        )
        for row, (filename, folders) in zip(self.platforms, PRACTICE.items()):
            target = link_targets(row["Checklist file"])[0]
            self.assertEqual(target, filename)
            path = local_path(target)
            self.assertTrue(path.is_file(), target)
            self.assertEqual(int(row["Checks"]), count_checks(path), filename)
            self.assertEqual(tuple(link_targets(row["Practice catalog"])), folders)

    def test_every_practice_catalog_has_a_row_and_every_link_exists(self) -> None:
        disk = {path.name for path in (ROOT / "test-catalogs").iterdir() if path.is_dir()}
        listed = []
        for row in self.catalogs:
            targets = link_targets(row["Folder"])
            self.assertEqual(len(targets), 1, row["Folder"])
            listed.append(Path(targets[0]).name)
            self.assertTrue(row["Source platform"].strip(), targets[0])
            self.assertTrue(row["What is planted"].strip(), targets[0])
        self.assertEqual(listed, [
            "small-clean",
            "common-mistakes",
            "variable-products",
            "magento-basic",
            "bigcommerce-basic",
            "squarespace-basic",
            "wix-basic",
        ])
        self.assertEqual(set(listed), disk)
        self.assertEqual(len(listed), len(disk))
        nothing = next(row for row in self.catalogs if "small-clean" in row["Folder"])
        self.assertEqual(nothing["What is planted"], "nothing; the two files match")

        for row in self.platforms + self.catalogs:
            for cell in row.values():
                for target in link_targets(cell):
                    self.assertFalse(target.startswith(("http://", "https://")), target)
                    path = local_path(target)
                    self.assertTrue(path.is_file() or path.is_dir(), target)


if __name__ == "__main__":
    unittest.main()
