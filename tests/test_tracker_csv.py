#!/usr/bin/env python3
"""Tracker CSV files match the checklist Markdown.

A check is a line that starts with "- [ ] ". The script file name has a
hyphen, so this module loads it with importlib and also runs it with
subprocess into a temporary directory.
"""

from __future__ import annotations

import csv
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "make-tracker-csv.py"
TRACKER = ROOT / "tracker-import"
CHECK_PREFIX = "- [ ] "
HEADING_PREFIX = "## "
BITE_MARKER = " Why it bites:"
FORMULA_PREFIXES = ("=", "+", "-", "@")
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
TRAILING_LINKS = re.compile(r"(?:[ \t]*\[[^\]]*\]\([^)\s]+\))+[ \t]*$")

PLATFORMS = (
    ("CHECKLIST.md", "woocommerce.csv"),
    ("MAGENTO.md", "magento.csv"),
    ("BIGCOMMERCE.md", "bigcommerce.csv"),
    ("SQUARESPACE.md", "squarespace.csv"),
    ("WIX.md", "wix.csv"),
    ("SPOT-CHECKS.md", "spot-checks.csv"),
)


def load_script():
    spec = importlib.util.spec_from_file_location("make_tracker_csv", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["make_tracker_csv"] = module
    spec.loader.exec_module(module)
    return module


def count_checks(path: Path) -> int:
    """A check is a line that starts with "- [ ] "."""
    text = path.read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines() if line.startswith(CHECK_PREFIX))


def guard_cell(value: str) -> str:
    if value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def expected_rows(path: Path) -> list[dict[str, str]]:
    """Independent reading of the mapping rules, not the generator."""
    phase = ""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(HEADING_PREFIX):
            phase = line[len(HEADING_PREFIX) :].strip()
            continue
        if not line.startswith(CHECK_PREFIX):
            continue
        body = line[len(CHECK_PREFIX) :]
        trailing = TRAILING_LINKS.search(body)
        if trailing:
            urls = [match.group(2) for match in LINK.finditer(trailing.group(0))]
            body = body[: trailing.start()].rstrip(" \t")
        else:
            urls = []
        check, rest = body.split(BITE_MARKER, 1)
        details = "Why it bites:" + rest
        rows.append(
            {
                "Phase": guard_cell(phase),
                "Check": guard_cell(check),
                "Details": guard_cell(details),
                "Source": guard_cell(" ".join(urls)),
            }
        )
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["Phase", "Check", "Details", "Source"]:
            raise AssertionError(f"{path.name} header is {reader.fieldnames}")
        return list(reader)


mod = load_script()


class TrackerCsvTests(unittest.TestCase):
    def test_row_count_matches_checks_and_check_text_is_present(self) -> None:
        """A check is a line that starts with "- [ ] "."""
        for source_name, csv_name in PLATFORMS:
            path = TRACKER / csv_name
            rows = read_csv(path)
            self.assertEqual(len(rows), count_checks(ROOT / source_name), csv_name)
            self.assertEqual(rows, expected_rows(ROOT / source_name), csv_name)
            for row in rows:
                self.assertTrue(row["Check"], csv_name)
                self.assertTrue(row["Phase"], csv_name)
                self.assertTrue(row["Details"].startswith("Why it bites:"), csv_name)
                for part in row["Source"].split(" ") if row["Source"] else []:
                    self.assertTrue(part, csv_name)
                    self.assertNotIn("[", part, csv_name)

    def test_known_rows_keep_inline_links_and_trailing_urls(self) -> None:
        woo = read_csv(TRACKER / "woocommerce.csv")
        freeze = woo[0]
        self.assertEqual(freeze["Phase"], "Before you start")
        self.assertEqual(
            freeze["Check"],
            "Freeze product edits, then take the WooCommerce product CSV you will actually import.",
        )
        self.assertEqual(
            freeze["Details"],
            "Why it bites: a product changed after that export is absent from every later comparison.",
        )
        self.assertEqual(freeze["Source"], "")

        recount = next(row for row in woo if "SPOT-CHECKS.md" in row["Check"])
        self.assertEqual(recount["Phase"], "The first week")
        self.assertIn("Use [SPOT-CHECKS.md](SPOT-CHECKS.md).", recount["Check"])
        self.assertEqual(recount["Source"], "")
        self.assertTrue(recount["Details"].startswith("Why it bites:"))

        magento = read_csv(TRACKER / "magento.csv")
        variation = next(row for row in magento if row["Check"].startswith("Recount simple variation SKUs"))
        self.assertIn("[test-catalogs/magento-basic](test-catalogs/magento-basic)", variation["Check"])
        self.assertEqual(
            variation["Source"],
            "https://experienceleague.adobe.com/en/docs/commerce-admin/systems/data-transfer/examples/data-transfer-configurable-products "
            "https://help.shopify.com/en/manual/migrating-to-shopify",
        )
        self.assertNotIn("http", variation["Details"])

        bigcommerce = read_csv(TRACKER / "bigcommerce.csv")
        quoted = "Type in Product for products, SKU for variants, and Rule for variant or modifier rules."
        self.assertTrue(any(quoted in row["Details"] for row in bigcommerce))

        wix = read_csv(TRACKER / "wix.csv")
        paths = next(row for row in wix if row["Check"].startswith("Recount variants, and recount the old product paths."))
        self.assertEqual(
            paths["Source"],
            "WIX.md https://help.shopify.com/en/manual/online-store/menus-and-links/url-redirect",
        )

    def test_files_are_utf8_without_bom_and_match_a_fresh_run(self) -> None:
        first = Path(tempfile.mkdtemp())
        second = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, first, ignore_errors=True)
        self.addCleanup(shutil.rmtree, second, ignore_errors=True)
        command = [sys.executable, str(SCRIPT)]
        subprocess.run([*command, str(first)], check=True, cwd=ROOT)
        subprocess.run([*command, str(second)], check=True, cwd=ROOT)
        names = [csv_name for _source, csv_name in PLATFORMS]
        self.assertEqual(sorted(path.name for path in TRACKER.glob("*.csv")), sorted(names))
        for name in names:
            committed = (TRACKER / name).read_bytes()
            self.assertFalse(committed.startswith(b"\xef\xbb\xbf"), name)
            self.assertNotIn(b"\r", committed, name)
            committed.decode("utf-8")
            self.assertTrue(committed.endswith(b"\n"), name)
            self.assertEqual(committed, (first / name).read_bytes(), name)
            self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(), name)
            for row in read_csv(TRACKER / name):
                for cell in row.values():
                    self.assertFalse(cell.startswith(FORMULA_PREFIXES), cell[:40])

    def test_formula_prefix_is_written_into_the_cell(self) -> None:
        self.assertEqual(mod.guard_cell("=1+1"), "'=1+1")
        self.assertEqual(mod.guard_cell("+1"), "'+1")
        self.assertEqual(mod.guard_cell("-1"), "'-1")
        self.assertEqual(mod.guard_cell("@sum"), "'@sum")
        self.assertEqual(mod.guard_cell("Price"), "Price")
        self.assertEqual(mod.guard_cell(""), "")
        self.assertEqual(mod.guard_cell(" =1"), " =1")
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / "formula.csv"
        mod.write_csv(path, [("=phase", "Check", "Details", "@https://example.test")])
        data = path.read_bytes()
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", data)
        rows = read_csv(path)
        self.assertEqual(rows[0]["Phase"], "'=phase")
        self.assertEqual(rows[0]["Check"], "Check")
        self.assertEqual(rows[0]["Source"], "'@https://example.test")


if __name__ == "__main__":
    unittest.main()
